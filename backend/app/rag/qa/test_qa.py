from __future__ import annotations

from app.rag.kb.models import RagAnswerResult
from app.rag.qa.answer import build_grounded_answer


def build_test_qa_answer(*, query: str, search_result) -> RagAnswerResult:
    return build_grounded_answer(query=query, hits=search_result.hits, trace=search_result.trace)

