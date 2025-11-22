"""
Unit tests for De-identification Service.

Tests validate de-identification methods against HIPAA Safe Harbor requirements.
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List

from app.services.deidentification_service import DeidentificationService
from app.schemas.deidentification import (
    PHIEntity,
    DeidentificationResult,
    ValidationReport,
)
from app.clients.modelserve_client import Entity


class TestDeidentificationServiceRemoval:
    """Test suite for removal method (default)."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_deidentify_removal_method(self, service, mock_phi_detection_service):
        """Test removal method replaces PHI with [TYPE] placeholders."""
        # Arrange
        text = "Patient John Doe was admitted on 01/15/2024"
        mock_phi_detection_service.detect_phi.return_value = [
            PHIEntity(
                entity_type="NAME",
                text="John Doe",
                start=8,
                end=16,
                confidence=0.95,
                cui=None,
            ),
            PHIEntity(
                entity_type="DATE",
                text="01/15/2024",
                start=33,
                end=43,
                confidence=0.92,
                cui=None,
            ),
        ]

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert
        assert result.deidentified_text == "Patient [NAME] was admitted on [DATE]"
        assert result.method_used == "removal"
        assert len(result.entities_removed) == 2
        assert result.entities_removed[0].entity_type == "phi_date"  # Sorted reverse, so date first
        assert result.entities_removed[1].entity_type == "phi_name"

    @pytest.mark.asyncio
    async def test_deidentify_multiple_same_phi(self, service, mock_medcat_client):
        """Test multiple occurrences of same PHI all removed."""
        # Arrange
        text = "John Doe visited. John Doe's records show..."
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=0,
                end=8,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=18,
                end=26,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert
        assert "[NAME]" in result.deidentified_text
        assert "John Doe" not in result.deidentified_text
        assert len(result.entities_removed) == 2


class TestDeidentificationServiceReplacement:
    """Test suite for replacement method (consistent mapping)."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_deidentify_replacement_consistent_mapping(
        self, service, mock_medcat_client
    ):
        """Test same PHI mapped to same replacement within document."""
        # Arrange
        text = "John Doe visited. John Doe is 65 years old."
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=0,
                end=8,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=18,
                end=26,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="replacement")

        # Assert: Same PHI → same replacement
        assert result.method_used == "replacement"
        assert "John Doe" not in result.deidentified_text
        # Both occurrences should map to same placeholder
        assert "Patient A" in result.deidentified_text or "PATIENT_1" in result.deidentified_text
        # Check mapping consistency
        assert len(result.entity_mappings) >= 1
        if "John Doe" in result.entity_mappings:
            replacement = result.entity_mappings["John Doe"]
            assert result.deidentified_text.count(replacement) == 2

    @pytest.mark.asyncio
    async def test_deidentify_replacement_different_phi_different_mapping(
        self, service, mock_medcat_client
    ):
        """Test different PHI entities get different replacements."""
        # Arrange
        text = "John Doe and Jane Smith visited."
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=0,
                end=8,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
            Entity(
                pretty_name="Jane Smith",
                types=["Person"],
                start=13,
                end=23,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="replacement")

        # Assert: Different PHI → different replacements
        assert "John Doe" not in result.deidentified_text
        assert "Jane Smith" not in result.deidentified_text
        assert len(result.entity_mappings) == 2
        # Verify different mappings
        assert result.entity_mappings["John Doe"] != result.entity_mappings["Jane Smith"]


class TestDeidentificationServiceGeneralization:
    """Test suite for generalization method."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_deidentify_generalization_dates(
        self, service, mock_medcat_client
    ):
        """Test dates generalized to year only."""
        # Arrange
        text = "Admitted on 01/15/2024"
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="01/15/2024",
                types=["Date"],
                start=12,
                end=22,
                accuracy=0.92,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="generalization")

        # Assert: Date → year only
        assert result.method_used == "generalization"
        assert "2024" in result.deidentified_text
        assert "01/15" not in result.deidentified_text

    @pytest.mark.asyncio
    async def test_deidentify_generalization_ages_over_89(
        self, service, mock_medcat_client
    ):
        """Test ages >89 generalized to 90+."""
        # Arrange
        text = "Patient is 92 years old"
        # For this test, we'll need to handle age detection differently
        # since MedCAT might not detect ages as PHI entities
        # We'll test the logic directly or mock appropriately
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="92",
                types=["Age"],
                start=11,
                end=13,
                accuracy=0.90,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="generalization")

        # Assert: Age >89 → "90+"
        assert result.method_used == "generalization"
        assert "90+" in result.deidentified_text or "90+ years old" in result.deidentified_text
        assert "92" not in result.deidentified_text

    @pytest.mark.asyncio
    async def test_deidentify_generalization_location_to_state(
        self, service, mock_medcat_client
    ):
        """Test locations generalized to state/region only."""
        # Arrange
        text = "Patient lives at 123 Main St, Boston, MA"
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="123 Main St, Boston, MA",
                types=["Address", "Location"],
                start=17,
                end=41,
                accuracy=0.93,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="generalization")

        # Assert: Address → state only
        assert result.method_used == "generalization"
        assert "Massachusetts" in result.deidentified_text or "MA" in result.deidentified_text
        assert "123 Main St" not in result.deidentified_text
        assert "Boston" not in result.deidentified_text


