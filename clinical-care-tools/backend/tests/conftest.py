"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.main import app
from app.models.patient import Patient
from app.models.user import User, UserRole

# Test database URL (use separate database for tests)
TEST_DATABASE_URL = settings.DATABASE_URL.replace("/clinical_care_tools", "/clinical_care_tools_test")


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    # Override database dependency
    async def override_get_db():
        yield db_session

    from app.core.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# User fixtures


@pytest_asyncio.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """Create test admin user."""
    user = User(
        email="admin@example.com",
        hashed_password=get_password_hash("adminpass123"),
        full_name="Admin User",
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_clinician_user(db_session: AsyncSession) -> User:
    """Create test clinician user."""
    user = User(
        email="clinician@example.com",
        hashed_password=get_password_hash("clinicianpass123"),
        full_name="Clinician User",
        role=UserRole.CLINICIAN,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_researcher_user(db_session: AsyncSession) -> User:
    """Create test researcher user."""
    user = User(
        email="researcher@example.com",
        hashed_password=get_password_hash("researcherpass123"),
        full_name="Researcher User",
        role=UserRole.RESEARCHER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_viewer_user(db_session: AsyncSession) -> User:
    """Create test viewer user."""
    user = User(
        email="viewer@example.com",
        hashed_password=get_password_hash("viewerpass123"),
        full_name="Viewer User",
        role=UserRole.VIEWER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def test_user(test_clinician_user: User) -> User:
    """Alias for test_clinician_user (default test user)."""
    return test_clinician_user


# Patient fixtures


@pytest_asyncio.fixture
async def test_patient(db_session: AsyncSession) -> Patient:
    """Create test patient."""
    patient = Patient(
        mrn="TEST12345",
        nhs_number="1234567890",
        first_name="John",
        last_name="Doe",
        date_of_birth="1980-01-01",
        gender="male",
    )
    db_session.add(patient)
    await db_session.commit()
    await db_session.refresh(patient)
    return patient
