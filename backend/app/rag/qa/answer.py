from __future__ import annotations

from app.rag.kb.models import RagAnswerResult, RagHit, RagTrace


def build_grounded_answer(*, query: str, hits: list[RagHit], trace: RagTrace) -> RagAnswerResult:
    if not hits:
        warning = "没有检索到可引用片段，无法生成有依据的 RAG 回答。"
        next_trace = trace.model_copy(update={"warnings": [*trace.warnings, warning], "degraded": True})
        return RagAnswerResult(answer=warning, hits=[], citations=[], retrieval_trace=next_trace)

    lines = [f"基于知识库命中的 {len(hits)} 个片段，下面是可追溯回答："]
    for index, hit in enumerate(hits[:5], start=1):
        snippet = hit.snippet.strip().replace("\n", " ")
        if len(snippet) > 220:
            snippet = snippet[:220] + "..."
        lines.append(f"{index}. {snippet}")
    citations = [hit_to_citation(hit, index=index) for index, hit in enumerate(hits, start=1)]
    return RagAnswerResult(answer="\n".join(lines), hits=hits, citations=citations, retrieval_trace=trace)


def hit_to_citation(hit: RagHit, *, index: int) -> dict:
    return {
        "reference_id": f"rag-ref-{index}",
        "source_type": hit.source_type,
        "title": hit.title,
        "kb_id": hit.kb_id,
        "chunk_id": hit.chunk_id,
        "doc_id": hit.doc_id,
        "file_id": hit.file_id,
        "knowledge_item_id": hit.knowledge_item_id,
        "page_number": hit.page_number,
        "sheet_name": hit.sheet_name,
        "slide_number": hit.slide_number,
        "section_title": hit.section_title,
        "snippet": hit.snippet[:500],
        "score": hit.score,
        "dense_score": hit.dense_score,
        "sparse_score": hit.sparse_score,
        "rrf_score": hit.rrf_score,
        "rerank_score": hit.rerank_score,
    }

