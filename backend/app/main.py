"""
Clinical Care Tools - Backend Application
FastAPI application entry point
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import audit, auth, break_glass, deidentification, documents, health, manual_annotations, patient_search, profile, roles, search, sessions, timeline, timeline_filter_presets, users

logger = logging.getLogger(__name__)

# Application metadata
APP_NAME = "Clinical Care Tools Backend"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Backend API for Clinical Care Tools - Patient Search and Timeline Visualization"

# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS (will be restricted in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://localhost:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(profile.router, prefix="/api/v1/users", tags=["profile"])
app.include_router(roles.router, prefix="/api/v1/roles", tags=["roles"])
app.include_router(break_glass.router, prefix="/api/v1/break-glass", tags=["break-glass"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(documents.router, prefix="/api/v1", tags=["documents"])
app.include_router(patient_search.router, prefix="/api/v1", tags=["patients"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(timeline.router, prefix="/api/v1", tags=["timeline"])
app.include_router(timeline_filter_presets.router, prefix="/api/v1/timeline/filters", tags=["timeline-filters"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(deidentification.router, prefix="/api/v1", tags=["de-identification"])
app.include_router(manual_annotations.router, prefix="/api/v1/deidentify", tags=["manual-annotations"])


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker/Kubernetes."""
    return {"status": "healthy", "version": APP_VERSION}


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Execute on application startup."""
    logger.info(f"🚀 {APP_NAME} v{APP_VERSION} starting...")

    # Start background job for document processing
    from app.jobs import start_background_job
    await start_background_job(interval_seconds=60, batch_size=10)
    logger.info("📄 Document processing job started")

    logger.info("✅ Application ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    logger.info(f"⏹️  {APP_NAME} shutting down...")

    # Stop background job
    from app.jobs import stop_background_job
    await stop_background_job()
    logger.info("📄 Document processing job stopped")

    logger.info("✅ Shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development only
        log_level="info",
    )
