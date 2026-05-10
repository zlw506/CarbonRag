from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    text: str
    chunk_index: int
    parent_chunk_id: str | None = None
    token_estimate: int = 0


def estimate_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, len(stripped) // 2)


def recursive_chunk_text(text: str, *, chunk_size: int = 900, overlap: int = 120) -> list[TextChunk]:
    normalized = text.strip()
    if not normalized:
        return []
    if len(normalized) <= chunk_size:
        return [TextChunk(text=normalized, chunk_index=0, token_estimate=estimate_tokens(normalized))]

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        window = normalized[start:end]
        split_at = max(window.rfind("\n\n"), window.rfind("。"), window.rfind("\n"))
        if split_at > chunk_size * 0.45 and end < len(normalized):
            end = start + split_at + 1
        chunk_text = normalized[start:end].strip()
        if chunk_text:
            chunks.append(TextChunk(text=chunk_text, chunk_index=index, token_estimate=estimate_tokens(chunk_text)))
            index += 1
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks

