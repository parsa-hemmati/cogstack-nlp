"""User Profile Management API endpoints.

Endpoints for users to manage their own profile:
- Update profile (email)
- Change password

All operations audit logged.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserChangePassword, UserResponse, UserUpdate
from app.services.audit_service import AuditService
from app.services.session_service import session_service

router = APIRouter()
audit_service = AuditService()


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's profile.

    Args:
        current_user: Current authenticated user
        db: Database session

    Returns:
        Current user's profile
    """
    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="VIEW_OWN_PROFILE",
        resource_type="user",
        resource_id=str(current_user.id),
    )

    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_my_profile(
    profile_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user's profile.

    Users can update their own email. Role changes require admin.

    Args:
        profile_data: Profile update data (email only for self-update)
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated user profile

    Raises:
        HTTPException: 400 if trying to change restricted fields
    """
    # Users cannot change their own role, is_active, or can_break_glass
    if profile_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role. Contact an administrator.",
        )

    if profile_data.is_active is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own active status. Contact an administrator.",
        )

    if profile_data.can_break_glass is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own break-glass permission. Contact an administrator.",
        )

    # Track changes for audit log
    changes = {}

    # Update email if provided
    if profile_data.email is not None:
        # Check for duplicate email
        stmt = select(User).where(User.email == profile_data.email, User.id != current_user.id)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user is not None:
            # Audit log the failure (details in audit trail, not user-facing error)
            await audit_service.log_action(
                db=db,
                user=current_user,
                action="UPDATE_OWN_PROFILE_FAILED",
                resource_type="user",
                resource_id=str(current_user.id),
                details={"reason": "duplicate_email", "attempted_email": profile_data.email},
                success="failure",
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address already in use. Please use a different email.",
            )

        changes["email"] = {"old": current_user.email, "new": profile_data.email}
        current_user.email = profile_data.email

    await db.commit()
    await db.refresh(current_user)

    # Audit log
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="UPDATE_OWN_PROFILE",
        resource_type="user",
        resource_id=str(current_user.id),
        details={"changes": changes},
    )

    return UserResponse.model_validate(current_user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    password_data: UserChangePassword,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change current user's password.

    Requires current password for verification.

    Args:
        password_data: Current and new passwords
        current_user: Current authenticated user
        db: Database session

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 400 if current password is incorrect
    """
    # Verify current password
    if not current_user.verify_password(password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Set new password
    current_user.set_password(password_data.new_password)

    await db.commit()

    # Invalidate all existing sessions for security (except current one handled by client)
    # After password change, all sessions should be invalidated to prevent compromised sessions
    invalidated_count = await session_service.invalidate_all_user_sessions(
        user_id=str(current_user.id)
    )

    # Audit log (IMPORTANT: password changes must be logged)
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="CHANGE_PASSWORD",
        resource_type="user",
        resource_id=str(current_user.id),
        details={"method": "self-service", "sessions_invalidated": invalidated_count},
    )

    return None
