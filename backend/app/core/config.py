"""
Application Configuration
Loads configuration from environment variables using Pydantic Settings
"""
from typing import List, Optional, Union
from pydantic import Field, PostgresDsn, RedisDsn, field_validator, model_validator
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

    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url_ssl(cls, v: PostgresDsn) -> PostgresDsn:
        """
        Validate DATABASE_URL has sslmode parameter.

        Warns if sslmode is not set or not 'require' in production.
        Issue #24: Enforce TLS for database connections.
        """
        import logging
        import warnings

        url_str = str(v)

        # Check if sslmode is present in query string
        if 'sslmode' not in url_str:
            warnings.warn(
                "DATABASE_URL missing 'sslmode' parameter. "
                "For HIPAA compliance, add '?sslmode=require' to enforce TLS encryption. "
                "See Issue #24.",
                UserWarning,
                stacklevel=2
            )
        elif 'sslmode=disable' in url_str or 'sslmode=allow' in url_str:
            warnings.warn(
                "DATABASE_URL has weak sslmode setting. "
                "Use 'sslmode=require' for HIPAA compliance. "
                "See Issue #24.",
                UserWarning,
                stacklevel=2
            )

        return v

    # Redis (sessions & cache)
    # Note: Using str instead of RedisDsn because passwords with special chars (+, /, =)
    # cause URL parsing errors. Redis client handles raw URLs correctly.
    REDIS_URL: str
    SESSION_EXPIRE_SECONDS: int = 28800  # 8 hours

    # Celery (background tasks)
    CELERY_BROKER_URL: Optional[str] = None  # Redis URL for Celery broker (optional for testing)
    CELERY_RESULT_BACKEND: Optional[str] = None  # Redis URL for Celery result backend (optional for testing)

    # JWT Authentication
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 8

    # CORS (allow frontend access)
    # Note: Stored as string in env, parsed to list via property
    # Format: comma-separated URLs: "http://localhost:8080,http://frontend:8080"
    cors_origins_str: str = Field(
        default="http://localhost:8080,http://localhost:3000",
        validation_alias="CORS_ORIGINS"
    )

    @property
    def CORS_ORIGINS(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins_str.split(',')]

    # MedCAT Service
    MEDCAT_SERVICE_URL: str = "http://medcat-service:5000"
    MEDCAT_SERVICE_TIMEOUT: int = 300  # 5 minutes

    # Meditech FHIR Integration (Sprint 6 Phase 6.2)
    MEDITECH_CLIENT_ID: Optional[str] = None  # OAuth 2.0 client ID
    MEDITECH_CLIENT_SECRET: Optional[str] = None  # OAuth 2.0 client secret
    MEDITECH_TOKEN_URL: str = "https://meditech-uk.cloud/oauth2/token"  # OAuth token endpoint
    MEDITECH_FHIR_BASE_URL: str = "https://meditech-uk.cloud/fhir/r4"  # FHIR API base URL
    USE_MOCK_FHIR: bool = True  # Use mock FHIR service (default True for local development)

    # Security
    ENCRYPTION_KEY: str  # AES-256 encryption key for PHI (64 hex characters = 32 bytes)
    BREAK_GLASS_LOG_RETENTION_DAYS: int = 2920  # 8 years (HIPAA compliance)

    @field_validator('ENCRYPTION_KEY')
    @classmethod
    def validate_encryption_key(cls, v: str) -> str:
        """
        Validate ENCRYPTION_KEY is cryptographically strong (32 bytes / 64 hex chars).

        Args:
            v: ENCRYPTION_KEY value from environment

        Returns:
            Validated encryption key (hex string)

        Raises:
            ValueError: If key is missing, wrong format, or wrong length
        """
        if not v:
            raise ValueError(
                "ENCRYPTION_KEY is required. Generate with: openssl rand -hex 32"
            )

        # Check if hex-encoded
        try:
            key_bytes = bytes.fromhex(v)
        except ValueError:
            raise ValueError(
                "ENCRYPTION_KEY must be 64 hexadecimal characters. "
                "Generate with: openssl rand -hex 32"
            )

        # Check length (must be 32 bytes = 256 bits for AES-256)
        if len(key_bytes) != 32:
            raise ValueError(
                f"ENCRYPTION_KEY must be 32 bytes (64 hex chars), got {len(key_bytes)} bytes. "
                "Generate with: openssl rand -hex 32"
            )

        return v

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
