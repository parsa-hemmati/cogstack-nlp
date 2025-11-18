"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import auth
from app.core.config import settings
from app.core.scheduler import scheduler
from app.db.session import close_db, init_db

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database (create tables if needed)
    # Note: In production, use Alembic migrations instead
    if settings.is_development:
        await init_db()
        logger.info("Database initialized")

    # Start background task scheduler
    scheduler.start()
    logger.info("Background scheduler started")

    yield

    # Shutdown
    logger.info("Shutting down application")
    scheduler.stop()
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Clinical Care Tools - Healthcare NLP Platform",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs" if settings.is_development else "disabled",
    }


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Used by Docker healthcheck and monitoring systems.
    """
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/info", tags=["Info"])
async def info() -> dict[str, Any]:
    """Application information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "features": {
            "fhir_export": settings.ENABLE_FHIR_EXPORT,
            "clinical_decision_support": settings.ENABLE_CLINICAL_DECISION_SUPPORT,
            "break_glass_access": settings.ENABLE_BREAK_GLASS_ACCESS,
        },
    }


# Include API routers
from app.api.v1 import (
    admin,
    clinical_incidents,
    clinical_overrides,
    critical_findings,
    patients,
    search,
    timeline,
)
from app.api.v1.endpoints import (
    deidentify, phi, clinical_coding,
    cds, fhir, alerting, population_health, analytics
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
app.include_router(timeline.router, prefix="/api/v1/timeline", tags=["Timeline"])
app.include_router(search.router, prefix="/api/v1", tags=["Search"])
app.include_router(deidentify.router, prefix="/api/v1", tags=["De-identification"])
app.include_router(clinical_coding.router, prefix="/api/v1", tags=["Clinical Coding"])
app.include_router(cds.router, prefix="/api/v1", tags=["Clinical Decision Support"])
app.include_router(fhir.router, prefix="/api/v1", tags=["FHIR R4"])
app.include_router(alerting.router, prefix="/api/v1", tags=["Automated Alerting"])
app.include_router(population_health.router, prefix="/api/v1", tags=["Population Health"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Advanced Analytics"])
app.include_router(phi.router, prefix="/api/v1", tags=["PHI Detection (Internal)"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin"])
app.include_router(
    clinical_overrides.router, prefix="/api/v1", tags=["Clinical Overrides"]
)
app.include_router(
    clinical_incidents.router, prefix="/api/v1", tags=["Clinical Incidents"]
)
app.include_router(
    critical_findings.router, prefix="/api/v1", tags=["Critical Findings"]
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """Handle uncaught exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if settings.is_development:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "type": type(exc).__name__},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_development,
        log_level=settings.LOG_LEVEL.lower(),
    )
