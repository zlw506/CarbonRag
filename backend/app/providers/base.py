from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    mode: str
    default_model: str | None = None


class BaseProvider(ABC):
    @abstractmethod
    def describe(self) -> ProviderDescriptor:
        raise NotImplementedError
