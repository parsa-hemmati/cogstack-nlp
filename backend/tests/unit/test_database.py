"""
Test Database Configuration
Unit tests for database connection, pooling, and session management
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from app.db.base import create_database_engine, engine
from app.db.session import AsyncSessionLocal, get_db
from app.core.config import settings


class TestDatabaseConfiguration:
    """Test database configuration and connection pooling."""

    def test_database_url_format(self):
        """Test that DATABASE_URL is in correct format."""
        db_url = str(settings.DATABASE_URL)
        assert db_url.startswith("postgresql+asyncpg://"), "Should use async driver (asyncpg)"
        assert "@postgres:" in db_url or "@localhost:" in db_url, "Should specify host"
        assert "/clinical_care_tools" in db_url, "Should specify database name"

    def test_connection_pool_settings(self):
        """Test that connection pool is configured correctly."""
        assert settings.DATABASE_POOL_SIZE == 10, "Pool size should be 10"
        assert settings.DATABASE_MAX_OVERFLOW == 20, "Max overflow should be 20"
        assert settings.DATABASE_POOL_TIMEOUT == 30, "Pool timeout should be 30 seconds"
        assert settings.DATABASE_POOL_RECYCLE == 3600, "Pool recycle should be 1 hour"

    def test_engine_creation(self):
        """Test that async engine can be created."""
        test_engine = create_database_engine()
        assert isinstance(test_engine, AsyncEngine), "Should create AsyncEngine"
        assert test_engine.pool.size() == settings.DATABASE_POOL_SIZE, "Pool size should match settings"

    def test_global_engine_exists(self):
        """Test that global engine instance exists."""
        assert engine is not None, "Global engine should be initialized"
        assert isinstance(engine, AsyncEngine), "Global engine should be AsyncEngine"

    def test_session_factory_exists(self):
        """Test that async session factory is configured."""
        assert AsyncSessionLocal is not None, "Session factory should exist"

    @pytest.mark.asyncio
    async def test_session_creation(self):
        """Test that async session can be created."""
        async with AsyncSessionLocal() as session:
            assert isinstance(session, AsyncSession), "Should create AsyncSession"
            assert session.is_active, "Session should be active"

    @pytest.mark.asyncio
    async def test_get_db_dependency(self):
        """Test that get_db() dependency works correctly."""
        async for db in get_db():
            assert isinstance(db, AsyncSession), "get_db() should yield AsyncSession"
            assert db.is_active, "Session should be active"
            break  # Only test first yield

    @pytest.mark.asyncio
    async def test_session_autocommit_disabled(self):
        """Test that sessions don't auto-commit (manual commit required)."""
        async with AsyncSessionLocal() as session:
            # autocommit=False is set in session factory
            assert session.autocommit is False, "Autocommit should be disabled"

    @pytest.mark.asyncio
    async def test_session_autoflush_disabled(self):
        """Test that sessions don't auto-flush (manual flush required)."""
        async with AsyncSessionLocal() as session:
            # autoflush=False is set in session factory
            assert session.autoflush is False, "Autoflush should be disabled"

    def test_pool_pre_ping_enabled(self):
        """Test that pool pre-ping is enabled (verifies connections)."""
        test_engine = create_database_engine()
        # pool_pre_ping=True ensures connections are validated before use
        assert test_engine.pool._pre_ping is True, "Pool pre-ping should be enabled"
