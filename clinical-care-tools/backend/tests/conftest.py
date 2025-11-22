"""
Pytest fixtures and configuration for Clinical Care Tools backend tests.

This module provides shared fixtures for:
- Database connections (SQLite for testing)
- HTTP clients (TestClient)
- Authentication (test users, JWT tokens)
- Mocking (external services like MedCAT, Elasticsearch)
- Test data factories (using factory-boy)
"""

import asyncio
from typing import AsyncGenerator, Generator
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import your app components (update paths as needed)
# from app.main import app
# from app.core.database import Base, get_db
# from app.core.config import settings
# from app.core.security import create_access_token
# from app.models.user import User
# from app.models.audit_log import AuditLog


# ==============================================================================
# DATABASE FIXTURES
# ==============================================================================

@pytest.fixture(scope="session")
def db_engine():
    """
    Create an in-memory SQLite database for testing.

    Using SQLite in-memory database avoids network overhead and ensures
    test isolation. StaticPool ensures proper concurrent access in tests.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    # Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    # Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Create a session factory for the test database."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
    )


@pytest.fixture
def db_session(db_session_factory) -> Generator[Session, None, None]:
    """
    Provide a database session for each test.

    Automatically rolls back after each test to ensure isolation.
    """
    session = db_session_factory()

    yield session

    # Rollback to ensure clean state
    session.rollback()
    session.close()


@pytest.fixture
def override_get_db(db_session):
    """
    Override FastAPI dependency for database session.

    Usage:
        def test_something(client, override_get_db):
            app.dependency_overrides[get_db] = override_get_db
    """
    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    return _override_get_db


# ==============================================================================
# HTTP CLIENT FIXTURES
# ==============================================================================

@pytest.fixture
def client(override_get_db):
    """
    Provide a FastAPI TestClient for API testing.

    Automatically overrides database dependency to use test database.
    """
    # NOTE: Uncomment when app is available
    # from app.main import app
    # from app.core.database import get_db
    #
    # app.dependency_overrides[get_db] = override_get_db
    #
    # return TestClient(app)

    # Placeholder
    class MockClient:
        def get(self, *args, **kwargs):
            return type('Response', (), {'status_code': 200, 'json': lambda: {}})()

        def post(self, *args, **kwargs):
            return type('Response', (), {'status_code': 201, 'json': lambda: {}})()

        def put(self, *args, **kwargs):
            return type('Response', (), {'status_code': 200, 'json': lambda: {}})()

        def delete(self, *args, **kwargs):
            return type('Response', (), {'status_code': 204, 'json': lambda: {}})()

    return MockClient()


# ==============================================================================
# AUTHENTICATION FIXTURES
# ==============================================================================

@pytest.fixture
def test_user_data():
    """Provide test user credentials."""
    return {
        "email": "testuser@example.com",
        "password": "test_password_123!",
        "full_name": "Test User",
        "is_active": True,
    }


@pytest.fixture
def test_admin_user_data():
    """Provide test admin user credentials."""
    return {
        "email": "admin@example.com",
        "password": "admin_password_123!",
        "full_name": "Admin User",
        "is_active": True,
        "is_admin": True,
    }


@pytest.fixture
def test_clinician_user_data():
    """Provide test clinician user credentials."""
    return {
        "email": "clinician@example.com",
        "password": "clinician_password_123!",
        "full_name": "Dr. Clinician",
        "is_active": True,
        "role": "clinician",
    }


@pytest.fixture
def access_token(test_user_data):
    """
    Generate a valid JWT access token for testing.

    Token expires in 1 hour (default test duration).
    """
    # NOTE: Uncomment when security module is available
    # from app.core.security import create_access_token
    #
    # return create_access_token(
    #     subject=test_user_data["email"],
    #     expires_delta=timedelta(hours=1),
    # )

    # Placeholder
    return "test_access_token_placeholder"


@pytest.fixture
def admin_access_token(test_admin_user_data):
    """Generate a valid JWT access token for admin user."""
    # NOTE: Uncomment when security module is available
    # from app.core.security import create_access_token
    #
    # return create_access_token(
    #     subject=test_admin_user_data["email"],
    #     expires_delta=timedelta(hours=1),
    # )

    # Placeholder
    return "test_admin_access_token_placeholder"


@pytest.fixture
def clinician_access_token(test_clinician_user_data):
    """Generate a valid JWT access token for clinician user."""
    # NOTE: Uncomment when security module is available
    # from app.core.security import create_access_token
    #
    # return create_access_token(
    #     subject=test_clinician_user_data["email"],
    #     expires_delta=timedelta(hours=1),
    # )

    # Placeholder
    return "test_clinician_access_token_placeholder"


@pytest.fixture
def auth_headers(access_token):
    """Provide authentication headers for API requests."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_access_token):
    """Provide authentication headers for admin API requests."""
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture
def clinician_auth_headers(clinician_access_token):
    """Provide authentication headers for clinician API requests."""
    return {"Authorization": f"Bearer {clinician_access_token}"}


