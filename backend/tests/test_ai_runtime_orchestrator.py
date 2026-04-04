from app.ai_runtime.providers.base import (
    BaseChatProvider,
    BaseEmbeddingProvider,
    ChatCompletionResult,
    ChatProviderError,
    EmbeddingResult,
    ProviderDescriptor,
)
from app.ai_runtime.runtime.orchestrator import AIRuntimeOrchestrator
from app.ai_runtime.schemas.chat import ChatRequest


class FakeChatProvider(BaseChatProvider):
    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="fake-chat-provider",
            provider_type="chat",
            mode="openai_compatible",
            default_model="gpt-5.4",
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        assert "CarbonRag" in system_prompt
        assert "公共政策片段" in system_prompt or "当前未检索到足够政策依据" in system_prompt
        return ChatCompletionResult(content=f"回答: {user_input}")


class FailingChatProvider(BaseChatProvider):
    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="failing-chat-provider",
            provider_type="chat",
            mode="openai_compatible",
            default_model="gpt-5.4",
        )

    def generate_response(self, *, system_prompt: str, user_input: str) -> ChatCompletionResult:
        raise ChatProviderError("boom", reason="network_error")


class FakeEmbeddingProvider(BaseEmbeddingProvider):
    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="fake-embedding-provider",
            provider_type="embedding",
            mode="openai_compatible",
            default_model="text-embedding-3-small",
        )

    def embed_stub(self, texts: list[str]) -> EmbeddingResult:
        return EmbeddingResult(vectors=[[1.0, 2.0, 3.0] for _ in texts])


def test_orchestrator_returns_runtime_result_for_ok_request() -> None:
    orchestrator = AIRuntimeOrchestrator(
        chat_provider=FakeChatProvider(),
        embedding_provider=FakeEmbeddingProvider(),
    )
    request = ChatRequest(
        mode="ask",
        user_input="什么是双碳目标？",
        payload={
            "knowledge_scope_requested": "public",
            "knowledge_scope_effective": "public",
            "top_k": 5,
        },
    )

    result = orchestrator.run(request)

    assert result.status == "ok"
    assert result.mode == "ask"
    assert result.trace_id == request.trace_id
    assert result.context_summary["knowledge_scope_requested"] == "public"
    assert result.context_summary["knowledge_scope_effective"] == "public"
    assert result.context_summary["memory_reserved"] is True
    assert result.context_summary["tool_count"] == 1
    assert result.context_summary["grounded_by_policy"] is True
    assert result.context_summary["retrieval_hit_count"] >= 1
    assert result.tool_calls[0].name == "policy_retrieve"
    assert result.tool_results[0].name == "policy_retrieve"
    assert result.citations
    assert result.response.mode == "ask"
    assert result.response.status == "ok"
    assert result.response.provider_mode == "openai_compatible"
    assert "forbidden_capabilities" in result.metadata


def test_orchestrator_returns_provider_error_when_chat_provider_fails() -> None:
    orchestrator = AIRuntimeOrchestrator(
        chat_provider=FailingChatProvider(),
        embedding_provider=FakeEmbeddingProvider(),
    )
    request = ChatRequest(
        mode="ask",
        user_input="什么是碳中和？",
        payload={
            "knowledge_scope_requested": "public",
            "knowledge_scope_effective": "public",
            "top_k": 5,
        },
    )

    result = orchestrator.run(request)

    assert result.status == "provider_error"
    assert result.tool_calls[0].name == "policy_retrieve"
    assert result.citations
    assert result.response.status == "provider_error"
    assert result.response.answer == "当前问答服务暂不可用，请稍后重试。"
