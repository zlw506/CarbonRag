from pydantic import BaseModel, Field


class ParsedFileChunkMeta(BaseModel):
    page_number: int | None = None
    sheet_name: str | None = None
    slide_number: int | None = None
    section_title: str | None = None


class ParsedFileResult(BaseModel):
    text: str
    markdown: str | None = None
    parser_name: str
    parser_version: str | None = None
    ocr_used: bool = False
    page_count: int | None = None
    sheet_count: int | None = None
    slide_count: int | None = None
    summary: str | None = None
    chunk_metadata: list[ParsedFileChunkMeta] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
