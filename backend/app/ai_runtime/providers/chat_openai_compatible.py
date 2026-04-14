import json
from dataclasses import dataclass
from typing import Any, Iterator

import httpx

from app.ai_runtime.providers.base import (
    BaseChatProvider,
    ChatCompletionResult,
    ChatProviderError,
    ChatStreamEvent,
    ProviderDescriptor,
)


@dataclass
class OpenAICompatibleChatProvider(BaseChatProvider):
    base_url: str
    api_key: str
    model_name: str = "gpt-5.4"
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout_seconds: float = 30.0
    max_retries: int = 2
    mode: str = "openai_compatible"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="openai-compatible-chat",
            provider_type="chat",
            mode=self.mode,
            default_model=self.model_name,
        )

    def generate_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        try:
            return self._aggregate_stream_response(
                system_prompt=system_prompt,
                user_input=user_input,
            )
        except ChatProviderError as stream_exc:
            if stream_exc.reason not in {"invalid_response", "empty_content"}:
                raise

        return self._generate_non_stream_response(
            system_prompt=system_prompt,
            user_input=user_input,
        )

    def stream_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> Iterator[ChatStreamEvent]:
        yield ChatStreamEvent(
            kind="status",
            data={
                "status": "thinking",
                "transport": "streaming_sse",
                "provider_mode": self.mode,
            },
        )
        try:
            yield from self._streaming_response(
                system_prompt=system_prompt,
                user_input=user_input,
            )
        except ChatProviderError as exc:
            if exc.reason in {"invalid_response", "empty_content"}:
                fallback_result = self._generate_non_stream_response(
                    system_prompt=system_prompt,
                    user_input=user_input,
                )
                yield ChatStreamEvent(
                    kind="status",
                    data={
                        "status": "streaming",
                        "transport": "chat_completions_json",
                        "provider_mode": self.mode,
                    },
                )
                yield ChatStreamEvent(kind="answer_delta", data={"delta": fallback_result.content})
                yield ChatStreamEvent(
                    kind="done",
                    data={
                        "answer": fallback_result.content,
                        "content": fallback_result.content,
                        "metadata": {
                            **fallback_result.metadata,
                            "provider_mode": self.mode,
                            "base_url": self.base_url,
                            "model_name": self.model_name,
                            "transport": "chat_completions_json",
                            "fallback_from_stream": True,
                        },
                    },
                )
                return
            raise

    def _streaming_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> Iterator[ChatStreamEvent]:
        url = self._chat_completions_url
        payload = self._build_payload(
            system_prompt=system_prompt,
            user_input=user_input,
            stream=True,
        )
        headers = self._build_headers()

        try:
            with httpx.stream(
                "POST",
                url,
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            ) as response:
                if response.status_code >= 400:
                    raise ChatProviderError(
                        f"Chat provider returned HTTP {response.status_code}.",
                        reason="http_error",
                        status_code=response.status_code,
                    )

                answer_fragments: list[str] = []
                thinking_fragments: list[str] = []
                response_id: str | None = None
                usage: dict[str, Any] = {}
                saw_data = False
                current_event_name: str | None = None
                answer_started = False

                for raw_line in response.iter_lines():
                    line = raw_line.decode("utf-8", errors="ignore") if isinstance(raw_line, bytes) else raw_line
                    if not line:
                        current_event_name = None
                        continue
                    if line.startswith("event:") or line.startswith(":"):
                        if line.startswith("event:"):
                            current_event_name = line[len("event:") :].strip() or None
                        continue
                    if not line.startswith("data:"):
                        continue

                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break

                    saw_data = True
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError as exc:
                        raise ChatProviderError(
                            "Chat provider returned malformed streaming chunks.",
                            reason="invalid_response",
                            status_code=response.status_code,
                        ) from exc

                    if response_id is None:
                        response_id = chunk.get("id")
                    if isinstance(chunk.get("usage"), dict):
                        usage = chunk["usage"]

                    thinking_delta, answer_delta = self._extract_stream_delta_text(chunk, current_event_name=current_event_name)
                    if thinking_delta:
                        thinking_fragments.append(thinking_delta)
                        yield ChatStreamEvent(kind="thinking_delta", data={"delta": thinking_delta})
                    if answer_delta:
                        if not answer_started:
                            answer_started = True
                            yield ChatStreamEvent(
                                kind="status",
                                data={
                                    "status": "streaming",
                                    "transport": "streaming_sse",
                                    "provider_mode": self.mode,
                                },
                            )
                        answer_fragments.append(answer_delta)
                        yield ChatStreamEvent(kind="answer_delta", data={"delta": answer_delta})

        except httpx.TimeoutException as exc:
            raise ChatProviderError("Chat provider request timed out.", reason="timeout") from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError("Chat provider request failed.", reason="network_error") from exc

        if not saw_data:
            raise ChatProviderError(
                "Chat provider returned an empty streaming response.",
                reason="invalid_response",
            )

        content = "".join(answer_fragments).strip()
        if not content:
            raise ChatProviderError("Chat provider returned empty content.", reason="empty_content")

        yield ChatStreamEvent(
            kind="done",
            data={
                "answer": content,
                "content": content,
                "metadata": {
                    "provider_mode": self.mode,
                    "base_url": self.base_url,
                    "model_name": self.model_name,
                    "response_id": response_id,
                    "usage": usage,
                    "transport": "streaming_sse_aggregate",
                    "thinking_chunk_count": len(thinking_fragments),
                    "answer_chunk_count": len(answer_fragments),
                },
            },
        )

    def _aggregate_stream_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        answer_fragments: list[str] = []
        final_metadata: dict[str, Any] = {}
        final_content = ""
        saw_done = False

        for event in self.stream_response(
            system_prompt=system_prompt,
            user_input=user_input,
        ):
            if event.kind == "answer_delta":
                delta = event.data.get("delta")
                if isinstance(delta, str) and delta:
                    answer_fragments.append(delta)
                continue
            if event.kind == "done":
                saw_done = True
                final_content = (
                    event.data.get("answer")
                    or event.data.get("content")
                    or "".join(answer_fragments)
                )
                metadata = event.data.get("metadata")
                if isinstance(metadata, dict):
                    final_metadata = metadata
                continue
            if event.kind == "error":
                raise ChatProviderError(
                    event.data.get("message", "Chat provider stream failed."),
                    reason=str(event.data.get("reason", "network_error")),
                    status_code=event.data.get("status_code"),
                )

        content = (final_content or "".join(answer_fragments)).strip()
        if not saw_done:
            raise ChatProviderError(
                "Chat provider returned an incomplete streaming response.",
                reason="invalid_response",
            )
        if not content:
            raise ChatProviderError(
                "Chat provider returned empty content.",
                reason="empty_content",
            )

        return ChatCompletionResult(
            content=content,
            metadata=final_metadata,
        )

    def _generate_non_stream_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        url = self._chat_completions_url
        payload = self._build_payload(
            system_prompt=system_prompt,
            user_input=user_input,
            stream=False,
        )
        headers = self._build_headers()

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
        except httpx.TimeoutException as exc:
            raise ChatProviderError(
                "Chat provider request timed out.",
                reason="timeout",
            ) from exc
        except httpx.HTTPError as exc:
            raise ChatProviderError(
                "Chat provider request failed.",
                reason="network_error",
            ) from exc

        if response.status_code >= 400:
            raise ChatProviderError(
                f"Chat provider returned HTTP {response.status_code}.",
                reason="http_error",
                status_code=response.status_code,
            )

        try:
            payload_json = response.json()
        except ValueError as exc:
            raise ChatProviderError(
                "Chat provider returned non-JSON content.",
                reason="invalid_response",
                status_code=response.status_code,
            ) from exc

        content = self._extract_non_stream_content(payload_json)
        if not content:
            raise ChatProviderError(
                "Chat provider returned empty content.",
                reason="empty_content",
                status_code=response.status_code,
            )

        return ChatCompletionResult(
            content=content,
            metadata={
                "provider_mode": self.mode,
                "base_url": self.base_url,
                "model_name": self.model_name,
                "response_id": payload_json.get("id"),
                "usage": payload_json.get("usage", {}),
                "transport": "chat_completions_json",
            },
        )

    @property
    def _chat_completions_url(self) -> str:
        return f"{self.base_url.rstrip('/')}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        *,
        system_prompt: str,
        user_input: str,
        stream: bool,
    ) -> dict[str, Any]:
        return {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stream": stream,
        }

    @staticmethod
    def _extract_non_stream_content(payload_json: dict[str, Any]) -> str:
        try:
            content = payload_json["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ChatProviderError(
                "Chat provider response is missing choices[0].message.content.",
                reason="invalid_response",
            ) from exc

        return OpenAICompatibleChatProvider._normalize_content(content)

    @staticmethod
    def _extract_stream_delta_text(chunk: dict[str, Any], *, current_event_name: str | None = None) -> tuple[str, str]:
        try:
            delta = chunk["choices"][0]["delta"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ChatProviderError(
                "Streaming chat chunk is missing choices[0].delta.",
                reason="invalid_response",
            ) from exc

        thinking_fragments: list[str] = []
        answer_fragments: list[str] = []

        for key in ("reasoning_content", "reasoning", "thinking", "thought"):
            normalized = OpenAICompatibleChatProvider._normalize_stream_content(delta.get(key))
            if normalized:
                thinking_fragments.append(normalized)

        content = delta.get("content")
        normalized_content = OpenAICompatibleChatProvider._normalize_stream_content(content)
        if normalized_content:
            if current_event_name and any(token in current_event_name.lower() for token in ("reason", "think", "thought")):
                thinking_fragments.append(normalized_content)
            else:
                answer_fragments.append(normalized_content)

        return ("".join(thinking_fragments), "".join(answer_fragments))

    @staticmethod
    def _normalize_content(content: Any) -> str:
        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str) and text.strip():
                        fragments.append(text.strip())
            return "\n".join(fragments).strip()

        if content is None:
            return ""

        raise ChatProviderError(
            "Chat provider returned unsupported content shape.",
            reason="invalid_response",
        )

    @staticmethod
    def _normalize_stream_content(content: Any) -> str:
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            fragments: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        fragments.append(text)
            return "".join(fragments)

        if content is None:
            return ""

        raise ChatProviderError(
            "Chat provider returned unsupported streaming content shape.",
            reason="invalid_response",
        )
