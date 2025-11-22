"""
Database connection and session management.

Uses SQLAlchemy 2.0 async engine for PostgreSQL.
Web environment: Native PostgreSQL connection.
Production: Docker-based PostgreSQL.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Create async engine
# Note: NullPool used for testing/development (web environment)
# Production: Use QueuePool with appropriate pool size
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.debug,
    future=True,
    poolclass=NullPool if settings.environment == "development" else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session.

    Usage:
        @app.get("/endpoint")
        async def endpoint(db: AsyncSession = Depends(get_db)):
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


async def init_db() -> None:
    """
    Initialize database.

    Creates all tables defined in Base metadata.
    Call this on application startup.
    """
    async with engine.begin() as conn:
        # Import all models here to ensure they're registered with Base
        from app.models import User  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database connections.

    Call this on application shutdown.
    """
    await engine.dispose()
