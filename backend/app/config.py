from __future__ import annotations
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Web Navigator AI"
    locale: str = "en-IN"
    # Add toggles as you grow:
    # headless: bool = True
    # max_concurrent_sites: int = 3
    # request_timeout_ms: int = 12000


settings = Settings()
