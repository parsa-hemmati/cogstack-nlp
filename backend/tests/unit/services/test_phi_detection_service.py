"""
Unit tests for PHI Detection Service.

Tests PHI entity detection using mocked MedCAT responses.
"""
import pytest
from unittest.mock import AsyncMock, Mock

from app.services.phi_detection_service import PHIDetectionService
from app.schemas.phi_entity import PHIEntity, ModelInfo
from app.clients.modelserve_client import Entity


@pytest.fixture
def mock_medcat_client():
    """Create mock MedCAT client."""
    client = AsyncMock()
    client.base_url = "http://localhost:8000"
    return client


@pytest.fixture
def phi_detection_service(mock_medcat_client):
    """Create PHI detection service with mocked client."""
    return PHIDetectionService(medcat_client=mock_medcat_client)


async def test_detect_phi_returns_phi_entities(phi_detection_service, mock_medcat_client):
    """Test PHI detection returns PHIEntity objects."""
    # Arrange
    mock_entities = [
        Entity(
            pretty_name="John Smith",
            types=["Person", "Name"],
            start=8,
            end=18,
            accuracy=0.95,
            cui=None,
            meta_anns={}
        )
    ]
    mock_medcat_client.detect_phi.return_value = mock_entities

    # Act
    result = await phi_detection_service.detect_phi("Patient John Smith has diabetes.")

    # Assert
    assert len(result) == 1
    assert isinstance(result[0], PHIEntity)
    assert result[0].entity_type == "NAME"
    assert result[0].text == "John Smith"
    assert result[0].start == 8
    assert result[0].end == 18
    assert result[0].confidence == 0.95


async def test_detect_phi_filters_non_phi_entities(phi_detection_service, mock_medcat_client):
    """Test only PHI categories returned, not clinical concepts."""
    # Arrange - Mix of PHI and clinical entities
    mock_entities = [
        Entity(
            pretty_name="John Smith",
            types=["Person", "Name"],
            start=0,
            end=10,
            accuracy=0.95,
            cui=None,
            meta_anns={}
        ),
        Entity(
            pretty_name="Diabetes",
            types=["Disease or Syndrome"],
            start=15,
            end=23,
            accuracy=0.92,
            cui="C0004238",
            meta_anns={}
        ),
    ]
    mock_medcat_client.detect_phi.return_value = mock_entities

    # Act
    result = await phi_detection_service.detect_phi("John Smith has diabetes.")

    # Assert - Only PHI entity returned
    assert len(result) == 1
    assert result[0].entity_type == "NAME"
    assert result[0].text == "John Smith"


async def test_detect_phi_confidence_threshold(phi_detection_service, mock_medcat_client):
    """Test low-confidence entities filtered out."""
    # Arrange
    mock_entities = [
        Entity(
            pretty_name="Smith",
            types=["Person", "Name"],
            start=0,
            end=5,
            accuracy=0.65,  # Below default threshold (0.7)
            cui=None,
            meta_anns={}
        ),
        Entity(
            pretty_name="John Smith",
            types=["Person", "Name"],
            start=10,
            end=20,
            accuracy=0.95,  # Above threshold
            cui=None,
            meta_anns={}
        ),
    ]
    mock_medcat_client.detect_phi.return_value = mock_entities

    # Act
    result = await phi_detection_service.detect_phi(
        "Smith and John Smith are patients.",
        confidence_threshold=0.7
    )

    # Assert - Only high-confidence entity returned
    assert len(result) == 1
    assert result[0].text == "John Smith"
    assert result[0].confidence == 0.95


async def test_detect_phi_batch_processing(phi_detection_service, mock_medcat_client):
    """Test batch processing maintains order."""
    # Arrange
    texts = [
        "Patient John Smith",
        "Contact: 555-1234",
        "No PHI here"
    ]
    # Mock detect_phi to return entities based on text content
    async def mock_detect(text, model_name="medcat_deid"):
        if "John Smith" in text:
            return [Entity(
                pretty_name="John Smith",
                types=["Person", "Name"],
                start=8,
                end=18,
                accuracy=0.95,
                cui=None,
                meta_anns={}
            )]
        elif "555-1234" in text:
            return [Entity(
                pretty_name="555-1234",
                types=["Phone"],
                start=9,
                end=17,
                accuracy=0.88,
                cui=None,
                meta_anns={}
            )]
        return []

    mock_medcat_client.detect_phi.side_effect = mock_detect

    # Act
    results = await phi_detection_service.detect_phi_batch(texts)

    # Assert - Order maintained
    assert len(results) == 3
    assert len(results[0]) == 1
    assert results[0][0].entity_type == "NAME"
    assert len(results[1]) == 1
    assert results[1][0].entity_type == "PHONE"
    assert len(results[2]) == 0


async def test_detect_phi_handles_empty_text(phi_detection_service, mock_medcat_client):
    """Test graceful handling of empty input."""
    # Arrange
    mock_medcat_client.detect_phi.return_value = []

    # Act
    result = await phi_detection_service.detect_phi("")

    # Assert
    assert result == []


async def test_detect_phi_handles_whitespace_only(phi_detection_service, mock_medcat_client):
    """Test graceful handling of whitespace-only input."""
    # Arrange
    mock_medcat_client.detect_phi.return_value = []

    # Act
    result = await phi_detection_service.detect_phi("   \n\t  ")

    # Assert
    assert result == []


