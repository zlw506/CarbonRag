from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "backend"
LOCAL_PROVIDER_CONFIG_PATH = BACKEND_DIR / "local_provider_config.json"


class Settings(BaseSettings):
    app_name: str = "CarbonRag"
    app_version: str = "v0.1.9C"
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    api_prefix: str = "/api/v1"
    model_provider_mode: str = "openai_compatible"

    model_api_base_url: str = "https://api.example.com/v1"
    model_api_key: str = "replace-with-model-api-key"
    model_name: str = "gpt-5.4"
    model_temperature: float = 0.2
    model_max_tokens: int = 4096

    embedding_api_base_url: str = "https://api.example.com/v1"
    embedding_api_key: str = "replace-with-embedding-api-key"
    embedding_model: str = "replace-with-embedding-model"

    vector_store_path: str = "./data/outputs/vector_store"
    public_data_dir: str = "./data/public"
    private_sample_dir: str = "./data/private_sample"
    factor_data_dir: str = "./data/factors"
    upload_dir: str = "./data/outputs/uploads"
    database_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