# ==============================================================================
# MOCK SERVICE FIXTURES
# ==============================================================================

@pytest.fixture
def mock_medcat_service(mocker):
    """
    Mock MedCAT NLP service responses.

    Provides realistic mock responses for:
    - Entity extraction
    - Meta-annotation inference
    - Linking
    """
    mock_service = mocker.MagicMock()

    # Mock successful entity extraction
    mock_service.get_entities.return_value = {
        "entities": [
            {
                "id": 0,
                "text": "diabetes",
                "start": 10,
                "end": 18,
                "cui": "C0011847",
                "pretty_name": "Diabetes Mellitus",
                "confidence": 0.92,
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Temporality": "Current",
                    "Experiencer": "Patient",
                    "Certainty": "Certain",
                }
            }
        ]
    }

    # Mock bulk processing
    mock_service.bulk_process.return_value = {
        "documents": [
            {
                "id": 1,
                "entities": []
            }
        ]
    }

    return mock_service


@pytest.fixture
def mock_elasticsearch_service(mocker):
    """
    Mock Elasticsearch service for patient search.

    Provides realistic mock responses for:
    - Patient search
    - Aggregations
    - Complex queries
    """
    mock_es = mocker.MagicMock()

    # Mock successful search
    mock_es.search.return_value = {
        "hits": {
            "total": {"value": 1},
            "hits": [
                {
                    "_id": "patient_123",
                    "_score": 0.85,
                    "_source": {
                        "mrn": "MRN123456",
                        "name": "John Doe",
                        "age": 65,
                        "conditions": ["diabetes", "hypertension"]
                    }
                }
            ]
        }
    }

    return mock_es


@pytest.fixture
def mock_redis_service(mocker):
    """
    Mock Redis service for caching.

    Provides realistic mock responses for:
    - Get/set operations
    - Expiration
    - Pattern matching
    """
    mock_redis = mocker.MagicMock()

    # Mock successful get
    mock_redis.get.return_value = None

    # Mock successful set
    mock_redis.set.return_value = True

    # Mock successful delete
    mock_redis.delete.return_value = 1

    return mock_redis


# ==============================================================================
# TEST DATA FACTORIES
# ==============================================================================

@pytest.fixture
def user_factory(db_session):
    """
    Factory for creating test users.

    Usage:
        test_user = user_factory(email="user@example.com", is_active=True)
    """
    # NOTE: Uncomment when factories are defined
    # from tests.factories.user_factory import UserFactory
    # return UserFactory._create

    # Placeholder
    def _create_user(**kwargs):
        user_data = {
            "email": kwargs.get("email", "testuser@example.com"),
            "full_name": kwargs.get("full_name", "Test User"),
            "is_active": kwargs.get("is_active", True),
        }
        return user_data

    return _create_user


@pytest.fixture
def patient_factory(db_session):
    """Factory for creating test patients."""
    # NOTE: Uncomment when factories are defined
    # from tests.factories.patient_factory import PatientFactory
    # return PatientFactory._create

    # Placeholder
    def _create_patient(**kwargs):
        patient_data = {
            "mrn": kwargs.get("mrn", "MRN123456"),
            "first_name": kwargs.get("first_name", "John"),
            "last_name": kwargs.get("last_name", "Doe"),
            "date_of_birth": kwargs.get("date_of_birth", "1960-01-01"),
        }
        return patient_data

    return _create_patient


@pytest.fixture
def document_factory(db_session):
    """Factory for creating test clinical documents."""
    # Placeholder
    def _create_document(**kwargs):
        document_data = {
            "patient_id": kwargs.get("patient_id", 1),
            "document_type": kwargs.get("document_type", "clinical_note"),
            "content": kwargs.get("content", "Patient presents with chest pain."),
            "created_at": kwargs.get("created_at", datetime.now()),
        }
        return document_data

    return _create_document


# ==============================================================================
# AUDIT LOGGING FIXTURES
# ==============================================================================

@pytest.fixture
def audit_logger_spy(mocker):
    """
    Spy on audit logger to verify PHI access is logged.

    Usage:
        def test_patient_access(client, audit_logger_spy):
            response = client.get("/api/v1/patients/123", headers=auth_headers)
            audit_logger_spy.assert_called_once()
    """
    return mocker.patch("app.services.audit_service.audit_log")


# ==============================================================================
# PYTEST CONFIGURATION
# ==============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for async tests.

    Ensures proper async/await support in pytest-asyncio.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "security: mark test as security-critical")
    config.addinivalue_line("markers", "compliance: mark test as compliance-related")
