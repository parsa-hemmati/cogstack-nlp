"""
Module Registry Service.

Dynamic module loading and registration for modular architecture.

Modules:
- patient-search: Search patients by clinical concepts
- timeline-view: Visualize patient timeline
- clinical-decision-support: CDS Hooks integration
- (Future modules can be registered)

Functions:
- get_enabled_modules(db): List all enabled modules
- get_module(db, name): Get module by name
- register_module_routes(app, module_name): Register module routes dynamically

Usage:
    >>> from app.services.module_registry import get_enabled_modules, get_module
    >>>
    >>> # List enabled modules (for UI nav)
    >>> modules = await get_enabled_modules(db)
    >>> for module in modules:
    ...     print(f"{module.display_name}: {module.description}")
    >>>
    >>> # Get specific module configuration
    >>> module = await get_module(db, "patient-search")
    >>> max_results = module.config["max_results"]
"""

import logging
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.module import Module


logger = logging.getLogger(__name__)


async def get_enabled_modules(db: AsyncSession) -> List[Module]:
    """
    Get list of enabled modules.

    Returns only modules where enabled=True, sorted alphabetically by name.
    Used for displaying available modules in UI navigation.

    Args:
        db: Database session

    Returns:
        List[Module]: Enabled modules sorted by name

    Example:
        >>> modules = await get_enabled_modules(db)
        >>> for module in modules:
        ...     print(f"{module.name}: {module.display_name}")
        patient-search: Patient Search
        timeline-view: Patient Timeline
    """
    logger.debug("Fetching enabled modules")

    # Query enabled modules, sorted by name
    result = await db.execute(
        select(Module)
        .where(Module.enabled == True)  # noqa: E712 (SQLAlchemy requires == True)
        .order_by(Module.name)
    )

    modules = result.scalars().all()

    logger.info(f"Found {len(modules)} enabled modules")

    return modules


async def get_module(db: AsyncSession, name: str) -> Optional[Module]:
    """
    Get module by name.

    Returns module regardless of enabled state (for admin management).

    Args:
        db: Database session
        name: Module name (e.g., "patient-search")

    Returns:
        Optional[Module]: Module if found, None otherwise

    Example:
        >>> module = await get_module(db, "patient-search")
        >>> if module:
        ...     print(f"Max results: {module.config['max_results']}")
        Max results: 100
    """
    logger.debug(f"Fetching module: {name}")

    # Query module by name
    result = await db.execute(
        select(Module).where(Module.name == name)
    )

    module = result.scalar_one_or_none()

    if module:
        logger.debug(f"Module found: {name} (enabled={module.enabled})")
    else:
        logger.warning(f"Module not found: {name}")

    return module


def register_module_routes(app, module_name: str) -> None:
    """
    Register module-specific routes dynamically.

    This is a placeholder for future dynamic route registration.
    When implemented, will load module-specific API routes based on module name.

    Args:
        app: FastAPI application instance
        module_name: Name of module to register routes for

    Example:
        >>> # Future usage
        >>> register_module_routes(app, "patient-search")
        # Registers /api/v1/modules/patient-search/* routes

    Note:
        Currently a no-op. Will be implemented when module routes are modularized.
    """
    logger.info(f"Placeholder: register_module_routes called for {module_name}")

    # TODO: Implement dynamic route registration
    # For now, routes are statically registered in app/api/v1/modules/*

    # Future implementation:
    # 1. Import module-specific router
    # 2. Register with FastAPI app
    # 3. Add to module permissions check
