"""
Integration tests for Project Management API.

Tests CRUD operations for projects with member-based access control.
"""

import uuid
from datetime import datetime
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.project import Project, ProjectMember
from app.core.security import hash_password


@pytest.fixture
async def test_users(test_db: AsyncSession):
    """Create test users."""
    users = {
        "owner": User(
            id=uuid.uuid4(),
            username="project_owner",
            email="owner@test.com",
            password_hash=hash_password("Owner@Pass123!"),
            role="clinician",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        "member": User(
            id=uuid.uuid4(),
            username="project_member",
            email="member@test.com",
            password_hash=hash_password("Member@Pass123!"),
            role="researcher",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        "non_member": User(
            id=uuid.uuid4(),
            username="non_member",
            email="nonmember@test.com",
            password_hash=hash_password("NonMember@Pass123!"),
            role="researcher",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        "admin": User(
            id=uuid.uuid4(),
            username="admin_user",
            email="admin@test.com",
            password_hash=hash_password("Admin@Pass123!"),
            role="admin",
            is_active=True,
            created_at=datetime.utcnow()
        )
    }

    for user in users.values():
        test_db.add(user)
    await test_db.commit()

    return users


@pytest.fixture
async def auth_tokens(test_client: AsyncClient, test_users):
    """Get authentication tokens for test users."""
    tokens = {}
    for key, user in test_users.items():
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": f"{key.title()}@Pass123!"}
        )
        assert response.status_code == 200
        tokens[key] = response.json()["access_token"]
    return tokens


@pytest.fixture
async def sample_project(test_db: AsyncSession, test_users):
    """Create a sample project with members."""
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        description="A test project for unit tests",
        project_type="patient_search",
        status="active",
        created_by=test_users["owner"].id,
        updated_by=test_users["owner"].id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(project)

    # Add owner as member
    owner_member = ProjectMember(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=test_users["owner"].id,
        role="owner",
        added_by=test_users["owner"].id,
        joined_at=datetime.utcnow()
    )
    test_db.add(owner_member)

    # Add regular member
    regular_member = ProjectMember(
        id=uuid.uuid4(),
        project_id=project.id,
        user_id=test_users["member"].id,
        role="member",
        added_by=test_users["owner"].id,
        joined_at=datetime.utcnow()
    )
    test_db.add(regular_member)

    await test_db.commit()
    await test_db.refresh(project)
    return project


class TestProjectsList:
    """Tests for GET /api/v1/projects endpoint."""

    async def test_list_user_projects(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Users should see projects they are members of."""
        response = await test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1
        assert any(p["id"] == str(sample_project.id) for p in data["items"])

    async def test_list_projects_empty_for_non_member(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Non-members should not see projects they're not part of."""
        response = await test_client.get(
            "/api/v1/projects",
            headers={"Authorization": f"Bearer {auth_tokens['non_member']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0

    async def test_list_projects_with_filters(
        self, test_client: AsyncClient, auth_tokens, test_db, test_users
    ):
        """Test filtering projects by type and status."""
        # Create additional projects
        for i, proj_type in enumerate(["timeline", "cds", "cohort"]):
            project = Project(
                id=uuid.uuid4(),
                name=f"Project {i}",
                description=f"Test {proj_type}",
                project_type=proj_type,
                status="active" if i % 2 == 0 else "complete",
                created_by=test_users["owner"].id,
                updated_by=test_users["owner"].id
            )
            test_db.add(project)

            member = ProjectMember(
                project_id=project.id,
                user_id=test_users["owner"].id,
                role="owner",
                added_by=test_users["owner"].id
            )
            test_db.add(member)

        await test_db.commit()

        # Filter by type
        response = await test_client.get(
            "/api/v1/projects?project_type=timeline",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        data = response.json()
        assert all(p["project_type"] == "timeline" for p in data["items"])

        # Filter by status
        response = await test_client.get(
            "/api/v1/projects?status=complete",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        data = response.json()
        assert all(p["status"] == "complete" for p in data["items"])

    async def test_list_projects_unauthorized(self, test_client: AsyncClient):
        """Unauthenticated requests should return 401."""
        response = await test_client.get("/api/v1/projects")
        assert response.status_code == 401


class TestCreateProject:
    """Tests for POST /api/v1/projects endpoint."""

    async def test_create_project_success(
        self, test_client: AsyncClient, auth_tokens
    ):
        """Authenticated users should be able to create projects."""
        project_data = {
            "name": "New Research Project",
            "description": "Testing project creation",
            "project_type": "cohort",
            "configuration": {"target_size": 100}
        }

        response = await test_client.post(
            "/api/v1/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == project_data["name"]
        assert data["project_type"] == "cohort"
        assert data["status"] == "active"
        assert "id" in data

        # Verify creator is added as owner
        assert len(data["members"]) == 1
        assert data["members"][0]["role"] == "owner"

    async def test_create_project_duplicate_name(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Creating project with duplicate name should fail."""
        project_data = {
            "name": sample_project.name,  # Duplicate
            "description": "Duplicate name test",
            "project_type": "patient_search"
        }

        response = await test_client.post(
            "/api/v1/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    async def test_create_project_invalid_type(
        self, test_client: AsyncClient, auth_tokens
    ):
        """Creating project with invalid type should fail."""
        project_data = {
            "name": "Invalid Type Project",
            "description": "Testing invalid type",
            "project_type": "invalid_type"
        }

        response = await test_client.post(
            "/api/v1/projects",
            json=project_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 422


class TestGetProject:
    """Tests for GET /api/v1/projects/{id} endpoint."""

    async def test_get_project_as_member(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Project members should be able to view project details."""
        response = await test_client.get(
            f"/api/v1/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {auth_tokens['member']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_project.id)
        assert data["name"] == sample_project.name
        assert "members" in data

    async def test_get_project_forbidden_for_non_member(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Non-members should not be able to view project details."""
        response = await test_client.get(
            f"/api/v1/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {auth_tokens['non_member']}"}
        )
        assert response.status_code == 403

    async def test_get_nonexistent_project(
        self, test_client: AsyncClient, auth_tokens
    ):
        """Getting non-existent project should return 404."""
        fake_id = uuid.uuid4()
        response = await test_client.get(
            f"/api/v1/projects/{fake_id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 404


class TestUpdateProject:
    """Tests for PATCH /api/v1/projects/{id} endpoint."""

    async def test_update_project_as_owner(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Project owner should be able to update project."""
        update_data = {
            "description": "Updated description",
            "status": "complete",
            "configuration": {"new_config": "value"}
        }

        response = await test_client.patch(
            f"/api/v1/projects/{sample_project.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["status"] == "complete"
        assert data["configuration"]["new_config"] == "value"

    async def test_update_project_forbidden_for_member(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Regular members should not be able to update project."""
        response = await test_client.patch(
            f"/api/v1/projects/{sample_project.id}",
            json={"description": "Hacker attempt"},
            headers={"Authorization": f"Bearer {auth_tokens['member']}"}
        )
        assert response.status_code == 403


class TestDeleteProject:
    """Tests for DELETE /api/v1/projects/{id} endpoint."""

    async def test_delete_project_as_owner(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Project owner should be able to delete project."""
        response = await test_client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 204

        # Verify project is deleted
        response = await test_client.get(
            f"/api/v1/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 404

    async def test_delete_project_forbidden_for_member(
        self, test_client: AsyncClient, auth_tokens, sample_project
    ):
        """Regular members should not be able to delete project."""
        response = await test_client.delete(
            f"/api/v1/projects/{sample_project.id}",
            headers={"Authorization": f"Bearer {auth_tokens['member']}"}
        )
        assert response.status_code == 403


class TestProjectMembers:
    """Tests for project member management endpoints."""

    async def test_add_member_as_owner(
        self, test_client: AsyncClient, auth_tokens, sample_project, test_users
    ):
        """Project owner should be able to add members."""
        member_data = {
            "user_id": str(test_users["non_member"].id),
            "role": "member"
        }

        response = await test_client.post(
            f"/api/v1/projects/{sample_project.id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == str(test_users["non_member"].id)
        assert data["role"] == "member"

    async def test_cannot_add_duplicate_member(
        self, test_client: AsyncClient, auth_tokens, sample_project, test_users
    ):
        """Adding existing member should fail."""
        member_data = {
            "user_id": str(test_users["member"].id),  # Already a member
            "role": "member"
        }

        response = await test_client.post(
            f"/api/v1/projects/{sample_project.id}/members",
            json=member_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 400
        assert "already a member" in response.json()["detail"].lower()

    async def test_remove_member_as_owner(
        self, test_client: AsyncClient, auth_tokens, sample_project, test_users
    ):
        """Project owner should be able to remove members."""
        response = await test_client.delete(
            f"/api/v1/projects/{sample_project.id}/members/{test_users['member'].id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 204

    async def test_cannot_remove_owner(
        self, test_client: AsyncClient, auth_tokens, sample_project, test_users
    ):
        """Cannot remove the project owner."""
        response = await test_client.delete(
            f"/api/v1/projects/{sample_project.id}/members/{test_users['owner'].id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 400
        assert "cannot remove owner" in response.json()["detail"].lower()