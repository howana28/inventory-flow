from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "InventoryFlow")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./inventoryflow.db")
    session_hours: int = int(os.getenv("SESSION_HOURS", "12"))
    cookie_secure: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
    allow_external_connections: bool = os.getenv("ALLOW_EXTERNAL_CONNECTIONS", "false").lower() == "true"
    erp_provider: str = os.getenv("ERP_PROVIDER", "demo").lower()
    bling_client_id: str = os.getenv("BLING_CLIENT_ID", "")
    bling_client_secret: str = os.getenv("BLING_CLIENT_SECRET", "")
    bling_redirect_uri: str = os.getenv("BLING_REDIRECT_URI", "http://127.0.0.1:10000/api/v1/integrations/bling/callback")
    token_encryption_key: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")
    count_lock_ttl_seconds: int = int(os.getenv("COUNT_LOCK_TTL_SECONDS", "1800"))
    recount_lock_ttl_seconds: int = int(os.getenv("RECOUNT_LOCK_TTL_SECONDS", "1800"))


settings = Settings()
