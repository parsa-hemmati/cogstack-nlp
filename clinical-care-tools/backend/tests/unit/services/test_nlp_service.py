"""
Unit tests for NLP Service

Tests NLP processing, entity extraction, and meta-annotation filtering.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from datetime import datetime

from app.services.nlp_service import NLPService
from app.clients.cogstack_client import CogStackResponse, ExtractedEntity, MetaAnnotation


@pytest.fixture
def mock_db():
    """Create mock database session."""
    db = AsyncMock()
    db.get = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_cogstack_client():
    """Create mock CogStack client."""
    client = AsyncMock()
    client.annotate_text = AsyncMock()
    client.detect_phi = AsyncMock()
    return client


@pytest.fixture
def mock_audit_service():
    """Create mock audit service."""
    return AsyncMock()


@pytest.fixture
def mock_document_service():
    """Create mock document service."""
    service = AsyncMock()
    service.update_processing_status = AsyncMock()
    return service


@pytest.fixture
def nlp_service(mock_db, mock_cogstack_client, mock_audit_service, mock_document_service):
    """Create NLP service instance."""
    return NLPService(mock_db, mock_cogstack_client, mock_audit_service, mock_document_service)


@pytest.fixture
def sample_document():
    """Create sample document."""
    doc = MagicMock()
    doc.id = uuid4()
    doc.project_id = uuid4()
    doc.content = b"encrypted_content"
    doc.encryption_key_id = "key-123"
    doc.medcat_status = "pending"
    doc.phi_types = []
    return doc


@pytest.fixture
def sample_medical_entities():
    """Create sample medical entities from CogStack."""
    return [
        ExtractedEntity(
            cui="C0004238",
            pretty_name="Atrial Flutter",
            source_value="atrial flutter",
            start=10,
            end=24,
            confidence=0.85,
            meta_anns=MetaAnnotation(
                Negation="Affirmed",
                Temporality="Current",
                Experiencer="Patient",
                Certainty="Confirmed"
            ),
            types=["CONDITION"]
        ),
        ExtractedEntity(
            cui="C0011849",
            pretty_name="Diabetes Mellitus",
            source_value="diabetes",
            start=50,
            end=58,
            confidence=0.92,
            meta_anns=MetaAnnotation(
                Negation="Negated",  # Should be filtered out
                Temporality="Current",
                Experiencer="Patient",
                Certainty="Confirmed"
            ),
            types=["CONDITION"]
        ),
        ExtractedEntity(
            cui="C0020538",
            pretty_name="Hypertension",
            source_value="hypertension",
            start=100,
            end=112,
            confidence=0.88,
            meta_anns=MetaAnnotation(
                Negation="Affirmed",
                Temporality="Historical",
                Experiencer="Family",  # Should be filtered out
                Certainty="Confirmed"
            ),
            types=["CONDITION"]
        )
    ]


@pytest.fixture
def sample_phi_entities():
    """Create sample PHI entities."""
    return [
        {
            "text": "John Smith",
            "start": 0,
            "end": 10,
            "phi_type": "NAME",
            "confidence": 0.95
        },
        {
            "text": "123 456 7890",
            "start": 25,
            "end": 37,
            "phi_type": "NHS_NUMBER",
            "confidence": 0.90
        }
    ]


class TestNLPService:
    """Test NLP service functionality."""

    @pytest.mark.asyncio
    async def test_process_document_success(
        self, nlp_service, mock_db, mock_cogstack_client, mock_audit_service,
        mock_document_service, sample_document, sample_medical_entities, sample_phi_entities
    ):
        """Test successful document processing."""
        # Arrange
        mock_db.get.return_value = sample_document

        mock_cogstack_response = CogStackResponse(
            entities=sample_medical_entities,
            processing_time_ms=150.0,
            model_version="1.0.0",
            success=True
        )
        mock_cogstack_client.annotate_text.return_value = mock_cogstack_response
        mock_cogstack_client.detect_phi.return_value = sample_phi_entities

        with patch('app.services.nlp_service.decrypt_document') as mock_decrypt:
            mock_decrypt.return_value = b"Patient has atrial flutter. No diabetes. Family history of hypertension."

            # Act
            result = await nlp_service.process_document(
                document_id=sample_document.id,
                user_id=uuid4()
            )

        # Assert
        assert result["status"] == "success"
        assert result["entities_count"] > 0
        assert result["medical_entities"] == 3
        assert result["phi_entities"] == 2
        mock_document_service.update_processing_status.assert_called()
        mock_audit_service.log_nlp_processing.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_document_already_complete(
        self, nlp_service, mock_db, sample_document
    ):
        """Test processing already completed document."""
        # Arrange
        sample_document.medcat_status = "complete"
        mock_db.get.return_value = sample_document

        # Act
        result = await nlp_service.process_document(
            document_id=sample_document.id,
            user_id=uuid4(),
            force_reprocess=False
        )

        # Assert
        assert result["status"] == "already_processed"

    @pytest.mark.asyncio
    async def test_process_document_not_found(
        self, nlp_service, mock_db
    ):
        """Test processing non-existent document."""
        # Arrange
        mock_db.get.return_value = None

        # Act & Assert
        with pytest.raises(ValueError) as exc:
            await nlp_service.process_document(
                document_id=uuid4(),
                user_id=uuid4()
            )
        assert "not found" in str(exc.value)

    def test_should_include_entity_filters_negated(
        self, nlp_service, sample_medical_entities
    ):
        """Test meta-annotation filtering for negated conditions."""
        # Entity with Negation="Negated" should be excluded
        entity = sample_medical_entities[1]
        assert nlp_service._should_include_entity(entity) is False

    def test_should_include_entity_filters_family_history(
        self, nlp_service, sample_medical_entities
    ):
        """Test meta-annotation filtering for family history."""
        # Entity with Experiencer="Family" should be excluded
        entity = sample_medical_entities[2]
        assert nlp_service._should_include_entity(entity) is False

    def test_should_include_entity_accepts_patient_current(
        self, nlp_service, sample_medical_entities
    ):
        """Test meta-annotation filtering accepts patient's current conditions."""
        # Entity with correct meta-annotations should be included
        entity = sample_medical_entities[0]
        assert nlp_service._should_include_entity(entity) is True

    def test_classify_phi_category_direct_identifier(self, nlp_service):
        """Test PHI category classification for direct identifiers."""
        result = nlp_service._classify_phi_category("NAME")
        assert result == "DIRECT_IDENTIFIER"

        result = nlp_service._classify_phi_category("NHS_NUMBER")
        assert result == "DIRECT_IDENTIFIER"

    def test_classify_phi_category_quasi_identifier(self, nlp_service):
        """Test PHI category classification for quasi-identifiers."""
        result = nlp_service._classify_phi_category("DATE")
        assert result == "QUASI_IDENTIFIER"

        result = nlp_service._classify_phi_category("POSTCODE")
        assert result == "QUASI_IDENTIFIER"

    def test_extract_structured_phi_name(self, nlp_service):
        """Test structured data extraction for names."""
        phi = {"phi_type": "NAME", "text": "John Smith"}
        result = nlp_service._extract_structured_phi(phi)

        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"

    def test_extract_structured_phi_nhs_number(self, nlp_service):
        """Test structured data extraction for NHS numbers."""
        phi = {"phi_type": "NHS_NUMBER", "text": "123 456 7890"}
        result = nlp_service._extract_structured_phi(phi)

        assert result["nhs_number"] == "1234567890"

    @pytest.mark.asyncio
    async def test_get_document_entities(
        self, nlp_service, mock_db
    ):
        """Test retrieving entities for a document."""
        # Arrange
        mock_entities = [MagicMock(), MagicMock()]
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_entities
        mock_db.execute.return_value = mock_result

        # Act
        result = await nlp_service.get_document_entities(
            document_id=uuid4(),
            include_phi=True
        )

        # Assert
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_batch_process_documents(
        self, nlp_service, mock_db, mock_cogstack_client
    ):
        """Test batch processing of multiple documents."""
        # Arrange
        doc_ids = [uuid4() for _ in range(3)]
        mock_db.get.return_value = MagicMock()

        mock_cogstack_response = CogStackResponse(
            entities=[],
            processing_time_ms=100.0,
            model_version="1.0.0",
            success=True
        )
        mock_cogstack_client.annotate_text.return_value = mock_cogstack_response
        mock_cogstack_client.detect_phi.return_value = []

        with patch('app.services.nlp_service.decrypt_document') as mock_decrypt:
            mock_decrypt.return_value = b"Test content"

            # Act
            results = await nlp_service.batch_process_documents(
                document_ids=doc_ids,
                user_id=uuid4(),
                batch_size=2
            )

        # Assert
        assert len(results) == 3
        for result in results:
            assert "status" in result