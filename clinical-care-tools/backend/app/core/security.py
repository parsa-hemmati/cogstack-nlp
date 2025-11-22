"""
Security utilities for authentication and authorization.

Handles password hashing, JWT token operations, and security validation.
HIPAA Compliance: Uses industry-standard bcrypt with cost factor 12.
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
import secrets
import hashlib
import re

from app.core.config import settings


# Password hashing configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.PASSWORD_BCRYPT_ROUNDS
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string

    Security Note: Uses bcrypt with cost factor 12 for HIPAA compliance.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_strength(password: str) -> tuple[bool, list[str]]:
    """
    Validate password meets security requirements.

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, list_of_errors)

    Requirements:
        - Minimum 12 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one number
        - At least one special character
    """
    errors = []

    if len(password) < settings.PASSWORD_MIN_LENGTH:
        errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")

    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")

    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")

    if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r"\d", password):
        errors.append("Password must contain at least one number")

    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
        errors.append("Password must contain at least one special character")

    return (len(errors) == 0, errors)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + settings.jwt_access_token_expire

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        user_id: User ID to encode in token

    Returns:
        Encoded JWT refresh token string
    """
    expire = datetime.now(timezone.utc) + settings.jwt_refresh_token_expire

    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16)  # JWT ID for revocation tracking
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str, expected_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.

    Args:
        token: JWT token to verify
        expected_type: Expected token type ('access' or 'refresh')

    Returns:
        Decoded token payload if valid, None otherwise

    Security Note: Validates expiration, signature, and token type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Validate token type
        if payload.get("type") != expected_type:
            return None

        return payload

    except JWTError:
        return None


def hash_session_identifier(ip_address: str, user_agent: str) -> str:
    """
    Create a hash of session identifiers for session binding.

    Args:
        ip_address: Client IP address
        user_agent: Client User-Agent string

    Returns:
        SHA-256 hash of combined identifiers

    Security Note: Used for session hijacking detection.
    """
    combined = f"{ip_address}:{user_agent}"
    return hashlib.sha256(combined.encode()).hexdigest()


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token.

    Args:
        length: Token length in bytes

    Returns:
        URL-safe token string
    """
    return secrets.token_urlsafe(length)


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data for logging.

    Args:
        data: Sensitive data to mask
        visible_chars: Number of characters to leave visible

    Returns:
        Masked string

    Example:
        "secret123" -> "secr****"
    """
    if not data or len(data) <= visible_chars:
        return "****"

    return data[:visible_chars] + "*" * (len(data) - visible_chars)