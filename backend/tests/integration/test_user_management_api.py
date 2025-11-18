"""
Integration tests for User Management APIs (Phase 2).

Tests full request/response cycles including:
- Authentication & authorization
- Database operations
- Audit logging
- Session management
- RBAC enforcement
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.audit_log import AuditLog
from app.models.user import User
from app.services.session_service import session_service


@pytest.fixture
def client():
    """Test client for API requests."""
    return TestClient(app)


@pytest.fixture
async def admin_user(db: AsyncSession) -> User:
    """Create admin user for testing."""
    user = User(
        username="admin_test",
        email="admin@test.com",
        role="admin",
        is_active=True,
        can_break_glass=True,
    )
    user.set_password("AdminPassword123!")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def clinician_user(db: AsyncSession) -> User:
    """Create clinician user for testing."""
    user = User(
        username="clinician_test",
        email="clinician@test.com",
        role="clinician",
        is_active=True,
        can_break_glass=True,
    )
    user.set_password("ClinicianPassword123!")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_token(client: TestClient, admin_user: User) -> str:
    """Get JWT token for admin user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_test", "password": "AdminPassword123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
async def clinician_token(client: TestClient, clinician_user: User) -> str:
    """Get JWT token for clinician user."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "clinician_test", "password": "ClinicianPassword123!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


class TestUserCRUDAPI:
    """Test User CRUD endpoints (Task 2.1)."""

    @pytest.mark.asyncio
    async def test_list_users_as_admin(
        self, client: TestClient, admin_token: str, admin_user: User, clinician_user: User
    ):
        """Test listing users with pagination (admin only)."""
        response = client.get(
            "/api/v1/users?page=1&page_size=10",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2  # admin + clinician

    @pytest.mark.asyncio
    async def test_list_users_as_clinician_forbidden(
        self, client: TestClient, clinician_token: str
    ):
        """Test listing users as non-admin returns 403."""
        response = client.get(
            "/api/v1/users", headers={"Authorization": f"Bearer {clinician_token}"}
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_create_user_as_admin(
        self, client: TestClient, admin_token: str, db: AsyncSession
    ):
        """Test creating a new user (admin only)."""
        response = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "newuser",
                "email": "newuser@test.com",
                "password": "NewUserPassword123!",
                "role": "researcher",
                "is_active": True,
                "can_break_glass": False,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@test.com"
        assert data["role"] == "researcher"

        # Verify user exists in database
        stmt = select(User).where(User.username == "newuser")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.username == "newuser"

    @pytest.mark.asyncio
    async def test_create_duplicate_username_fails(
        self, client: TestClient, admin_token: str, admin_user: User
    ):
        """Test creating user with duplicate username fails."""
        response = client.post(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "username": "admin_test",  # Duplicate
                "email": "different@test.com",
                "password": "Password123!",
                "role": "clinician",
            },
        )
        assert response.status_code == 400
        assert "username already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_user_as_admin(
        self, client: TestClient, admin_token: str, clinician_user: User, db: AsyncSession
    ):
        """Test updating user details (admin only)."""
        response = client.put(
            f"/api/v1/users/{clinician_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"email": "updated_clinician@test.com", "role": "researcher"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "updated_clinician@test.com"
        assert data["role"] == "researcher"

        # Verify in database
        await db.refresh(clinician_user)
        assert clinician_user.email == "updated_clinician@test.com"
        assert clinician_user.role == "researcher"

    @pytest.mark.asyncio
    async def test_delete_user_soft_delete(
        self, client: TestClient, admin_token: str, clinician_user: User, db: AsyncSession
    ):
        """Test deleting user (soft delete)."""
        response = client.delete(
            f"/api/v1/users/{clinician_user.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 204

        # Verify user is soft-deleted (is_active = False)
        await db.refresh(clinician_user)
        assert clinician_user.is_active is False


class TestUserSearchAPI:
    """Test User Search endpoint (Task 2.5)."""

    @pytest.mark.asyncio
    async def test_search_users_by_username(
        self, client: TestClient, admin_token: str, admin_user: User
    ):
        """Test searching users by username."""
        response = client.get(
            "/api/v1/users/search?query=admin",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        usernames = [user["username"] for user in data["items"]]
        assert "admin_test" in usernames

    @pytest.mark.asyncio
    async def test_search_users_by_email(
        self, client: TestClient, admin_token: str, clinician_user: User
    ):
        """Test searching users by email."""
        response = client.get(
            "/api/v1/users/search?query=clinician@test.com",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        emails = [user["email"] for user in data["items"]]
        assert "clinician@test.com" in emails

    @pytest.mark.asyncio
    async def test_search_users_min_length_validation(
        self, client: TestClient, admin_token: str
    ):
        """Test search requires minimum 2 characters."""
        response = client.get(
            "/api/v1/users/search?query=a",  # Too short
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 422  # Validation error


class TestProfileManagementAPI:
    """Test Profile Management endpoints (Tasks 2.4+2.7)."""

    @pytest.mark.asyncio
    async def test_get_own_profile(
        self, client: TestClient, clinician_token: str, clinician_user: User
    ):
        """Test getting current user's profile."""
        response = client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {clinician_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "clinician_test"
        assert data["email"] == "clinician@test.com"
        assert "password_hash" not in data  # Security: never expose password

    @pytest.mark.asyncio
    async def test_update_own_profile(
        self, client: TestClient, clinician_token: str, db: AsyncSession, clinician_user: User
    ):
        """Test updating own profile (email only)."""
        response = client.put(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {clinician_token}"},
            json={"email": "new_email@test.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "new_email@test.com"

        # Verify in database
        await db.refresh(clinician_user)
        assert clinician_user.email == "new_email@test.com"

    @pytest.mark.asyncio
    async def test_change_password_with_session_invalidation(
        self, client: TestClient, clinician_token: str, db: AsyncSession, clinician_user: User
    ):
        """Test changing password invalidates all sessions."""
        # Create a session for the user
        from app.models.session import Session
        from datetime import datetime, timedelta

        test_session = Session(
            session_id="test-session-123",
            user_id=str(clinician_user.id),
            token_jti="test-jti-456",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=8),
            ip_address="127.0.0.1",
            user_agent="test-agent",
        )
        await session_service.create_session(test_session)

        # Change password
        response = client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {clinician_token}"},
            json={
                "current_password": "ClinicianPassword123!",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 204

        # Verify password changed
        await db.refresh(clinician_user)
        assert clinician_user.verify_password("NewPassword123!")

        # Verify session invalidated
        sessions = await session_service.list_user_sessions(user_id=str(clinician_user.id))
        assert len(sessions) == 0  # All sessions invalidated

    @pytest.mark.asyncio
    async def test_change_password_incorrect_current(
        self, client: TestClient, clinician_token: str
    ):
        """Test changing password with incorrect current password fails."""
        response = client.post(
            "/api/v1/users/me/change-password",
            headers={"Authorization": f"Bearer {clinician_token}"},
            json={
                "current_password": "WrongPassword!",
                "new_password": "NewPassword123!",
            },
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()


class TestSessionManagementAPI:
    """Test Session Management endpoints (Task 2.8)."""

    @pytest.mark.asyncio
    async def test_list_active_sessions(
        self, client: TestClient, clinician_token: str, clinician_user: User
    ):
        """Test listing active sessions for current user."""
        # Create test sessions
        from app.models.session import Session
        from datetime import datetime, timedelta

        session1 = Session(
            session_id="session-1",
            user_id=str(clinician_user.id),
            token_jti="jti-1",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=8),
            ip_address="192.168.1.1",
            user_agent="Browser 1",
        )
        session2 = Session(
            session_id="session-2",
            user_id=str(clinician_user.id),
            token_jti="jti-2",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=8),
            ip_address="192.168.1.2",
            user_agent="Browser 2",
        )
        await session_service.create_session(session1)
        await session_service.create_session(session2)

        response = client.get(
            "/api/v1/sessions/me", headers={"Authorization": f"Bearer {clinician_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["sessions"]) >= 2

    @pytest.mark.asyncio
    async def test_revoke_specific_session(
        self, client: TestClient, clinician_token: str, clinician_user: User
    ):
        """Test revoking a specific session."""
        # Create test session
        from app.models.session import Session
        from datetime import datetime, timedelta

        test_session = Session(
            session_id="revoke-test-session",
            user_id=str(clinician_user.id),
            token_jti="revoke-jti",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=8),
            ip_address="192.168.1.1",
            user_agent="Browser",
        )
        await session_service.create_session(test_session)

        # Revoke session
        response = client.delete(
            "/api/v1/sessions/revoke-test-session",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )
        assert response.status_code == 204

        # Verify session deleted
        session = await session_service.get_session("revoke-test-session")
        assert session is None

    @pytest.mark.asyncio
    async def test_revoke_all_sessions_except_current(
        self, client: TestClient, clinician_token: str, clinician_user: User
    ):
        """Test revoking all sessions except current."""
        # Create multiple test sessions
        from app.models.session import Session
        from datetime import datetime, timedelta

        for i in range(3):
            session = Session(
                session_id=f"session-{i}",
                user_id=str(clinician_user.id),
                token_jti=f"jti-{i}",
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=8),
                ip_address=f"192.168.1.{i}",
                user_agent=f"Browser {i}",
            )
            await session_service.create_session(session)

        # Revoke all sessions
        response = client.delete(
            "/api/v1/sessions/me/all", headers={"Authorization": f"Bearer {clinician_token}"}
        )
        assert response.status_code == 204


class TestActivityLogsAPI:
    """Test Activity Logs endpoint (Task 2.12)."""

    @pytest.mark.asyncio
    async def test_view_own_activity_logs(
        self, client: TestClient, clinician_token: str, clinician_user: User, db: AsyncSession
    ):
        """Test users can view their own activity logs."""
        # Create test audit log
        from app.services.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user=clinician_user,
            action="TEST_ACTION",
            resource_type="test",
            details={"test": "data"},
        )

        response = client.get(
            f"/api/v1/users/{clinician_user.id}/activity",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(log["action"] == "TEST_ACTION" for log in data["items"])

    @pytest.mark.asyncio
    async def test_admin_can_view_any_user_activity(
        self, client: TestClient, admin_token: str, clinician_user: User, db: AsyncSession
    ):
        """Test admins can view any user's activity logs."""
        # Create test audit log for clinician
        from app.services.audit_service import AuditService

        audit_service = AuditService()
        await audit_service.log_action(
            db=db,
            user=clinician_user,
            action="CLINICIAN_ACTION",
            resource_type="test",
            details={"test": "data"},
        )

        # Admin views clinician's logs
        response = client.get(
            f"/api/v1/users/{clinician_user.id}/activity",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1

    @pytest.mark.asyncio
    async def test_non_admin_cannot_view_other_user_activity(
        self, client: TestClient, clinician_token: str, admin_user: User
    ):
        """Test non-admins cannot view other users' activity logs."""
        response = client.get(
            f"/api/v1/users/{admin_user.id}/activity",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )
        assert response.status_code == 403


class TestBreakGlassWorkflow:
    """Test Break-Glass emergency access (Task 2.3)."""

    @pytest.mark.asyncio
    async def test_request_break_glass_access(
        self, client: TestClient, clinician_token: str, db: AsyncSession
    ):
        """Test requesting break-glass emergency access."""
        response = client.post(
            "/api/v1/break-glass/access",
            headers={"Authorization": f"Bearer {clinician_token}"},
            json={
                "patient_id": "patient-123",
                "resource_type": "patient",
                "justification": "Emergency situation requiring immediate access to patient records",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["access_granted"] is True
        assert data["patient_id"] == "patient-123"
        assert "expires_at" in data

        # Verify audit log created
        stmt = select(AuditLog).where(AuditLog.action == "BREAK_GLASS_ACCESS")
        result = await db.execute(stmt)
        logs = result.scalars().all()
        assert len(logs) >= 1

    @pytest.mark.asyncio
    async def test_break_glass_without_permission_fails(
        self, client: TestClient, db: AsyncSession
    ):
        """Test break-glass fails without permission."""
        # Create user without can_break_glass permission
        no_permission_user = User(
            username="no_permission",
            email="no_permission@test.com",
            role="researcher",
            is_active=True,
            can_break_glass=False,  # No permission
        )
        no_permission_user.set_password("Password123!")
        db.add(no_permission_user)
        await db.commit()

        # Login
        client_test = TestClient(app)
        login_response = client_test.post(
            "/api/v1/auth/login",
            json={"username": "no_permission", "password": "Password123!"},
        )
        token = login_response.json()["access_token"]

        # Attempt break-glass
        response = client_test.post(
            "/api/v1/break-glass/access",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "patient_id": "patient-123",
                "resource_type": "patient",
                "justification": "Emergency situation",
            },
        )
        assert response.status_code == 403


class TestRoleManagementAPI:
    """Test Role Management endpoints (Task 2.2)."""

    @pytest.mark.asyncio
    async def test_list_roles(self, client: TestClient, admin_token: str):
        """Test listing available roles."""
        response = client.get(
            "/api/v1/roles", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["roles"]) == 3  # clinician, researcher, admin
        role_names = [role["role"] for role in data["roles"]]
        assert "clinician" in role_names
        assert "researcher" in role_names
        assert "admin" in role_names

    @pytest.mark.asyncio
    async def test_get_role_details(self, client: TestClient, admin_token: str):
        """Test getting details for a specific role."""
        response = client.get(
            "/api/v1/roles/clinician", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "clinician"
        assert "permissions" in data
        assert len(data["permissions"]) > 0

    @pytest.mark.asyncio
    async def test_get_user_permissions(
        self, client: TestClient, clinician_token: str, clinician_user: User
    ):
        """Test getting permissions for a specific user."""
        response = client.get(
            f"/api/v1/roles/users/{clinician_user.id}/permissions",
            headers={"Authorization": f"Bearer {clinician_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == str(clinician_user.id)
        assert data["role"] == "clinician"
        assert "permissions" in data
