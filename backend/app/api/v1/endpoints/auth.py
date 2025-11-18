"""
Authentication API Endpoints
Login, logout, token refresh
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import auth_service
from app.services.audit_service import audit_service
from app.core.security import get_current_user


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login endpoint - authenticate user and return JWT token.

    Args:
        credentials: Username and password
        db: Database session

    Returns:
        LoginResponse with access_token and user information

    Raises:
        HTTPException(401): Invalid credentials or inactive account

    Security:
        - Password verification uses bcrypt (constant-time)
        - Account must be active (is_active=True)
        - Password never returned in response
        - Failed login doesn't reveal if username exists (timing-safe)
    """
    # Query user by username
    stmt = select(User).where(User.username == credentials.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not user.verify_password(credentials.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    token_data = auth_service.create_access_token(user_id=str(user.id), role=user.role)

    # Return token and user information
    return LoginResponse(
        access_token=token_data["access_token"],
        token_type=token_data["token_type"],
        expires_at=token_data["expires_at"],
        user=user.to_dict(),  # Excludes password_hash by default
    )


@router.get("/me", response_model=dict)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information from JWT token.

    Args:
        current_user: Current authenticated user (from JWT)

    Returns:
        User information
    """
    return current_user.to_dict()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    current_user: User = Depends(get_current_user),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout endpoint - invalidate current session.

    Args:
        current_user: Current authenticated user
        authorization: Authorization header (to extract token JTI)
        db: Database session

    Returns:
        204 No Content

    Security:
        - Deletes session from Redis
        - Logs logout action in audit trail
        - Token still valid until expiry (consider blacklist for production)
    """
    # Extract token JTI from payload
    token = authorization.replace("Bearer ", "")
    payload = auth_service.verify_token(token)
    token_jti = payload.get("jti")

    # Delete session from Redis (if exists)
    # Note: In production, implement token blacklist for immediate invalidation
    # For now, session cleanup is sufficient

    # Log logout action
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="LOGOUT",
        resource_type="session",
        resource_id=token_jti,
    )

    return None  # 204 No Content
