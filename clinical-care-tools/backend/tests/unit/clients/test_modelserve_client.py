"""
Unit tests for CogStack-ModelServe Client.

Tests async HTTP client for SNOMED entity extraction and PHI detection.
Mocks CogStack-ModelServe API responses.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import Response

from app.clients.modelserve_client import CogStackModelServeClient


pytestmark = pytest.mark.asyncio


@pytest.fixture
def modelserve_client():
    """Create CogStack-ModelServe client with test URL."""
    return CogStackModelServeClient(base_url="http://test-modelserve:8000")


@pytest.fixture
def mock_snomed_response():
    """Mock response from SNOMED model."""
    return {
        "entities": [
            {
                "cui": "C0011849",
                "pretty_name": "Diabetes Mellitus",
                "start": 0,
                "end": 8,
                "meta_anns": {
                    "Negation": {
                        "value": "Affirmed",
                        "confidence": 0.95
                    },
                    "Temporality": {
                        "value": "Current",
                        "confidence": 0.89
                    },
                    "Experiencer": {
                        "value": "Patient",
                        "confidence": 0.98
                    },
                    "Certainty": {
                        "value": "Certain",
                        "confidence": 0.92
                    }
                }
            }
        ]
    }


@pytest.fixture
def mock_deid_response():
    """Mock response from DeID model."""
    return {
        "entities": [
            {
                "cui": "PHI-NAME",
                "pretty_name": "John Doe",
                "start": 8,
                "end": 16,
                "entity_type": "PHI-NAME"
            },
            {
                "cui": "PHI-NHS-NUMBER",
                "pretty_name": "123 456 7890",
                "start": 30,
                "end": 42,
                "entity_type": "PHI-NHS-NUMBER"
            }
        ]
    }


async def test_process_text_returns_entities(modelserve_client, mock_snomed_response):
    """Test that process_text calls SNOMED model and returns entities."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        # Mock response
        mock_response = Response(200, json=mock_snomed_response)
        mock_post.return_value = mock_response

        # Call process_text
        entities = await modelserve_client.process_text("Diabetes diagnosis")

        # Verify request
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "/api/process"
        assert call_args[1]["json"]["text"] == "Diabetes diagnosis"
        assert call_args[1]["json"]["model_name"] == "medcat_snomed"

        # Verify entities returned
        assert len(entities) == 1
        assert entities[0]["cui"] == "C0011849"
        assert entities[0]["pretty_name"] == "Diabetes Mellitus"
        assert "meta_anns" in entities[0]


async def test_process_text_parses_meta_annotations(modelserve_client, mock_snomed_response):
    """Test that meta-annotations are correctly parsed."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        mock_response = Response(200, json=mock_snomed_response)
        mock_post.return_value = mock_response

        entities = await modelserve_client.process_text("Diabetes diagnosis")

        # Verify meta-annotations
        entity = entities[0]
        assert entity["meta_anns"]["Negation"]["value"] == "Affirmed"
        assert entity["meta_anns"]["Temporality"]["value"] == "Current"
        assert entity["meta_anns"]["Experiencer"]["value"] == "Patient"
        assert entity["meta_anns"]["Certainty"]["value"] == "Certain"

        # Verify confidence scores
        assert entity["meta_anns"]["Negation"]["confidence"] == 0.95
        assert entity["meta_anns"]["Temporality"]["confidence"] == 0.89


async def test_detect_phi_calls_deid_model(modelserve_client, mock_deid_response):
    """Test that detect_phi calls DeID model."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        mock_response = Response(200, json=mock_deid_response)
        mock_post.return_value = mock_response

        phi_entities = await modelserve_client.detect_phi("Patient John Doe, NHS number: 123 456 7890")

        # Verify request to DeID model
        call_args = mock_post.call_args
        assert call_args[1]["json"]["model_name"] == "medcat_deid"

        # Verify PHI entities returned
        assert len(phi_entities) == 2
        assert phi_entities[0]["entity_type"] == "PHI-NAME"
        assert phi_entities[0]["pretty_name"] == "John Doe"
        assert phi_entities[1]["entity_type"] == "PHI-NHS-NUMBER"


async def test_classify_entity_type_identifies_phi(modelserve_client):
    """Test that classify_entity_type correctly identifies PHI types."""
    # PHI entity (name)
    phi_name_entity = {
        "cui": "PHI-NAME",
        "entity_type": "PHI-NAME"
    }
    assert modelserve_client.classify_entity_type(phi_name_entity) == "phi_name"

    # PHI entity (NHS number)
    phi_nhs_entity = {
        "cui": "PHI-NHS-NUMBER",
        "entity_type": "PHI-NHS-NUMBER"
    }
    assert modelserve_client.classify_entity_type(phi_nhs_entity) == "phi_nhs_number"

    # PHI entity (date)
    phi_date_entity = {
        "cui": "PHI-DATE",
        "entity_type": "PHI-DATE"
    }
    assert modelserve_client.classify_entity_type(phi_date_entity) == "phi_date"


