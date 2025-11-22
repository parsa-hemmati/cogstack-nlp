"""
User Service for Clinical Care Tools.

Handles user management operations with audit logging and security.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserList
from app.core.security import hash_password


class UserService:
    """Service for handling user management operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize user service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_user(
        self,
        user_data: UserCreate,
        created_by: UUID
    ) -> User:
        """
        Create a new user.

        Args:
            user_data: User creation data
            created_by: ID of user creating this account

        Returns:
            Created user object

        Raises:
            HTTPException: If username/email already exists
        """
        # Check if username or email already exists
        result = await self.db.execute(
            select(User).where(
                or_(
                    User.username == user_data.username,
                    User.email == user_data.email
                )
            )
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            if existing_user.email == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

        # Create new user
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            role=user_data.role,
            is_active=user_data.is_active,
            must_change_password=user_data.must_change_password,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            updated_at=datetime.now(timezone.utc),
            updated_by=created_by
        )

        self.db.add(new_user)

        # Audit log
        await self._audit_log(
            action="USER_CREATED",
            user_id=created_by,
            resource_type="user",
            resource_id=new_user.id,
            details={"email": user_data.email, "role": user_data.role}
        )

        await self.db.commit()
        await self.db.refresh(new_user)

        return new_user

    async def get_users(
        self,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> UserList:
        """
        Get paginated list of users.

        Args:
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search term for username/email
            role: Filter by role
            is_active: Filter by active status

        Returns:
            Paginated user list
        """
        # Build query
        query = select(User)

        # Apply filters
        if search:
            query = query.where(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%")
                )
            )

        if role:
            query = query.where(User.role == role)

        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(User)
        if search or role or is_active is not None:
            count_query = count_query.where(query.whereclause)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(User.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        users = result.scalars().all()

        # Calculate pages
        pages = (total + per_page - 1) // per_page

        return UserList(
            items=[UserResponse.model_validate(user) for user in users],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            HTTPException: If user not found
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return user

    async def update_user(
        self,
        user_id: UUID,
        user_data: UserUpdate,
        updated_by: UUID
    ) -> User:
        """
        Update user information.

        Args:
            user_id: User ID to update
            user_data: Update data
            updated_by: ID of user performing update

        Returns:
            Updated user object

        Raises:
            HTTPException: If user not found or duplicate email/username
        """
        # Get existing user
        user = await self.get_user_by_id(user_id)

        # Check for duplicate username/email if being changed
        if user_data.username and user_data.username != user.username:
            existing = await self.db.execute(
                select(User).where(User.username == user_data.username)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )

        if user_data.email and user_data.email != user.email:
            existing = await self.db.execute(
                select(User).where(User.email == user_data.email)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already exists"
                )

        # Update fields
        update_dict = user_data.model_dump(exclude_unset=True)

        # Handle password update
        if "password" in update_dict:
            update_dict["password_hash"] = hash_password(update_dict.pop("password"))
            update_dict["must_change_password"] = False  # Reset flag after password change

        # Update timestamp and user
        update_dict["updated_at"] = datetime.now(timezone.utc)
        update_dict["updated_by"] = updated_by

        # Apply updates
        for field, value in update_dict.items():
            setattr(user, field, value)

        # Audit log
        await self._audit_log(
            action="USER_UPDATED",
            user_id=updated_by,
            resource_type="user",
            resource_id=user_id,
            details={"updated_fields": list(update_dict.keys())}
        )

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete_user(
        self,
        user_id: UUID,
        deleted_by: UUID
    ) -> None:
        """
        Soft delete a user (set is_active to False).

        Args:
            user_id: User ID to delete
            deleted_by: ID of user performing deletion

        Raises:
            HTTPException: If user not found or trying to delete self
        """
        # Prevent self-deletion
        if user_id == deleted_by:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )

        # Get user
        user = await self.get_user_by_id(user_id)

        # Soft delete
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        user.updated_by = deleted_by

        # Audit log
        await self._audit_log(
            action="USER_DELETED",
            user_id=deleted_by,
            resource_type="user",
            resource_id=user_id,
            details={"email": user.email}
        )

        await self.db.commit()

    async def get_user_stats(self, user_id: UUID) -> Dict[str, Any]:
        """
        Get user statistics (projects, tasks, etc.).

        Args:
            user_id: User ID

        Returns:
            Dictionary with user statistics
        """
        user = await self.get_user_by_id(user_id)

        # Get project count
        from app.models.project import ProjectMember
        project_count_result = await self.db.execute(
            select(func.count(ProjectMember.id)).where(ProjectMember.user_id == user_id)
        )
        project_count = project_count_result.scalar() or 0

        # Get task count
        from app.models.project import Task
        task_count_result = await self.db.execute(
            select(func.count(Task.id)).where(Task.assigned_to == user_id)
        )
        task_count = task_count_result.scalar() or 0

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "last_login": user.last_login,
            "projects_count": project_count,
            "tasks_assigned": task_count
        }

    async def _audit_log(
        self,
        action: str,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create audit log entry.

        Args:
            action: Action performed
            user_id: User performing action
            resource_type: Type of resource
            resource_id: ID of resource
            details: Additional details
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details or {},
            ip_address="system",  # Will be set from request context
            user_agent="system",  # Will be set from request context
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)