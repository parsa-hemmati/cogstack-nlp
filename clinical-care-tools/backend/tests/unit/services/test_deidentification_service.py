"""Unit tests for De-identification Service (Sprint 4, Phase 4.2)"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.deidentification.deidentification_service import DeidentificationService
from app.services.deidentification.surrogate_service import SurrogateGenerationService
from app.services.phi.phi_detection_service import PHIDetectionService
from app.schemas.deidentification import RedactionMode
from app.schemas.phi import DetectedEntity, PHIEntityType


class TestDeidentificationService:
    """Test de-identification service"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return MagicMock()

    @pytest.fixture
    def phi_service(self):
        """Create PHI detection service"""
        return PHIDetectionService(use_mock=True)

    @pytest.fixture
    def surrogate_service(self):
        """Create surrogate generation service"""
        return SurrogateGenerationService()

    @pytest.fixture
    def service(self, mock_db, phi_service, surrogate_service):
        """Create de-identification service"""
        return DeidentificationService(
            db=mock_db,
            phi_service=phi_service,
            surrogate_service=surrogate_service
        )

    def test_apply_redaction_mask_mode(self, service):
        """Test redaction with mask mode"""
        text = "Patient John Doe (DOB: 01/15/1980)"
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=8, end=16, confidence=0.98),
            DetectedEntity(text="01/15/1980", label=PHIEntityType.DATE, start=23, end=33, confidence=0.95)
        ]

        redacted = service._apply_redaction(text, entities, RedactionMode.MASK)

        assert "[REDACTED]" in redacted
        assert "John Doe" not in redacted
        assert "01/15/1980" not in redacted

    def test_apply_redaction_surrogate_mode(self, service):
        """Test redaction with surrogate mode"""
        text = "Patient John Doe (DOB: 01/15/1980)"
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=8, end=16, confidence=0.98),
            DetectedEntity(text="01/15/1980", label=PHIEntityType.DATE, start=23, end=33, confidence=0.95)
        ]

        mappings = {"John Doe": "Patient-A", "01/15/1980": "01/15/19XX"}
        redacted = service._apply_redaction(text, entities, RedactionMode.SURROGATE, mappings)

        assert "Patient-A" in redacted
        assert "01/15/19XX" in redacted
        assert "John Doe" not in redacted
        assert "01/15/1980" not in redacted

    def test_apply_redaction_remove_mode(self, service):
        """Test redaction with remove mode"""
        text = "Patient John Doe (DOB: 01/15/1980)"
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=8, end=16, confidence=0.98)
        ]

        redacted = service._apply_redaction(text, entities, RedactionMode.REMOVE)

        # Entity removed entirely (no replacement)
        assert "John Doe" not in redacted
        assert "Patient  (" in redacted or "Patient (" in redacted  # Spaces may collapse

    def test_redaction_preserves_non_phi_text(self, service):
        """Test that non-PHI text is preserved"""
        text = "Patient John Doe presents with chest pain and shortness of breath."
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=8, end=16, confidence=0.98)
        ]

        redacted = service._apply_redaction(text, entities, RedactionMode.MASK)

        # Clinical content preserved
        assert "presents with chest pain" in redacted
        assert "shortness of breath" in redacted

    def test_redaction_multiple_entities_same_type(self, service):
        """Test redacting multiple entities of same type"""
        text = "Dr. John Doe referred patient to Dr. Jane Smith."
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=4, end=12, confidence=0.98),
            DetectedEntity(text="Jane Smith", label=PHIEntityType.PERSON, start=38, end=48, confidence=0.97)
        ]

        mappings = {"John Doe": "Patient-A", "Jane Smith": "Patient-B"}
        redacted = service._apply_redaction(text, entities, RedactionMode.SURROGATE, mappings)

        assert "Patient-A" in redacted
        assert "Patient-B" in redacted
        assert "John Doe" not in redacted
        assert "Jane Smith" not in redacted

    def test_redaction_overlapping_entities_handled(self, service):
        """Test handling of overlapping entities"""
        text = "John Doe Smith"
        # Overlapping: "John Doe" [0:8] and "Doe Smith" [5:15]
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=0, end=8, confidence=0.98),
            DetectedEntity(text="Doe Smith", label=PHIEntityType.PERSON, start=5, end=14, confidence=0.95)
        ]

        # Should handle without crashing
        redacted = service._apply_redaction(text, entities, RedactionMode.MASK)
        assert isinstance(redacted, str)

    def test_empty_entities_returns_original(self, service):
        """Test that empty entity list returns original text"""
        text = "No PHI in this text."
        entities = []

        redacted = service._apply_redaction(text, entities, RedactionMode.MASK)
        assert redacted == text

    @pytest.mark.asyncio
    async def test_preview_deidentification(self, service, mock_db):
        """Test preview deidentification"""
        doc_id = uuid4()
        user_id = uuid4()

        previews = await service.preview_deidentification(
            document_ids=[doc_id],
            redaction_mode=RedactionMode.SURROGATE,
            user_id=user_id
        )

        assert len(previews) == 1
        preview = previews[0]
        assert preview.document_id == doc_id
        assert len(preview.entities) > 0  # Mock text has PHI
        assert preview.redacted_text != preview.original_text

    @pytest.mark.asyncio
    async def test_preview_multiple_documents(self, service, mock_db):
        """Test preview for multiple documents"""
        doc_ids = [uuid4(), uuid4(), uuid4()]
        user_id = uuid4()

        previews = await service.preview_deidentification(
            document_ids=doc_ids,
            redaction_mode=RedactionMode.MASK,
            user_id=user_id
        )

        assert len(previews) == 3

    @pytest.mark.asyncio
    async def test_apply_deidentification(self, service, mock_db):
        """Test apply de-identification"""
        doc_id = uuid4()
        user_id = uuid4()

        results = await service.apply_deidentification(
            document_ids=[doc_id],
            redaction_mode=RedactionMode.SURROGATE,
            store_mapping=True,
            user_id=user_id
        )

        assert len(results) == 1
        result = results[0]
        assert result.original_document_id == doc_id
        assert result.entities_redacted > 0
        assert result.deidentified_document_id is not None


