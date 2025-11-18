"""
Unit tests for CogStack-ModelServe Client.

Tests async HTTP client for SNOMED and DeID models.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.clients.modelserve_client import (
    CogStackModelServeClient,
    Entity,
    ProcessingError,
)


@pytest.fixture
def modelserve_client():
    """Create ModelServe client with test URL."""
    return CogStackModelServeClient(base_url="http://localhost:8000")


@pytest.fixture
def sample_snomed_response():
    """Sample response from CogStack-ModelServe SNOMED model."""
    return {
        "entities": [
            {
                "cui": "C0011849",
                "pretty_name": "Diabetes mellitus",
                "types": ["Disease or Syndrome"],
                "start": 10,
                "end": 28,
                "accuracy": 0.95,
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Temporality": "Current",
                    "Experiencer": "Patient",
                    "Certainty": "Definite",
                },
            },
            {
                "cui": "C0020538",
                "pretty_name": "Hypertension",
                "types": ["Disease or Syndrome"],
                "start": 34,
                "end": 46,
                "accuracy": 0.98,
                "meta_anns": {
                    "Negation": "Affirmed",
                    "Temporality": "Current",
                    "Experiencer": "Patient",
                    "Certainty": "Definite",
                },
            },
        ]
    }


@pytest.fixture
def sample_deid_response():
    """Sample response from CogStack-ModelServe DeID model."""
    return {
        "entities": [
            {
                "pretty_name": "John Smith",
                "types": ["Person", "Name"],
                "start": 0,
                "end": 10,
                "accuracy": 0.99,
            },
            {
                "pretty_name": "1234567890",
                "types": ["NHS Number"],
                "start": 25,
                "end": 35,
                "accuracy": 0.98,
            },
        ]
    }


@pytest.mark.asyncio
async def test_process_text_snomed_model(
    modelserve_client, sample_snomed_response
):
    """Test processing text with SNOMED model."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = Mock(
            status_code=200, json=lambda: sample_snomed_response
        )

        entities = await modelserve_client.process_text(
            text="Patient has diabetes mellitus and hypertension.",
            model_name="medcat_snomed",
        )

        assert len(entities) == 2
        assert entities[0].cui == "C0011849"
        assert entities[0].pretty_name == "Diabetes mellitus"
        assert entities[0].meta_anns["Negation"] == "Affirmed"
        assert entities[1].cui == "C0020538"


@pytest.mark.asyncio
async def test_detect_phi_deid_model(modelserve_client, sample_deid_response):
    """Test PHI detection with DeID model."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = Mock(
            status_code=200, json=lambda: sample_deid_response
        )

        entities = await modelserve_client.detect_phi(
            text="John Smith, NHS number 1234567890"
        )

        assert len(entities) == 2
        assert entities[0].pretty_name == "John Smith"
        assert "Person" in entities[0].types
        assert entities[1].pretty_name == "1234567890"
        assert "NHS Number" in entities[1].types


@pytest.mark.asyncio
async def test_meta_annotations_parsed_correctly(
    modelserve_client, sample_snomed_response
):
    """Test meta-annotations are parsed from response."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = Mock(
            status_code=200, json=lambda: sample_snomed_response
        )

        entities = await modelserve_client.process_text(
            text="Patient has diabetes.", model_name="medcat_snomed"
        )

        entity = entities[0]
        assert entity.meta_anns["Negation"] == "Affirmed"
        assert entity.meta_anns["Temporality"] == "Current"
        assert entity.meta_anns["Experiencer"] == "Patient"
        assert entity.meta_anns["Certainty"] == "Definite"


@pytest.mark.asyncio
async def test_process_text_bulk(modelserve_client, sample_snomed_response):
    """Test bulk processing of multiple texts."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = Mock(
            status_code=200, json=lambda: sample_snomed_response
        )

        texts = [
            "Patient has diabetes.",
            "Patient has hypertension.",
            "No signs of infection.",
        ]

        results = await modelserve_client.process_text_bulk(
            texts=texts, model_name="medcat_snomed"
        )

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)


@pytest.mark.asyncio
async def test_classify_entity_type_clinical(modelserve_client):
    """Test classifying clinical entity."""
    entity = Entity(
        cui="C0011849",
        pretty_name="Diabetes",
        types=["Disease or Syndrome"],
        start=0,
        end=8,
        accuracy=0.95,
    )

    entity_type = modelserve_client.classify_entity_type(entity)

    assert entity_type == "clinical"


@pytest.mark.asyncio
async def test_classify_entity_type_phi_name(modelserve_client):
    """Test classifying PHI: name."""
    entity = Entity(
        pretty_name="John Smith", types=["Person", "Name"], start=0, end=10, accuracy=0.99
    )

    entity_type = modelserve_client.classify_entity_type(entity)

    assert entity_type == "phi_name"


@pytest.mark.asyncio
async def test_classify_entity_type_phi_nhs_number(modelserve_client):
    """Test classifying PHI: NHS number."""
    entity = Entity(
        pretty_name="1234567890",
        types=["NHS Number"],
        start=0,
        end=10,
        accuracy=0.98,
    )

    entity_type = modelserve_client.classify_entity_type(entity)

    assert entity_type == "phi_nhs_number"


@pytest.mark.asyncio
async def test_health_check_success(modelserve_client):
    """Test health check endpoint."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = Mock(status_code=200, json=lambda: {"status": "ok"})

        is_healthy = await modelserve_client.health_check()

        assert is_healthy is True


@pytest.mark.asyncio
async def test_health_check_failure(modelserve_client):
    """Test health check failure."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = Mock(status_code=500)

        is_healthy = await modelserve_client.health_check()

        assert is_healthy is False


@pytest.mark.asyncio
async def test_get_available_models(modelserve_client):
    """Test listing available models."""
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = Mock(
            status_code=200,
            json=lambda: {"models": ["medcat_snomed", "medcat_deid"]},
        )

        models = await modelserve_client.get_available_models()

        assert "medcat_snomed" in models
        assert "medcat_deid" in models


@pytest.mark.asyncio
async def test_processing_error_handling(modelserve_client):
    """Test error handling for failed processing."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = Mock(
            status_code=500, text="Internal server error"
        )

        with pytest.raises(ProcessingError):
            await modelserve_client.process_text(
                text="Test", model_name="medcat_snomed"
            )


@pytest.mark.asyncio
async def test_empty_text_processing(modelserve_client):
    """Test processing empty text returns empty list."""
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = Mock(status_code=200, json=lambda: {"entities": []})

        entities = await modelserve_client.process_text(
            text="", model_name="medcat_snomed"
        )

        assert entities == []
