from datetime import datetime

from pydantic import BaseModel


class SystemInfoResponse(BaseModel):
    app_name: str
    version: str
    env: str
    api_prefix: str
    model_provider_mode: str
    model_name: str | None = None
    timestamp: datetime
