"""
Health Check API Endpoint
Detailed system health monitoring
"""
from datetime import datetime
from typing import Dict, Any
import httpx
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings


router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=Dict[str, Any])
async def health_check_detailed(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check endpoint.

    Checks:
    - Database connectivity (PostgreSQL)
    - Redis connectivity
    - MedCAT service availability
    - Application version and uptime

    Returns:
        Health status with details for each component

    Usage:
        - Docker health check
        - Kubernetes liveness/readiness probes
        - Monitoring systems (Prometheus, Datadog)
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "components": {}
    }

    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        health_status["components"]["database"] = {
            "status": "healthy",
            "type": "PostgreSQL",
        }
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check Redis connection
    try:
        from app.services.session_service import session_service
        redis = await session_service.get_redis()
        await redis.ping()
        health_status["components"]["redis"] = {
            "status": "healthy",
            "type": "Redis",
        }
    except Exception as e:
        health_status["status"] = "degraded"  # Non-critical for basic operation
        health_status["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    # Check MedCAT service
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.MEDCAT_SERVICE_URL}/api/info")
            if response.status_code == 200:
                medcat_info = response.json()
                health_status["components"]["medcat"] = {
                    "status": "healthy",
                    "version": medcat_info.get("service_version"),
                    "model": medcat_info.get("service_model"),
                }
            else:
                health_status["status"] = "degraded"
                health_status["components"]["medcat"] = {
                    "status": "unhealthy",
                    "http_status": response.status_code
                }
    except Exception as e:
        health_status["status"] = "degraded"  # Non-critical for basic operation
        health_status["components"]["medcat"] = {
            "status": "unhealthy",
            "error": str(e)
        }

    return health_status
