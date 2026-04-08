import csv
import io
import re

from app.retrieval.private_schemas import PrivateSampleDocument
from app.retrieval.schemas import RetrievedChunk

MIN_CHUNK_LENGTH = 80
MAX_CHUNK_LENGTH = 420
SENTENCE_BREAK_PATTERN = re.compile(r"(?<=[。！？；])")


def _normalize_paragraphs(body: str) -> list[str]:
    paragraphs = []
    for segment in re.split(r"\r?\n\s*\r?\n", body):
        paragraph = " ".join(segment.strip().split())
        if paragraph:
            paragraphs.append(paragraph)
    return paragraphs


def _split_large_paragraph(paragraph: str) -> list[str]:
    if len(paragraph) <= MAX_CHUNK_LENGTH:
        return [paragraph]

    sentences = [fragment.strip() for fragment in SENTENCE_BREAK_PATTERN.split(paragraph) if fragment.strip()]
    if not sentences:
        return [paragraph]

    parts: list[str] = []
    buffer = ""
    for sentence in sentences:
        candidate = f"{buffer}{sentence}"
        if buffer and len(candidate) > MAX_CHUNK_LENGTH:
            parts.append(buffer.strip())
            buffer = sentence
        else:
            buffer = candidate
    if buffer:
        parts.append(buffer.strip())
    return parts


def _chunk_markdown(document: PrivateSampleDocument) -> list[RetrievedChunk]:
    metadata = document.metadata
    raw_paragraphs = _normalize_paragraphs(document.body)
    normalized_paragraphs: list[str] = []
    for paragraph in raw_paragraphs:
        normalized_paragraphs.extend(_split_large_paragraph(paragraph))

    chunks: list[str] = []
    buffer = ""
    for paragraph in normalized_paragraphs:
        if not buffer:
            buffer = paragraph
            continue

        candidate = f"{buffer}\n\n{paragraph}"
        if len(candidate) <= MAX_CHUNK_LENGTH:
            buffer = candidate
            continue

        chunks.append(buffer)
        buffer = paragraph

    if buffer:
        chunks.append(buffer)

    result: list[RetrievedChunk] = []
    for index, chunk in enumerate(chunks, start=1):
        result.append(
            RetrievedChunk(
                doc_id=metadata.doc_id,
                title=metadata.title,
                source_type="private_sample",
                source="脱敏企业样例",
                source_url=None,
                sample_type=metadata.sample_type,
                business_topic=metadata.business_topic,
                chunk_id=f"{metadata.doc_id}_chunk_{index:02d}",
                snippet=chunk,
                score=0.0,
            )
        )
    return result


def _chunk_csv(document: PrivateSampleDocument) -> list[RetrievedChunk]:
    metadata = document.metadata
    csv_text = io.StringIO(document.body)
    rows: list[dict[str, str]] = []
    for line in csv_text.getvalue().splitlines():
        if not line.strip():
            continue
        if line.startswith("样例表《"):
            continue
        if not line.startswith("第 "):
            continue
        _, content = line.split("：", 1)
        row: dict[str, str] = {}
        for cell in content.split("；"):
            if "=" not in cell:
                continue
            key, value = cell.split("=", 1)
            row[key] = value
        if row:
            rows.append(row)

    result: list[RetrievedChunk] = []
    for index, row in enumerate(rows, start=1):
        description = "；".join(f"{key}={value}" for key, value in row.items())
        snippet = f"脱敏样例表《{metadata.title}》第 {index} 行：{description}"
        result.append(
            RetrievedChunk(
                doc_id=metadata.doc_id,
                title=metadata.title,
                source_type="private_sample",
                source="脱敏企业样例",
                source_url=None,
                sample_type=metadata.sample_type,
                business_topic=metadata.business_topic,
                chunk_id=f"{metadata.doc_id}_row_{index:02d}",
                snippet=snippet,
                score=0.0,
            )
        )
    return result


def chunk_private_sample_document(document: PrivateSampleDocument) -> list[RetrievedChunk]:
    if document.metadata.sample_type == "table":
        return _chunk_csv(document)
    return _chunk_markdown(document)