class TestDeidentificationServiceReviewFlagging:
    """Test suite for manual review flagging."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_deidentify_flags_low_confidence(
        self, service, mock_medcat_client
    ):
        """Test review_required=True for confidence <0.8."""
        # Arrange
        text = "Patient John Doe visited"
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=8,
                end=16,
                accuracy=0.75,  # Low confidence (above threshold 0.7 but below 0.8)
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert: Low confidence → review required
        assert result.review_required is True
        assert result.confidence_score == 0.75

    @pytest.mark.asyncio
    async def test_deidentify_no_flag_high_confidence(
        self, service, mock_medcat_client
    ):
        """Test review_required=False for confidence ≥0.8."""
        # Arrange
        text = "Patient John Doe visited"
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=8,
                end=16,
                accuracy=0.95,  # High confidence
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert: High confidence → no review needed
        assert result.review_required is False
        assert result.confidence_score == 0.95

    @pytest.mark.asyncio
    async def test_deidentify_flags_high_phi_density(
        self, service, mock_medcat_client
    ):
        """Test review_required=True for >20 PHI entities."""
        # Arrange
        text = "Long text with many PHI entities..."
        # Generate 25 PHI entities
        phi_entities = [
            Entity(
                pretty_name=f"Entity{i}",
                types=["Person"],
                start=i * 10,
                end=i * 10 + 8,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            )
            for i in range(25)
        ]
        mock_medcat_client.detect_phi.return_value = phi_entities

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert: >20 entities → review required
        assert result.review_required is True
        assert len(result.entities_removed) == 25


class TestDeidentificationServiceValidation:
    """Test suite for validation checks."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_validate_deidentification_catches_remaining_phi(
        self, service, mock_medcat_client
    ):
        """Test validation detects PHI that wasn't removed."""
        # Arrange
        original_text = "Patient John Doe, NHS 123456789"
        deidentified_text = "Patient [NAME], NHS 123456789"  # NHS number not removed!

        # Mock: PHI still detected in deidentified text
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="123456789",
                types=["NHS Number"],
                start=20,
                end=29,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        report = await service.validate_deidentification(
            original_text, deidentified_text
        )

        # Assert: Validation failed (PHI detected)
        assert report.is_valid is False
        assert len(report.phi_detected) == 1
        assert report.phi_detected[0].text == "123456789"

    @pytest.mark.asyncio
    async def test_validate_deidentification_passes_clean_text(
        self, service, mock_medcat_client
    ):
        """Test validation passes when no PHI detected."""
        # Arrange
        original_text = "Patient John Doe visited"
        deidentified_text = "Patient [NAME] visited"

        # Mock: No PHI detected
        mock_medcat_client.detect_phi.return_value = []

        # Act
        report = await service.validate_deidentification(
            original_text, deidentified_text
        )

        # Assert: Validation passed
        assert report.is_valid is True
        assert len(report.phi_detected) == 0

    @pytest.mark.asyncio
    async def test_validate_deidentification_readability(
        self, service, mock_medcat_client
    ):
        """Test validation checks text readability."""
        # Arrange
        original_text = "Patient John Doe has diabetes"
        deidentified_text = "Patient [NAME] has diabetes"

        mock_medcat_client.detect_phi.return_value = []

        # Act
        report = await service.validate_deidentification(
            original_text, deidentified_text
        )

        # Assert: Readability score reasonable
        assert 0.0 <= report.readability_score <= 1.0
        # Should be high since we only replaced name
        assert report.readability_score > 0.7


