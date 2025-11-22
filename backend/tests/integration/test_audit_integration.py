"""
Integration tests for Audit API.

Tests audit log export and search endpoints with real database.
"""
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services.audit_service import audit_service


client = TestClient(app)


@pytest.fixture
async def admin_user(db: AsyncSession):
    """Create admin user for testing."""
    user = User(
        username="admin",
        email="admin@test.com",
        role="admin",
    )
    user.set_password("adminpass")
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def test_audit_logs(db: AsyncSession, admin_user: User):
    """Create test audit logs."""
    logs = []

    # Create 10 de-identification logs
    for i in range(10):
        log = await audit_service.log_deidentification(
            db=db,
            user=admin_user,
            job_id=f"job-{i}",
            note_id=f"note-{i}",
            entities_detected=10 + i,
            entities_removed=8 + i,
            method="removal",
        )
        logs.append(log)

    # Create 5 job creation logs
    for i in range(5):
        log = await audit_service.log_job_created(
            db=db,
            user=admin_user,
            job_id=f"job-{i}",
            total_notes=100,
            method="removal",
        )
        logs.append(log)

    return logs


@pytest.mark.asyncio
async def test_search_audit_logs_requires_auth(db: AsyncSession):
    """Test search endpoint requires authentication."""
    # Act
    response = client.get("/api/v1/audit/search")

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_search_audit_logs_requires_admin(db: AsyncSession):
    """Test search endpoint requires admin role."""
    # Arrange - create non-admin user
    user = User(username="clinician", email="clinician@test.com", role="clinician")
    user.set_password("pass123")
    db.add(user)
    await db.commit()

    # Login as clinician
    login_response = client.post("/api/v1/auth/login", json={
        "username": "clinician",
        "password": "pass123"
    })
    token = login_response.json()["access_token"]

    # Act - try to access audit logs
    response = client.get(
        "/api/v1/audit/search",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_search_audit_logs_success(db: AsyncSession, admin_user: User, test_audit_logs):
    """Test successful audit log search."""
    # Arrange - login as admin
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    token = login_response.json()["access_token"]

    # Act - search all logs
    response = client.get(
        "/api/v1/audit/search",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "total" in data
    assert len(data["logs"]) > 0


@pytest.mark.asyncio
async def test_search_audit_logs_filter_by_action(db: AsyncSession, admin_user: User, test_audit_logs):
    """Test filtering audit logs by action."""
    # Arrange
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    token = login_response.json()["access_token"]

    # Act - filter by DEIDENTIFY_NOTE action
    response = client.get(
        "/api/v1/audit/search?action=DEIDENTIFY_NOTE",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert all(log["action"] == "DEIDENTIFY_NOTE" for log in data["logs"])


@pytest.mark.asyncio
async def test_export_audit_logs_csv(db: AsyncSession, admin_user: User, test_audit_logs):
    """Test exporting audit logs as CSV."""
    # Arrange
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    token = login_response.json()["access_token"]

    start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()

    # Act
    response = client.get(
        f"/api/v1/audit/export?start_date={start_date}&end_date={end_date}&format=csv",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert "audit_logs_" in response.headers["content-disposition"]

    # Verify CSV format
    csv_data = response.text
    assert "id,timestamp,user_id,username,action" in csv_data


@pytest.mark.asyncio
async def test_export_audit_logs_json(db: AsyncSession, admin_user: User, test_audit_logs):
    """Test exporting audit logs as JSON."""
    # Arrange
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    token = login_response.json()["access_token"]

    start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()

    # Act
    response = client.get(
        f"/api/v1/audit/export?start_date={start_date}&end_date={end_date}&format=json",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"

    # Verify JSON format
    import json
    json_data = json.loads(response.text)
    assert isinstance(json_data, list)
    if len(json_data) > 0:
        assert "id" in json_data[0]
        assert "timestamp" in json_data[0]
        assert "action" in json_data[0]


@pytest.mark.asyncio
async def test_export_audit_logs_invalid_date_format(db: AsyncSession, admin_user: User):
    """Test export with invalid date format."""
    # Arrange
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    token = login_response.json()["access_token"]

    # Act - invalid date format
    response = client.get(
        "/api/v1/audit/export?start_date=invalid&end_date=2025-12-31T00:00:00",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_export_logs_audit_trail(db: AsyncSession, admin_user: User, test_audit_logs):
    """Test that export action is logged in audit trail."""
    # Arrange
    login_response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "adminpass"
    })
    token = login_response.json()["access_token"]

    start_date = (datetime.utcnow() - timedelta(days=1)).isoformat()
    end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()

    # Act - export logs
    response = client.get(
        f"/api/v1/audit/export?start_date={start_date}&end_date={end_date}&format=csv",
        headers={"Authorization": f"Bearer {token}"}
    )

    # Assert export succeeded
    assert response.status_code == 200

    # Verify export action was logged
    export_logs = await audit_service.search_audit_logs(db, {
        "action": "EXPORT_AUDIT_LOGS",
        "user_id": str(admin_user.id),
    })

    assert len(export_logs) > 0
    latest_export = export_logs[0]
    assert latest_export.details["format"] == "csv"
    assert "count" in latest_export.details
