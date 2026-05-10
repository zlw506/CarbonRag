from types import SimpleNamespace
from datetime import datetime, timezone

from app.rag.embeddings import RagEmbeddingUnavailable
from app.rag.kb.models import KnowledgeBaseCreate, RagDocumentCreate, RagSearchRequest
from app.rag.kb.storage import RagKnowledgeStore
from app.rag.spine import RagSpineService


def test_milvus_bge_unavailable_does_not_mark_fake_success(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.rag.spine.get_settings", lambda: SimpleNamespace(rag_vector_backend="milvus_lite"))
    monkeypatch.setattr(
        "app.rag.kb.storage.embed_documents",
        lambda _texts: (_ for _ in ()).throw(RagEmbeddingUnavailable("BGE-M3 unavailable in test")),
    )
    store = RagKnowledgeStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3")
    _insert_user(store, "user-1")
    service = RagSpineService(store=store)
    kb = service.create_kb(owner_user_id="user-1", payload=KnowledgeBaseCreate(name="真实向量失败测试"))
    doc = service.create_document(
        owner_user_id="user-1",
        kb_id=kb.kb_id,
        payload=RagDocumentCreate(title="测试文档", text="双碳目标包括碳达峰和碳中和。"),
    )

    service.parse_document(owner_user_id="user-1", kb_id=kb.kb_id, doc_id=doc.doc_id)
    service.chunk_document(owner_user_id="user-1", kb_id=kb.kb_id, doc_id=doc.doc_id)
    indexed = service.index_document(owner_user_id="user-1", kb_id=kb.kb_id, doc_id=doc.doc_id)

    assert indexed.status == "failed"
    assert indexed.index_status == "failed"
    assert indexed.vector_backend == "milvus_lite"
    assert indexed.degraded is True
    assert "BGE-M3 unavailable" in (indexed.error_message or "")


def test_memory_backend_remains_explicit_dev_fallback(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.rag.spine.get_settings", lambda: SimpleNamespace(rag_vector_backend="memory"))
    store = RagKnowledgeStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3")
    _insert_user(store, "user-1")
    service = RagSpineService(store=store)
    kb = service.create_kb(owner_user_id="user-1", payload=KnowledgeBaseCreate(name="开发 fallback 测试"))
    doc = service.create_document(
        owner_user_id="user-1",
        kb_id=kb.kb_id,
        payload=RagDocumentCreate(title="测试文档", text="企业应建立能源数据台账，记录用电量和燃气量。"),
    )

    service.parse_document(owner_user_id="user-1", kb_id=kb.kb_id, doc_id=doc.doc_id)
    service.chunk_document(owner_user_id="user-1", kb_id=kb.kb_id, doc_id=doc.doc_id)
    indexed = service.index_document(owner_user_id="user-1", kb_id=kb.kb_id, doc_id=doc.doc_id)

    assert indexed.status == "indexed"
    assert indexed.vector_backend == "memory"
    result = service.search(
        owner_user_id="user-1",
        request=RagSearchRequest(query="能源数据台账", kb_id=kb.kb_id, mode="hybrid", top_k=3),
    )
    assert result.hits
    assert result.trace.vector_backend == "memory"


def _insert_user(store: RagKnowledgeStore, user_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    store._execute(
        """
        INSERT INTO users (user_id, username, password_hash, role, is_active, password_must_change, created_at, updated_at)
        VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
        """,
        [user_id, user_id, "hash", "user", True, False, now, now],
    )
