from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderDescriptor:
    name: str
    mode: str


class BaseProvider(ABC):
    @abstractmethod
    def describe(self) -> ProviderDescriptor:
        raise NotImplementedError
