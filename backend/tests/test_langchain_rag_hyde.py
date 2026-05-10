from app.langchain_rag.hyde import HyDEGenerator


class FailingProvider:
    def generate_response(self, *, system_prompt: str, user_input: str):
        raise RuntimeError("network unavailable")


def test_hyde_falls_back_to_original_query(monkeypatch) -> None:
    monkeypatch.setattr("app.langchain_rag.hyde.get_chat_provider", lambda: FailingProvider())

    query, warnings = HyDEGenerator().generate("外购电力排放因子")

    assert query == "外购电力排放因子"
    assert warnings
    assert "HyDE" in warnings[0]
