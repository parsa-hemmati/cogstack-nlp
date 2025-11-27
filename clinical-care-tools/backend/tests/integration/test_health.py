"""
Integration tests for health check endpoint.

Tests service health monitoring for Docker health checks.
"""

import pytest
import httpx
from datetime import datetime
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.core.database import engine, Base


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_when_healthy(client):
    """Test that /health returns 200 OK when service is healthy."""
    # Act
    response = await client.get("/health")

    # Assert
    assert response.status_code == 200, \
        "Health endpoint should return 200 when healthy"


@pytest.mark.asyncio
async def test_health_endpoint_response_includes_status(client):
    """Test that health response includes status field."""
    # Act
    response = await client.get("/health")
    data = response.json()

    # Assert
    assert "status" in data, \
        "Health response should include 'status' field"
    assert data["status"] in ["healthy", "unhealthy"], \
        "Status should be either 'healthy' or 'unhealthy'"


@pytest.mark.asyncio
async def test_health_endpoint_response_includes_version(client):
    """Test that health response includes version field."""
    # Act
    response = await client.get("/health")
    data = response.json()

    # Assert
    assert "version" in data, \
        "Health response should include 'version' field"
    assert isinstance(data["version"], str), \
        "Version should be a string"


@pytest.mark.asyncio
async def test_health_endpoint_response_includes_database_status(client):
    """Test that health response includes database status."""
    # Act
    response = await client.get("/health")
    data = response.json()

    # Assert
    assert "database" in data, \
        "Health response should include 'database' field"
    assert isinstance(data["database"], dict), \
        "Database field should be an object"
    assert "status" in data["database"], \
        "Database object should have 'status' field"


@pytest.mark.asyncio
async def test_health_endpoint_response_includes_timestamp(client):
    """Test that health response includes timestamp."""
    # Act
    before_time = datetime.utcnow()
    response = await client.get("/health")
    after_time = datetime.utcnow()
    data = response.json()

    # Assert
    assert "timestamp" in data, \
        "Health response should include 'timestamp' field"
    assert isinstance(data["timestamp"], str), \
        "Timestamp should be a string (ISO format)"

    # Parse timestamp
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert before_time <= timestamp <= after_time, \
        "Timestamp should be between request start and end"


@pytest.mark.asyncio
async def test_health_endpoint_database_status_connected(client):
    """Test that database status shows 'connected' when database is available."""
    # Note: This will fail if PostgreSQL is unavailable
    # When DB is unavailable, status should be 'disconnected'

    # Act
    response = await client.get("/health")
    data = response.json()

    # Assert
    db_status = data["database"]["status"]
    assert db_status in ["connected", "disconnected"], \
        "Database status should be 'connected' or 'disconnected'"

    # If database is connected, overall status should be healthy
    if db_status == "connected":
        assert data["status"] == "healthy", \
            "Overall status should be 'healthy' when database is connected"


@pytest.mark.asyncio
async def test_health_endpoint_returns_503_when_database_down(client):
    """Test that /health returns 503 when database is unavailable."""
    # Note: This test depends on database state
    # If PostgreSQL is down, health check should return 503
    # If PostgreSQL is up, health check should return 200

    # Act
    response = await client.get("/health")
    data = response.json()

    # Assert - check consistency between status code and database status
    db_status = data["database"]["status"]

    if db_status == "disconnected":
        assert response.status_code == 503, \
            "Health endpoint should return 503 when database is disconnected"
        assert data["status"] == "unhealthy", \
            "Status should be 'unhealthy' when database is disconnected"
    else:
        assert response.status_code == 200, \
            "Health endpoint should return 200 when database is connected"
        assert data["status"] == "healthy", \
            "Status should be 'healthy' when database is connected"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