class TestDeidentificationServiceErrorHandling:
    """Test suite for error handling."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_deidentify_handles_empty_text(self, service, mock_medcat_client):
        """Test graceful handling of empty input."""
        # Arrange
        text = ""

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert: Returns as-is with warning
        assert result.deidentified_text == ""
        assert len(result.entities_removed) == 0
        assert result.review_required is True  # Flag for review due to empty text

    @pytest.mark.asyncio
    async def test_deidentify_handles_phi_detection_failure(
        self, service, mock_medcat_client
    ):
        """Test error handling when PHI detection fails."""
        # Arrange
        text = "Patient John Doe visited"
        mock_medcat_client.detect_phi.side_effect = Exception("Service unavailable")

        # Act & Assert: Should raise appropriate error
        with pytest.raises(Exception) as exc_info:
            await service.deidentify(text, method="removal")

        assert "Service unavailable" in str(exc_info.value) or "PHI detection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_deidentify_handles_overlapping_entities(
        self, service, mock_medcat_client
    ):
        """Test entities at same offset handled gracefully."""
        # Arrange
        text = "Patient John Doe visited"
        # Overlapping entities (same offset)
        mock_medcat_client.detect_phi.return_value = [
            Entity(
                pretty_name="John Doe",
                types=["Person"],
                start=8,
                end=16,
                accuracy=0.95,
                cui=None,
                meta_anns={},
            ),
            Entity(
                pretty_name="John",
                types=["Person"],
                start=8,
                end=12,
                accuracy=0.90,
                cui=None,
                meta_anns={},
            ),
        ]

        # Act
        result = await service.deidentify(text, method="removal")

        # Assert: Should handle gracefully (keep longer entity, discard shorter)
        assert "[NAME]" in result.deidentified_text
        assert "John Doe" not in result.deidentified_text


class TestDeidentificationServiceBatch:
    """Test suite for batch processing."""

    @pytest.fixture
    def mock_phi_detection_service(self):
        """Mock PHI detection service."""
        service = Mock()
        service.detect_phi = AsyncMock()
        return service

    @pytest.fixture
    def service(self, mock_phi_detection_service):
        """Create deidentification service."""
        return DeidentificationService(phi_detection_service=mock_phi_detection_service)

    @pytest.mark.asyncio
    async def test_deidentify_batch(self, service, mock_medcat_client):
        """Test batch processing maintains order."""
        # Arrange
        texts = [
            "Patient John Doe visited",
            "Jane Smith has diabetes",
        ]

        # Mock different PHI for each text
        async def mock_detect_phi(text):
            if "John Doe" in text:
                return [
                    Entity(
                        pretty_name="John Doe",
                        types=["Person"],
                        start=8,
                        end=16,
                        accuracy=0.95,
                        cui=None,
                        meta_anns={},
                    )
                ]
            elif "Jane Smith" in text:
                return [
                    Entity(
                        pretty_name="Jane Smith",
                        types=["Person"],
                        start=0,
                        end=10,
                        accuracy=0.95,
                        cui=None,
                        meta_anns={},
                    )
                ]
            return []

        mock_medcat_client.detect_phi.side_effect = mock_detect_phi

        # Act
        results = await service.deidentify_batch(texts, method="removal")

        # Assert: Order maintained
        assert len(results) == 2
        assert "[NAME]" in results[0].deidentified_text
        assert "John Doe" not in results[0].deidentified_text
        assert "[NAME]" in results[1].deidentified_text
        assert "Jane Smith" not in results[1].deidentified_text