def test_detect_phi_all_18_phi_types():
    """Test mapping of all 18 HIPAA PHI types."""
    # This test verifies the entity type mapping logic
    service = PHIDetectionService(medcat_client=AsyncMock())

    # Test each PHI type mapping
    test_cases = [
        (["Person", "Name"], "NAME"),
        (["Location"], "LOCATION"),
        (["Date"], "DATE"),
        (["Phone"], "PHONE"),
        (["Fax"], "FAX"),
        (["Email"], "EMAIL"),
        (["SSN"], "SSN"),
        (["Medical Record Number"], "MRN"),
        (["NHS Number"], "MRN"),  # NHS Number maps to MRN
        (["Health Plan"], "HEALTHPLAN"),
        (["Account"], "ACCOUNT"),
        (["License"], "LICENSE"),
        (["Vehicle"], "VEHICLE"),
        (["Device"], "DEVICE"),
        (["URL"], "URL"),
        (["IP Address"], "IPADDR"),
        (["Biometric"], "BIOMETRIC"),
        (["Photo"], "PHOTO"),
        (["Identifier"], "IDENTIFIER"),
    ]

    for entity_types, expected_phi_type in test_cases:
        entity = Entity(
            pretty_name="test",
            types=entity_types,
            start=0,
            end=4,
            accuracy=0.9,
            cui=None,
            meta_anns={}
        )
        phi_type = service._map_entity_to_phi_type(entity)
        assert phi_type == expected_phi_type, f"Expected {expected_phi_type} for {entity_types}, got {phi_type}"


async def test_detect_phi_preserves_offsets(phi_detection_service, mock_medcat_client):
    """Test character offsets are correctly preserved."""
    # Arrange
    text = "Patient name: John Smith (NHS: 1234567890)"
    #               0123456789012345678901234567890123456789012
    #               0         1         2         3         4
    # "John Smith" is at position 14-24
    # "1234567890" is at position 31-41
    mock_entities = [
        Entity(
            pretty_name="John Smith",
            types=["Person", "Name"],
            start=14,
            end=24,
            accuracy=0.95,
            cui=None,
            meta_anns={}
        ),
        Entity(
            pretty_name="1234567890",
            types=["NHS Number"],
            start=31,
            end=41,
            accuracy=0.92,
            cui=None,
            meta_anns={}
        ),
    ]
    mock_medcat_client.detect_phi.return_value = mock_entities

    # Act
    result = await phi_detection_service.detect_phi(text)

    # Assert
    assert len(result) == 2
    assert text[result[0].start:result[0].end] == "John Smith"
    assert text[result[1].start:result[1].end] == "1234567890"


async def test_detect_phi_connection_error(phi_detection_service, mock_medcat_client):
    """Test handling of MedCAT service connection errors."""
    # Arrange
    from app.clients.modelserve_client import ProcessingError
    mock_medcat_client.detect_phi.side_effect = ProcessingError("Connection timeout")

    # Act & Assert
    with pytest.raises(ProcessingError, match="Connection timeout"):
        await phi_detection_service.detect_phi("Test text")


def test_get_model_info(phi_detection_service, mock_medcat_client):
    """Test model info retrieval."""
    # Arrange
    mock_medcat_client.get_available_models.return_value = ["medcat_deid"]

    # Act
    info = phi_detection_service.get_model_info()

    # Assert
    assert isinstance(info, ModelInfo)
    assert info.model_name == "medcat_deid"
    assert "NAME" in info.supported_phi_types
    assert "DATE" in info.supported_phi_types
    assert len(info.supported_phi_types) == 18


async def test_detect_phi_batch_partial_failures(phi_detection_service, mock_medcat_client):
    """Test batch processing with partial failures."""
    # Arrange
    texts = ["Text 1", "Text 2", "Text 3"]
    from app.clients.modelserve_client import ProcessingError

    # Mock: First succeeds, second fails, third succeeds
    call_count = [0]
    async def mock_detect(text):
        call_count[0] += 1
        if call_count[0] == 2:  # Second call
            raise ProcessingError("Processing failed")
        return []

    mock_medcat_client.detect_phi.side_effect = mock_detect

    # Act
    results = await phi_detection_service.detect_phi_batch(texts, skip_errors=True)

    # Assert - Should have results for texts 1 and 3, None for text 2
    assert len(results) == 3
    assert results[0] == []  # Text 1 processed (no entities)
    assert results[1] is None  # Text 2 failed
    assert results[2] == []  # Text 3 processed (no entities)


async def test_detect_phi_custom_confidence_threshold(phi_detection_service, mock_medcat_client):
    """Test custom confidence threshold."""
    # Arrange
    mock_entities = [
        Entity(
            pretty_name="Low confidence",
            types=["Person", "Name"],
            start=0,
            end=14,
            accuracy=0.5,
            cui=None,
            meta_anns={}
        ),
        Entity(
            pretty_name="High confidence",
            types=["Person", "Name"],
            start=20,
            end=35,
            accuracy=0.95,
            cui=None,
            meta_anns={}
        ),
    ]
    mock_medcat_client.detect_phi.return_value = mock_entities

    # Act - Use custom threshold of 0.9
    result = await phi_detection_service.detect_phi("Test text", confidence_threshold=0.9)

    # Assert - Only high confidence entity returned
    assert len(result) == 1
    assert result[0].confidence == 0.95


async def test_detect_phi_zero_confidence_threshold(phi_detection_service, mock_medcat_client):
    """Test zero confidence threshold returns all entities."""
    # Arrange
    mock_entities = [
        Entity(
            pretty_name="Very low",
            types=["Person", "Name"],
            start=0,
            end=8,
            accuracy=0.1,
            cui=None,
            meta_anns={}
        ),
    ]
    mock_medcat_client.detect_phi.return_value = mock_entities

    # Act - Threshold of 0.0 should return everything
    result = await phi_detection_service.detect_phi("Test", confidence_threshold=0.0)

    # Assert
    assert len(result) == 1
    assert result[0].confidence == 0.1
