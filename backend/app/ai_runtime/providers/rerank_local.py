from dataclasses import dataclass
from typing import Sequence

import jieba

from app.ai_runtime.providers.base import (
    BaseRerankProvider,
    ProviderDescriptor,
    RerankItem,
    RerankResult,
)


@dataclass
class NoopRerankProvider(BaseRerankProvider):
    mode: str = "disabled"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="noop-rerank",
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
                "reason": "rag_rerank_noop",
                "provider_name": "noop-rerank",
                "query_length": len(query),
                "candidate_count": len(items),
                "top_k": top_k,
            },
        )


@dataclass
class FakeRerankProvider(BaseRerankProvider):
    mode: str = "fake"

    def describe(self) -> ProviderDescriptor:
        return ProviderDescriptor(
            name="fake-rerank",
            provider_type="rerank",
            mode=self.mode,
            default_model="keyword-overlap",
        )

    def rerank_stub(
        self,
        *,
        query: str,
        items: Sequence[RerankItem],
        top_k: int,
    ) -> RerankResult:
        query_tokens = set(_tokenize(query))
        scored_items = [
            (
                _keyword_overlap_score(query_tokens=query_tokens, item=item),
                index,
                item,
            )
            for index, item in enumerate(items)
        ]
        scored_items.sort(key=lambda entry: (entry[0], -entry[1]), reverse=True)
        selected = scored_items[:top_k]
        ranked_ids = [item.item_id for _, _, item in selected]
        return RerankResult(
            ranked_ids=ranked_ids,
            scores={item.item_id: round(score, 6) for score, _, item in selected},
            metadata={
                "status": "applied",
                "provider_name": "fake-rerank",
                "scoring": "keyword_overlap",
                "query_length": len(query),
                "candidate_count": len(items),
                "top_k": top_k,
            },
        )


def _keyword_overlap_score(*, query_tokens: set[str], item: RerankItem) -> float:
    if not query_tokens:
        return 0.0
    text_tokens = set(_tokenize(item.text))
    title = item.metadata.get("title")
    if isinstance(title, str):
        text_tokens.update(_tokenize(title))
    return float(len(query_tokens & text_tokens)) / float(len(query_tokens))


def _tokenize(text: str) -> list[str]:
    return [
        token.strip().lower()
        for token in jieba.lcut_for_search(text)
        if token.strip() and any(character.isalnum() or "\u4e00" <= character <= "\u9fff" for character in token)
    ]
