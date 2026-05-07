from dataclasses import dataclass
from typing import Sequence

from app.ai_runtime.providers.base import (
    BaseRerankProvider,
    ProviderDescriptor,
    RerankItem,
    RerankResult,
)


@dataclass
class DisabledRerankProvider(BaseRerankProvider):
    mode: str = "disabled"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="disabled-rerank",
            provider_type="rerank",
            mode=self.mode,
            default_model=None,
        )

    def rerank_stub(
        self,
        *,
        query: str,
        items: Sequence[RerankItem],
        top_k: int,
    ) -> RerankResult:
        ranked_ids = [item.item_id for item in items[:top_k]]
        return RerankResult(
            ranked_ids=ranked_ids,
            scores={item_id: 0.0 for item_id in ranked_ids},
            metadata={
                "status": "skipped",
                "reason": "rag_rerank_disabled",
                "query_length": len(query),
                "candidate_count": len(items),
            },
        )
