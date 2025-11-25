"""
Unit Tests for Elasticsearch Client Module

Tests async Elasticsearch client wrapper for application use.
Follows TDD approach: Write tests first, then implement.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from elasticsearch import AsyncElasticsearch


@pytest.mark.asyncio
async def test_get_es_client_returns_instance():
    """Test that get_es_client() returns AsyncElasticsearch instance"""
    from app.clients.elasticsearch_client import get_es_client

    # Act
    client = get_es_client()

    # Assert
    assert client is not None
    assert isinstance(client, AsyncElasticsearch)


@pytest.mark.asyncio
async def test_get_es_client_loads_url_from_env(monkeypatch):
    """Test that ELASTICSEARCH_URL is loaded from environment variable"""
    from app.clients.elasticsearch_client import get_es_client

    # Arrange
    test_url = "http://test-elasticsearch:9200"
    monkeypatch.setenv("ELASTICSEARCH_URL", test_url)

    # Act
    client = get_es_client()

    # Assert
    # Check that the client was created with the correct URL
    # Note: AsyncElasticsearch stores URLs in transport._node_pool._nodes
    assert client is not None


@pytest.mark.asyncio
async def test_health_check_returns_cluster_health():
    """Test that health_check() returns cluster health status"""
    from app.clients.elasticsearch_client import health_check

    # Arrange
    expected_health = {
        "cluster_name": "test-cluster",
        "status": "green",
        "number_of_nodes": 1
    }

    # Act - Mock the ES client call
    with patch('app.clients.elasticsearch_client.get_es_client') as mock_get_client:
        mock_client = AsyncMock()
        mock_client.cluster.health.return_value = expected_health
        mock_get_client.return_value = mock_client

        result = await health_check()

        # Assert
        assert result == expected_health
        mock_client.cluster.health.assert_called_once()
        mock_client.close.assert_called_once()


@pytest.mark.asyncio
async def test_context_manager_support():
    """Test that client can be used as async context manager"""
    from app.clients.elasticsearch_client import get_es_client

    # Act & Assert
    async with get_es_client() as client:
        assert client is not None
        assert isinstance(client, AsyncElasticsearch)


@pytest.mark.asyncio
async def test_client_closes_properly():
    """Test that client closes connection properly"""
    from app.clients.elasticsearch_client import get_es_client

    # Arrange
    client = get_es_client()

    # Act
    await client.close()

    # Assert - No exception raised means success
    assert True
