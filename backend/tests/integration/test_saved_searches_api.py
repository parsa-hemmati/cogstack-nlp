"""
Integration tests for Saved Searches API endpoints.

Tests POST /api/v1/search/saved (create), GET /api/v1/search/saved (list),
DELETE /api/v1/search/saved/{id} (delete), and authentication/authorization.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.saved_search import SavedSearch
from app.models.user import User


@pytest.mark.asyncio
async def test_create_saved_search_success(
    async_client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """Test POST /api/v1/search/saved creates saved search successfully."""
    # Arrange
    payload = {
        "name": "Diabetes Patients",
        "description": "Search for diabetes patients in cardiology",
        "query": "diabetes mellitus",
        "filters": {
            "document_types": ["rtf"],
            "departments": ["Cardiology"]
        },
        "is_shared": False
    }

    # Act
    response = await async_client.post(
        "/api/v1/search/saved",
        json=payload,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert data["query"] == payload["query"]
    assert data["filters"] == payload["filters"]
    assert data["is_shared"] == payload["is_shared"]
    assert data["user_id"] == str(test_user.id)
    assert "id" in data
    assert data["execution_count"] == 0
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_saved_search_duplicate_name_fails(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User
):
    """Test creating saved search with duplicate name fails."""
    # Arrange: Create existing saved search
    existing_search = SavedSearch(
        user_id=test_user.id,
        name="Diabetes Patients",
        query="diabetes",
        filters={}
    )
    db_session.add(existing_search)
    await db_session.commit()

    # Attempt to create duplicate
    payload = {
        "name": "Diabetes Patients",  # Same name
        "query": "diabetes mellitus type 2",
        "filters": {}
    }

    # Act
    response = await async_client.post(
        "/api/v1/search/saved",
        json=payload,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 409, f"Expected 409, got {response.status_code}: {response.text}"
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_create_saved_search_requires_authentication(
    async_client: AsyncClient
):
    """Test creating saved search requires valid JWT token."""
    # Arrange
    payload = {
        "name": "Test Search",
        "query": "test query",
        "filters": {}
    }

    # Act (no auth headers)
    response = await async_client.post(
        "/api/v1/search/saved",
        json=payload
    )

    # Assert
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_create_saved_search_validates_empty_name(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test creating saved search validates empty name."""
    # Arrange
    payload = {
        "name": "   ",  # Whitespace only
        "query": "diabetes",
        "filters": {}
    }

    # Act
    response = await async_client.post(
        "/api/v1/search/saved",
        json=payload,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_list_saved_searches_returns_user_searches(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User
):
    """Test GET /api/v1/search/saved lists user's saved searches."""
    # Arrange: Create 3 saved searches for test user
    searches = [
        SavedSearch(
            user_id=test_user.id,
            name=f"Search {i}",
            query=f"query {i}",
            filters={"test": i},
            execution_count=i * 5
        )
        for i in range(1, 4)
    ]
    for search in searches:
        db_session.add(search)
    await db_session.commit()

    # Create search for different user (should not appear)
    other_user_id = uuid4()
    other_search = SavedSearch(
        user_id=other_user_id,
        name="Other User Search",
        query="other query",
        filters={}
    )
    db_session.add(other_search)
    await db_session.commit()

    # Act
    response = await async_client.get(
        "/api/v1/search/saved",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert len(data) == 3, f"Expected 3 searches, got {len(data)}"

    # Verify searches belong to test user
    for search_data in data:
        assert search_data["user_id"] == str(test_user.id)

    # Verify sorting (newest first by default)
    names = [s["name"] for s in data]
    assert names == ["Search 3", "Search 2", "Search 1"]


@pytest.mark.asyncio
async def test_list_saved_searches_empty_when_no_searches(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test GET /api/v1/search/saved returns empty list when no searches."""
    # Act
    response = await async_client.get(
        "/api/v1/search/saved",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert data == [], f"Expected empty list, got {data}"


@pytest.mark.asyncio
async def test_list_saved_searches_requires_authentication(
    async_client: AsyncClient
):
    """Test listing saved searches requires valid JWT token."""
    # Act (no auth headers)
    response = await async_client.get("/api/v1/search/saved")

    # Assert
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_delete_saved_search_success(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User
):
    """Test DELETE /api/v1/search/saved/{id} deletes saved search."""
    # Arrange: Create saved search
    saved_search = SavedSearch(
        user_id=test_user.id,
        name="Test Search",
        query="test query",
        filters={}
    )
    db_session.add(saved_search)
    await db_session.commit()
    await db_session.refresh(saved_search)
    search_id = saved_search.id

    # Act
    response = await async_client.delete(
        f"/api/v1/search/saved/{search_id}",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    # Verify deletion
    await db_session.refresh(saved_search, attribute_names=["id"])
    deleted_search = await db_session.get(SavedSearch, search_id)
    assert deleted_search is None, "Search should be deleted"


@pytest.mark.asyncio
async def test_delete_saved_search_not_found(
    async_client: AsyncClient,
    auth_headers: dict
):
    """Test deleting non-existent saved search returns 404."""
    # Arrange
    non_existent_id = uuid4()

    # Act
    response = await async_client.delete(
        f"/api/v1/search/saved/{non_existent_id}",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_saved_search_requires_ownership(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession
):
    """Test user can only delete their own saved searches."""
    # Arrange: Create saved search for different user
    other_user_id = uuid4()
    other_search = SavedSearch(
        user_id=other_user_id,
        name="Other User Search",
        query="other query",
        filters={}
    )
    db_session.add(other_search)
    await db_session.commit()
    await db_session.refresh(other_search)

    # Act: Try to delete other user's search
    response = await async_client.delete(
        f"/api/v1/search/saved/{other_search.id}",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 403, f"Expected 403, got {response.status_code}"
    assert "permission" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_delete_saved_search_requires_authentication(
    async_client: AsyncClient
):
    """Test deleting saved search requires valid JWT token."""
    # Arrange
    search_id = uuid4()

    # Act (no auth headers)
    response = await async_client.delete(f"/api/v1/search/saved/{search_id}")

    # Assert
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"


@pytest.mark.asyncio
async def test_create_saved_search_creates_audit_log(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User
):
    """Test creating saved search logs audit trail."""
    # Arrange
    payload = {
        "name": "Audit Test Search",
        "query": "audit test",
        "filters": {}
    }

    # Act
    response = await async_client.post(
        "/api/v1/search/saved",
        json=payload,
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    # Verify audit log created
    from app.models.audit_log import AuditLog
    from sqlalchemy import select

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.user_id == test_user.id,
            AuditLog.action == "SEARCH_SAVED"
        ).order_by(AuditLog.created_at.desc())
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log should be created"
    assert audit_log.action == "SEARCH_SAVED"
    assert audit_log.resource_type == "saved_search"
    assert payload["name"] in str(audit_log.metadata)


@pytest.mark.asyncio
async def test_delete_saved_search_creates_audit_log(
    async_client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    test_user: User
):
    """Test deleting saved search logs audit trail."""
    # Arrange: Create saved search
    saved_search = SavedSearch(
        user_id=test_user.id,
        name="Delete Audit Test",
        query="delete test",
        filters={}
    )
    db_session.add(saved_search)
    await db_session.commit()
    await db_session.refresh(saved_search)
    search_id = saved_search.id

    # Act
    response = await async_client.delete(
        f"/api/v1/search/saved/{search_id}",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 204, f"Expected 204, got {response.status_code}"

    # Verify audit log created
    from app.models.audit_log import AuditLog
    from sqlalchemy import select

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.user_id == test_user.id,
            AuditLog.action == "SEARCH_DELETED"
        ).order_by(AuditLog.created_at.desc())
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, "Audit log should be created"
    assert audit_log.action == "SEARCH_DELETED"
    assert audit_log.resource_type == "saved_search"
    assert str(search_id) in str(audit_log.metadata)
