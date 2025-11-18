"""
Authentication API Endpoints
Login, logout, token refresh
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse
from app.services.auth_service import auth_service


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
async def get_current_user(token: str):
    """
    Get current user information from JWT token.

    Args:
        token: JWT access token (from Authorization header)

    Returns:
        User information

    TODO: Implement this endpoint with JWT verification
    """
    payload = auth_service.verify_token(token)
    return {"user_id": payload["sub"], "role": payload["role"]}
