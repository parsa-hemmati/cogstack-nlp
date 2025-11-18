"""
Pytest configuration and fixtures for testing.

Provides shared fixtures for all tests including:
- Database session (async)
- Test client
- Authentication tokens
"""
import asyncio
import pytest
from datetime import datetime, date
from typing import AsyncGenerator, Generator, Dict
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient

from app.db.base import Base
from app.core.config import settings
from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.document import Document, ProcessingStatus
from app.models.extracted_entity import ExtractedEntity, EntityType
from app.services.auth_service import auth_service

# Override settings for testing
settings.DATABASE_URL = "sqlite+aiosqlite:///:memory:"
settings.JWT_SECRET_KEY = "test-secret-key-do-not-use-in-production"
settings.ENCRYPTION_KEY = "test-encryption-key-32-bytes-min"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create test database session with in-memory SQLite.

    Each test gets a fresh database with all tables created.
    Database is cleaned up after each test.
    """
    # Create async engine with in-memory SQLite
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,  # Set to True for SQL debugging
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    # Provide session to test
    async with async_session() as session:
        yield session

    # Cleanup: drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # Dispose engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create FastAPI test client with database override.

    Uses httpx.AsyncClient for async HTTP requests.
    Overrides database dependency to use test database.
    """
    # Override database dependency
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    # Create async client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clear overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user_clinician(db: AsyncSession) -> User:
    """
    Create test clinician user.

    Returns:
        User with clinician role for authentication tests
    """
    user = User(
        id=uuid4(),
        username="test_clinician",
        email="clinician@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=False,
    )
    user.set_password("test_password_123")

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@pytest.fixture(scope="function")
async def test_user_researcher(db: AsyncSession) -> User:
    """
    Create test researcher user (viewer role).

    Returns:
        User with researcher role for limited access tests
    """
    user = User(
        id=uuid4(),
        username="test_researcher",
        email="researcher@test.com",
        role="researcher",
        is_active=True,
        can_break_glass=False,
    )
    user.set_password("test_password_123")

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@pytest.fixture(scope="function")
async def auth_headers_clinician(test_user_clinician: User) -> Dict[str, str]:
    """
    Generate JWT token for clinician user.

    Returns:
        Authorization headers dict with Bearer token
    """
    token_data = auth_service.create_access_token(
        user_id=str(test_user_clinician.id),
        role=test_user_clinician.role
    )

    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


@pytest.fixture(scope="function")
async def auth_headers_viewer(test_user_researcher: User) -> Dict[str, str]:
    """
    Generate JWT token for researcher user (viewer role).

    Returns:
        Authorization headers dict with Bearer token
    """
    token_data = auth_service.create_access_token(
        user_id=str(test_user_researcher.id),
        role=test_user_researcher.role
    )

    return {
        "Authorization": f"Bearer {token_data['access_token']}"
    }


@pytest.fixture(scope="function")
async def test_db_with_search_data(db: AsyncSession, test_user_clinician: User) -> AsyncSession:
    """
    Create test database with patients and diabetes annotations.

    Creates sample data for patient search tests:
    - 3 patients with diabetes annotations
    - Documents with encrypted content
    - Extracted entities with meta-annotations

    Returns:
        Database session with test data
    """
    now = datetime.utcnow()

    # Patient 1: Has diabetes (Current, Affirmed, Patient)
    patient1 = Patient(
        id=uuid4(),
        nhs_number="1234567890",
        full_name="John Smith",
        date_of_birth=date(1980, 1, 15),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient1)

    doc1 = Document(
        id=uuid4(),
        filename="patient1_note.rtf",
        content_type="application/rtf",
        content_hash="hash1234567890abcdef1234567890abcdef1234567890abcdef1234567890ab",
        encrypted_content=b"encrypted content here (test)",
        file_size=1024,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc1)

    entity1 = ExtractedEntity(
        id=uuid4(),
        document_id=doc1.id,
        patient_id=patient1.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",  # Diabetes mellitus CUI
        pretty_name="Diabetes mellitus",
        start_char=10,
        end_char=28,
        accuracy=0.95,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Definite",
        },
    )
    db.add(entity1)

    # Patient 2: Has diabetes with different meta-annotations
    patient2 = Patient(
        id=uuid4(),
        nhs_number="2345678901",
        full_name="Jane Doe",
        date_of_birth=date(1975, 5, 20),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient2)

    doc2 = Document(
        id=uuid4(),
        filename="patient2_note.rtf",
        content_type="application/rtf",
        content_hash="hash2345678901abcdef1234567890abcdef1234567890abcdef1234567890ab",
        encrypted_content=b"encrypted content here (test)",
        file_size=1024,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc2)

    entity2 = ExtractedEntity(
        id=uuid4(),
        document_id=doc2.id,
        patient_id=patient2.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",
        pretty_name="Diabetes mellitus",
        start_char=15,
        end_char=33,
        accuracy=0.92,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Probable",
        },
    )
    db.add(entity2)

    # Patient 3: Different condition (not diabetes)
    patient3 = Patient(
        id=uuid4(),
        nhs_number="3456789012",
        full_name="Bob Johnson",
        date_of_birth=date(1990, 10, 10),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient3)

    doc3 = Document(
        id=uuid4(),
        filename="patient3_note.rtf",
        content_type="application/rtf",
        content_hash="hash3456789012abcdef1234567890abcdef1234567890abcdef1234567890ab",
        encrypted_content=b"encrypted content here (test)",
        file_size=1024,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc3)

    entity3 = ExtractedEntity(
        id=uuid4(),
        document_id=doc3.id,
        patient_id=patient3.id,
        entity_type=EntityType.CLINICAL,
        cui="C0020538",  # Hypertension CUI
        pretty_name="Hypertension",
        start_char=20,
        end_char=32,
        accuracy=0.98,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Definite",
        },
    )
    db.add(entity3)

    await db.commit()
    return db


