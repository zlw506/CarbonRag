from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from time import perf_counter

from app.rag.kb.models import RagChunk


TOKEN_PATTERN = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


@dataclass(slots=True)
class SparseSearchResult:
    hits: list[tuple[RagChunk, float]]
    elapsed_ms: float
    cache_hit: bool
    loaded_chunk_count: int


def sparse_search(*, query: str, chunks: list[RagChunk], top_k: int) -> list[tuple[RagChunk, float]]:
    return sparse_search_with_trace(query=query, chunks=chunks, top_k=top_k).hits


def sparse_search_with_trace(*, query: str, chunks: list[RagChunk], top_k: int) -> SparseSearchResult:
    started = perf_counter()
    query_terms = _tokens(query)
    if not query_terms:
        return SparseSearchResult(hits=[], elapsed_ms=_elapsed_ms(started), cache_hit=False, loaded_chunk_count=len(chunks))
    query_counter = Counter(query_terms)
    corpus, cache_hit = _corpus_for_chunks(chunks)
    scored: list[tuple[RagChunk, float]] = []
    for chunk, chunk_counter in corpus:
        score = 0.0
        for term, q_count in query_counter.items():
            tf = chunk_counter.get(term, 0)
            if tf:
                score += (1.0 + math.log(tf)) * q_count
        if score > 0:
            scored.append((chunk, float(score)))
    scored.sort(key=lambda item: item[1], reverse=True)
    return SparseSearchResult(hits=scored[:top_k], elapsed_ms=_elapsed_ms(started), cache_hit=cache_hit, loaded_chunk_count=len(corpus))


def _tokens(text: str) -> list[str]:
    tokens = [token.lower() for token in TOKEN_PATTERN.findall(text or "")]
    cjk_chars = [char for char in (text or "") if "\u4e00" <= char <= "\u9fff"]
    cjk_bigrams = ["".join(cjk_chars[index:index + 2]) for index in range(max(len(cjk_chars) - 1, 0))]
    return tokens + cjk_chars + cjk_bigrams


_CORPUS_CACHE: dict[tuple[str, str], list[tuple[RagChunk, Counter[str]]]] = {}


def _corpus_for_chunks(chunks: list[RagChunk]) -> tuple[list[tuple[RagChunk, Counter[str]]], bool]:
    key = _corpus_key(chunks)
    cached = _CORPUS_CACHE.get(key)
    if cached is not None:
        return cached, True
    corpus: list[tuple[RagChunk, Counter[str]]] = []
    for chunk in chunks:
        chunk_terms = _tokens(chunk.text)
        if chunk_terms:
            corpus.append((chunk, Counter(chunk_terms)))
    _CORPUS_CACHE[key] = corpus
    if len(_CORPUS_CACHE) > 32:
        first_key = next(iter(_CORPUS_CACHE))
        _CORPUS_CACHE.pop(first_key, None)
    return corpus, False


def _corpus_key(chunks: list[RagChunk]) -> tuple[str, str]:
    if not chunks:
        return ("empty", "0")
    kb_ids = sorted({chunk.kb_id for chunk in chunks})
    watermark = max(str(chunk.updated_at) for chunk in chunks)
    return ("|".join(kb_ids), f"{len(chunks)}:{watermark}")


def _elapsed_ms(started: float) -> float:
    return round((perf_counter() - started) * 1000, 3)
