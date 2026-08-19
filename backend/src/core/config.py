"""
NyayaAI Backend — Core Configuration

Loads settings from environment variables / .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Database ──
    DATABASE_URL: str = "postgresql+asyncpg://nyaya:nyaya_dev_password@localhost:5432/nyayaai"

    # ── Google Gemini ──
    GEMINI_API_KEY: str = ""

    # ── File Upload ──
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 20

    # ── Logging ──
    LOG_LEVEL: str = "INFO"

    # ── CORS ──
    FRONTEND_URL: str = "http://localhost:5173"

    @property
    def upload_path(self) -> Path:
        """Resolved upload directory path."""
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024


# Singleton instance — import this everywhere
settings = Settings()
