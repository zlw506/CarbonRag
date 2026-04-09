from fastapi.testclient import TestClient

from app.main import app
from tests.test_helpers import register_and_login

client = TestClient(app)


def test_system_info() -> None:
    register_and_login(client, prefix="system")
    response = client.get("/api/v1/system/info")
    payload = response.json()

    assert response.status_code == 200
    assert payload["app_name"] == "CarbonRag"
    assert payload["api_prefix"] == "/api/v1"
    assert payload["model_provider_mode"] == "openai_compatible"
    assert payload["model_name"] == "gpt-5.4"
    assert "timestamp" in payload
