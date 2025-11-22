"""
Database Configuration and Session Management

Provides async SQLAlchemy engine, session factory, and database utilities
for the Clinical Care Tools application.
"""

from typing import AsyncGenerator, Optional

from sqlalchemy import MetaData, event, pool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import DeclarativeMeta

from app.config import settings

# Define naming convention for database constraints
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)

# Create base class for declarative models
Base: DeclarativeMeta = declarative_base(metadata=metadata)


class DatabaseManager:
    """
    Manages database connections and sessions.

    This class provides a centralized way to manage the database
    engine and session factory, with support for health checks
    and graceful shutdown.
    """

    def __init__(self) -> None:
        """Initialize the database manager."""
        self._engine: Optional[AsyncEngine] = None
        self._sessionmaker: Optional[async_sessionmaker] = None

    @property
    def engine(self) -> AsyncEngine:
        """
        Get or create the database engine.

        Returns:
            AsyncEngine: The SQLAlchemy async engine.
        """
        if self._engine is None:
            self._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                pool_size=settings.DATABASE_POOL_SIZE,
                max_overflow=settings.DATABASE_MAX_OVERFLOW,
                pool_pre_ping=settings.DATABASE_POOL_PRE_PING,
                pool_recycle=3600,  # Recycle connections after 1 hour
                connect_args={
                    "server_settings": {"application_name": settings.APP_NAME},
                    "command_timeout": 60,
                }
            )
        return self._engine

    @property
    def sessionmaker(self) -> async_sessionmaker:
        """
        Get or create the async session factory.

        Returns:
            async_sessionmaker: The session factory.
        """
        if self._sessionmaker is None:
            self._sessionmaker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return self._sessionmaker

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async database session for dependency injection.

        Yields:
            AsyncSession: Database session instance.

        Raises:
            Exception: On database connection or transaction errors.
        """
        async with self.sessionmaker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def init_db(self) -> None:
        """
        Initialize database (create tables).

        This should typically be handled by Alembic migrations
        in production environments.
        """
        async with self.engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import Base  # noqa: F401

            await conn.run_sync(Base.metadata.create_all)

    async def check_health(self) -> bool:
        """
        Check database health by executing a simple query.

        Returns:
            bool: True if database is healthy, False otherwise.
        """
        try:
            async with self.sessionmaker() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception:
            return False

    async def close(self) -> None:
        """
        Close all database connections.

        Should be called during application shutdown.
        """
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._sessionmaker = None


# Create global database manager instance
db_manager = DatabaseManager()

# Export commonly used functions for backward compatibility
engine = db_manager.engine
get_session = db_manager.get_session
init_db = db_manager.init_db


async def check_db_health() -> bool:
    """
    Check database health.

    Returns:
        bool: True if database is healthy, False otherwise.
    """
    return await db_manager.check_health()


async def close_db() -> None:
    """
    Close database connections.

    Called at application shutdown.
    """
    await db_manager.close()


# Configure connection pool logging in debug mode
if settings.DEBUG:
    @event.listens_for(pool.Pool, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Log new database connections in debug mode."""
        connection_record.info['pid'] = dbapi_conn.get_backend_pid()

    @event.listens_for(pool.Pool, "checkout")
    def receive_checkout(dbapi_conn, connection_record, connection_proxy):
        """Log connection checkouts in debug mode."""
        pid = connection_record.info.get('pid', 'unknown')
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Connection {pid} checked out from pool")