async def test_classify_entity_type_identifies_clinical(modelserve_client):
    """Test that classify_entity_type correctly identifies clinical entities."""
    clinical_entity = {
        "cui": "C0011849",
        "entity_type": "CLINICAL"
    }
    assert modelserve_client.classify_entity_type(clinical_entity) == "clinical"


async def test_process_text_bulk_processes_multiple_texts(modelserve_client):
    """Test that process_text_bulk handles batch processing."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        # Mock response for each text
        mock_response = Response(200, json={"entities": []})
        mock_post.return_value = mock_response

        texts = ["Text 1", "Text 2", "Text 3"]
        results = await modelserve_client.process_text_bulk(texts, model_name="medcat_snomed")

        # Verify 3 separate calls made
        assert mock_post.call_count == 3

        # Verify results structure
        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)


async def test_health_check_returns_true_when_healthy(modelserve_client):
    """Test that health_check returns True when service is healthy."""
    with patch.object(modelserve_client.client, 'get') as mock_get:
        mock_response = Response(200, json={"status": "healthy"})
        mock_get.return_value = mock_response

        is_healthy = await modelserve_client.health_check()

        assert is_healthy is True
        mock_get.assert_called_once_with("/health")


async def test_health_check_returns_false_when_unhealthy(modelserve_client):
    """Test that health_check returns False when service is unhealthy."""
    with patch.object(modelserve_client.client, 'get') as mock_get:
        mock_response = Response(503, json={"status": "unhealthy"})
        mock_get.return_value = mock_response

        is_healthy = await modelserve_client.health_check()

        assert is_healthy is False


async def test_health_check_handles_connection_errors(modelserve_client):
    """Test that health_check handles connection errors gracefully."""
    with patch.object(modelserve_client.client, 'get') as mock_get:
        mock_get.side_effect = Exception("Connection refused")

        is_healthy = await modelserve_client.health_check()

        assert is_healthy is False


async def test_get_available_models_returns_model_list(modelserve_client):
    """Test that get_available_models returns list of available models."""
    with patch.object(modelserve_client.client, 'get') as mock_get:
        mock_response = Response(200, json={
            "models": ["medcat_snomed", "medcat_deid", "medcat_umls"]
        })
        mock_get.return_value = mock_response

        models = await modelserve_client.get_available_models()

        assert len(models) == 3
        assert "medcat_snomed" in models
        assert "medcat_deid" in models
        assert "medcat_umls" in models
        mock_get.assert_called_once_with("/models")


async def test_process_text_handles_http_errors(modelserve_client):
    """Test that process_text handles HTTP errors gracefully."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        # Mock 500 error
        mock_response = Response(500, text="Internal Server Error")
        mock_post.return_value = mock_response

        with pytest.raises(Exception) as exc_info:
            await modelserve_client.process_text("Test text")

        assert "500" in str(exc_info.value) or "error" in str(exc_info.value).lower()


async def test_process_text_with_custom_model_name(modelserve_client):
    """Test that process_text accepts custom model names."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        mock_response = Response(200, json={"entities": []})
        mock_post.return_value = mock_response

        await modelserve_client.process_text("Test text", model_name="custom_model")

        call_args = mock_post.call_args
        assert call_args[1]["json"]["model_name"] == "custom_model"


async def test_client_uses_environment_url():
    """Test that client uses MODELSERVE_URL from environment."""
    with patch.dict('os.environ', {'MODELSERVE_URL': 'http://custom-url:9000'}):
        client = CogStackModelServeClient()
        assert client.base_url == "http://custom-url:9000"


async def test_client_uses_default_url_when_no_env():
    """Test that client uses default URL when env var not set."""
    with patch.dict('os.environ', {}, clear=True):
        client = CogStackModelServeClient()
        assert client.base_url == "http://cogstack-modelserve:8000"


async def test_process_text_empty_response(modelserve_client):
    """Test handling of empty entity response."""
    with patch.object(modelserve_client.client, 'post') as mock_post:
        mock_response = Response(200, json={"entities": []})
        mock_post.return_value = mock_response

        entities = await modelserve_client.process_text("No medical terms here")

        assert entities == []
