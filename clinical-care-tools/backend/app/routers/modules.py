"""
Module Management API Router

Endpoints for managing pluggable modules in the Clinical Care Tools application.
"""

import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.module_system import get_module_system
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.module import Module
from app.models.user import User
from app.schemas.module import (
    ModuleCreateRequest,
    ModuleEnableRequest,
    ModuleListResponse,
    ModuleResponse,
    ModuleStatus,
    ModuleUpdateRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/modules",
    tags=["modules"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=ModuleListResponse)
async def list_modules(
    skip: int = 0,
    limit: int = 100,
    enabled_only: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ModuleListResponse:
    """
    List all installed modules.

    Args:
        skip: Number of modules to skip
        limit: Maximum number of modules to return
        enabled_only: Only return enabled modules
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of modules with metadata
    """
    # Check permission
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user cannot view modules",
        )

    query = db.query(Module)

    if enabled_only:
        query = query.filter(Module.is_enabled == True)

    total = query.count()
    modules = query.offset(skip).limit(limit).all()

    return ModuleListResponse(
        modules=[ModuleResponse.model_validate(module) for module in modules],
        total=total,
    )


@router.get("/status", response_model=dict)
async def get_module_status(
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Get runtime status of all loaded modules.

    Args:
        current_user: Current authenticated user

    Returns:
        Dictionary of module status information
    """
    # Check permission
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can view module status",
        )

    module_system = get_module_system()
    return module_system.get_module_status()


@router.get("/{module_id}", response_model=ModuleResponse)
async def get_module(
    module_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ModuleResponse:
    """
    Get details of a specific module.

    Args:
        module_id: Module UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Module details
    """
    # Check permission
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user cannot view modules",
        )

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found",
        )

    return ModuleResponse.model_validate(module)


@router.post("/", response_model=ModuleResponse)
async def create_module(
    request: ModuleCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ModuleResponse:
    """
    Create/install a new module.

    Args:
        request: Module creation request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created module

    Note:
        This endpoint registers a module in the database but does not
        load its code. The module system will load it on next startup.
    """
    # Check permission
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can install modules",
        )

    # Check if module already exists
    existing = db.query(Module).filter(Module.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Module '{request.name}' already exists",
        )

    # Create module record
    module = Module(
        name=request.name,
        display_name=request.display_name,
        description=request.description,
        version=request.version,
        is_enabled=False,  # Start disabled
        configuration=request.configuration.model_dump(),
        permissions=[],  # Will be populated when module loads
        routes=[],  # Will be populated when module loads
        installed_by=current_user.id,
    )

    db.add(module)
    db.commit()
    db.refresh(module)

    logger.info(f"Module '{request.name}' installed by {current_user.username}")

    return ModuleResponse.model_validate(module)


@router.patch("/{module_id}", response_model=ModuleResponse)
async def update_module(
    module_id: UUID,
    request: ModuleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ModuleResponse:
    """
    Update module configuration.

    Args:
        module_id: Module UUID
        request: Update request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated module
    """
    # Check permission
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can update modules",
        )

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found",
        )

    # Update fields if provided
    if request.display_name is not None:
        module.display_name = request.display_name

    if request.description is not None:
        module.description = request.description

    if request.configuration is not None:
        module.configuration = request.configuration.model_dump()

    module.updated_by = current_user.id

    db.commit()
    db.refresh(module)

    logger.info(f"Module '{module.name}' updated by {current_user.username}")

    return ModuleResponse.model_validate(module)


@router.post("/{module_id}/enable", response_model=ModuleResponse)
async def enable_module(
    module_id: UUID,
    request: ModuleEnableRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ModuleResponse:
    """
    Enable or disable a module.

    Args:
        module_id: Module UUID
        request: Enable/disable request
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated module
    """
    # Check permission
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can enable/disable modules",
        )

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found",
        )

    module_system = get_module_system()

    # Enable or disable the module
    if request.enabled:
        success = module_system.enable_module(module.name, db)
        action = "enabled"
    else:
        success = module_system.disable_module(module.name, db)
        action = "disabled"

    if not success and not request.force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to {action[:-1]} module '{module.name}' - check dependencies",
        )

    # Update database if forced
    if request.force:
        module.is_enabled = request.enabled
        module.updated_by = current_user.id
        db.commit()

    db.refresh(module)

    logger.info(f"Module '{module.name}' {action} by {current_user.username}")

    return ModuleResponse.model_validate(module)


@router.delete("/{module_id}")
async def delete_module(
    module_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """
    Delete/uninstall a module.

    Args:
        module_id: Module UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message
    """
    # Check permission
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can uninstall modules",
        )

    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Module {module_id} not found",
        )

    # Check if module is enabled
    if module.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete enabled module - disable it first",
        )

    module_name = module.name
    db.delete(module)
    db.commit()

    logger.info(f"Module '{module_name}' uninstalled by {current_user.username}")

    return {"message": f"Module '{module_name}' uninstalled successfully"}