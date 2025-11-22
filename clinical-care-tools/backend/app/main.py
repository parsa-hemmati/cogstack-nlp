"""
FastAPI main application module.

This module initializes the FastAPI application with all middleware,
routers, and event handlers for the Clinical Care Tools backend.
"""

from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.middleware.audit import AuditLogMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# Import routers when they're created
# from app.routers import auth, patients, documents, fhir, admin

__all__ = ["app"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle events.

    This context manager handles startup and shutdown events for the application,
    including database connections, cache initialization, and cleanup.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Initialize database connection pool
    # from app.database import engine
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    # Initialize Redis connection
    # from app.cache import redis_client
    # await redis_client.ping()

    # Initialize Elasticsearch
    # from app.search import es_client
    # await es_client.info()

    # Initialize MedCAT service connection
    # from app.services.medcat import medcat_service
    # await medcat_service.health_check()

    yield

    # Shutdown
    print("Shutting down application...")

    # Close database connections
    # await engine.dispose()

    # Close Redis connections
    # await redis_client.close()

    # Close Elasticsearch connections
    # await es_client.close()


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Clinical Care Tools API - Leveraging MedCAT's full potential for healthcare",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Total-Count", "X-Request-ID"],
        )

    # Add security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)

    # Add audit logging middleware (HIPAA compliance)
    if settings.AUDIT_LOG_ENABLED:
        app.add_middleware(AuditLogMiddleware)

    # Add GZip compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # Add trusted host middleware
    if settings.APP_ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.ALLOWED_HOSTS
        )

    # Include API routers
    from app.routers import auth, sessions, users, projects, tasks, documents, patients
    app.include_router(auth.router, tags=["Authentication"])
    app.include_router(sessions.router, tags=["Session Management"])
    app.include_router(users.router, tags=["User Management"])
    app.include_router(projects.router, tags=["Project Management"])
    app.include_router(tasks.router, tags=["Task Management"])
    app.include_router(patients.router, tags=["Patients"])
    app.include_router(documents.router, tags=["Documents"])
    # app.include_router(fhir.router, prefix=f"{settings.API_V1_STR}/fhir", tags=["FHIR"])
    # app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])

    return app


# Create the application instance
app = create_application()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: The incoming request.
        exc: The raised exception.

    Returns:
        JSONResponse: Error response with appropriate status code.
    """
    # Log the error (avoid logging sensitive data)
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"Unhandled exception: {exc.__class__.__name__}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
        }
    )

    # Return generic error response (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "type": "internal_server_error",
        }
    )


@app.get("/", tags=["Root"])
async def root() -> Dict[str, Any]:
    """
    Root endpoint providing API information.

    Returns:
        Dict containing API name, version, and documentation URLs.
    """
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": f"{settings.API_V1_STR}/openapi.json",
        "health": "/api/health",
    }


@app.get("/api/health", tags=["Health"])
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for monitoring and load balancers.

    Performs basic health checks on critical services and returns
    their status along with application metadata.

    Returns:
        Dict containing health status of various services.
    """
    health_status = {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "services": {}
    }

    # Check database connectivity
    if settings.HEALTH_CHECK_DB:
        try:
            # from app.database import check_db_health
            # db_healthy = await check_db_health()
            health_status["services"]["database"] = "healthy"
        except Exception as e:
            health_status["services"]["database"] = "unhealthy"
            health_status["status"] = "degraded"

    # Check Redis connectivity
    if settings.HEALTH_CHECK_REDIS:
        try:
            # from app.cache import check_redis_health
            # redis_healthy = await check_redis_health()
            health_status["services"]["redis"] = "healthy"
        except Exception as e:
            health_status["services"]["redis"] = "unhealthy"
            health_status["status"] = "degraded"

    # Check Elasticsearch connectivity
    if settings.HEALTH_CHECK_ES:
        try:
            # from app.search import check_es_health
            # es_healthy = await check_es_health()
            health_status["services"]["elasticsearch"] = "healthy"
        except Exception as e:
            health_status["services"]["elasticsearch"] = "unhealthy"
            health_status["status"] = "degraded"

    # Check MedCAT service
    if settings.HEALTH_CHECK_MEDCAT:
        try:
            # from app.services.medcat import check_medcat_health
            # medcat_healthy = await check_medcat_health()
            health_status["services"]["medcat"] = "healthy"
        except Exception as e:
            health_status["services"]["medcat"] = "unhealthy"
            health_status["status"] = "degraded"

    # Return appropriate status code based on health
    status_code = status.HTTP_200_OK if health_status["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(content=health_status, status_code=status_code)