@pytest.fixture(scope="function")
async def test_db_with_annotations(db: AsyncSession, test_user_clinician: User) -> AsyncSession:
    """
    Create test database with varied meta-annotation examples.

    Creates data for testing meta-annotation filtering:
    - Negated mentions ("no diabetes")
    - Family history ("father has diabetes")
    - Historical conditions ("had diabetes 10 years ago")
    - Current patient conditions (control group)

    Returns:
        Database session with varied test data
    """
    now = datetime.utcnow()

    # Patient A: Affirmed, Current, Patient (should match all filters)
    patient_a = Patient(
        id=uuid4(),
        nhs_number="1111111111",
        full_name="Alice Anderson",
        date_of_birth=date(1985, 1, 1),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient_a)

    doc_a = Document(
        id=uuid4(),
        filename="patient_a_note.rtf",
        content_type="application/rtf",
        content_hash="hashAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
        encrypted_content=b"Patient has diabetes.",
        file_size=100,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc_a)

    entity_a = ExtractedEntity(
        id=uuid4(),
        document_id=doc_a.id,
        patient_id=patient_a.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",
        pretty_name="Diabetes mellitus",
        start_char=12,
        end_char=20,
        accuracy=0.95,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Definite",
        },
    )
    db.add(entity_a)

    # Patient B: Negated (should be excluded by includeNegated=false)
    patient_b = Patient(
        id=uuid4(),
        nhs_number="2222222222",
        full_name="Bob Brown",
        date_of_birth=date(1990, 2, 2),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient_b)

    doc_b = Document(
        id=uuid4(),
        filename="patient_b_note.rtf",
        content_type="application/rtf",
        content_hash="hashBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
        encrypted_content=b"Patient denies diabetes.",
        file_size=100,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc_b)

    entity_b = ExtractedEntity(
        id=uuid4(),
        document_id=doc_b.id,
        patient_id=patient_b.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",
        pretty_name="Diabetes mellitus",
        start_char=15,
        end_char=23,
        accuracy=0.90,
        meta_anns={
            "Negation": "Negated",  # Negated!
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Definite",
        },
    )
    db.add(entity_b)

    # Patient C: Family history (should be excluded by includeFamily=false)
    patient_c = Patient(
        id=uuid4(),
        nhs_number="3333333333",
        full_name="Carol Clark",
        date_of_birth=date(1988, 3, 3),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient_c)

    doc_c = Document(
        id=uuid4(),
        filename="patient_c_note.rtf",
        content_type="application/rtf",
        content_hash="hashCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC",
        encrypted_content=b"Father has diabetes.",
        file_size=100,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc_c)

    entity_c = ExtractedEntity(
        id=uuid4(),
        document_id=doc_c.id,
        patient_id=patient_c.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",
        pretty_name="Diabetes mellitus",
        start_char=11,
        end_char=19,
        accuracy=0.93,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Family",  # Family!
            "Certainty": "Definite",
        },
    )
    db.add(entity_c)

    # Patient D: Historical (should be excluded by temporal=current)
    patient_d = Patient(
        id=uuid4(),
        nhs_number="4444444444",
        full_name="David Davis",
        date_of_birth=date(1970, 4, 4),
        first_seen_at=now,
        last_seen_at=now,
        document_count=1,
    )
    db.add(patient_d)

    doc_d = Document(
        id=uuid4(),
        filename="patient_d_note.rtf",
        content_type="application/rtf",
        content_hash="hashDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDDD",
        encrypted_content=b"Had diabetes 10 years ago.",
        file_size=100,
        uploaded_by=test_user_clinician.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc_d)

    entity_d = ExtractedEntity(
        id=uuid4(),
        document_id=doc_d.id,
        patient_id=patient_d.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",
        pretty_name="Diabetes mellitus",
        start_char=4,
        end_char=12,
        accuracy=0.88,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Historical",  # Historical!
            "Experiencer": "Patient",
            "Certainty": "Definite",
        },
    )
    db.add(entity_d)

    await db.commit()
    return db
