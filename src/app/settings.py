"""Application settings defined via environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        populate_by_name=True,
    )

    app_name: str = Field(default="Waifu Material Backend")
    debug: bool = Field(default=False)

    database_url: str = Field(
        default="sqlite+aiosqlite:///./dev.db",
        validation_alias=AliasChoices(
            "database_url",
            "DATABASE_URL",
            "RAILWAY_DATABASE_URL",
            "NEON_DATABASE_URL",
        ),
    )

    b2_key_id: str = Field(
        default="dev-key-id",
        validation_alias=AliasChoices("b2_key_id", "B2_KEY_ID"),
    )
    b2_application_key: str = Field(
        default="dev-application-key",
        validation_alias=AliasChoices("b2_application_key", "B2_APPLICATION_KEY"),
    )
    b2_bucket_id: str = Field(
        default="dev-bucket-id",
        validation_alias=AliasChoices("b2_bucket_id", "B2_BUCKET_ID"),
    )
    b2_download_url: AnyHttpUrl = Field(
        default="https://example.com",
        validation_alias=AliasChoices("b2_download_url", "B2_DOWNLOAD_URL"),
    )
    b2_api_url: AnyHttpUrl = Field(default="https://api.backblazeb2.com")

    background_remover_url: AnyHttpUrl = Field(
        default="https://example.com/background-remover",
        validation_alias=AliasChoices("background_remover_url", "BACKGROUND_REMOVER_URL"),
    )
    seedream_url: AnyHttpUrl = Field(
        default="https://example.com/seedream",
        validation_alias=AliasChoices("seedream_url", "SEEDREAM_URL"),
    )
    google_generation_url: AnyHttpUrl = Field(
        default="https://example.com/google-generation",
        validation_alias=AliasChoices("google_generation_url", "GOOGLE_GENERATION_URL"),
    )

    feature_workflows_enabled: bool = Field(default=True)
    catalog_refresh_cron: str = Field(default="0 3 * * *")

    workflow_tmp_prefix: str = Field(default="tmp")
    workflow_log_prefix: str = Field(default="logs")
    asset_cleanup_days: int = Field(default=30)
    analytics_enabled: bool = Field(default=True)
    user_session_timeout_hours: int = Field(default=24)

    environment: Literal["local", "staging", "production"] = Field(default="local")


@lru_cache()
def get_settings() -> AppSettings:
    return AppSettings()
