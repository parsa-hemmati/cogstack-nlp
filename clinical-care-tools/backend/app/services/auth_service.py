"""
JWT authentication service.

Provides token creation and verification for user authentication.
Uses python-jose for JWT operations with HS256 algorithm.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict
import uuid

from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.core.config import settings


# JWT Configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def create_access_token(
    user_id: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> Dict[str, str]:
    """
    Create JWT access token for authenticated user.

    Args:
        user_id: User's unique identifier (UUID as string)
        role: User's role (admin, clinician, researcher, viewer)
        expires_delta: Optional custom expiration time (default: 8 hours)

    Returns:
        Dictionary with:
            - access_token: JWT token string
            - token_type: "bearer"

    Example:
        >>> result = create_access_token(user_id="abc-123", role="clinician")
        >>> token = result["access_token"]
        >>> # Use token in Authorization: Bearer <token>
    """
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    # Build JWT payload with standard and custom claims
    payload = {
        "sub": user_id,              # Subject (user ID)
        "role": role,                # Custom claim: user role
        "exp": int(expire.timestamp()),  # Expiration time (Unix timestamp)
        "iat": int(datetime.utcnow().timestamp()),  # Issued at (Unix timestamp)
        "jti": str(uuid.uuid4()),    # JWT ID (unique token identifier)
    }

    # Encode JWT
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

    return {
        "access_token": encoded_jwt,
        "token_type": "bearer"
    }


def verify_token(token: str) -> Dict:
    """
    Verify JWT access token and return payload.

    Args:
        token: JWT token string

    Returns:
        Token payload dictionary with claims (sub, role, exp, iat, jti)

    Raises:
        HTTPException: 401 if token is invalid, expired, or malformed

    Example:
        >>> payload = verify_token(token)
        >>> user_id = payload["sub"]
        >>> role = payload["role"]
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and verify JWT
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])

        # Verify required claims are present
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return payload

    except JWTError as e:
        # Handle various JWT errors (expired, invalid signature, malformed)
        error_str = str(e).lower()

        if "expired" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        elif "signature" in error_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token signature",
                headers={"WWW-Authenticate": "Bearer"},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
