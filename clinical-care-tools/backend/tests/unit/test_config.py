"""Tests for application configuration."""

import pytest

from app.core.config import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()

    assert settings.APP_NAME == "Clinical Care Tools"
    assert settings.APP_VERSION == "0.1.0"
    assert settings.ENVIRONMENT == "development"
    assert settings.DEBUG is False


def test_settings_postgres_url():
    """Test PostgreSQL URL construction."""
    settings = Settings(
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpass",
        POSTGRES_HOST="testhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb",
    )

    assert "postgresql+asyncpg://" in settings.DATABASE_URL
    assert "testuser:testpass@testhost:5432/testdb" in settings.DATABASE_URL


def test_settings_redis_url():
    """Test Redis URL construction."""
    settings = Settings(
        REDIS_HOST="redishost",
        REDIS_PORT=6379,
        REDIS_DB=0,
    )

    assert settings.REDIS_URL == "redis://redishost:6379/0"


def test_is_development():
    """Test development environment detection."""
    settings = Settings(ENVIRONMENT="development")
    assert settings.is_development is True
    assert settings.is_production is False


def test_is_production():
    """Test production environment detection."""
    settings = Settings(ENVIRONMENT="production")
    assert settings.is_production is True
    assert settings.is_development is False


def test_get_settings_cached():
    """Test settings are cached."""
    settings1 = get_settings()
    settings2 = get_settings()

    assert settings1 is settings2
