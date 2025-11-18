"""
Database Base Configuration
SQLAlchemy declarative base and database engine setup
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from app.core.config import settings


# Declarative base for all ORM models
Base = declarative_base()


def create_database_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.

    Returns:
        AsyncEngine configured with connection pool settings
    """
    return create_async_engine(
        str(settings.DATABASE_URL),
        echo=settings.DATABASE_ECHO,  # SQL logging
        pool_size=settings.DATABASE_POOL_SIZE,  # Minimum connections in pool
        max_overflow=settings.DATABASE_MAX_OVERFLOW,  # Max additional connections
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,  # Connection timeout (seconds)
        pool_recycle=settings.DATABASE_POOL_RECYCLE,  # Recycle connections after 1 hour
        pool_pre_ping=True,  # Verify connections before using
    )


# Create global engine instance
engine = create_database_engine()
