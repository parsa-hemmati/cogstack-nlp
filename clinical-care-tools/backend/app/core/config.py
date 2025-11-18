"""Application configuration management."""

from functools import lru_cache
from typing import Any, Dict, List, Optional

from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "Clinical Care Tools"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="INFO")

    # Database
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="changeme")
    POSTGRES_HOST: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="clinical_care_tools")

    DATABASE_URL: Optional[str] = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Optional[str], info: Any) -> str:
        """Construct database URL from components if not provided."""
        if isinstance(v, str) and v:
            return v

        data = info.data
        return str(
            PostgresDsn.build(
                scheme="postgresql+asyncpg",
                username=data.get("POSTGRES_USER"),
                password=data.get("POSTGRES_PASSWORD"),
                host=data.get("POSTGRES_HOST"),
                port=data.get("POSTGRES_PORT"),
                path=data.get("POSTGRES_DB", ""),
            )
        )

    # Database connection pool
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)
    DB_POOL_TIMEOUT: int = Field(default=30)
    DB_ECHO: bool = Field(default=False)

    # Redis
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_URL: Optional[str] = None

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: Optional[str], info: Any) -> str:
        """Construct Redis URL from components if not provided."""
        if isinstance(v, str) and v:
            return v

        data = info.data
        return f"redis://{data.get('REDIS_HOST')}:{data.get('REDIS_PORT')}/{data.get('REDIS_DB')}"

    REDIS_POOL_SIZE: int = Field(default=10)
    REDIS_POOL_MAX_SIZE: int = Field(default=20)

    # Elasticsearch
    ELASTICSEARCH_HOST: str = Field(default="localhost")
    ELASTICSEARCH_PORT: int = Field(default=9200)
    ELASTICSEARCH_URL: Optional[str] = None

    @field_validator("ELASTICSEARCH_URL", mode="before")
    @classmethod
    def assemble_elasticsearch_url(cls, v: Optional[str], info: Any) -> str:
        """Construct Elasticsearch URL from components if not provided."""
        if isinstance(v, str) and v:
            return v

        data = info.data
        return f"http://{data.get('ELASTICSEARCH_HOST')}:{data.get('ELASTICSEARCH_PORT')}"

    ELASTICSEARCH_INDEX: str = Field(default="documents")

    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-use-openssl-rand-hex-32"
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    # Security
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8080", "http://localhost:3000"]
    )
    SESSION_TIMEOUT_MINUTES: int = Field(default=30)
    MAX_LOGIN_ATTEMPTS: int = Field(default=5)
    LOCKOUT_DURATION_MINUTES: int = Field(default=15)

    # CogStack-ModelServe
    MODELSERVE_URL: str = Field(default="http://localhost:8001")
    MODELSERVE_TIMEOUT: int = Field(default=30)

    # Audit Logging (HIPAA compliance)
    AUDIT_LOG_ENABLED: bool = Field(default=True)
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=2920)  # 8 years

    # Feature Flags
    ENABLE_FHIR_EXPORT: bool = Field(default=False)
    ENABLE_CLINICAL_DECISION_SUPPORT: bool = Field(default=False)
    ENABLE_BREAK_GLASS_ACCESS: bool = Field(default=True)

    # Performance
    BACKEND_WORKERS: int = Field(default=4)

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
