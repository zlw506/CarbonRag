from datetime import datetime, timezone

from app.files.parser.chunker import build_file_chunks
from app.files.parser.models import ParsedFileChunkMeta, ParsedFileResult
from app.knowledge.schemas import KnowledgeItem


def test_file_chunking_preserves_file_locator_metadata() -> None:
    now = datetime.now(timezone.utc)
    item = KnowledgeItem(
        knowledge_item_id="file-001",
        owner_user_id="user-001",
        library_scope="personal",
        source_type="uploaded_file",
        source_ref="file-001",
        file_id="file-001",
        source="用户上传知识",
        title="电费账单.pdf",
        mime_type="application/pdf",
        storage_path="/tmp/file-001.pdf",
        parse_status="parsed",
        ingest_status="ingested",
        index_status="indexed",
        created_at=now,
        updated_at=now,
    )
    parsed = ParsedFileResult(
        text="第 2 页显示用电量为 1200 kWh。\n\n企业应按外购电力因子核算 Scope 2。",
        markdown="第 2 页显示用电量为 1200 kWh。",
        parser_name="docling",
        parser_version="1.0",
        page_count=2,
        summary="用电量 1200 kWh",
        chunk_metadata=[ParsedFileChunkMeta(page_number=2, section_title="电量明细")],
    )

    chunks = build_file_chunks(item=item, parsed=parsed, created_at=now)

    assert chunks
    assert chunks[0].metadata["file_id"] == "file-001"
    assert chunks[0].metadata["parser_name"] == "docling"
    assert chunks[0].metadata["page_number"] == 2
    assert chunks[0].metadata["section_title"] == "电量明细"
