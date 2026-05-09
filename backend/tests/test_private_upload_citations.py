from app.ai_runtime.runtime.response_formatter import _extract_citations
from app.ai_runtime.schemas.tool import ToolResult


def test_private_upload_citation_keeps_file_locator_fields() -> None:
    citations = _extract_citations(
        [
            ToolResult(
                name="session_file_search",
                status="success",
                output={
                    "hits": [
                        {
                            "doc_id": "file-001",
                            "knowledge_item_id": "file-001",
                            "title": "电费账单.pdf",
                            "source_type": "private_upload",
                            "source": "用户上传知识",
                            "snippet": "第 2 页显示用电量为 1200 kWh。",
                            "chunk_id": "chunk-upload",
                            "library_scope": "personal",
                            "file_id": "file-001",
                            "page_number": 2,
                            "sheet_name": None,
                            "slide_number": None,
                            "section_title": "电量明细",
                        }
                    ]
                },
                metadata={},
            )
        ]
    )

    assert citations[0]["source_type"] == "private_upload"
    assert citations[0]["file_id"] == "file-001"
    assert citations[0]["page_number"] == 2
    assert citations[0]["section_title"] == "电量明细"
