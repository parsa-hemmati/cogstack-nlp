"""
Authentication Service for Clinical Care Tools.

Handles user authentication, token management, and password operations.
HIPAA Compliance: All authentication events are audit logged.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.core.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.config import settings
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import UserCreate, UserLogin, Token


class AuthService:
    """Service for handling authentication operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize authentication service.

        Args:
            db: Database session
        """
        self.db = db

    async def register_user(
        self,
        user_data: UserCreate,
        created_by: Optional[str] = None
    ) -> User:
        """
        Register a new user.

        Args:
            user_data: User registration data
            created_by: ID of user creating this account (for admin creation)

        Returns:
            Created user object

        Raises:
            HTTPException: If email already exists or password is weak
        """
        # Check if user already exists
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            await self._audit_log(
                action="REGISTRATION_FAILED",
                user_id=None,
                details={"reason": "email_exists", "email": user_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Validate password strength
        is_valid, errors = validate_password_strength(user_data.password)
        if not is_valid:
            await self._audit_log(
                action="REGISTRATION_FAILED",
                user_id=None,
                details={"reason": "weak_password", "email": user_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "Password does not meet requirements", "errors": errors}
            )

        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password,
            role=user_data.role,
            is_active=True,
            created_at=datetime.now(timezone.utc),
            created_by=created_by
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)

        # Audit log successful registration
        await self._audit_log(
            action="USER_REGISTERED",
            user_id=str(new_user.id),
            details={
                "email": new_user.email,
                "role": new_user.role,
                "created_by": created_by
            }
        )

        return new_user

    async def authenticate_user(
        self,
        login_data: UserLogin,
        ip_address: str,
        user_agent: str
    ) -> Optional[Token]:
        """
        Authenticate a user and create tokens.

        Args:
            login_data: Login credentials
            ip_address: Client IP address
            user_agent: Client User-Agent

        Returns:
            Token object with access and refresh tokens if successful

        Raises:
            HTTPException: If authentication fails
        """
        # Find user by email
        result = await self.db.execute(
            select(User).where(User.email == login_data.email)
        )
        user = result.scalar_one_or_none()

        # Check user exists and password is correct
        if not user or not verify_password(login_data.password, user.hashed_password):
            await self._audit_log(
                action="LOGIN_FAILED",
                user_id=None,
                details={
                    "email": login_data.email,
                    "ip_address": ip_address,
                    "reason": "invalid_credentials"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Check if user is active
        if not user.is_active:
            await self._audit_log(
                action="LOGIN_FAILED",
                user_id=str(user.id),
                details={
                    "email": login_data.email,
                    "reason": "account_inactive"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )

        # Update last login
        await self.db.execute(
            update(User).where(User.id == user.id).values(
                last_login=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        # Create tokens
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role
            }
        )
        refresh_token = create_refresh_token(str(user.id))

        # Audit successful login
        await self._audit_log(
            action="USER_LOGIN",
            user_id=str(user.id),
            details={
                "ip_address": ip_address,
                "user_agent": user_agent[:200]  # Truncate user agent
            }
        )

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token if refresh token is valid

        Raises:
            HTTPException: If refresh token is invalid
        """
        # Verify refresh token
        payload = verify_token(refresh_token, expected_type="refresh")
        if not payload:
            await self._audit_log(
                action="TOKEN_REFRESH_FAILED",
                user_id=None,
                details={"reason": "invalid_token"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

        user_id = payload.get("sub")

        # Get user from database
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            await self._audit_log(
                action="TOKEN_REFRESH_FAILED",
                user_id=user_id,
                details={"reason": "user_not_found_or_inactive"}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive"
            )

        # Create new access token
        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "role": user.role
            }
        )

        # Audit token refresh
        await self._audit_log(
            action="TOKEN_REFRESHED",
            user_id=str(user.id),
            details={}
        )

        return access_token

    async def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from access token.

        Args:
            token: JWT access token

        Returns:
            User object if token is valid

        Raises:
            HTTPException: If token is invalid or user not found
        """
        # Verify token
        payload = verify_token(token, expected_type="access")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user_id = payload.get("sub")

        # Get user from database
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )

        # Update last activity
        await self.db.execute(
            update(User).where(User.id == user.id).values(
                last_activity=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        return user

    async def change_password(
        self,
        user: User,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        Change user password.

        Args:
            user: User object
            old_password: Current password
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            HTTPException: If old password incorrect or new password weak
        """
        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            await self._audit_log(
                action="PASSWORD_CHANGE_FAILED",
                user_id=str(user.id),
                details={"reason": "incorrect_old_password"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )

        # Validate new password
        is_valid, errors = validate_password_strength(new_password)
        if not is_valid:
            await self._audit_log(
                action="PASSWORD_CHANGE_FAILED",
                user_id=str(user.id),
                details={"reason": "weak_new_password"}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"message": "New password does not meet requirements", "errors": errors}
            )

        # Check password not reused
        if verify_password(new_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password"
            )

        # Update password
        hashed_password = hash_password(new_password)
        await self.db.execute(
            update(User).where(User.id == user.id).values(
                hashed_password=hashed_password,
                password_changed_at=datetime.now(timezone.utc)
            )
        )
        await self.db.commit()

        # Audit password change
        await self._audit_log(
            action="PASSWORD_CHANGED",
            user_id=str(user.id),
            details={}
        )

        return True

    async def _audit_log(
        self,
        action: str,
        user_id: Optional[str],
        details: Dict[str, Any]
    ):
        """
        Create audit log entry.

        Args:
            action: Action performed
            user_id: ID of user performing action
            details: Additional details to log
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type="AUTH",
            resource_id=user_id,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)
        await self.db.commit()