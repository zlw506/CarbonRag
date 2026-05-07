from app.ai_runtime.providers.rerank_local import NoopRerankProvider


class DisabledRerankProvider(NoopRerankProvider):
    pass
