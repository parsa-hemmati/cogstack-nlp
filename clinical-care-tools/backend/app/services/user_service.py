"""
User management service.

Provides CRUD operations for user management:
- get_all_users: Retrieve all users
- get_user_by_id: Retrieve specific user
- create_user: Create new user with hashed password
- update_user: Update existing user
- check_username_exists: Check if username already exists
"""

from typing import List, Optional
import uuid

import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


async def get_all_users(db: AsyncSession) -> List[User]:
    """
    Retrieve all users.

    Args:
        db: Database session

    Returns:
        List of all users

    Example:
        users = await get_all_users(db)
        for user in users:
            print(f"{user.username} - {user.role}")
    """
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    return list(result.scalars().all())


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    """
    Retrieve user by ID.

    Args:
        db: Database session
        user_id: User ID (UUID string)

    Returns:
        User if found, None otherwise

    Example:
        user = await get_user_by_id(db, "550e8400-e29b-41d4-a716-446655440000")
        if user:
            print(f"Found user: {user.username}")
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return None

    result = await db.execute(
        select(User).where(User.id == user_uuid)
    )
    return result.scalar_one_or_none()


async def check_username_exists(db: AsyncSession, username: str) -> bool:
    """
    Check if username already exists.

    Args:
        db: Database session
        username: Username to check

    Returns:
        True if username exists, False otherwise

    Example:
        exists = await check_username_exists(db, "john_doe")
        if exists:
            raise ValueError("Username already taken")
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    existing_user = result.scalar_one_or_none()
    return existing_user is not None


async def create_user(
    db: AsyncSession,
    user_data: UserCreate
) -> User:
    """
    Create new user with hashed password.

    Args:
        db: Database session
        user_data: User creation data (username, password, role, etc.)

    Returns:
        Created user

    Raises:
        HTTPException: 400 if username already exists or password is weak

    Example:
        user_data = UserCreate(
            username="john_doe",
            full_name="John Doe",
            password="SecurePass123!",
            role="clinician"
        )
        user = await create_user(db, user_data)
        print(f"Created user: {user.id}")
    """
    # Check if username already exists
    if await check_username_exists(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )

    # Hash password using bcrypt
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    # Create user
    new_user = User(
        id=uuid.uuid4(),
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        role=user_data.role.value,
        is_active=True,
        must_change_password=True  # New users must change password on first login
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def update_user(
    db: AsyncSession,
    user_id: str,
    update_data: UserUpdate
) -> User:
    """
    Update existing user.

    Args:
        db: Database session
        user_id: User ID (UUID string)
        update_data: User update data (only provided fields will be updated)

    Returns:
        Updated user

    Raises:
        HTTPException: 404 if user not found

    Example:
        update_data = UserUpdate(full_name="John Doe Updated", is_active=False)
        user = await update_user(db, user_id, update_data)
        print(f"Updated user: {user.full_name}")
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        # Convert role enum to string if present
        if field == "role" and value is not None:
            value = value.value
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(db: AsyncSession, user_id: str) -> None:
    """
    Delete user (soft delete by setting is_active=False).

    Args:
        db: Database session
        user_id: User ID (UUID string)

    Raises:
        HTTPException: 404 if user not found

    Example:
        await delete_user(db, user_id)
    """
    user = await get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found"
        )

    # Soft delete
    user.is_active = False
    await db.commit()
