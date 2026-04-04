from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Sequence


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    provider_type: str
    mode: str
    default_model: str | None = None


@dataclass(frozen=True)
class ChatCompletionResult:
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ChatProviderError(Exception):
    def __init__(self, message: str, *, reason: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.status_code = status_code


@dataclass(frozen=True)
class EmbeddingResult:
    vectors: list[list[float]]
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseChatProvider(ABC):
    @abstractmethod
    def describe(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    def generate_response(
        self,
        *,
        system_prompt: str,
        user_input: str,
    ) -> ChatCompletionResult:
        raise NotImplementedError


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def describe(self) -> ProviderDescriptor:
        raise NotImplementedError

    @abstractmethod
    def embed_stub(self, texts: Sequence[str]) -> EmbeddingResult:
        raise NotImplementedError
