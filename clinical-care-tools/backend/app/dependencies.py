"""
FastAPI Dependencies

Common dependencies for dependency injection across the application.
Includes database sessions, authentication, authorization, and rate limiting.
"""

from typing import AsyncGenerator, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session

# Security scheme for JWT Bearer tokens
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.

    Yields:
        AsyncSession: Database session for the request.
    """
    async for session in get_session():
        yield session


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get the current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header.
        db: Database session.

    Returns:
        dict: User information from the JWT token.

    Raises:
        HTTPException: 401 if token is invalid or missing.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # NOTE: Fetch user from database
        # from app.models.user import User
        # user = await db.get(User, user_id)
        # if not user or not user.is_active:
        #     raise HTTPException(status_code=401, detail="User not found or inactive")

        # For now, return the payload
        return {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "username": payload.get("username")
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Get current active user.

    Args:
        current_user: The current authenticated user.

    Returns:
        dict: The user if active.

    Raises:
        HTTPException: 400 if user is inactive.
    """
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(allowed_roles: list[str]):
    """
    Create a dependency that checks if user has required role.

    Args:
        allowed_roles: List of roles that are allowed.

    Returns:
        Dependency function that validates user role.

    Example:
        @app.get("/admin", dependencies=[Depends(require_role(["admin"]))])
        async def admin_endpoint():
            return {"message": "Admin only"}
    """
    async def role_checker(
        current_user: dict = Depends(get_current_user)
    ) -> dict:
        """
        Check if user has required role.

        Args:
            current_user: The current authenticated user.

        Returns:
            dict: The user if they have required role.

        Raises:
            HTTPException: 403 if user doesn't have required role.
        """
        user_role = current_user.get("role", "user")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not authorized. Required roles: {allowed_roles}"
            )
        return current_user

    return role_checker


def require_admin():
    """
    Dependency that requires admin role.

    Returns:
        Dependency function that validates admin role.
    """
    return require_role(["admin"])


def require_clinician():
    """
    Dependency that requires clinician or admin role.

    Returns:
        Dependency function that validates clinician role.
    """
    return require_role(["clinician", "admin"])


def require_researcher():
    """
    Dependency that requires researcher, clinician, or admin role.

    Returns:
        Dependency function that validates researcher role.
    """
    return require_role(["researcher", "clinician", "admin"])


class RateLimiter:
    """
    Rate limiting dependency for protecting endpoints.

    Attributes:
        requests_per_minute: Maximum requests allowed per minute.
    """

    def __init__(self, requests_per_minute: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute.
        """
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def __call__(self, request: Request) -> None:
        """
        Check if request exceeds rate limit.

        Args:
            request: The incoming request.

        Raises:
            HTTPException: 429 if rate limit exceeded.
        """
        if not settings.RATE_LIMIT_ENABLED:
            return

        # Get client identifier (IP address or user ID)
        client_id = request.client.host if request.client else "unknown"

        # NOTE: Implement actual rate limiting with Redis
        # For now, this is a placeholder
        # from app.cache import redis_client
        # key = f"rate_limit:{client_id}"
        # count = await redis_client.incr(key)
        # if count == 1:
        #     await redis_client.expire(key, 60)
        # if count > self.requests_per_minute:
        #     raise HTTPException(
        #         status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        #         detail="Rate limit exceeded"
        #     )


# Create rate limiter instances
rate_limit_default = RateLimiter(requests_per_minute=60)
rate_limit_strict = RateLimiter(requests_per_minute=10)
rate_limit_search = RateLimiter(requests_per_minute=30)


async def get_request_id(request: Request) -> str:
    """
    Get or generate request ID for tracing.

    Args:
        request: The incoming request.

    Returns:
        str: Request ID.
    """
    # Check if request ID exists in headers
    request_id = request.headers.get("X-Request-ID")

    if not request_id:
        # Generate new request ID
        import uuid
        request_id = str(uuid.uuid4())

    # Store in request state for access in other places
    request.state.request_id = request_id
    return request_id


async def verify_api_key(
    api_key: Optional[str] = None
) -> bool:
    """
    Verify API key for service-to-service authentication.

    Args:
        api_key: API key from header or query parameter.

    Returns:
        bool: True if API key is valid.

    Raises:
        HTTPException: 401 if API key is invalid.
    """
    # NOTE: Implement API key verification
    # This would check against a database or environment variable
    # For now, this is a placeholder

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )

    # Example validation (replace with actual logic)
    valid_keys = ["test-api-key"]  # Should come from secure storage
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )

    return True


async def check_feature_flag(feature: str) -> bool:
    """
    Check if a feature flag is enabled.

    Args:
        feature: Name of the feature to check.

    Returns:
        bool: True if feature is enabled.
    """
    feature_flags = {
        "patient_search": settings.FEATURE_PATIENT_SEARCH,
        "timeline_view": settings.FEATURE_TIMELINE_VIEW,
        "meta_annotations": settings.FEATURE_META_ANNOTATIONS,
        "fhir_export": settings.FEATURE_FHIR_EXPORT,
        "bulk_processing": settings.FEATURE_BULK_PROCESSING,
    }

    return feature_flags.get(feature, False)


def require_feature(feature: str):
    """
    Create a dependency that checks if a feature is enabled.

    Args:
        feature: Name of the feature to check.

    Returns:
        Dependency function that validates feature availability.
    """
    async def feature_checker() -> None:
        """
        Check if feature is enabled.

        Raises:
            HTTPException: 503 if feature is not enabled.
        """
        if not await check_feature_flag(feature):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Feature '{feature}' is not enabled"
            )

    return feature_checker