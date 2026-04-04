import re

from app.retrieval.schemas import PublicPolicyDocument, RetrievedChunk

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


def chunk_public_policy_document(document: PublicPolicyDocument) -> list[RetrievedChunk]:
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

    merged_chunks: list[str] = []
    for chunk in chunks:
        if merged_chunks and len(chunk) < MIN_CHUNK_LENGTH and len(merged_chunks[-1]) + len(chunk) + 2 <= MAX_CHUNK_LENGTH:
            merged_chunks[-1] = f"{merged_chunks[-1]}\n\n{chunk}"
        else:
            merged_chunks.append(chunk)

    result: list[RetrievedChunk] = []
    for index, chunk in enumerate(merged_chunks, start=1):
        metadata = document.metadata
        result.append(
            RetrievedChunk(
                doc_id=metadata.doc_id,
                title=metadata.title,
                source=metadata.source,
                source_url=metadata.source_url,
                issued_at=metadata.issued_at,
                region=metadata.region,
                doc_type=metadata.doc_type,
                chunk_id=f"{metadata.doc_id}_chunk_{index:02d}",
                snippet=chunk,
                score=0.0,
            )
        )
    return result
