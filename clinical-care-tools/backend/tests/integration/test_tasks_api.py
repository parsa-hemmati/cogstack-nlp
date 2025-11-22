"""
Integration tests for Task Management API.

Tests CRUD operations for tasks with project member access control.
"""

import uuid
from datetime import datetime, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.project import Project, ProjectMember, Task
from app.core.security import hash_password


@pytest.fixture
async def test_setup(test_db: AsyncSession):
    """Create test users, project, and members."""
    # Create users
    users = {
        "owner": User(
            id=uuid.uuid4(),
            username="task_owner",
            email="task_owner@test.com",
            password_hash=hash_password("Owner@Pass123!"),
            role="clinician",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        "member1": User(
            id=uuid.uuid4(),
            username="task_member1",
            email="member1@test.com",
            password_hash=hash_password("Member1@Pass123!"),
            role="researcher",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        "member2": User(
            id=uuid.uuid4(),
            username="task_member2",
            email="member2@test.com",
            password_hash=hash_password("Member2@Pass123!"),
            role="researcher",
            is_active=True,
            created_at=datetime.utcnow()
        ),
        "non_member": User(
            id=uuid.uuid4(),
            username="task_non_member",
            email="nonmember@test.com",
            password_hash=hash_password("NonMember@Pass123!"),
            role="researcher",
            is_active=True,
            created_at=datetime.utcnow()
        )
    }

    for user in users.values():
        test_db.add(user)

    # Create project
    project = Project(
        id=uuid.uuid4(),
        name="Task Test Project",
        description="Project for task testing",
        project_type="annotation",
        status="active",
        created_by=users["owner"].id,
        updated_by=users["owner"].id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(project)

    # Add members
    for user_key in ["owner", "member1", "member2"]:
        member = ProjectMember(
            id=uuid.uuid4(),
            project_id=project.id,
            user_id=users[user_key].id,
            role="owner" if user_key == "owner" else "member",
            added_by=users["owner"].id,
            joined_at=datetime.utcnow()
        )
        test_db.add(member)

    await test_db.commit()

    return {"users": users, "project": project}


@pytest.fixture
async def auth_tokens(test_client: AsyncClient, test_setup):
    """Get authentication tokens for test users."""
    tokens = {}
    password_map = {
        "owner": "Owner@Pass123!",
        "member1": "Member1@Pass123!",
        "member2": "Member2@Pass123!",
        "non_member": "NonMember@Pass123!"
    }

    for key, user in test_setup["users"].items():
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": user.email, "password": password_map[key]}
        )
        assert response.status_code == 200
        tokens[key] = response.json()["access_token"]

    return tokens


@pytest.fixture
async def sample_task(test_db: AsyncSession, test_setup):
    """Create a sample task."""
    task = Task(
        id=uuid.uuid4(),
        project_id=test_setup["project"].id,
        assigned_to=test_setup["users"]["member1"].id,
        created_by=test_setup["users"]["owner"].id,
        updated_by=test_setup["users"]["owner"].id,
        name="Sample Annotation Task",
        description="Annotate patient records for conditions",
        task_type="annotation",
        status="pending",
        priority="medium",
        due_date=datetime.utcnow() + timedelta(days=7),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(task)
    await test_db.commit()
    await test_db.refresh(task)
    return task


class TestTasksList:
    """Tests for GET /api/v1/projects/{project_id}/tasks endpoint."""

    async def test_list_project_tasks_as_member(
        self, test_client: AsyncClient, auth_tokens, test_setup, sample_task
    ):
        """Project members should be able to list project tasks."""
        project_id = test_setup["project"].id
        response = await test_client.get(
            f"/api/v1/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {auth_tokens['member1']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1
        assert any(t["id"] == str(sample_task.id) for t in data["items"])

    async def test_list_tasks_with_filters(
        self, test_client: AsyncClient, auth_tokens, test_setup, test_db
    ):
        """Test filtering tasks by status, priority, and assigned user."""
        project_id = test_setup["project"].id

        # Create tasks with different properties
        tasks_data = [
            {"status": "pending", "priority": "high", "assigned_to": test_setup["users"]["member1"].id},
            {"status": "in_progress", "priority": "medium", "assigned_to": test_setup["users"]["member1"].id},
            {"status": "complete", "priority": "low", "assigned_to": test_setup["users"]["member2"].id},
        ]

        for task_data in tasks_data:
            task = Task(
                project_id=project_id,
                name=f"Task {task_data['status']}",
                description="Test task",
                task_type="review",
                status=task_data["status"],
                priority=task_data["priority"],
                assigned_to=task_data["assigned_to"],
                created_by=test_setup["users"]["owner"].id,
                updated_by=test_setup["users"]["owner"].id
            )
            test_db.add(task)
        await test_db.commit()

        # Filter by status
        response = await test_client.get(
            f"/api/v1/projects/{project_id}/tasks?status=pending",
            headers={"Authorization": f"Bearer {auth_tokens['member1']}"}
        )
        data = response.json()
        assert all(t["status"] == "pending" for t in data["items"])

        # Filter by priority
        response = await test_client.get(
            f"/api/v1/projects/{project_id}/tasks?priority=high",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        data = response.json()
        assert all(t["priority"] == "high" for t in data["items"])

        # Filter by assigned user
        response = await test_client.get(
            f"/api/v1/projects/{project_id}/tasks?assigned_to={test_setup['users']['member2'].id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        data = response.json()
        assert all(t["assigned_to"] == str(test_setup["users"]["member2"].id) for t in data["items"])

    async def test_list_tasks_forbidden_for_non_member(
        self, test_client: AsyncClient, auth_tokens, test_setup
    ):
        """Non-members should not be able to list project tasks."""
        project_id = test_setup["project"].id
        response = await test_client.get(
            f"/api/v1/projects/{project_id}/tasks",
            headers={"Authorization": f"Bearer {auth_tokens['non_member']}"}
        )
        assert response.status_code == 403


class TestCreateTask:
    """Tests for POST /api/v1/projects/{project_id}/tasks endpoint."""

    async def test_create_task_as_member(
        self, test_client: AsyncClient, auth_tokens, test_setup
    ):
        """Project members should be able to create tasks."""
        project_id = test_setup["project"].id
        task_data = {
            "name": "New Review Task",
            "description": "Review clinical notes for accuracy",
            "task_type": "review",
            "assigned_to": str(test_setup["users"]["member2"].id),
            "priority": "high",
            "due_date": (datetime.utcnow() + timedelta(days=3)).isoformat()
        }

        response = await test_client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {auth_tokens['member1']}"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Review Task"
        assert data["status"] == "pending"
        assert data["priority"] == "high"
        assert data["assigned_to"] == str(test_setup["users"]["member2"].id)

    async def test_create_task_assign_to_non_member(
        self, test_client: AsyncClient, auth_tokens, test_setup
    ):
        """Cannot assign task to non-member."""
        project_id = test_setup["project"].id
        task_data = {
            "name": "Invalid Assignment",
            "description": "This should fail",
            "task_type": "annotation",
            "assigned_to": str(test_setup["users"]["non_member"].id),  # Not a member
            "priority": "medium"
        }

        response = await test_client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 400
        assert "not a member" in response.json()["detail"].lower()

    async def test_create_task_forbidden_for_non_member(
        self, test_client: AsyncClient, auth_tokens, test_setup
    ):
        """Non-members should not be able to create tasks."""
        project_id = test_setup["project"].id
        task_data = {
            "name": "Unauthorized Task",
            "description": "Should fail",
            "task_type": "annotation",
            "assigned_to": str(test_setup["users"]["member1"].id),
            "priority": "low"
        }

        response = await test_client.post(
            f"/api/v1/projects/{project_id}/tasks",
            json=task_data,
            headers={"Authorization": f"Bearer {auth_tokens['non_member']}"}
        )
        assert response.status_code == 403


class TestUpdateTask:
    """Tests for PATCH /api/v1/tasks/{id} endpoint."""

    async def test_update_task_as_member(
        self, test_client: AsyncClient, auth_tokens, sample_task
    ):
        """Project members should be able to update tasks."""
        update_data = {
            "name": "Updated Task Name",
            "description": "Updated description",
            "priority": "urgent"
        }

        response = await test_client.patch(
            f"/api/v1/tasks/{sample_task.id}",
            json=update_data,
            headers={"Authorization": f"Bearer {auth_tokens['member1']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Task Name"
        assert data["priority"] == "urgent"

    async def test_update_task_forbidden_for_non_member(
        self, test_client: AsyncClient, auth_tokens, sample_task
    ):
        """Non-members should not be able to update tasks."""
        response = await test_client.patch(
            f"/api/v1/tasks/{sample_task.id}",
            json={"name": "Hacker update"},
            headers={"Authorization": f"Bearer {auth_tokens['non_member']}"}
        )
        assert response.status_code == 403


class TestDeleteTask:
    """Tests for DELETE /api/v1/tasks/{id} endpoint."""

    async def test_delete_task_as_member(
        self, test_client: AsyncClient, auth_tokens, sample_task
    ):
        """Project members should be able to delete tasks."""
        response = await test_client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 204

    async def test_delete_task_forbidden_for_non_member(
        self, test_client: AsyncClient, auth_tokens, sample_task
    ):
        """Non-members should not be able to delete tasks."""
        response = await test_client.delete(
            f"/api/v1/tasks/{sample_task.id}",
            headers={"Authorization": f"Bearer {auth_tokens['non_member']}"}
        )
        assert response.status_code == 403


class TestUpdateTaskStatus:
    """Tests for PATCH /api/v1/tasks/{id}/status endpoint."""

    async def test_update_task_status(
        self, test_client: AsyncClient, auth_tokens, sample_task
    ):
        """Project members should be able to update task status."""
        status_data = {"status": "in_progress"}

        response = await test_client.patch(
            f"/api/v1/tasks/{sample_task.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {auth_tokens['member1']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    async def test_complete_task_sets_timestamp(
        self, test_client: AsyncClient, auth_tokens, sample_task
    ):
        """Completing a task should set completed_at timestamp."""
        status_data = {"status": "complete"}

        response = await test_client.patch(
            f"/api/v1/tasks/{sample_task.id}/status",
            json=status_data,
            headers={"Authorization": f"Bearer {auth_tokens['member1']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["completed_at"] is not None


class TestAssignTask:
    """Tests for PATCH /api/v1/tasks/{id}/assign endpoint."""

    async def test_assign_task_to_member(
        self, test_client: AsyncClient, auth_tokens, sample_task, test_setup
    ):
        """Project members should be able to reassign tasks."""
        assign_data = {"user_id": str(test_setup["users"]["member2"].id)}

        response = await test_client.patch(
            f"/api/v1/tasks/{sample_task.id}/assign",
            json=assign_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == str(test_setup["users"]["member2"].id)

    async def test_assign_task_to_non_member(
        self, test_client: AsyncClient, auth_tokens, sample_task, test_setup
    ):
        """Cannot assign task to non-member."""
        assign_data = {"user_id": str(test_setup["users"]["non_member"].id)}

        response = await test_client.patch(
            f"/api/v1/tasks/{sample_task.id}/assign",
            json=assign_data,
            headers={"Authorization": f"Bearer {auth_tokens['owner']}"}
        )
        assert response.status_code == 400
        assert "not a member" in response.json()["detail"].lower()