import os
from dataclasses import dataclass, field
from typing import Optional


def _get_env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _get_env_int(key: str, default: int) -> int:
    try:
        return int(os.environ[key])
    except (KeyError, ValueError):
        return default


def _get_env_float(key: str, default: float) -> float:
    try:
        return float(os.environ[key])
    except (KeyError, ValueError):
        return default


@dataclass(slots=True)
class Settings:
    backend_port: int = field(default_factory=lambda: _get_env_int("BACKEND_PORT", 8000))

    # OCR services
    paddleocr_url: str = field(default_factory=lambda: _get_env("PADDLEOCR_URL", "http://10.19.26.153:8080"))
    mineru_url: str = field(default_factory=lambda: _get_env("MINERU_URL", "http://10.19.26.153:8000"))

    # Timeouts
    paddleocr_timeout: int = field(default_factory=lambda: _get_env_int("PADDLEOCR_TIMEOUT", 600))
    mineru_timeout: int = field(default_factory=lambda: _get_env_int("MINERU_TIMEOUT", 600))

    # Upload
    max_upload_size_mb: int = field(default_factory=lambda: _get_env_int("MAX_UPLOAD_SIZE_MB", 100))
    upload_dir: str = field(default_factory=lambda: _get_env("UPLOAD_DIR", "./uploads"))

    # Batch
    batch_poll_interval: int = field(default_factory=lambda: _get_env_int("BATCH_POLL_INTERVAL", 5))
    batch_max_concurrent: int = field(default_factory=lambda: _get_env_int("BATCH_MAX_CONCURRENT", 2))

    # Database
    database_path: str = field(default_factory=lambda: _get_env("DATABASE_PATH", "./data/jobs.db"))

    # Logging
    log_level: str = field(default_factory=lambda: _get_env("LOG_LEVEL", "INFO"))


def load_settings() -> Settings:
    return Settings()