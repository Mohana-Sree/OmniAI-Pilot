"""
Application configuration module.
Centralized settings using Pydantic.
"""

from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # Application
    app_name: str = "OmniTrust AI"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Database
    database_url: str
    database_pool_size: int = 20
    database_max_overflow: int = 0
    database_echo: bool = False

    # Redis
    redis_url: str
    redis_cache_url: str
    redis_celery_url: str

    # JWT
    secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]

    # MinIO
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_uploads: str = "uploads"
    minio_bucket_models: str = "models"

    # Elasticsearch
    elasticsearch_host: str = "elasticsearch"
    elasticsearch_port: int = 9200
    elasticsearch_index_prefix: str = "omnitrust"

    # Celery
    celery_broker_url: str
    celery_result_backend: str

    # Whisper
    whisper_model: str = "base"
    whisper_device: str = "cpu"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # Monitoring
    prometheus_port: int = 8001

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
