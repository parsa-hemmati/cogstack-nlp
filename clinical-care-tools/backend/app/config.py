"""
Application Configuration

Handles all application settings including database, security, and environment variables.
Uses Pydantic Settings for type validation and environment variable loading.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import timedelta

from pydantic import AnyHttpUrl, PostgresDsn, RedisDsn, field_validator, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All settings can be overridden via environment variables or .env file.
    """

    # Application Settings
    APP_NAME: str = "Clinical Care Tools"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"  # development, staging, production
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # API Settings
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WORKERS: int = 4

    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-this-in-production-min-32-chars"
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[Union[str, AnyHttpUrl]] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost"
    ]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database Settings (PostgreSQL)
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "clinical_care_tools"
    DATABASE_USER: str = "cct_user"
    DATABASE_PASSWORD: str = "change-this-password"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    DATABASE_POOL_PRE_PING: bool = True
    DATABASE_ECHO: bool = False

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return (
            f"postgresql+asyncpg://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@"
            f"{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_SSL: bool = False
    REDIS_POOL_SIZE: int = 10

    @property
    def REDIS_URL(self) -> str:
        """Construct Redis URL from components."""
        password_part = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        protocol = "rediss" if self.REDIS_SSL else "redis"
        return f"{protocol}://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Elasticsearch Settings
    ELASTICSEARCH_HOST: str = "localhost"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: Optional[str] = "elastic"
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    ELASTICSEARCH_USE_SSL: bool = False
    ELASTICSEARCH_VERIFY_CERTS: bool = False

    # MedCAT Service Settings
    MEDCAT_SERVICE_URL: str = "http://localhost:5000"
    MEDCAT_SERVICE_TIMEOUT: int = 30
    MEDCAT_MODEL_PATH: str = "/models/medcat"

    # FHIR Server Settings (optional)
    FHIR_SERVER_URL: Optional[str] = None
    FHIR_SERVER_AUTH_TYPE: str = "none"  # none, basic, oauth2

    # Audit Logging Settings
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_FILE: str = "/app/logs/audit.log"
    AUDIT_LOG_MAX_BYTES: int = 10485760  # 10MB
    AUDIT_LOG_BACKUP_COUNT: int = 10

    # File Storage Settings
    UPLOAD_FOLDER: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "txt", "docx", "rtf", "json"]
    TEMP_FOLDER: str = "/app/temp"

    # Session Settings
    SESSION_TIMEOUT_MINUTES: int = 60
    SESSION_EXTEND_ON_ACTIVITY: bool = True
    SESSION_IDLE_TIMEOUT_MINUTES: int = 15  # Phase 5: Idle timeout
    SESSION_ABSOLUTE_TIMEOUT_HOURS: int = 24  # Phase 5: Absolute timeout
    SESSION_BINDING_ENABLED: bool = True  # Phase 5: IP + User-Agent binding
    SESSION_HIJACK_DETECTION: bool = True  # Phase 5: Hijacking detection
    SESSION_MAX_CONCURRENT: int = 2  # Phase 5: Max concurrent sessions

    @property
    def session_idle_timeout(self) -> timedelta:
        """Get idle timeout as timedelta."""
        return timedelta(minutes=self.SESSION_IDLE_TIMEOUT_MINUTES)

    @property
    def session_absolute_timeout(self) -> timedelta:
        """Get absolute timeout as timedelta."""
        return timedelta(hours=self.SESSION_ABSOLUTE_TIMEOUT_HOURS)

    # Break-Glass Access Settings (Phase 5)
    BREAK_GLASS_ENABLED: bool = True
    BREAK_GLASS_ACCESS_WINDOW_MINUTES: int = 60  # Emergency access duration
    BREAK_GLASS_REVIEW_DEADLINE_HOURS: int = 24  # Mandatory review deadline
    BREAK_GLASS_REQUIRED_ROLE: str = "clinician"  # Role that can request
    BREAK_GLASS_REVIEWER_ROLE: str = "security_team"  # Role that reviews

    # Data Retention Settings (Phase 6)
    DATA_RETENTION_ENABLED: bool = True
    CLINICAL_DOCUMENTS_RETENTION_YEARS: int = 8  # NHS requirement
    AUDIT_LOGS_RETENTION_YEARS: int = 7  # HIPAA requirement
    SESSION_DATA_RETENTION_DAYS: int = 90  # After last activity
    TEMP_FILES_RETENTION_DAYS: int = 7
    RESEARCH_DATA_RETENTION_YEARS: int = 10
    RETENTION_JOB_ENABLED: bool = True
    RETENTION_JOB_CRON: str = "0 2 * * *"  # 2 AM daily

    # Clinical Safety Settings (Phase 6)
    CLINICAL_SAFETY_ENABLED: bool = True
    NLP_CONFIDENCE_THRESHOLD: float = 0.7  # Warn if < this
    CLINICAL_SAFETY_CRITICAL_CONCEPTS: List[str] = [
        "allergy",
        "adverse_reaction",
        "contraindication",
        "critical_finding"
    ]
    DUPLICATE_PATIENT_CHECK_ENABLED: bool = True
    REQUIRED_DEMOGRAPHIC_FIELDS: List[str] = ["first_name", "last_name", "date_of_birth", "mrn"]
    FUTURE_DATE_CHECK_ENABLED: bool = True

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000

    # Health Check Settings
    HEALTH_CHECK_DB: bool = True
    HEALTH_CHECK_REDIS: bool = True
    HEALTH_CHECK_ES: bool = True
    HEALTH_CHECK_MEDCAT: bool = False

    # Feature Flags
    FEATURE_PATIENT_SEARCH: bool = True
    FEATURE_TIMELINE_VIEW: bool = True
    FEATURE_META_ANNOTATIONS: bool = True
    FEATURE_FHIR_EXPORT: bool = False
    FEATURE_BULK_PROCESSING: bool = False

    # Compliance Settings
    HIPAA_COMPLIANCE_MODE: bool = True
    GDPR_COMPLIANCE_MODE: bool = True
    PHI_ENCRYPTION_ENABLED: bool = True
    AUDIT_ALL_PHI_ACCESS: bool = True

    # Email Settings (for notifications)
    EMAIL_ENABLED: bool = False
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: str = "noreply@clinical-care-tools.local"

    # Monitoring Settings
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PORT: int = 9090
    OPENTELEMETRY_ENABLED: bool = False
    OPENTELEMETRY_ENDPOINT: Optional[str] = None

    # Development Settings (disable in production)
    RELOAD: bool = True
    PROFILING_ENABLED: bool = False
    SQL_QUERY_LOGGING: bool = False

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Ensure secret key is sufficiently long for security."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """Validate application environment."""
        valid_envs = ["development", "staging", "production", "testing"]
        if v not in valid_envs:
            raise ValueError(f"APP_ENV must be one of {valid_envs}")
        return v

    def dict(self) -> Dict[str, Any]:
        """
        Override to exclude sensitive information when serializing.

        Returns:
            Dict with sensitive fields masked.
        """
        data = super().model_dump()
        # Mask sensitive fields
        sensitive_fields = [
            "SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_PASSWORD",
            "REDIS_PASSWORD", "ELASTICSEARCH_PASSWORD", "SMTP_PASSWORD"
        ]
        for field in sensitive_fields:
            if field in data and data[field]:
                data[field] = "***REDACTED***"
        return data


# Create global settings instance
settings = Settings()
