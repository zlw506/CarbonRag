from __future__ import annotations

from app.ai_runtime.providers.base import ChatProviderError
from app.ai_runtime.providers.factory import get_chat_provider


class HyDEGenerator:
    def generate(self, query: str) -> tuple[str, list[str]]:
        prompt = (
            "请基于用户问题生成一段用于检索的假设性回答。"
            "要求保留关键词、政策名、指标和可能出现的术语，不要编造具体引用。\n\n"
            f"用户问题：{query}\n\n假设性回答："
        )
        try:
            provider = get_chat_provider()
            result = provider.generate_response(system_prompt=prompt, user_input=query)
            generated = result.content.strip()
            if generated:
                return generated, []
        except ChatProviderError as exc:
            return query, [f"HyDE 生成失败，已回退原始问题：{exc.reason}"]
        except Exception as exc:  # noqa: BLE001
            return query, [f"HyDE 生成失败，已回退原始问题：{type(exc).__name__}"]
        return query, ["HyDE 生成结果为空，已回退原始问题。"]
