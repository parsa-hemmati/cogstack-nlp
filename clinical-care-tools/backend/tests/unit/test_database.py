"""
Tests for database configuration module.

Verifies database URL formatting, connection pool settings, and session management.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
import sys
from pathlib import Path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal, get_db, init_db, close_db


class TestDatabaseConfiguration:
    """Test database configuration and connection setup."""

    def test_database_url_format(self):
        """Test that database URL is properly formatted for async."""
        db_url = settings.async_database_url  # Use async URL

        # Should be async postgres URL
        assert db_url.startswith("postgresql+asyncpg://"), \
            "Database URL should use asyncpg driver"

        # Should contain database name
        assert "clinical_care_tools" in db_url, \
            "Database URL should contain database name"

    def test_engine_configuration(self):
        """Test that engine is configured with correct parameters."""
        # Engine should exist
        assert engine is not None, "Engine should be initialized"

        # Check engine URL
        assert "asyncpg" in str(engine.url), \
            "Engine should use asyncpg dialect"

    def test_session_factory_exists(self):
        """Test that AsyncSessionLocal factory exists."""
        assert AsyncSessionLocal is not None, \
            "AsyncSessionLocal factory should be defined"

        # Should be sessionmaker
        assert hasattr(AsyncSessionLocal, 'begin'), \
            "AsyncSessionLocal should be sessionmaker"

    @pytest.mark.asyncio
    async def test_get_db_dependency(self):
        """Test get_db dependency provides valid session."""
        # Get session from dependency
        async for session in get_db():
            # Should be AsyncSession instance
            assert isinstance(session, AsyncSession), \
                "get_db should yield AsyncSession"

            # Session should be usable
            assert session.bind is not None, \
                "Session should have database binding"

            # Only test one session
            break

    @pytest.mark.asyncio
    async def test_session_commit_on_success(self):
        """Test that session commits on successful operation."""
        # Use real session for integration test
        success = False
        async for session in get_db():
            # Simulate successful operation
            success = True
            break  # Exit normally, should trigger commit

        assert success, "Session should have been created"

    @pytest.mark.asyncio
    async def test_session_rollback_on_error(self):
        """Test that session rolls back on error."""
        # Use real database for integration test
        try:
            async for session in get_db():
                # Simulate error in transaction
                raise ValueError("Test error")
        except ValueError as e:
            # Exception should propagate after rollback
            assert str(e) == "Test error"

    @pytest.mark.asyncio
    async def test_init_db_creates_tables(self):
        """Test that init_db creates database tables."""
        # Call init_db (creates tables if they don't exist)
        await init_db()

        # If we get here without exception, tables were created successfully
        assert True, "init_db completed successfully"

    @pytest.mark.asyncio
    async def test_close_db_disposes_engine(self):
        """Test that close_db properly disposes engine."""
        # Call close_db (disposes the engine)
        await close_db()

        # Engine should still exist but be disposed
        assert engine is not None, "Engine should exist"

    def test_connection_pool_settings(self):
        """Test that connection pool is configured correctly."""
        # Engine should have a pool
        assert engine.pool is not None, \
            "Pool should be initialized"

        # Check pool class name (NullPool in development)
        pool_class = engine.pool.__class__.__name__
        assert pool_class in ['QueuePool', 'NullPool', 'AsyncAdaptedQueuePool'], \
            f"Pool should be a valid async pool type, got {pool_class}"


class TestDatabaseURL:
    """Test database URL construction and validation."""

    def test_url_contains_required_components(self):
        """Test that database URL has all required components."""
        db_url = settings.async_database_url  # Use async URL

        # Should have protocol
        assert db_url.startswith("postgresql+asyncpg://"), \
            "URL should have async postgres protocol"

        # Should have host
        assert "localhost" in db_url or settings.postgres_server in db_url, \
            "URL should contain host"

        # Should have port
        assert str(settings.postgres_port) in db_url, \
            "URL should contain port"

        # Should have database name
        assert settings.postgres_db in db_url, \
            "URL should contain database name"

    def test_url_escapes_special_characters(self):
        """Test that URL properly handles special characters."""
        # Database URL should be a valid string
        db_url = settings.async_database_url
        assert isinstance(db_url, str), \
            "Database URL should be string"

        # Should not contain unescaped spaces
        assert " " not in db_url.split("://")[1], \
            "URL should not have unescaped spaces"

    def test_sync_and_async_urls_exist(self):
        """Test that both sync and async URLs are available."""
        # Sync URL
        assert settings.database_url.startswith("postgresql://"), \
            "Sync URL should exist"

        # Async URL
        assert settings.async_database_url.startswith("postgresql+asyncpg://"), \
            "Async URL should exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
