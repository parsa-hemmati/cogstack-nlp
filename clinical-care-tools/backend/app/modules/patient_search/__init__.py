"""
Patient Search Module

Provides advanced patient search capabilities with medical concept filtering
and meta-annotation support for 95% precision.
"""

import logging
from fastapi import APIRouter

from .router import router as search_router
from .service import PatientSearchService

logger = logging.getLogger(__name__)

# Module version
__version__ = "1.0.0"

# Module metadata
__module_name__ = "patient-search"
__display_name__ = "Patient Search"


def create_router() -> APIRouter:
    """
    Create and configure the module router.

    Returns:
        Configured FastAPI router
    """
    return search_router


def on_enable():
    """
    Called when the module is enabled.

    Perform initialization tasks like:
    - Checking service connectivity
    - Loading cached data
    - Starting background tasks
    """
    logger.info("Patient Search module enabled")

    # Initialize service
    service = PatientSearchService()

    # Check MedCAT service connectivity
    try:
        if service.check_medcat_connectivity():
            logger.info("Successfully connected to MedCAT service")
        else:
            logger.warning("MedCAT service not available - searches will be limited")
    except Exception as e:
        logger.error(f"Failed to check MedCAT connectivity: {e}")


def on_disable():
    """
    Called when the module is disabled.

    Perform cleanup tasks like:
    - Stopping background tasks
    - Clearing caches
    - Closing connections
    """
    logger.info("Patient Search module disabled")

    # Cleanup tasks could go here
    pass


# Export public interface
__all__ = [
    "create_router",
    "on_enable",
    "on_disable",
    "PatientSearchService",
    "__version__",
    "__module_name__",
    "__display_name__",
]