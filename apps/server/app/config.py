from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "SmartLab Control Center"
    database_url: str = "sqlite:///./smartlab.db"
    jwt_secret: str = "change-this-local-secret-before-production"
    jwt_expire_minutes: int = 480
    server_host: str = "127.0.0.1"
    server_port: int = 8765
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    telemetry_retention_days: int = 30
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

