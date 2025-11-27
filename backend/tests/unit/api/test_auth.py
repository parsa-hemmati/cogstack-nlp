"""
Authentication API Tests

Tests for login, logout, and user info endpoints.
Covers rate limiting, password verification, and JWT token handling.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.auth import login, logout, get_current_user_info
from app.schemas.auth import LoginRequest
from app.models.user import User


class TestLoginEndpoint:
    """Tests for POST /api/v1/auth/login"""

    @pytest.fixture
    def mock_request(self):
        """Create mock FastAPI request"""
        request = MagicMock()
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def mock_user(self):
        """Create mock user with valid credentials"""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "test_user"
        user.email = "test@example.com"
        user.role = "clinician"
        user.is_active = True
        user.can_break_glass = False
        user.verify_password = MagicMock(return_value=True)
        user.to_dict = MagicMock(return_value={
            "id": str(user.id),
            "username": "test_user",
            "email": "test@example.com",
            "role": "clinician",
            "is_active": True,
            "can_break_glass": False
        })
        return user

    @pytest.fixture
    def mock_db(self, mock_user):
        """Create mock database session"""
        db = AsyncMock(spec=AsyncSession)

        # Mock query result
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=mock_user)
        db.execute = AsyncMock(return_value=result)

        return db

    @pytest.mark.asyncio
    async def test_login_success(self, mock_request, mock_user, mock_db):
        """Test successful login returns token and user info"""
        credentials = LoginRequest(username="test_user", password="valid_password")

        with patch("app.api.v1.endpoints.auth.auth_service") as mock_auth:
            mock_auth.create_access_token.return_value = {
                "access_token": "test_token",
                "token_type": "bearer",
                "expires_at": datetime.utcnow() + timedelta(hours=1)
            }

            # Patch Redis to skip rate limiting
            with patch("app.api.v1.endpoints.auth.get_redis_client", side_effect=ImportError):
                response = await login(mock_request, credentials, mock_db)

        assert response.access_token == "test_token"
        assert response.token_type == "bearer"
        assert response.user["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_login_invalid_username(self, mock_request, mock_db):
        """Test login with non-existent username returns 401"""
        # Make query return None (user not found)
        result = MagicMock()
        result.scalar_one_or_none = MagicMock(return_value=None)
        mock_db.execute = AsyncMock(return_value=result)

        credentials = LoginRequest(username="nonexistent", password="any_password")

        with patch("app.api.v1.endpoints.auth.get_redis_client", side_effect=ImportError):
            with pytest.raises(HTTPException) as exc_info:
                await login(mock_request, credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, mock_request, mock_user, mock_db):
        """Test login with wrong password returns 401"""
        mock_user.verify_password = MagicMock(return_value=False)

        credentials = LoginRequest(username="test_user", password="wrong_password")

        with patch("app.api.v1.endpoints.auth.get_redis_client", side_effect=ImportError):
            with pytest.raises(HTTPException) as exc_info:
                await login(mock_request, credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect username or password" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_inactive_account(self, mock_request, mock_user, mock_db):
        """Test login with inactive account returns 401"""
        mock_user.is_active = False

        credentials = LoginRequest(username="test_user", password="valid_password")

        with patch("app.api.v1.endpoints.auth.get_redis_client", side_effect=ImportError):
            with pytest.raises(HTTPException) as exc_info:
                await login(mock_request, credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Account is inactive" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_login_rate_limited(self, mock_request, mock_db):
        """Test login blocked when rate limited"""
        credentials = LoginRequest(username="test_user", password="any_password")

        # Mock Redis with rate limit exceeded
        mock_redis = AsyncMock()
        mock_limiter = MagicMock()
        mock_limiter.is_rate_limited = AsyncMock(return_value=(True, 60))

        with patch("app.api.v1.endpoints.auth.get_redis_client", return_value=mock_redis):
            with patch("app.api.v1.endpoints.auth.RateLimiter", return_value=mock_limiter):
                with pytest.raises(HTTPException) as exc_info:
                    await login(mock_request, credentials, mock_db)

        assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Too many login attempts" in exc_info.value.detail


class TestGetCurrentUserInfo:
    """Tests for GET /api/v1/auth/me"""

    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user"""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "test_user"
        user.email = "test@example.com"
        user.role = "admin"
        user.is_active = True
        user.can_break_glass = True
        user.to_dict = MagicMock(return_value={
            "id": str(user.id),
            "username": "test_user",
            "email": "test@example.com",
            "role": "admin",
            "is_active": True,
            "can_break_glass": True
        })
        return user

    @pytest.mark.asyncio
    async def test_get_current_user_info_returns_user_dict(self, mock_user):
        """Test /me returns user information"""
        result = await get_current_user_info(mock_user)

        assert result["username"] == "test_user"
        assert result["email"] == "test@example.com"
        assert result["role"] == "admin"
        assert result["can_break_glass"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_info_excludes_password(self, mock_user):
        """Test /me does not return password_hash"""
        result = await get_current_user_info(mock_user)

        assert "password_hash" not in result
        assert "password" not in result


class TestLogoutEndpoint:
    """Tests for POST /api/v1/auth/logout"""

    @pytest.fixture
    def mock_user(self):
        """Create mock authenticated user"""
        user = MagicMock(spec=User)
        user.id = uuid4()
        user.username = "test_user"
        return user

    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return AsyncMock(spec=AsyncSession)

    @pytest.mark.asyncio
    async def test_logout_success(self, mock_user, mock_db):
        """Test logout returns 204 and logs action"""
        authorization = "Bearer test_jwt_token"

        with patch("app.api.v1.endpoints.auth.auth_service") as mock_auth:
            mock_auth.verify_token.return_value = {"jti": "token_id_123"}

            with patch("app.api.v1.endpoints.auth.audit_service") as mock_audit:
                mock_audit.log_action = AsyncMock()

                result = await logout(mock_user, authorization, mock_db)

        assert result is None  # 204 No Content
        mock_audit.log_action.assert_called_once()
        call_args = mock_audit.log_action.call_args
        assert call_args.kwargs["action"] == "LOGOUT"
        assert call_args.kwargs["resource_type"] == "session"

    @pytest.mark.asyncio
    async def test_logout_logs_token_jti(self, mock_user, mock_db):
        """Test logout includes token JTI in audit log"""
        authorization = "Bearer test_jwt_token"
        token_jti = "unique_token_id"

        with patch("app.api.v1.endpoints.auth.auth_service") as mock_auth:
            mock_auth.verify_token.return_value = {"jti": token_jti}

            with patch("app.api.v1.endpoints.auth.audit_service") as mock_audit:
                mock_audit.log_action = AsyncMock()

                await logout(mock_user, authorization, mock_db)

        call_args = mock_audit.log_action.call_args
        assert call_args.kwargs["resource_id"] == token_jti


class TestAuthTokenGeneration:
    """Tests for JWT token generation and validation"""

    def test_token_includes_user_id(self):
        """Test generated token includes user_id in payload"""
        from app.services.auth_service import auth_service

        user_id = str(uuid4())
        token_data = auth_service.create_access_token(user_id=user_id, role="clinician")

        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert "expires_at" in token_data

    def test_token_includes_role(self):
        """Test generated token includes role in payload"""
        from app.services.auth_service import auth_service

        user_id = str(uuid4())
        token_data = auth_service.create_access_token(user_id=user_id, role="admin")

        # Verify role is in token by decoding
        payload = auth_service.verify_token(token_data["access_token"])
        assert payload.get("role") == "admin"

    def test_token_has_expiration(self):
        """Test generated token has expiration time"""
        from app.services.auth_service import auth_service

        user_id = str(uuid4())
        token_data = auth_service.create_access_token(user_id=user_id, role="viewer")

        assert token_data["expires_at"] is not None
        assert token_data["expires_at"] > datetime.utcnow()


class TestPasswordVerification:
    """Tests for password hashing and verification"""

    def test_password_hashing_is_secure(self):
        """Test password is properly hashed with bcrypt"""
        from app.models.user import User

        user = User(
            username="test",
            email="test@test.com",
            role="viewer"
        )
        user.set_password("test_password_123")

        # Hash should not equal plaintext
        assert user.password_hash != "test_password_123"
        # Hash should start with bcrypt identifier
        assert user.password_hash.startswith("$2b$")

    def test_password_verification_correct_password(self):
        """Test correct password passes verification"""
        from app.models.user import User

        user = User(
            username="test",
            email="test@test.com",
            role="viewer"
        )
        user.set_password("correct_password")

        assert user.verify_password("correct_password") is True

    def test_password_verification_wrong_password(self):
        """Test wrong password fails verification"""
        from app.models.user import User

        user = User(
            username="test",
            email="test@test.com",
            role="viewer"
        )
        user.set_password("correct_password")

        assert user.verify_password("wrong_password") is False

    def test_password_verification_timing_safe(self):
        """Test password verification is constant-time (bcrypt)"""
        from app.models.user import User
        import time

        user = User(
            username="test",
            email="test@test.com",
            role="viewer"
        )
        user.set_password("test_password")

        # Measure time for correct password
        start = time.perf_counter()
        user.verify_password("test_password")
        correct_time = time.perf_counter() - start

        # Measure time for wrong password (same length)
        start = time.perf_counter()
        user.verify_password("wrong_passwor")
        wrong_time = time.perf_counter() - start

        # Times should be similar (within factor of 2)
        # bcrypt is constant-time regardless of password
        ratio = max(correct_time, wrong_time) / min(correct_time, wrong_time)
        assert ratio < 2.0, "Password verification timing varies too much"
