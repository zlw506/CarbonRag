from __future__ import annotations

import math
import re
from collections import Counter

from app.rag.kb.models import RagChunk


TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def sparse_search(*, query: str, chunks: list[RagChunk], top_k: int) -> list[tuple[RagChunk, float]]:
    query_terms = _tokens(query)
    if not query_terms:
        return []
    query_counter = Counter(query_terms)
    scored: list[tuple[RagChunk, float]] = []
    for chunk in chunks:
        chunk_terms = _tokens(chunk.text)
        if not chunk_terms:
            continue
        chunk_counter = Counter(chunk_terms)
        score = 0.0
        for term, q_count in query_counter.items():
            tf = chunk_counter.get(term, 0)
            if tf:
                score += (1.0 + math.log(tf)) * q_count
        if score > 0:
            scored.append((chunk, float(score)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return scored[:top_k]


def _tokens(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text or "")]
    cjk_chars = [char for char in (text or "") if "\u4e00" <= char <= "\u9fff"]
    cjk_bigrams = ["".join(cjk_chars[index:index + 2]) for index in range(max(len(cjk_chars) - 1, 0))]
    return tokens + cjk_chars + cjk_bigrams
