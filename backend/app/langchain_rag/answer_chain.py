from __future__ import annotations

from app.ai_runtime.providers.base import ChatProviderError
from app.ai_runtime.providers.factory import get_chat_provider
from app.langchain_rag.citations import citations_from_hits
from app.langchain_rag.schemas import LangChainRagAnswerResult, LangChainRagHit, LangChainRagTrace


class LangChainRagAnswerChain:
    def answer(self, *, question: str, hits: list[LangChainRagHit], trace: LangChainRagTrace) -> LangChainRagAnswerResult:
        citations = citations_from_hits(hits)
        if not hits:
            return LangChainRagAnswerResult(
                answer="当前 RAG 没有检索到足够依据，无法给出带引用的回答。",
                citations=[],
                retrieval_trace=trace,
                hits=[],
            )
        context = "\n\n".join(
            f"[{index}] {hit.title} / {hit.source_type} / {hit.chunk_id}\n{hit.snippet}"
            for index, hit in enumerate(hits, start=1)
        )
        system_prompt = (
            "你是 CarbonRag 的 RAG 回答链。只能使用给定检索片段回答，必须保持中文，"
            "不要编造来源。若片段不足，请明确说明限制。\n\n"
            f"检索片段：\n{context}"
        )
        try:
            provider = get_chat_provider()
            result = provider.generate_response(system_prompt=system_prompt, user_input=question)
            answer = result.content.strip() or "已检索到依据，但模型未生成有效回答。"
        except ChatProviderError as exc:
            answer = f"RAG 检索已完成，但生成回答失败：{exc.reason}"
            trace.warnings.append(answer)
        except Exception as exc:  # noqa: BLE001
            answer = f"RAG 检索已完成，但生成回答失败：{type(exc).__name__}"
            trace.warnings.append(answer)
        return LangChainRagAnswerResult(answer=answer, citations=citations, retrieval_trace=trace, hits=hits)
