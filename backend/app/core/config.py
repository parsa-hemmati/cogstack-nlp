"""
Application Configuration
Loads configuration from environment variables using Pydantic Settings
"""
from typing import List, Optional
from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Clinical Care Tools"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Database (PostgreSQL with async driver)
    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600  # 1 hour
    DATABASE_ECHO: bool = False  # SQL logging (True in development)

    # Redis (sessions & cache)
    REDIS_URL: RedisDsn
    SESSION_EXPIRE_SECONDS: int = 28800  # 8 hours

    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # CORS
    CORS_ORIGINS: List[AnyHttpUrl] = ["http://localhost:8080", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # MedCAT Service
    MEDCAT_SERVICE_URL: AnyHttpUrl = "http://medcat-service:5000"
    MEDCAT_SERVICE_TIMEOUT: int = 300  # 5 minutes

    # Security
    ENCRYPTION_KEY: str  # AES-256 encryption key for PHI
    BREAK_GLASS_LOG_RETENTION_DAYS: int = 2920  # 8 years (HIPAA compliance)

    # Audit Logging
    AUDIT_LOG_RETENTION_DAYS: int = 2920  # 8 years
    AUDIT_LOG_PHI_ACCESS: bool = True

    # Testing
    TESTING: bool = False


# Create global settings instance
settings = Settings()


# Database URL for Alembic (sync driver for migrations)
def get_sync_database_url() -> str:
    """
    Get synchronous database URL for Alembic migrations.

    Converts async driver (asyncpg) to sync driver (psycopg2).
    """
    db_url = str(settings.DATABASE_URL)
    return db_url.replace("postgresql+asyncpg://", "postgresql://")
