from __future__ import annotations

import os


class Settings:
    def __init__(self) -> None:
        self.app_name = os.getenv("APP_NAME", "buildit")
        self.app_env = os.getenv("APP_ENV", "local")
        self.database_url = os.getenv("DATABASE_URL", "sqlite+pysqlite:///./buildit.db")
        self.cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")


settings = Settings()
