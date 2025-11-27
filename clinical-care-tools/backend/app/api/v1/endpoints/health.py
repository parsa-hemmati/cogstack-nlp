"""
Health check endpoint.

Provides service health status for monitoring and Docker health checks.
"""

from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.database import engine
from app.core.config import settings


router = APIRouter()


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint.

    Returns service status including database connectivity.
    Used by Docker health checks and monitoring systems.

    Returns:
        Health status with 200 OK if healthy, 503 Service Unavailable if unhealthy

    Response Format:
        {
            "status": "healthy" | "unhealthy",
            "version": "1.0.0",
            "timestamp": "2025-11-22T23:59:59.123456",
            "database": {
                "status": "connected" | "disconnected",
                "message": "Optional error message"
            }
        }

    Example:
        GET /health

        Response (200):
        {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2025-11-22T23:59:59",
            "database": {
                "status": "connected"
            }
        }

        Response (503):
        {
            "status": "unhealthy",
            "version": "1.0.0",
            "timestamp": "2025-11-22T23:59:59",
            "database": {
                "status": "disconnected",
                "message": "Connection refused"
            }
        }
    """
    # Check database connectivity
    database_status = await check_database()

    # Determine overall health status
    overall_status = "healthy" if database_status["status"] == "connected" else "unhealthy"

    # Determine HTTP status code
    http_status = (
        status.HTTP_200_OK
        if overall_status == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    # Build response
    response_data = {
        "status": overall_status,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "database": database_status,
    }

    # Return with appropriate status code
    return JSONResponse(
        content=response_data,
        status_code=http_status
    )


async def check_database() -> dict:
    """
    Check database connectivity.

    Returns:
        Dictionary with database status and optional error message

    Example:
        {"status": "connected"}
        {"status": "disconnected", "message": "Connection refused"}
    """
    try:
        # Try to execute simple query
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        return {"status": "connected"}

    except Exception as e:
        return {
            "status": "disconnected",
            "message": str(e)[:100]  # Truncate long error messages
        }
