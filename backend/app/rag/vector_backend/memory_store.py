from __future__ import annotations

import math
import re
from collections import Counter

from app.rag.kb.models import RagChunk
from app.rag.vector_backend.base import BaseVectorStore, VectorSearchHit, VectorSearchResult


TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


class MemoryVectorStore(BaseVectorStore):
    backend_name = "memory"

    def search(self, *, query: str, chunks: list[RagChunk], top_k: int) -> VectorSearchResult:
        query_vector = _term_vector(query)
        hits: list[VectorSearchHit] = []
        for chunk in chunks:
            score = _cosine(query_vector, _term_vector(chunk.text))
            if score > 0:
                hits.append(VectorSearchHit(chunk=chunk, score=score))
        hits.sort(key=lambda item: item.score, reverse=True)
        return VectorSearchResult(hits=hits[:top_k], backend=self.backend_name, available=True)


def _term_vector(text: str) -> Counter[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text or "")]
    cjk_chars = [char for char in (text or "") if "\u4e00" <= char <= "\u9fff"]
    cjk_bigrams = ["".join(cjk_chars[index:index + 2]) for index in range(max(len(cjk_chars) - 1, 0))]
    return Counter(tokens + cjk_chars + cjk_bigrams)


def _cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    dot = sum(left[key] * right.get(key, 0) for key in left)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return float(dot / (left_norm * right_norm))
