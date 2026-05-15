from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.knowledge.policy_ingestion import CrawledDocument, FakeCrawlerProvider
from app.knowledge.policy_live_crawler import PolicyCrawlerScheduler, PolicyCrawlerStore
from app.rag.kb.crawler_bridge import publish_crawled_candidate_to_rag_kb
from app.rag.kb.models import KnowledgeBase, RagPipelineResult
from app.core.config import Settings


def test_policy_candidate_publish_to_rag_kb(monkeypatch, tmp_path) -> None:
    scheduler = _seed_scheduler_with_candidate(tmp_path)
    candidate = scheduler.list_candidates()[0]
    fake_service = _FakeRagService()
    monkeypatch.setattr("app.rag.kb.crawler_bridge.get_policy_crawler_scheduler", lambda: scheduler)

    result = publish_crawled_candidate_to_rag_kb(
        candidate_id=candidate.candidate_id,
        reviewed_by_user_id=None,
        rag_service=fake_service,
    )
    refreshed = scheduler.store.get_candidate(candidate.candidate_id)

    assert result.failed_stage is None
    assert fake_service.created_documents[0]["kb_id"] == "kb-policy-auto"
    assert fake_service.created_documents[0]["payload"].source_type == "public_policy"
    assert fake_service.created_documents[0]["payload"].file_path.endswith("document.md")
    assert refreshed is not None
    assert refreshed.status == "published"
    assert refreshed.metadata["rag_kb_id"] == "kb-policy-auto"
    assert refreshed.metadata["rag_doc_id"] == "rag-doc-policy"
    assert refreshed.metadata["rag_pipeline_status"] == "indexed"
    assert refreshed.metadata["rag_search_smoke_passed"] is True
    assert refreshed.metadata["rag_indexed_chunk_count"] == 3


def test_crawler_publish_runs_rag_quick_pipeline(monkeypatch, tmp_path) -> None:
    scheduler = _seed_scheduler_with_candidate(tmp_path)
    candidate = scheduler.list_candidates()[0]
    fake_service = _FakeRagService()
    monkeypatch.setattr("app.rag.kb.crawler_bridge.get_policy_crawler_scheduler", lambda: scheduler)

    publish_crawled_candidate_to_rag_kb(
        candidate_id=candidate.candidate_id,
        reviewed_by_user_id=None,
        rag_service=fake_service,
    )

    assert fake_service.pipeline_calls == [
        {
            "owner_user_id": "system-policy-crawler",
            "kb_id": "kb-policy-auto",
            "doc_id": "rag-doc-policy",
            "pipeline_mode": "quick",
        }
    ]


def test_crawler_search_after_publish(monkeypatch, tmp_path) -> None:
    scheduler = _seed_scheduler_with_candidate(tmp_path)
    candidate = scheduler.list_candidates()[0]
    fake_service = _FakeRagService()
    monkeypatch.setattr("app.rag.kb.crawler_bridge.get_policy_crawler_scheduler", lambda: scheduler)

    publish_crawled_candidate_to_rag_kb(
        candidate_id=candidate.candidate_id,
        reviewed_by_user_id=None,
        rag_service=fake_service,
    )

    refreshed = scheduler.store.get_candidate(candidate.candidate_id)
    assert refreshed is not None
    assert refreshed.metadata["rag_search_smoke_passed"] is True


def test_low_quality_candidate_cannot_publish_to_rag(monkeypatch, tmp_path) -> None:
    scheduler = _seed_scheduler_with_candidate(tmp_path)
    candidate = scheduler.list_candidates()[0]
    scheduler.store.update_candidate_review(
        candidate_id=candidate.candidate_id,
        status="pending_review",
        reviewed_by_user_id=None,
        metadata={"candidate_quality_score": 42},
    )
    monkeypatch.setattr("app.rag.kb.crawler_bridge.get_policy_crawler_scheduler", lambda: scheduler)

    with pytest.raises(ValueError, match="below 60"):
        publish_crawled_candidate_to_rag_kb(
            candidate_id=candidate.candidate_id,
            reviewed_by_user_id=None,
            rag_service=_FakeRagService(),
        )


def test_publish_to_rag_requires_non_empty_markdown(monkeypatch, tmp_path) -> None:
    scheduler = _seed_scheduler_with_candidate(tmp_path)
    candidate = scheduler.list_candidates()[0]
    scheduler.store.update_candidate_review(
        candidate_id=candidate.candidate_id,
        status="pending_review",
        reviewed_by_user_id=None,
        metadata={
            "candidate_quality_score": 90,
            "extraction_quality_score": 90,
            "markdown_size": 20,
            "cleaned_size": 20,
            "estimated_chunk_count": 1,
        },
    )
    monkeypatch.setattr("app.rag.kb.crawler_bridge.get_policy_crawler_scheduler", lambda: scheduler)

    with pytest.raises(ValueError, match="empty_extraction"):
        publish_crawled_candidate_to_rag_kb(
            candidate_id=candidate.candidate_id,
            reviewed_by_user_id=None,
            rag_service=_FakeRagService(),
        )


