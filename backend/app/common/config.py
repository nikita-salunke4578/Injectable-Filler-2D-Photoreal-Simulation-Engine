"""
Application configuration.

Centralises all environment-driven settings so that no module needs to
read os.environ directly.  Credentials (Cloudinary, etc.) are loaded
from environment variables and must never be committed to source control.

Usage:
    from app.common.config import get_settings
    settings = get_settings()
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Immutable application settings populated from the environment."""

    # ── Cloudinary ──────────────────────────────────────────────────
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: str = ""

    # ── Runtime ─────────────────────────────────────────────────────
    environment: Literal["development", "staging", "production"] = "development"
    max_image_size_mb: int = 10

    # ── CORS (development convenience) ──────────────────────────────
    cors_allowed_origins: list[str] = ["http://localhost:5173"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton of the application settings."""
    return Settings()
