"""
Database Base Configuration
SQLAlchemy declarative base and database engine setup
"""
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from app.db.base_class import Base  # Import Base from settings-free module


# Base is imported from base_class.py (no settings dependency)


def create_database_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.

    Returns:
        AsyncEngine configured with connection pool settings
    """
    # Import settings here to avoid loading during migrations
    from app.core.config import settings

    return create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DATABASE_ECHO,  # SQL logging
        pool_size=settings.DATABASE_POOL_SIZE,  # Minimum connections in pool
        max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Max additional connections
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Connection timeout (seconds)
        pool_recycle=settings.DATABASE_POOL_RECYCLE,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using
    )


def get_engine() -> AsyncEngine:
    """
    Get or create the global engine instance.
    Lazy initialization to avoid loading settings during migrations.
    """
    global _engine
    if '_engine' not in globals():
        _engine = create_database_engine()
    return _engine