class TestSurrogateGenerationService:
    """Test surrogate generation service"""

    @pytest.fixture
    def service(self):
        """Create surrogate service"""
        return SurrogateGenerationService()

    def test_generate_person_surrogate(self, service):
        """Test person name surrogate generation"""
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=0, end=8, confidence=0.98)
        ]

        mappings = service.generate_surrogates(entities)

        assert "John Doe" in mappings
        assert mappings["John Doe"] == "Patient-A"

    def test_generate_multiple_person_surrogates(self, service):
        """Test multiple person surrogates"""
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=0, end=8, confidence=0.98),
            DetectedEntity(text="Jane Smith", label=PHIEntityType.PERSON, start=10, end=20, confidence=0.97)
        ]

        mappings = service.generate_surrogates(entities)

        assert mappings["John Doe"] == "Patient-A"
        assert mappings["Jane Smith"] == "Patient-B"

    def test_generate_date_surrogate(self, service):
        """Test date surrogate generation (year masking)"""
        entities = [
            DetectedEntity(text="01/15/1980", label=PHIEntityType.DATE, start=0, end=10, confidence=0.95)
        ]

        mappings = service.generate_surrogates(entities)

        assert "01/15/1980" in mappings
        assert "19XX" in mappings["01/15/1980"]  # Year masked
        assert "01/15" in mappings["01/15/1980"]  # Month/day preserved

    def test_generate_id_surrogate(self, service):
        """Test ID surrogate generation"""
        entities = [
            DetectedEntity(text="123-45-6789", label=PHIEntityType.ID, start=0, end=11, confidence=0.99)
        ]

        mappings = service.generate_surrogates(entities)

        assert "123-45-6789" in mappings
        assert mappings["123-45-6789"] == "ID-0001"

    def test_consistent_mapping(self, service):
        """Test that same entity gets same surrogate"""
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=0, end=8, confidence=0.98),
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=20, end=28, confidence=0.98)
        ]

        mappings = service.generate_surrogates(entities)

        # Both instances should map to same surrogate
        assert mappings["John Doe"] == "Patient-A"
        # Only one mapping for "John Doe"
        person_mappings = [v for k, v in mappings.items() if k == "John Doe"]
        assert len(person_mappings) == 1

    def test_number_to_alpha_conversion(self, service):
        """Test alphabetic sequence conversion"""
        assert service._number_to_alpha(1) == "A"
        assert service._number_to_alpha(2) == "B"
        assert service._number_to_alpha(26) == "Z"
        assert service._number_to_alpha(27) == "AA"
        assert service._number_to_alpha(28) == "AB"

    def test_mask_date_formats(self, service):
        """Test date masking for various formats"""
        # MM/DD/YYYY
        assert service._mask_date("01/15/1980") == "01/15/19XX"

        # YYYY-MM-DD
        assert service._mask_date("2023-11-17") == "2023-11-XX"

        # Month DD, YYYY
        masked = service._mask_date("January 15, 1980")
        assert "19XX" in masked

    def test_reset_counters(self, service):
        """Test counter reset"""
        entities = [
            DetectedEntity(text="John Doe", label=PHIEntityType.PERSON, start=0, end=8, confidence=0.98)
        ]

        mappings1 = service.generate_surrogates(entities)
        assert mappings1["John Doe"] == "Patient-A"

        service.reset_counters()

        entities2 = [
            DetectedEntity(text="Jane Smith", label=PHIEntityType.PERSON, start=0, end=10, confidence=0.97)
        ]
        mappings2 = service.generate_surrogates(entities2)
        assert mappings2["Jane Smith"] == "Patient-A"  # Counter reset, starts at A again
