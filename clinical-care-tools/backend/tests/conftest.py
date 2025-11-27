"""
Pytest configuration and fixtures for integration and unit tests.

Provides:
- Database session fixtures
- Authenticated HTTP client fixtures
- Test user fixtures (admin, clinician, researcher, viewer)
- Test data fixtures
"""

import asyncio
import os
import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import bcrypt
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.services.auth_service import create_access_token


# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/clinical_care_tools_test"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

# Create test session factory
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Uses transactions and rollback to ensure test isolation.
    """
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session = TestSessionLocal(bind=connection)

    yield session

    await session.close()
    await transaction.rollback()
    await connection.close()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    Create all tables before each test, drop after.

    Ensures clean database state for each test.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db():
    """Override database dependency for testing."""
    connection = await test_engine.connect()
    transaction = await connection.begin()

    session = TestSessionLocal(bind=connection)

    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for unauthenticated requests."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as ac:
        yield ac


# ===== User Fixtures =====


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    """Create test admin user."""
    password = "AdminPass123!"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        id=uuid.uuid4(),
        username="test_admin",
        full_name="Test Admin",
        hashed_password=hashed_password,
        role="admin",
        is_active=True,
        must_change_password=False
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_clinician(db_session: AsyncSession) -> User:
    """Create test clinician user."""
    password = "ClinicianPass123!"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        id=uuid.uuid4(),
        username="test_clinician",
        full_name="Test Clinician",
        hashed_password=hashed_password,
        role="clinician",
        is_active=True,
        must_change_password=False
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_researcher(db_session: AsyncSession) -> User:
    """Create test researcher user."""
    password = "ResearcherPass123!"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        id=uuid.uuid4(),
        username="test_researcher",
        full_name="Test Researcher",
        hashed_password=hashed_password,
        role="researcher",
        is_active=True,
        must_change_password=False
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def test_viewer(db_session: AsyncSession) -> User:
    """Create test viewer user."""
    password = "ViewerPass123!"
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    user = User(
        id=uuid.uuid4(),
        username="test_viewer",
        full_name="Test Viewer",
        hashed_password=hashed_password,
        role="viewer",
        is_active=True,
        must_change_password=False
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


# ===== Authenticated Client Fixtures =====


@pytest_asyncio.fixture
async def admin_client(test_admin: User) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client authenticated as admin."""
    token = create_access_token(
        data={"sub": test_admin.username, "user_id": str(test_admin.id), "role": test_admin.role}
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def clinician_client(test_clinician: User) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client authenticated as clinician."""
    token = create_access_token(
        data={"sub": test_clinician.username, "user_id": str(test_clinician.id), "role": test_clinician.role}
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def researcher_client(test_researcher: User) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client authenticated as researcher."""
    token = create_access_token(
        data={"sub": test_researcher.username, "user_id": str(test_researcher.id), "role": test_researcher.role}
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def viewer_client(test_viewer: User) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client authenticated as viewer."""
    token = create_access_token(
        data={"sub": test_viewer.username, "user_id": str(test_viewer.id), "role": test_viewer.role}
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"}
    ) as ac:
        yield ac
