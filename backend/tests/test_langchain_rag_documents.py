from datetime import datetime, timezone

from app.knowledge.schemas import KnowledgeChunk, KnowledgeItem
from app.langchain_rag.documents import load_visible_documents


class FakeKnowledgeService:
    def list_admin_items(self, **kwargs):
        return []

    def list_visible_items(self, *, owner_user_id: str, filters):
        assert owner_user_id == "user-1"
        assert filters.knowledge_item_ids == ["ki-upload"]
        return [
            KnowledgeItem(
                knowledge_item_id="ki-upload",
                owner_user_id="user-1",
                library_scope="personal",
                source_type="uploaded_file",
                source_ref="file-1",
                file_id="file-1",
                title="电费账单.xlsx",
                mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                storage_path="uploads/file-1.xlsx",
                parse_status="parsed",
                ingest_status="ingested",
                index_status="indexed",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        ]

    def list_chunks(self, *, knowledge_item_ids: list[str]):
        assert knowledge_item_ids == ["ki-upload"]
        return [
            KnowledgeChunk(
                chunk_id="chunk-sheet",
                knowledge_item_id="ki-upload",
                owner_user_id="user-1",
                visibility="private",
                title="电费账单.xlsx",
                source_type="private_upload",
                library_scope="personal",
                source="上传文件",
                source_url=None,
                snippet="2026 年 1 月用电量 12000 kWh。",
                order_index=0,
                metadata={"sheet_name": "2026-01", "section_title": "电费"},
            )
        ]


def test_visible_upload_chunks_convert_to_langchain_documents(monkeypatch) -> None:
    monkeypatch.setattr("app.langchain_rag.documents.get_knowledge_service", lambda: FakeKnowledgeService())

    documents = load_visible_documents(
        owner_user_id="user-1",
        knowledge_scope="private_sample",
        allowed_knowledge_item_ids=["ki-upload"],
    )

    assert len(documents) == 1
    assert documents[0].page_content == "2026 年 1 月用电量 12000 kWh。"
    assert documents[0].metadata["file_id"] == "file-1"
    assert documents[0].metadata["source_type"] == "private_upload"
    assert documents[0].metadata["sheet_name"] == "2026-01"
