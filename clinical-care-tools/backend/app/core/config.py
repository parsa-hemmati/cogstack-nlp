"""
Configuration settings for Clinical Care Tools Backend.

This module defines all configuration parameters for the application including
security settings, database connections, and service configurations.

HIPAA Compliance: All sensitive configuration loaded from environment variables.
"""
from typing import List, Optional
from datetime import timedelta
from pydantic_settings import BaseSettings
from pydantic import Field, validator
import secrets


class Settings(BaseSettings):
    """Application configuration settings."""

    # Application
    APP_NAME: str = "Clinical Care Tools"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = Field(default=False, env="DEBUG")

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_care_tools",
        env="DATABASE_URL"
    )

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )

    # JWT Settings
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 8  # 8 hours as per spec
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # 7 days as per spec

    # Session Settings
    SESSION_IDLE_TIMEOUT_MINUTES: int = 15  # 15 minutes idle timeout
    SESSION_ABSOLUTE_TIMEOUT_HOURS: int = 24  # Force re-auth after 24 hours
    SESSION_MAX_CONCURRENT: int = 2  # Max 2 concurrent sessions per user
    SESSION_BINDING_ENABLED: bool = True  # IP and User-Agent binding
    SESSION_HIJACK_DETECTION: bool = True  # Detect session hijacking

    # Security
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_BCRYPT_ROUNDS: int = 12  # Cost factor 12 as per spec
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8080", "http://localhost:3000"],
        env="CORS_ORIGINS"
    )
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_PHI_ACCESS: bool = True  # HIPAA requirement
    AUDIT_LOG_AUTH_EVENTS: bool = True
    AUDIT_LOG_ADMIN_ACTIONS: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_LOGIN_ATTEMPTS: int = 5  # Max 5 login attempts per 15 minutes
    RATE_LIMIT_LOGIN_WINDOW_MINUTES: int = 15

    # Break-Glass Access (Phase 5)
    BREAK_GLASS_ENABLED: bool = True
    BREAK_GLASS_DURATION_MINUTES: int = 60  # 60 minute expiry
    BREAK_GLASS_REQUIRE_REASON: bool = True
    BREAK_GLASS_NOTIFY_SECURITY: bool = True
    BREAK_GLASS_REVIEW_HOURS: int = 24  # Review within 24 hours

    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = Field(default=None, env="SMTP_HOST")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    SMTP_FROM_EMAIL: str = Field(default="noreply@clinical-care-tools.local", env="SMTP_FROM_EMAIL")
    SECURITY_ALERT_EMAIL: Optional[str] = Field(default=None, env="SECURITY_ALERT_EMAIL")

    # MedCAT Service
    MEDCAT_SERVICE_URL: str = Field(
        default="http://localhost:8001",
        env="MEDCAT_SERVICE_URL"
    )
    MEDCAT_TIMEOUT_SECONDS: int = 30

    # Feature Flags
    FEATURE_PATIENT_SEARCH: bool = True
    FEATURE_FHIR_EXPORT: bool = False
    FEATURE_BREAK_GLASS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("JWT_SECRET_KEY")
    def validate_jwt_secret(cls, v):
        """Ensure JWT secret is sufficiently long."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @property
    def jwt_access_token_expire(self) -> timedelta:
        """Get JWT access token expiration as timedelta."""
        return timedelta(hours=self.JWT_ACCESS_TOKEN_EXPIRE_HOURS)

    @property
    def jwt_refresh_token_expire(self) -> timedelta:
        """Get JWT refresh token expiration as timedelta."""
        return timedelta(days=self.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    @property
    def session_idle_timeout(self) -> timedelta:
        """Get session idle timeout as timedelta."""
        return timedelta(minutes=self.SESSION_IDLE_TIMEOUT_MINUTES)

    @property
    def session_absolute_timeout(self) -> timedelta:
        """Get session absolute timeout as timedelta."""
        return timedelta(hours=self.SESSION_ABSOLUTE_TIMEOUT_HOURS)


# Singleton instance
settings = Settings()