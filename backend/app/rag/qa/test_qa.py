from __future__ import annotations

from typing import Any

from app.ai_runtime.providers.base import BaseChatProvider, ChatProviderError
from app.rag.kb.models import RagHit, RagSearchResult, RagTrace
from app.rag.qa.answer import hit_to_citation


def build_test_qa_answer(
    *,
    query: str,
    search_result: RagSearchResult,
    chat_provider: BaseChatProvider,
    provider_ref: str | None = None,
) -> dict[str, Any]:
    """Generate a workbench-only grounded answer from retrieved RAG evidence."""

    if not search_result.hits:
        warning = "no_hits: 没有检索到可引用片段，Test QA 不调用大模型，也不编造答案。"
        descriptor = chat_provider.describe()
        trace = _with_generation_metadata(
            trace=_append_trace_warning(trace=search_result.trace, warning=warning, degraded=True),
            provider_name=descriptor.name,
            model_name=descriptor.default_model,
            provider_ref=provider_ref,
            thinking_content=None,
        )
        return {
            "answer": "没有检索到可引用片段，无法生成有依据的 RAG 测试回答。",
            "answer_mode": "no_hits",
            "provider_name": None,
            "model_name": None,
            "selected_chunks": [],
            "evidence_quality": "none",
            "confidence": 0.0,
            "citations": [],
            "hits": [],
            "retrieval_trace": trace,
        }

    descriptor = chat_provider.describe()
    selected_hits = search_result.hits[: min(len(search_result.hits), 8)]
    citations = [hit_to_citation(hit, index=index) for index, hit in enumerate(selected_hits, start=1)]
    system_prompt, user_input = _build_grounded_prompt(query=query, hits=selected_hits)
    evidence_quality, confidence = _score_evidence_quality(hits=selected_hits, trace=search_result.trace)

    try:
        provider_result = chat_provider.generate_response(system_prompt=system_prompt, user_input=user_input)
    except ChatProviderError as exc:
        warning = f"provider_error:{exc.reason}"
        trace = _with_generation_metadata(
            trace=_append_trace_warning(trace=search_result.trace, warning=warning, degraded=True),
            provider_name=descriptor.name,
            model_name=descriptor.default_model,
            provider_ref=provider_ref,
            thinking_content=None,
        )
        return {
            "answer": f"检索已完成，但大模型生成失败：{exc.reason}",
            "answer_mode": "retrieval_only",
            "provider_name": descriptor.name,
            "model_name": descriptor.default_model,
            "selected_chunks": [hit.to_tool_hit() for hit in selected_hits],
            "evidence_quality": evidence_quality,
            "confidence": max(0.0, confidence - 0.25),
            "citations": citations,
            "hits": selected_hits,
            "retrieval_trace": trace,
        }
    except Exception as exc:  # noqa: BLE001
        warning = f"provider_error:{type(exc).__name__}"
        trace = _with_generation_metadata(
            trace=_append_trace_warning(trace=search_result.trace, warning=warning, degraded=True),
            provider_name=descriptor.name,
            model_name=descriptor.default_model,
            provider_ref=provider_ref,
            thinking_content=None,
        )
        return {
            "answer": f"检索已完成，但大模型生成失败：{type(exc).__name__}",
            "answer_mode": "retrieval_only",
            "provider_name": descriptor.name,
            "model_name": descriptor.default_model,
            "selected_chunks": [hit.to_tool_hit() for hit in selected_hits],
            "evidence_quality": evidence_quality,
            "confidence": max(0.0, confidence - 0.25),
            "citations": citations,
            "hits": selected_hits,
            "retrieval_trace": trace,
        }

    answer = provider_result.content.strip() or "大模型已调用，但没有生成有效回答。"
    trace = _with_generation_metadata(
        trace=search_result.trace,
        provider_name=descriptor.name,
        model_name=descriptor.default_model,
        provider_ref=provider_ref,
        thinking_content=_metadata_text(provider_result.metadata.get("thinking_content")),
    )
    return {
        "answer": answer,
        "answer_mode": "llm_grounded",
        "provider_name": descriptor.name,
        "model_name": descriptor.default_model,
        "selected_chunks": [hit.to_tool_hit() for hit in selected_hits],
        "evidence_quality": evidence_quality,
        "confidence": confidence,
        "citations": citations,
        "hits": selected_hits,
        "retrieval_trace": trace,
    }


def _build_grounded_prompt(*, query: str, hits: list[RagHit]) -> tuple[str, str]:
    evidence_blocks = []
    for index, hit in enumerate(hits, start=1):
        location_parts = []
        if hit.page_number is not None:
            location_parts.append(f"page={hit.page_number}")
        if hit.sheet_name:
            location_parts.append(f"sheet={hit.sheet_name}")
        if hit.slide_number is not None:
            location_parts.append(f"slide={hit.slide_number}")
        if hit.section_title:
            location_parts.append(f"section={hit.section_title}")
        location = " · ".join(location_parts) if location_parts else "no explicit location"
        evidence_blocks.append(
            "\n".join(
                [
                    f"[{index}] title={hit.title}",
                    f"chunk_id={hit.chunk_id}; doc_id={hit.doc_id}; kb_id={hit.kb_id}; {location}",
                    f"snippet={hit.snippet}",
                ]
            )
        )

    system_prompt = (
        "你是 CarbonRag 知识库工作台的 Test QA 助手。"
        "只能依据给定检索片段回答，必须使用中文。"
        "如果片段不足，请明确说明缺口；不要编造来源、页码、表格或事实。"
        "回答要给出结论，并在必要处提及引用片段编号。"
    )
    user_input = f"问题：{query}\n\n可用检索片段：\n\n" + "\n\n".join(evidence_blocks)
    return system_prompt, user_input


def _score_evidence_quality(*, hits: list[RagHit], trace: RagTrace) -> tuple[str, float]:
    if not hits:
        return "none", 0.0
    score = min(0.95, 0.35 + 0.12 * len(hits))
    if trace.rerank_applied:
        score += 0.08
    if trace.degraded:
        score -= 0.2
    score = max(0.1, min(score, 0.95))
    if score >= 0.75:
        return "strong", score
    if score >= 0.5:
        return "usable", score
    return "weak", score


def _append_trace_warning(*, trace: RagTrace, warning: str, degraded: bool) -> RagTrace:
    warnings = [*trace.warnings]
    if warning not in warnings:
        warnings.append(warning)
    return trace.model_copy(update={"warnings": warnings, "degraded": bool(degraded or trace.degraded)})


def _with_generation_metadata(
    *,
    trace: RagTrace,
    provider_name: str | None,
    model_name: str | None,
    provider_ref: str | None,
    thinking_content: str | None,
) -> RagTrace:
    return trace.model_copy(
        update={
            "generation_provider": provider_name,
            "generation_model": model_name,
            "provider_ref": provider_ref,
            "thinking_content": thinking_content,
        }
    )


def _metadata_text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None

