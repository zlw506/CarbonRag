from app.ai_runtime.providers.base import RerankItem
from app.ai_runtime.providers.factory import get_rerank_provider, reset_provider_factory_cache
from app.ai_runtime.providers.rerank_local import FakeRerankProvider, NoopRerankProvider


def test_noop_rerank_provider_preserves_candidate_order() -> None:
    provider = NoopRerankProvider()
    items = [
        RerankItem(item_id="a", text="alpha"),
        RerankItem(item_id="b", text="beta"),
        RerankItem(item_id="c", text="gamma"),
    ]

    result = provider.rerank_stub(query="beta", items=items, top_k=2)

    assert result.ranked_ids == ["a", "b"]
    assert result.metadata["status"] == "skipped"
    assert result.metadata["reason"] == "rag_rerank_noop"


def test_fake_rerank_provider_uses_predictable_keyword_overlap() -> None:
    provider = FakeRerankProvider()
    items = [
        RerankItem(item_id="low", text="建筑 交通"),
        RerankItem(item_id="high", text="碳核算 统计 排放"),
        RerankItem(item_id="middle", text="碳核算 能源"),
    ]

    result = provider.rerank_stub(query="碳核算 统计 排放", items=items, top_k=3)

    assert result.ranked_ids == ["high", "middle", "low"]
    assert result.scores["high"] > result.scores["middle"] > result.scores["low"]
    assert result.metadata["status"] == "applied"


def test_rerank_factory_defaults_to_noop_disabled_provider() -> None:
    reset_provider_factory_cache()

    provider = get_rerank_provider()
    descriptor = provider.describe()

    assert isinstance(provider, NoopRerankProvider)
    assert descriptor.provider_type == "rerank"
    assert descriptor.mode == "disabled"
