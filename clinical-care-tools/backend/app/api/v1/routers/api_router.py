"""
API v1 router.

Aggregates all v1 API endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, projects, tasks

# Create API v1 router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(projects.router, tags=["projects"])
api_router.include_router(tasks.router, tags=["tasks"])
