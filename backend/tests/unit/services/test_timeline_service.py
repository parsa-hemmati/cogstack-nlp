"""
Unit tests for TimelineService.

Tests use mocked database and Elasticsearch to avoid external dependencies.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.timeline_service import TimelineService
from app.schemas.timeline import (
    TimelineFilters, DateRange, ConceptMention, MetaAnnotations,
    PatientTimeline, TimelineConcept, TimelineDocument
)
from app.models.user import User
from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity


@pytest.fixture
def mock_db():
    """Mock async database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Mock user for audit logging."""
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.username = "test_user"
    return user


@pytest.fixture
def mock_audit_service():
    """Mock audit service."""
    with patch('app.services.timeline_service.AuditService') as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_es_repo():
    """Mock Elasticsearch repository."""
    with patch('app.services.timeline_service.ElasticsearchTimelineRepository') as mock:
        instance = AsyncMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def sample_documents():
    """Sample documents."""
    patient_id = uuid4()
    doc1_id = uuid4()
    doc2_id = uuid4()

    doc1 = Document(
        id=doc1_id,
        filename="clinical_note_001.rtf",
        created_at=datetime(2023, 1, 15, 10, 30),
        content_type="application/rtf",
        content_hash="hash1",
        encrypted_content=b"encrypted",
        file_size=1024,
        uploaded_by=uuid4()
    )

    doc2 = Document(
        id=doc2_id,
        filename="lab_results_2023.rtf",
        created_at=datetime(2023, 2, 20, 14, 15),
        content_type="application/rtf",
        content_hash="hash2",
        encrypted_content=b"encrypted",
        file_size=2048,
        uploaded_by=uuid4()
    )

    return [doc1, doc2], patient_id


@pytest.fixture
def sample_concept_mentions():
    """Sample concept mentions from Elasticsearch."""
    return [
        ConceptMention(
            concept_cui="C0011849",
            concept_name="Diabetes Mellitus",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 1, 15, 10, 30),
            sentence="Patient diagnosed with Type 2 Diabetes.",
            meta_annotations=MetaAnnotations(
                Negation="Affirmed",
                Temporality="Current",
                Experiencer="Patient",
                Certainty="High"
            ),
            confidence=0.95
        ),
        ConceptMention(
            concept_cui="C0011849",
            concept_name="Diabetes Mellitus",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 2, 20, 14, 15),
            sentence="HbA1c 8.5%, diabetes management plan updated.",
            meta_annotations=MetaAnnotations(
                Negation="Affirmed",
                Temporality="Current",
                Experiencer="Patient",
                Certainty="High"
            ),
            confidence=0.92
        ),
        ConceptMention(
            concept_cui="C0020538",
            concept_name="Hypertension",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 1, 10, 9, 0),
            sentence="History of hypertension.",
            meta_annotations=MetaAnnotations(
                Negation="Affirmed",
                Temporality="Historical",
                Experiencer="Patient",
                Certainty="High"
            ),
            confidence=0.88
        )
    ]


@pytest.mark.asyncio
async def test_get_patient_timeline_basic(
    mock_db, mock_user, mock_audit_service, mock_es_repo, sample_documents, sample_concept_mentions
):
    """Test basic patient timeline retrieval."""
    # Arrange
    service = TimelineService(mock_db)
    service.audit_service = mock_audit_service
    service.es_repo = mock_es_repo

    docs, patient_id = sample_documents

    # Mock database queries
    # Query 1: Get document IDs via extracted_entities
    doc_ids_result = AsyncMock()
    doc_ids_result.fetchall.return_value = [(docs[0].id,), (docs[1].id,)]

    # Query 2: Get documents
    docs_result = AsyncMock()
    docs_result.scalars.return_value.all.return_value = docs

    # Query 3 & 4: Get concept CUIs for each document
    concepts_result = AsyncMock()
    concepts_result.fetchall.return_value = [("C0011849",), ("C0020538",)]

    mock_db.execute.side_effect = [doc_ids_result, docs_result, concepts_result, concepts_result]

    # Mock Elasticsearch query
    mock_es_repo.query_concepts_by_patient.return_value = sample_concept_mentions

    # Act
    filters = TimelineFilters()
    timeline = await service.get_patient_timeline(
        patient_id=patient_id,
        filters=filters,
        user=mock_user
    )

    # Assert
    assert isinstance(timeline, PatientTimeline)
    assert timeline.patient_id == str(patient_id)
    assert len(timeline.documents) == 2
    assert len(timeline.concepts) == 2  # 2 unique concepts
    assert timeline.date_range is not None

    # Verify audit logging
    mock_audit_service.log_phi_access.assert_called_once()
    call_args = mock_audit_service.log_phi_access.call_args
    assert call_args.kwargs["user"] == mock_user
    assert call_args.kwargs["patient_id"] == str(patient_id)
    assert call_args.kwargs["action"] == "VIEW_TIMELINE"


@pytest.mark.asyncio
async def test_get_patient_timeline_with_filters(
    mock_db, mock_user, mock_audit_service, mock_es_repo, sample_documents, sample_concept_mentions
):
    """Test patient timeline with filters applied."""
    # Arrange
    service = TimelineService(mock_db)
    service.audit_service = mock_audit_service
    service.es_repo = mock_es_repo

    docs, patient_id = sample_documents

    # Mock database queries
    doc_ids_result = AsyncMock()
    doc_ids_result.fetchall.return_value = [(docs[0].id,)]

    docs_result = AsyncMock()
    docs_result.scalars.return_value.all.return_value = [docs[0]]

    concepts_result = AsyncMock()
    concepts_result.fetchall.return_value = [("C0011849",)]

    mock_db.execute.side_effect = [doc_ids_result, docs_result, concepts_result]

    # Mock Elasticsearch query with filtered results
    filtered_mentions = [sample_concept_mentions[0]]
    mock_es_repo.query_concepts_by_patient.return_value = filtered_mentions

    # Act
    filters = TimelineFilters(
        concepts=["C0011849"],
        date_range=DateRange(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 1, 31)
        ),
        meta_annotations={"Negation": "Affirmed"}
    )
    timeline = await service.get_patient_timeline(
        patient_id=patient_id,
        filters=filters,
        user=mock_user
    )

    # Assert
    assert len(timeline.concepts) == 1
    assert timeline.concepts[0].concept_cui == "C0011849"
    assert timeline.filters_applied == filters

    # Verify Elasticsearch was called with filters
    mock_es_repo.query_concepts_by_patient.assert_called_once_with(
        patient_id=str(patient_id),
        concept_filter=["C0011849"],
        date_range=filters.date_range,
        meta_annotations={"Negation": "Affirmed"}
    )


@pytest.mark.asyncio
async def test_aggregate_concepts_multiple_mentions(mock_db, sample_concept_mentions):
    """Test concept aggregation with multiple mentions."""
    # Arrange
    service = TimelineService(mock_db)

    # Act
    concepts = service._aggregate_concepts(sample_concept_mentions)

    # Assert
    assert len(concepts) == 2  # 2 unique concepts (Diabetes, Hypertension)

    # Find diabetes concept
    diabetes = next(c for c in concepts if c.concept_cui == "C0011849")
    assert diabetes.concept_name == "Diabetes Mellitus"
    assert diabetes.mention_count == 2
    assert len(diabetes.mentions) == 2
    assert diabetes.first_mention_date == datetime(2023, 1, 15, 10, 30)

    # Find hypertension concept
    hypertension = next(c for c in concepts if c.concept_cui == "C0020538")
    assert hypertension.concept_name == "Hypertension"
    assert hypertension.mention_count == 1
    assert len(hypertension.mentions) == 1


@pytest.mark.asyncio
async def test_aggregate_concepts_first_mention_date(mock_db):
    """Test first mention date is calculated correctly."""
    # Arrange
    service = TimelineService(mock_db)

    mentions = [
        ConceptMention(
            concept_cui="C0011849",
            concept_name="Diabetes",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 2, 1),
            sentence="Sentence 1",
            meta_annotations=MetaAnnotations(
                Negation="Affirmed", Temporality="Current",
                Experiencer="Patient", Certainty="High"
            ),
            confidence=0.9
        ),
        ConceptMention(
            concept_cui="C0011849",
            concept_name="Diabetes",
            concept_type="condition",
            document_id=str(uuid4()),
            date=datetime(2023, 1, 1),  # Earlier date
            sentence="Sentence 2",
            meta_annotations=MetaAnnotations(
                Negation="Affirmed", Temporality="Current",
                Experiencer="Patient", Certainty="High"
            ),
            confidence=0.9
        )
    ]

    # Act
    concepts = service._aggregate_concepts(mentions)

    # Assert
    assert len(concepts) == 1
    assert concepts[0].first_mention_date == datetime(2023, 1, 1)  # Earliest date
    assert concepts[0].mention_count == 2


@pytest.mark.asyncio
async def test_calculate_date_range_from_documents_and_concepts(mock_db, sample_documents, sample_concept_mentions):
    """Test date range calculation from both documents and concepts."""
    # Arrange
    service = TimelineService(mock_db)
    docs, _ = sample_documents

    timeline_docs = [
        TimelineDocument(
            document_id=str(docs[0].id),
            title=docs[0].filename,
            document_type="clinical_note",
            date=docs[0].created_at,
            author=None,
            concepts=[]
        )
    ]

    # Act
    date_range = service._calculate_date_range(timeline_docs, sample_concept_mentions)

    # Assert
    # Earliest: 2023-01-10 (from hypertension concept)
    # Latest: 2023-02-20 (from second diabetes concept)
    assert date_range.start == datetime(2023, 1, 10, 9, 0)
    assert date_range.end == datetime(2023, 2, 20, 14, 15)


@pytest.mark.asyncio
async def test_calculate_date_range_empty_data(mock_db):
    """Test date range calculation with no data."""
    # Arrange
    service = TimelineService(mock_db)

    # Act
    date_range = service._calculate_date_range([], [])

    # Assert
    # Should return current datetime when no data
    assert isinstance(date_range.start, datetime)
    assert isinstance(date_range.end, datetime)
    assert date_range.start == date_range.end


@pytest.mark.asyncio
async def test_infer_document_type(mock_db):
    """Test document type inference from filename."""
    # Arrange
    service = TimelineService(mock_db)

    # Act & Assert
    assert service._infer_document_type("discharge_summary_2023.rtf") == "discharge_summary"
    assert service._infer_document_type("lab_results_Jan.rtf") == "lab_result"
    assert service._infer_document_type("referral_letter.rtf") == "letter"
    assert service._infer_document_type("clinic_note_001.rtf") == "clinical_note"
    assert service._infer_document_type("radiology_report.rtf") == "report"
    assert service._infer_document_type("unknown_file.rtf") == "clinical_note"  # Default


@pytest.mark.asyncio
async def test_service_context_manager(mock_db, mock_es_repo):
    """Test service as async context manager."""
    # Arrange
    service = TimelineService(mock_db)
    service.es_repo = mock_es_repo

    # Act
    async with service as svc:
        assert svc is service

    # Assert
    mock_es_repo.close.assert_called_once()


@pytest.mark.asyncio
async def test_service_close(mock_db, mock_es_repo):
    """Test service close method."""
    # Arrange
    service = TimelineService(mock_db)
    service.es_repo = mock_es_repo

    # Act
    await service.close()

    # Assert
    mock_es_repo.close.assert_called_once()


@pytest.mark.asyncio
async def test_get_patient_timeline_no_documents(
    mock_db, mock_user, mock_audit_service, mock_es_repo
):
    """Test timeline retrieval with no documents."""
    # Arrange
    service = TimelineService(mock_db)
    service.audit_service = mock_audit_service
    service.es_repo = mock_es_repo

    patient_id = uuid4()

    # Mock database query returning no documents
    doc_ids_result = AsyncMock()
    doc_ids_result.fetchall.return_value = []
    mock_db.execute.return_value = doc_ids_result

    # Mock Elasticsearch query returning no concepts
    mock_es_repo.query_concepts_by_patient.return_value = []

    # Act
    timeline = await service.get_patient_timeline(
        patient_id=patient_id,
        filters=TimelineFilters(),
        user=mock_user
    )

    # Assert
    assert len(timeline.documents) == 0
    assert len(timeline.concepts) == 0
    assert timeline.date_range is not None  # Should return current datetime


@pytest.mark.asyncio
async def test_audit_logging_includes_filters(
    mock_db, mock_user, mock_audit_service, mock_es_repo, sample_documents, sample_concept_mentions
):
    """Test that audit log includes filter details."""
    # Arrange
    service = TimelineService(mock_db)
    service.audit_service = mock_audit_service
    service.es_repo = mock_es_repo

    docs, patient_id = sample_documents

    # Mock database queries
    doc_ids_result = AsyncMock()
    doc_ids_result.fetchall.return_value = []
    mock_db.execute.return_value = doc_ids_result

    mock_es_repo.query_concepts_by_patient.return_value = []

    # Act
    filters = TimelineFilters(
        concepts=["C0011849"],
        meta_annotations={"Negation": "Affirmed"}
    )
    await service.get_patient_timeline(
        patient_id=patient_id,
        filters=filters,
        user=mock_user,
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0"
    )

    # Assert
    call_args = mock_audit_service.log_phi_access.call_args.kwargs
    assert call_args["details"]["filters"]["concepts"] == ["C0011849"]
    assert call_args["details"]["filters"]["meta_annotations"] == {"Negation": "Affirmed"}
    assert call_args["ip_address"] == "192.168.1.1"
    assert call_args["user_agent"] == "Mozilla/5.0"
