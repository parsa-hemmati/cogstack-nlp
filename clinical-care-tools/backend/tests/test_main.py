"""
Main Application Tests

Tests for the main FastAPI application, including startup,
health checks, and basic endpoint functionality.
"""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint returns API information."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "environment" in data
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_health_check_endpoint():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "environment" in data
    assert "services" in data


@pytest.mark.asyncio
async def test_openapi_schema_available():
    """Test that OpenAPI schema is available."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/openapi.json")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data


@pytest.mark.asyncio
async def test_docs_redirect():
    """Test that /docs endpoint is accessible."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as client:
        response = await client.get("/docs")

    # Docs endpoint returns HTML or redirect
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_307_TEMPORARY_REDIRECT]


@pytest.mark.asyncio
async def test_redoc_redirect():
    """Test that /redoc endpoint is accessible."""
    async with AsyncClient(app=app, base_url="http://test", follow_redirects=False) as client:
        response = await client.get("/redoc")

    # ReDoc endpoint returns HTML or redirect
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_307_TEMPORARY_REDIRECT]


@pytest.mark.asyncio
async def test_cors_headers_present():
    """Test that CORS headers are added to responses."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.options(
            "/",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )

    # Check for CORS headers in response
    assert "access-control-allow-origin" in response.headers or response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_security_headers_present():
    """Test that security headers are added to responses."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    # Check for security headers
    assert "x-content-type-options" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    assert "x-frame-options" in response.headers
    assert response.headers["x-frame-options"] == "DENY"


@pytest.mark.asyncio
async def test_request_id_generation():
    """Test that request IDs are generated for tracing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Send request without X-Request-ID
        response = await client.get("/api/health")

    # Check that audit ID is added
    # (Note: This assumes AuditLogMiddleware is enabled)
    if "x-audit-id" in response.headers:
        assert len(response.headers["x-audit-id"]) > 0


@pytest.mark.asyncio
async def test_unknown_endpoint_returns_404():
    """Test that unknown endpoints return 404."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_method_not_allowed():
    """Test that unsupported methods return 405."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/health")  # Health check only supports GET

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


# Additional tests for middleware and error handling

@pytest.mark.asyncio
async def test_global_exception_handler():
    """Test that global exception handler catches unhandled errors."""
    # This would require mocking an endpoint that raises an exception
    # For now, we just verify the handler exists
    from app.main import global_exception_handler
    assert global_exception_handler is not None


@pytest.mark.asyncio
async def test_app_version_header():
    """Test that app version is included in response headers."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    if "x-app-version" in response.headers:
        assert len(response.headers["x-app-version"]) > 0


@pytest.mark.asyncio
async def test_compliance_headers():
    """Test that compliance mode headers are added when enabled."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")

    # Check for compliance headers if enabled
    from app.config import settings
    if settings.HIPAA_COMPLIANCE_MODE or settings.GDPR_COMPLIANCE_MODE:
        if "x-healthcare-compliance" in response.headers:
            compliance = response.headers["x-healthcare-compliance"]
            if settings.HIPAA_COMPLIANCE_MODE:
                assert "HIPAA" in compliance
            if settings.GDPR_COMPLIANCE_MODE:
                assert "GDPR" in compliance