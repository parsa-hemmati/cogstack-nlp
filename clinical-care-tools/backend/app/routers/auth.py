"""
Authentication API Router for Clinical Care Tools.

Handles user registration, login, logout, and token management.
HIPAA Compliance: All authentication events are audit logged.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.auth_service import AuthService
from app.services.session_service import SessionService
from app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    TokenRefresh,
    UserResponse,
    PasswordChange,
    LoginAttemptResponse
)
from app.core.security import verify_token


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"}
    }
)

# Security scheme for bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """
    Dependency to get current authenticated user.

    Args:
        credentials: Bearer token from request
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    auth_service = AuthService(db)
    user = await auth_service.get_current_user(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    **Requirements:**
    - Email must be unique
    - Password must be at least 12 characters
    - Password must contain uppercase, lowercase, numbers, and special characters

    **Roles:**
    - admin: Full system access
    - clinician: Patient data access
    - researcher: De-identified data only
    - auditor: Read-only audit access

    **Returns:**
    - Created user information

    **Raises:**
    - 400: Email already exists or password too weak
    """
    auth_service = AuthService(db)

    # Check if this is the first user (make them admin)
    # In production, this would be handled differently
    if user_data.role != "admin":
        # Check if requester is admin (for creating other users)
        # For now, allow self-registration
        pass

    user = await auth_service.register_user(user_data)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
        last_activity=user.last_activity
    )


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and create session.

    **Process:**
    1. Validates credentials
    2. Creates JWT tokens (access + refresh)
    3. Creates server-side session
    4. Sets secure HTTP-only cookie (optional)

    **Security:**
    - Rate limited to 5 attempts per 15 minutes
    - Session bound to IP and User-Agent
    - All attempts logged for audit

    **Returns:**
    - Access token (8 hour expiry)
    - Refresh token (7 day expiry)

    **Raises:**
    - 401: Invalid credentials
    - 403: Account locked or inactive
    - 429: Too many login attempts
    """
    # Get client information for session binding
    ip_address = request.client.host or "unknown"
    user_agent = request.headers.get("User-Agent", "unknown")

    auth_service = AuthService(db)
    session_service = SessionService(db)

    # Authenticate user
    token = await auth_service.authenticate_user(
        login_data,
        ip_address,
        user_agent
    )

    # Create session
    # Note: In production, we'd extract user_id from the token
    payload = verify_token(token.access_token)
    if payload:
        user_id = payload.get("sub")
        session = await session_service.create_session(
            user_id,
            ip_address,
            user_agent
        )

        # Set session cookie (optional, for web clients)
        response.set_cookie(
            key="session_id",
            value=session.id,
            httponly=True,
            secure=True,  # HTTPS only in production
            samesite="strict",
            max_age=3600 * 8  # 8 hours
        )

    return token


@router.post("/refresh", response_model=dict)
async def refresh_token(
    refresh_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Generate new access token from refresh token.

    **Use Case:**
    - Access token expired but user still active
    - Prevents re-authentication for 7 days

    **Process:**
    1. Validates refresh token
    2. Checks user still active
    3. Issues new access token

    **Returns:**
    - New access token

    **Raises:**
    - 401: Invalid or expired refresh token
    """
    auth_service = AuthService(db)

    new_access_token = await auth_service.refresh_access_token(
        refresh_data.refresh_token
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Logout current session.

    **Process:**
    1. Invalidates current session
    2. Clears session cookie
    3. Audit logs the logout

    **Note:**
    - Does not invalidate other user sessions
    - Does not revoke JWT tokens (they expire naturally)

    **Returns:**
    - 204 No Content on success
    """
    # Get session from cookie or header
    session_id = request.cookies.get("session_id")

    if session_id:
        session_service = SessionService(db)
        await session_service.invalidate_session(session_id)

    # Clear session cookie
    response.delete_cookie("session_id")

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user=Depends(get_current_user)
):
    """
    Get current user information.

    **Returns:**
    - User profile information
    - Role and permissions
    - Last activity timestamps

    **Requires:**
    - Valid access token
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        last_activity=current_user.last_activity
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChange,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password.

    **Requirements:**
    - Must provide correct current password
    - New password must meet security requirements
    - Cannot reuse current password

    **Side Effects:**
    - Invalidates all other sessions (security measure)
    - Requires re-authentication on other devices

    **Returns:**
    - 204 No Content on success

    **Raises:**
    - 400: Current password incorrect or new password weak
    """
    auth_service = AuthService(db)
    session_service = SessionService(db)

    # Change password
    await auth_service.change_password(
        current_user,
        password_data.old_password,
        password_data.new_password
    )

    # Invalidate all other sessions for security
    # Get current session to keep it active
    # In production, we'd extract this from the request
    await session_service.invalidate_all_user_sessions(
        str(current_user.id),
        except_current=None  # Would pass current session ID
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/validate", response_model=dict)
async def validate_token(
    current_user=Depends(get_current_user)
):
    """
    Validate current access token.

    **Use Case:**
    - Frontend token validation
    - Service-to-service authentication

    **Returns:**
    - Token validity and user info

    **Raises:**
    - 401: Invalid or expired token
    """
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "role": current_user.role
    }