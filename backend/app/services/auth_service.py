"""
Authentication Service
JWT token generation and verification using python-jose
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from jose import jwt, JWTError
from fastapi import HTTPException, status
from app.core.config import settings


class AuthService:
    """Service for creating and verifying JWT tokens."""

    @staticmethod
    def create_access_token(user_id: str, role: str, expires_delta: Optional[timedelta] = None) -> Dict[str, str]:
        """
        Create JWT access token.

        Args:
            user_id: User UUID (string)
            role: User role (clinician, researcher, admin)
            expires_delta: Optional custom expiry time

        Returns:
            Dictionary with 'access_token', 'token_type', 'expires_at'

        Security:
            - Token contains: sub (user_id), role, exp (expiry), iat (issued at), jti (token ID)
            - Signed with HS256 algorithm
            - 8-hour expiry by default
        """
        if expires_delta is None:
            expires_delta = timedelta(hours=settings.JWT_EXPIRE_HOURS)

        now = datetime.utcnow()
        expires_at = now + expires_delta

        payload = {
            "sub": user_id,  # Subject (user ID)
            "role": role,  # User role for RBAC
            "exp": expires_at,  # Expiration time
            "iat": now,  # Issued at
            "jti": str(uuid.uuid4()),  # JWT ID (unique token identifier)
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expires_at.isoformat(),
        }

    @staticmethod
    def verify_token(token: str) -> Dict:
        """
        Verify JWT token and return payload.

        Args:
            token: JWT access token (string)

        Returns:
            Token payload dictionary

        Raises:
            HTTPException(401): If token is invalid, expired, or signature doesn't match

        Security:
            - Validates signature with secret key
            - Checks expiration time
            - Prevents token reuse with jti (optional - implement blacklist)
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

            user_id: str = payload.get("sub")
            if user_id is None:
                raise credentials_exception

            return payload

        except JWTError:
            raise credentials_exception


# Create global service instance
auth_service = AuthService()
