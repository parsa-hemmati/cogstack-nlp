"""
CORS Middleware Configuration

Handles Cross-Origin Resource Sharing (CORS) for the API.
This is handled by FastAPI's built-in CORSMiddleware in main.py,
but this module provides additional utilities and configuration.
"""

from typing import List, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def configure_cors(app: FastAPI) -> None:
    """
    Configure CORS middleware for the FastAPI application.

    Args:
        app: The FastAPI application instance.
    """
    # Only add CORS if origins are configured
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=[
                "X-Total-Count",  # For pagination
                "X-Request-ID",   # For request tracking
                "X-Audit-ID",     # For audit trail
            ],
        )


def is_cors_origin_allowed(origin: str) -> bool:
    """
    Check if an origin is allowed for CORS.

    Args:
        origin: The origin to check.

    Returns:
        bool: True if origin is allowed.
    """
    if not settings.BACKEND_CORS_ORIGINS:
        return False

    # Allow exact matches
    if origin in settings.BACKEND_CORS_ORIGINS:
        return True

    # Allow wildcard subdomains (e.g., *.example.com)
    for allowed_origin in settings.BACKEND_CORS_ORIGINS:
        if isinstance(allowed_origin, str) and allowed_origin.startswith("*."):
            # Extract domain from wildcard
            domain = allowed_origin[2:]  # Remove *.
            if origin.endswith(domain):
                return True

    return False


def get_cors_headers() -> dict:
    """
    Get CORS headers for manual response construction.

    Returns:
        dict: CORS headers.
    """
    return {
        "Access-Control-Allow-Origin": "*" if "*" in settings.BACKEND_CORS_ORIGINS else ",".join(settings.BACKEND_CORS_ORIGINS),
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true" if settings.BACKEND_CORS_ORIGINS else "false",
    }