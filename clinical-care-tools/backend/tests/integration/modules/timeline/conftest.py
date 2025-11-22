"""
Timeline Integration Test Fixtures.

Provides test data and fixtures for timeline integration tests.
"""

import pytest
from uuid import uuid4
from datetime import date, datetime, timedelta
from app.modules.patient.models import Patient
from app.modules.document.models import Document
from app.modules.timeline.models import TimelineFilter, TimelineExport
from app.modules.auth.models import User
from app.models.project import Project


@pytest.fixture
def test_patient(db_session, test_user):
    """Create a test patient with complete demographics."""
    patient = Patient(
        id=uuid4(),
        nhs_number="1234567890",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1980, 1, 1),
        gender="M",
        email="john.doe@test.com",
        phone="+44 20 1234 5678"
    )
    db_session.add(patient)
    db_session.commit()
    db_session.refresh(patient)
    return patient


@pytest.fixture
def test_patient_with_documents(db_session, test_patient, test_project):
    """Create a test patient with multiple documents for timeline testing."""
    documents = []

    # Create 5 documents over 6 month period
    base_date = datetime(2024, 1, 1)
    document_types = ["Clinical Note", "Lab Report", "Discharge Summary", "Radiology Report", "Progress Note"]

    for i, doc_type in enumerate(document_types):
        document_date = base_date + timedelta(days=i * 30)
        doc = Document(
            id=uuid4(),
            patient_id=test_patient.id,
            project_id=test_project.id,
            title=f"{doc_type} {i+1}",
            content=f"Test content for {doc_type}. Patient has diabetes and hypertension. No chest pain reported.",
            document_date=document_date.date(),
            document_type=doc_type,
            author=f"Dr. Smith {i+1}",
            source="Test System"
        )
        db_session.add(doc)
        documents.append(doc)

    db_session.commit()

    for doc in documents:
        db_session.refresh(doc)

    return test_patient, documents


@pytest.fixture
def test_concepts_data():
    """Mock Elasticsearch concept data for timeline testing."""
    return [
        {
            "concept_cui": "C0011849",
            "name": "Diabetes Mellitus",
            "type": "Disease",
            "first_mention_date": "2024-01-01",
            "last_mention_date": "2024-05-01",
            "mention_count": 4,
            "mentions": [
                {
                    "document_id": "doc-1",
                    "document_date": "2024-01-01",
                    "sentence": "Patient has diabetes and hypertension.",
                    "start_char": 13,
                    "end_char": 21,
                    "meta_annotations": {
                        "negation": "Affirmed",
                        "experiencer": "Patient",
                        "temporality": "Current",
                        "certainty": "Confirmed"
                    },
                    "confidence": 0.95
                },
                {
                    "document_id": "doc-2",
                    "document_date": "2024-02-01",
                    "sentence": "Patient has diabetes and hypertension.",
                    "start_char": 13,
                    "end_char": 21,
                    "meta_annotations": {
                        "negation": "Affirmed",
                        "experiencer": "Patient",
                        "temporality": "Current",
                        "certainty": "Confirmed"
                    },
                    "confidence": 0.93
                }
            ]
        },
        {
            "concept_cui": "C0020538",
            "name": "Hypertension",
            "type": "Disease",
            "first_mention_date": "2024-01-01",
            "last_mention_date": "2024-04-01",
            "mention_count": 3,
            "mentions": [
                {
                    "document_id": "doc-1",
                    "document_date": "2024-01-01",
                    "sentence": "Patient has diabetes and hypertension.",
                    "start_char": 26,
                    "end_char": 38,
                    "meta_annotations": {
                        "negation": "Affirmed",
                        "experiencer": "Patient",
                        "temporality": "Current",
                        "certainty": "Confirmed"
                    },
                    "confidence": 0.92
                }
            ]
        },
        {
            "concept_cui": "C0008031",
            "name": "Chest Pain",
            "type": "Symptom",
            "first_mention_date": "2024-01-01",
            "last_mention_date": "2024-01-01",
            "mention_count": 1,
            "mentions": [
                {
                    "document_id": "doc-1",
                    "document_date": "2024-01-01",
                    "sentence": "No chest pain reported.",
                    "start_char": 3,
                    "end_char": 13,
                    "meta_annotations": {
                        "negation": "Negated",
                        "experiencer": "Patient",
                        "temporality": "Current",
                        "certainty": "Confirmed"
                    },
                    "confidence": 0.88
                }
            ]
        }
    ]


@pytest.fixture
def test_timeline_filter(db_session, test_user):
    """Create a test timeline filter preset."""
    timeline_filter = TimelineFilter(
        id=uuid4(),
        user_id=test_user.id,
        name="Active Patient Conditions",
        description="Filter for active, confirmed patient conditions",
        filters={
            "negation": "Affirmed",
            "experiencer": "Patient",
            "temporality": "Current",
            "certainty": "Confirmed"
        },
        is_default=False
    )
    db_session.add(timeline_filter)
    db_session.commit()
    db_session.refresh(timeline_filter)
    return timeline_filter


@pytest.fixture
def mock_elasticsearch_timeline_repo(mocker):
    """Mock Elasticsearch timeline repository for integration tests."""
    mock_repo = mocker.MagicMock()

    # Mock query_patient_concepts to return test concept data
    mock_repo.query_patient_concepts.return_value = [
        {
            "concept_cui": "C0011849",
            "name": "Diabetes Mellitus",
            "type": "Disease",
            "first_mention_date": "2024-01-01",
            "mention_count": 4
        },
        {
            "concept_cui": "C0020538",
            "name": "Hypertension",
            "type": "Disease",
            "first_mention_date": "2024-01-01",
            "mention_count": 3
        }
    ]

    # Mock aggregate_concept_frequency
    mock_repo.aggregate_concept_frequency.return_value = {
        "C0011849": {"2024-01": 2, "2024-02": 1, "2024-03": 1},
        "C0020538": {"2024-01": 1, "2024-02": 1, "2024-03": 1}
    }

    return mock_repo
