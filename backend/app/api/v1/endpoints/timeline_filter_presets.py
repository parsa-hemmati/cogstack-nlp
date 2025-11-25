"""Timeline filter preset API endpoints."""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.db.session import get_db
from app.models.user import User
from app.models.timeline_filter_preset import TimelineFilterPreset
from app.schemas.timeline_filter_preset import (
    FilterPresetCreate,
    FilterPresetUpdate,
    FilterPresetResponse,
    FilterPresetListResponse
)
from app.core.security import get_current_user
from app.services.audit_service import audit_service

router = APIRouter()


@router.post("", response_model=FilterPresetResponse, status_code=status.HTTP_201_CREATED)
async def create_filter_preset(
    preset_data: FilterPresetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FilterPresetResponse:
    """
    Create a new filter preset.

    - **name**: Preset name (1-100 characters, unique per user)
    - **filters**: Filter configuration (JSONB)
    - **is_default**: Set as default preset (optional)

    If is_default=True, automatically un-sets other defaults for this user.

    Requires authentication.
    """
    # Check if preset name already exists for this user
    stmt = select(TimelineFilterPreset).where(
        and_(
            TimelineFilterPreset.user_id == current_user.id,
            TimelineFilterPreset.name == preset_data.name
        )
    )
    result = await db.execute(stmt)
    existing_preset = result.scalar_one_or_none()

    if existing_preset:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Preset with name '{preset_data.name}' already exists"
        )

    # If setting as default, un-set other defaults
    if preset_data.is_default:
        stmt = select(TimelineFilterPreset).where(
            and_(
                TimelineFilterPreset.user_id == current_user.id,
                TimelineFilterPreset.is_default == True
            )
        )
        result = await db.execute(stmt)
        existing_defaults = result.scalars().all()

        for default_preset in existing_defaults:
            default_preset.is_default = False
            db.add(default_preset)

    # Create new preset
    new_preset = TimelineFilterPreset(
        user_id=current_user.id,
        name=preset_data.name,
        filters=preset_data.filters,
        is_default=preset_data.is_default
    )

    db.add(new_preset)
    await db.commit()
    await db.refresh(new_preset)

    # Audit log
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        action="CREATE_FILTER_PRESET",
        resource_type="timeline_filter_preset",
        resource_id=str(new_preset.id),
        details={"name": preset_data.name, "is_default": preset_data.is_default}
    )

    return FilterPresetResponse.model_validate(new_preset)


@router.get("", response_model=FilterPresetListResponse)
async def list_filter_presets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FilterPresetListResponse:
    """
    List all filter presets for the current user.

    Returns presets ordered by:
    1. Default presets first (is_default=True)
    2. Then by creation date (newest first)

    Requires authentication.
    """
    # Query user's presets
    stmt = select(TimelineFilterPreset).where(
        TimelineFilterPreset.user_id == current_user.id
    ).order_by(
        TimelineFilterPreset.is_default.desc(),
        TimelineFilterPreset.created_at.desc()
    )

    result = await db.execute(stmt)
    presets = result.scalars().all()

    # Audit log
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        action="LIST_FILTER_PRESETS",
        resource_type="timeline_filter_preset",
        resource_id=None,
        details={"count": len(presets)}
    )

    return FilterPresetListResponse(
        presets=[FilterPresetResponse.model_validate(p) for p in presets],
        total=len(presets)
    )


@router.get("/{preset_id}", response_model=FilterPresetResponse)
async def get_filter_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FilterPresetResponse:
    """
    Get a specific filter preset by ID.

    - **preset_id**: UUID of the preset

    Returns 404 if preset doesn't exist or doesn't belong to current user.

    Requires authentication.
    """
    # Query preset (check ownership)
    stmt = select(TimelineFilterPreset).where(
        and_(
            TimelineFilterPreset.id == preset_id,
            TimelineFilterPreset.user_id == current_user.id
        )
    )

    result = await db.execute(stmt)
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter preset not found"
        )

    # Audit log
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        action="VIEW_FILTER_PRESET",
        resource_type="timeline_filter_preset",
        resource_id=str(preset.id),
        details={"name": preset.name}
    )

    return FilterPresetResponse.model_validate(preset)


@router.put("/{preset_id}", response_model=FilterPresetResponse)
async def update_filter_preset(
    preset_id: UUID,
    update_data: FilterPresetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> FilterPresetResponse:
    """
    Update a filter preset.

    - **preset_id**: UUID of the preset
    - **name**: Updated preset name (optional)
    - **filters**: Updated filter configuration (optional)
    - **is_default**: Update default status (optional)

    If setting is_default=True, automatically un-sets other defaults.

    Returns 404 if preset doesn't exist or doesn't belong to current user.

    Requires authentication.
    """
    # Query preset (check ownership)
    stmt = select(TimelineFilterPreset).where(
        and_(
            TimelineFilterPreset.id == preset_id,
            TimelineFilterPreset.user_id == current_user.id
        )
    )

    result = await db.execute(stmt)
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter preset not found"
        )

    # Check name uniqueness if changing name
    if update_data.name and update_data.name != preset.name:
        stmt = select(TimelineFilterPreset).where(
            and_(
                TimelineFilterPreset.user_id == current_user.id,
                TimelineFilterPreset.name == update_data.name,
                TimelineFilterPreset.id != preset_id
            )
        )
        result = await db.execute(stmt)
        existing_preset = result.scalar_one_or_none()

        if existing_preset:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Preset with name '{update_data.name}' already exists"
            )

    # If setting as default, un-set other defaults
    if update_data.is_default:
        stmt = select(TimelineFilterPreset).where(
            and_(
                TimelineFilterPreset.user_id == current_user.id,
                TimelineFilterPreset.is_default == True,
                TimelineFilterPreset.id != preset_id
            )
        )
        result = await db.execute(stmt)
        existing_defaults = result.scalars().all()

        for default_preset in existing_defaults:
            default_preset.is_default = False
            db.add(default_preset)

    # Update fields
    if update_data.name is not None:
        preset.name = update_data.name
    if update_data.filters is not None:
        preset.filters = update_data.filters
    if update_data.is_default is not None:
        preset.is_default = update_data.is_default

    db.add(preset)
    await db.commit()
    await db.refresh(preset)

    # Audit log
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        action="UPDATE_FILTER_PRESET",
        resource_type="timeline_filter_preset",
        resource_id=str(preset.id),
        details={"updated_fields": update_data.model_dump(exclude_unset=True)}
    )

    return FilterPresetResponse.model_validate(preset)


@router.delete("/{preset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a filter preset.

    - **preset_id**: UUID of the preset

    Hard delete (permanent removal).

    Returns 404 if preset doesn't exist or doesn't belong to current user.

    Requires authentication.
    """
    # Query preset (check ownership)
    stmt = select(TimelineFilterPreset).where(
        and_(
            TimelineFilterPreset.id == preset_id,
            TimelineFilterPreset.user_id == current_user.id
        )
    )

    result = await db.execute(stmt)
    preset = result.scalar_one_or_none()

    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Filter preset not found"
        )

    # Audit log (before deletion)
    await audit_service.log_action(
        db=db,
        user_id=current_user.id,
        action="DELETE_FILTER_PRESET",
        resource_type="timeline_filter_preset",
        resource_id=str(preset.id),
        details={"name": preset.name}
    )

    # Delete preset
    await db.delete(preset)
    await db.commit()
