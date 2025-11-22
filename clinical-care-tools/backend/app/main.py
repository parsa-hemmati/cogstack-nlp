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
from app.core.redis_client import redis_client


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


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns:
        Application health status including database and Redis connectivity.
    """
    # Check database
    db_healthy = True
    db_error = None
    try:
        from app.core.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        db_healthy = False
        db_error = str(e)

    # Check Redis
    redis_healthy = await redis_client.ping()

    # Overall status
    healthy = db_healthy and redis_healthy

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={
            "status": "healthy" if healthy else "unhealthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {
                "database": {
                    "status": "healthy" if db_healthy else "unhealthy",
                    "error": db_error if not db_healthy else None,
                },
                "redis": {
                    "status": "healthy" if redis_healthy else "unhealthy",
                },
            },
        },
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


# API v1 router (placeholder - will add endpoints later)
# from app.api.v1.routers import api_router
# app.include_router(api_router, prefix=settings.api_v1_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
