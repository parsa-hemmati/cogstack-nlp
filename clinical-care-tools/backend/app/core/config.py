"""
Application configuration settings.

Environment-aware configuration using pydantic-settings.
Adapts to Claude Code on Web environment (no Docker).
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn, Field


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application
    app_name: str = "Clinical Care Tools"
    app_version: str = "0.1.0"
    debug: bool = True
    environment: str = "development"  # development, staging, production

    # API
    api_v1_prefix: str = "/api/v1"

    # Security
    secret_key: str = "development-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    backend_cors_origins: list[str] = ["http://localhost:8080", "http://localhost:3000"]

    # Database - Web Environment Adaptation
    # Note: In web environment, use native PostgreSQL (not Docker)
    # Production: Use Docker-based PostgreSQL
    postgres_server: str = Field(default="localhost", description="PostgreSQL server host")
    postgres_port: int = Field(default=5432, description="PostgreSQL server port")
    postgres_user: str = Field(default="postgres", description="PostgreSQL username")
    postgres_password: str = Field(default="postgres", description="PostgreSQL password")
    postgres_db: str = Field(default="clinical_care_tools", description="PostgreSQL database name")

    @property
    def database_url(self) -> str:
        """Build PostgreSQL database URL."""
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"

    @property
    def async_database_url(self) -> str:
        """Build async PostgreSQL database URL."""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_server}:{self.postgres_port}/{self.postgres_db}"

    # Redis - Web Environment Adaptation
    # Note: In web environment, use native Redis (not Docker)
    # Production: Use Docker-based Redis
    redis_host: str = Field(default="localhost", description="Redis server host")
    redis_port: int = Field(default=6379, description="Redis server port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")

    @property
    def redis_url(self) -> str:
        """Build Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # CogStack-ModelServe - Web Environment Adaptation
    # Note: In web environment, use mock client for testing
    # Production: Use actual CogStack-ModelServe in Docker
    medcat_service_url: str = Field(
        default="http://localhost:8001",
        description="CogStack-ModelServe URL (mocked in web environment)"
    )
    medcat_api_key: Optional[str] = Field(default=None, description="CogStack-ModelServe API key")

    # Audit Logging
    audit_log_enabled: bool = True
    audit_log_file: str = "logs/audit.log"

    # Session Management
    session_timeout_minutes: int = 60
    max_concurrent_sessions: int = 5

    # File Storage (Web Environment: In-memory or PostgreSQL BYTEA)
    # Production: S3 or network file system
    file_storage_backend: str = "postgresql"  # postgresql, s3, filesystem
    max_file_size_mb: int = 50

    # Data Retention (NHS requirement: 8 years)
    data_retention_years: int = 8

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100


# Global settings instance
settings = Settings()