def test_publish_to_rag_requires_indexed_chunks(monkeypatch, tmp_path) -> None:
    scheduler = _seed_scheduler_with_candidate(tmp_path)
    candidate = scheduler.list_candidates()[0]
    fake_service = _FakeRagService(indexed_chunk_count=0, chunk_count=3, search_smoke_passed=True)
    monkeypatch.setattr("app.rag.kb.crawler_bridge.get_policy_crawler_scheduler", lambda: scheduler)

    with pytest.raises(ValueError, match="index_failed"):
        publish_crawled_candidate_to_rag_kb(
            candidate_id=candidate.candidate_id,
            reviewed_by_user_id=None,
            rag_service=fake_service,
        )

    refreshed = scheduler.store.get_candidate(candidate.candidate_id)
    assert refreshed is not None
    assert refreshed.status == "pending_review"
    assert refreshed.metadata["rag_pipeline_status"] == "failed"
    assert refreshed.metadata["rag_error_stage"] == "index_failed"


def test_policy_crawler_local_scrapy_smoke(tmp_path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "crawler" / "gov_cn_policy_fixture.html"
    document = CrawledDocument(
        url="https://www.gov.cn/zhengce/gov-cn-policy-fixture.html",
        title="国务院关于碳达峰政策的测试文件",
        content=fixture.read_text(encoding="utf-8"),
        content_type="text/html",
        source_name="中国政府网",
    )
    scheduler = _build_scheduler(tmp_path, provider=FakeCrawlerProvider(documents=[document]))

    run = scheduler.run_source_now(source_id="gov-cn-policy-library", triggered_by_user_id=None)
    candidates = scheduler.list_candidates()

    assert run.status == "succeeded"
    assert run.candidate_count == 1
    assert candidates[0].metadata["matched_policy_keywords"]
    assert "碳达峰" in Path(candidates[0].metadata["markdown_storage_path"]).read_text(encoding="utf-8")


def _seed_scheduler_with_candidate(tmp_path) -> PolicyCrawlerScheduler:
    body = "本文件要求推进碳达峰和碳中和，完善节能降碳、碳排放核算、温室气体管理和绿色低碳服务体系。" * 35
    document = CrawledDocument(
        url="https://www.gov.cn/zhengce/rag-publish-policy.html",
        title="国务院碳达峰政策测试文件",
        content=f"<html><body><h1>碳达峰政策</h1><p>{body}</p></body></html>",
        content_type="text/html",
        source_name="中国政府网",
    )
    scheduler = _build_scheduler(tmp_path, provider=FakeCrawlerProvider(documents=[document]))
    scheduler.run_source_now(source_id="gov-cn-policy-library", triggered_by_user_id=None)
    return scheduler


def _build_scheduler(tmp_path, *, provider) -> PolicyCrawlerScheduler:
    store = PolicyCrawlerStore(sqlite_db_path=tmp_path / "carbonrag.sqlite3")
    store.seed_default_sources()
    return PolicyCrawlerScheduler(
        store=store,
        provider=provider,
        settings=Settings(
            public_data_dir=str(tmp_path / "public"),
            rag_policy_live_crawler_scheduled_enabled=False,
            rag_policy_live_crawler_auto_publish=False,
        ),
        candidate_dir=tmp_path / "public" / "policy_crawl_candidates",
    )


class _FakeRagService:
    def __init__(self, *, indexed_chunk_count: int = 3, chunk_count: int = 3, search_smoke_passed: bool = True) -> None:
        now = datetime.now(timezone.utc)
        self.indexed_chunk_count = indexed_chunk_count
        self.chunk_count = chunk_count
        self.search_smoke_passed = search_smoke_passed
        self.kb = KnowledgeBase(
            kb_id="kb-policy-auto",
            owner_user_id="admin-1",
            name="官方政策自动更新库",
            description=None,
            visibility="shared",
            retrieval_mode="hybrid_rerank",
            created_at=now,
            updated_at=now,
        )
        self.created_documents = []
        self.pipeline_calls = []

    def list_kbs(self, *, owner_user_id: str):
        del owner_user_id
        return [self.kb]

    def create_kb(self, *, owner_user_id: str, payload):
        del owner_user_id, payload
        return self.kb

    def create_document(self, *, owner_user_id: str, kb_id: str, payload):
        self.created_documents.append({"owner_user_id": owner_user_id, "kb_id": kb_id, "payload": payload})
        return SimpleNamespace(doc_id="rag-doc-policy")

    def run_document_pipeline(self, *, owner_user_id: str, kb_id: str, doc_id: str, pipeline_mode: str):
        self.pipeline_calls.append(
            {
                "owner_user_id": owner_user_id,
                "kb_id": kb_id,
                "doc_id": doc_id,
                "pipeline_mode": pipeline_mode,
            }
        )
        return RagPipelineResult(
            doc_id=doc_id,
            pipeline_mode="quick",
            parse_status="parsed",
            chunk_status="chunked",
            index_status="indexed",
            chunk_count=self.chunk_count,
            indexed_chunk_count=self.indexed_chunk_count,
            vector_runtime="memory_dev",
            degraded=False,
            search_smoke_passed=self.search_smoke_passed,
        )
