"""
Clinical Care Tools - Backend Application
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import auth

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
    print(f"🚀 {APP_NAME} v{APP_VERSION} starting...")
    # TODO: Initialize database connection pool
    # TODO: Load MedCAT models
    print("✅ Application ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Execute on application shutdown."""
    print(f"⏹️  {APP_NAME} shutting down...")
    # TODO: Close database connections
    # TODO: Cleanup resources
    print("✅ Shutdown complete")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development only
        log_level="info",
    )
