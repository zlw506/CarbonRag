from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_system_info() -> None:
    response = client.get("/api/v1/system/info")
    payload = response.json()

    assert response.status_code == 200
    assert payload["app_name"] == "CarbonRag"
    assert payload["version"] == "v0.0.2"
    assert payload["env"] == "development"
    assert payload["api_prefix"] == "/api/v1"
    assert payload["model_provider_mode"] in {"cloud_api_stub", "openai_compatible"}
    assert payload["model_name"] == "gpt-5.4"
    assert "timestamp" in payload
