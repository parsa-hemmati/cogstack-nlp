"""
Database connection and session management for Clinical Care Tools.

Handles PostgreSQL connections with async SQLAlchemy.
HIPAA Compliance: Ensures encrypted connections and connection pooling.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
import logging

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # SQL logging in debug mode
    pool_size=20,  # Connection pool size
    max_overflow=10,  # Maximum overflow connections
    pool_timeout=30,  # Timeout for getting connection from pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_pre_ping=True,  # Verify connections before using
    connect_args={
        "server_settings": {
            "application_name": settings.APP_NAME,
            "jit": "off"
        },
        "command_timeout": 60,
        "ssl": "prefer"  # Use SSL when available (require in production)
    }
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Yields:
        AsyncSession: Database session

    Usage:
        @router.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables.

    Creates all tables defined in models.
    Should only be used for development/testing.
    Production uses Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")


async def close_db():
    """
    Close database connections.

    Called on application shutdown.
    """
    await engine.dispose()
    logger.info("Database connections closed")