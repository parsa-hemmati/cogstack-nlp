"""
Clinical Care Tools - FastAPI Application

Main entry point for the FastAPI application.
Web environment: Uses native PostgreSQL and Redis (no Docker).
Production: Uses Docker-based infrastructure.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.database import init_db, close_db
from app.core.redis_client import redis_client
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting Clinical Care Tools API...")
    print(f"📌 Environment: {settings.environment}")
    print(f"📌 Database: {settings.postgres_server}:{settings.postgres_port}/{settings.postgres_db}")
    print(f"📌 Redis: {settings.redis_host}:{settings.redis_port}")

    # Initialize database
    try:
        await init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")

    # Initialize Redis
    try:
        await redis_client.connect()
        if await redis_client.ping():
            print("✅ Redis connected")
        else:
            print("⚠️  Redis connection unhealthy")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")

    print("✅ Application startup complete")

    yield

    # Shutdown
    print("🛑 Shutting down Clinical Care Tools API...")

    # Close database connections
    try:
        await close_db()
        print("✅ Database connections closed")
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")

    # Close Redis connection
    try:
        await redis_client.disconnect()
        print("✅ Redis connection closed")
    except Exception as e:
        print(f"❌ Redis cleanup failed: {e}")

    print("✅ Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Clinical Care Tools API for healthcare NLP workflows",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument Prometheus metrics
Instrumentator().instrument(app).expose(app)


# Health check endpoint
@app.get("/health", tags=["health"])
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
            "version": "0.1.0",
            "timestamp": "2025-11-22T23:59:59.123456",
            "database": {
                "status": "connected" | "disconnected",
                "message": "Optional error message"
            }
        }
    """
    from datetime import datetime
    from app.core.database import engine
    from sqlalchemy import text

    # Check database connectivity
    database_status = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        database_status = {"status": "connected"}
    except Exception as e:
        database_status = {
            "status": "disconnected",
            "message": str(e)[:100]  # Truncate long error messages
        }

    # Determine overall health status
    overall_status = "healthy" if database_status["status"] == "connected" else "unhealthy"

    # Determine HTTP status code
    http_status = 200 if overall_status == "healthy" else 503

    # Build response
    response_data = {
        "status": overall_status,
        "version": settings.app_version,
        "timestamp": datetime.utcnow().isoformat(),
        "database": database_status,
    }

    return JSONResponse(
        content=response_data,
        status_code=http_status
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint.

    Returns:
        Welcome message and API information.
    """
    return {
        "message": "Clinical Care Tools API",
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health",
        "api": settings.api_v1_prefix,
    }


# API v1 router
from app.api.v1.routers.api_router import api_router

app.include_router(api_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
