"""
Integration tests for Tasks API endpoints.

Tests:
- GET /api/v1/projects/{id}/tasks (list tasks in project)
- POST /api/v1/projects/{id}/tasks (create task)
- PATCH /api/v1/tasks/{id} (update task)
- DELETE /api/v1/tasks/{id} (delete task)
- Permission checks (project membership required)
- Audit logging
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.models.audit_log import AuditLog
from sqlalchemy import select


pytestmark = pytest.mark.asyncio


async def test_create_task_returns_201(
    admin_client: AsyncClient,
    db_session,
    test_admin
):
    """Test that project member can create task."""
    # Create project
    project_data = {"name": "Task Test Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Create task
    task_data = {
        "title": "Implement user authentication",
        "description": "Add JWT-based authentication system",
        "priority": "high",
        "status": "pending"
    }

    response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )

    assert response.status_code == 201, \
        "Creating task should return 201"

    data = response.json()
    assert data["title"] == "Implement user authentication"
    assert data["description"] == "Add JWT-based authentication system"
    assert data["priority"] == "high"
    assert data["status"] == "pending"
    assert data["created_by"] == str(test_admin.id)
    assert data["assigned_to"] is None  # Not assigned


async def test_create_task_with_assignment(
    admin_client: AsyncClient,
    db_session,
    test_admin,
    test_clinician
):
    """Test creating task with assignment to project member."""
    # Create project
    project_data = {"name": "Assignment Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Add clinician to project
    member_data = {
        "user_id": str(test_clinician.id),
        "role": "member"
    }
    await admin_client.post(f"/api/v1/projects/{project_id}/members", json=member_data)

    # Create task assigned to clinician
    task_data = {
        "title": "Review patient records",
        "assigned_to": str(test_clinician.id),
        "priority": "medium"
    }

    response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["assigned_to"] == str(test_clinician.id)


async def test_create_task_with_due_date(admin_client: AsyncClient):
    """Test creating task with due date."""
    # Create project
    project_data = {"name": "Due Date Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Create task with due date
    due_date = (datetime.utcnow() + timedelta(days=7)).isoformat()
    task_data = {
        "title": "Task with deadline",
        "due_date": due_date
    }

    response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )

    assert response.status_code == 201
    data = response.json()
    assert data["due_date"] is not None


async def test_create_task_creates_audit_log(
    admin_client: AsyncClient,
    db_session,
    test_admin
):
    """Test that creating task generates audit log."""
    # Create project
    project_data = {"name": "Audit Test Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Create task
    task_data = {"title": "Audit Test Task"}
    response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    assert response.status_code == 201

    task_id = response.json()["id"]

    # Check audit log
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.action == "CREATE_TASK")
        .where(AuditLog.resource_id == task_id)
        .where(AuditLog.user_id == str(test_admin.id))
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None
    assert audit_log.resource_type == "task"


async def test_get_project_tasks_returns_200(admin_client: AsyncClient):
    """Test that GET /projects/{id}/tasks returns tasks."""
    # Create project
    project_data = {"name": "Task List Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Create 3 tasks
    for i in range(3):
        task_data = {"title": f"Task {i+1}"}
        await admin_client.post(f"/api/v1/projects/{project_id}/tasks", json=task_data)

    # Get all tasks
    response = await admin_client.get(f"/api/v1/projects/{project_id}/tasks")

    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3


async def test_get_project_tasks_as_non_member_returns_403(
    admin_client: AsyncClient,
    clinician_client: AsyncClient
):
    """Test that non-member cannot view project tasks."""
    # Admin creates project
    project_data = {"name": "Private Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Clinician (not a member) tries to view tasks
    response = await clinician_client.get(f"/api/v1/projects/{project_id}/tasks")

    assert response.status_code == 403


async def test_update_task_as_member_returns_200(admin_client: AsyncClient):
    """Test that project member can update task."""
    # Create project
    project_data = {"name": "Update Test Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Create task
    task_data = {"title": "Original Task", "status": "pending"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Update task
    update_data = {
        "title": "Updated Task",
        "status": "in_progress",
        "priority": "urgent"
    }
    response = await admin_client.patch(f"/api/v1/tasks/{task_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["status"] == "in_progress"
    assert data["priority"] == "urgent"


async def test_update_task_partial_fields(admin_client: AsyncClient):
    """Test updating only some task fields."""
    # Create project and task
    project_data = {"name": "Partial Update Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    task_data = {
        "title": "Original",
        "description": "Original description",
        "priority": "low"
    }
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Update only status
    update_data = {"status": "in_progress"}
    response = await admin_client.patch(f"/api/v1/tasks/{task_id}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "in_progress"
    assert data["title"] == "Original"  # Unchanged
    assert data["description"] == "Original description"  # Unchanged
    assert data["priority"] == "low"  # Unchanged


async def test_update_task_creates_audit_log(
    admin_client: AsyncClient,
    db_session,
    test_admin
):
    """Test that updating task generates audit log."""
    # Create project and task
    project_data = {"name": "Audit Update Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    task_data = {"title": "Audit Task"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Update task
    update_data = {"status": "completed"}
    response = await admin_client.patch(f"/api/v1/tasks/{task_id}", json=update_data)
    assert response.status_code == 200

    # Check audit log
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.action == "UPDATE_TASK")
        .where(AuditLog.resource_id == task_id)
        .where(AuditLog.user_id == str(test_admin.id))
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None
    assert audit_log.resource_type == "task"


async def test_delete_task_as_owner_returns_204(admin_client: AsyncClient):
    """Test that project owner can delete task."""
    # Create project and task
    project_data = {"name": "Delete Test Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    task_data = {"title": "Task to Delete"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Delete task
    response = await admin_client.delete(f"/api/v1/tasks/{task_id}")

    assert response.status_code == 204


async def test_delete_task_as_member_returns_403(
    admin_client: AsyncClient,
    clinician_client: AsyncClient,
    db_session,
    test_clinician
):
    """Test that regular member cannot delete task."""
    # Admin creates project
    project_data = {"name": "Delete Permission Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Add clinician as regular member
    member_data = {
        "user_id": str(test_clinician.id),
        "role": "member"
    }
    await admin_client.post(f"/api/v1/projects/{project_id}/members", json=member_data)

    # Admin creates task
    task_data = {"title": "Protected Task"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Clinician (member) tries to delete task
    response = await clinician_client.delete(f"/api/v1/tasks/{task_id}")

    assert response.status_code == 403


async def test_delete_task_creates_audit_log(
    admin_client: AsyncClient,
    db_session,
    test_admin
):
    """Test that deleting task generates audit log."""
    # Create project and task
    project_data = {"name": "Delete Audit Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    task_data = {"title": "Task for Deletion"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Delete task
    response = await admin_client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204

    # Check audit log
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.action == "DELETE_TASK")
        .where(AuditLog.resource_id == task_id)
        .where(AuditLog.user_id == str(test_admin.id))
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None
    assert audit_log.resource_type == "task"


async def test_create_task_with_invalid_assignment_returns_400(
    admin_client: AsyncClient,
    db_session,
    test_viewer
):
    """Test that assigning task to non-member fails."""
    # Create project (without viewer as member)
    project_data = {"name": "Invalid Assignment Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    # Try to assign task to viewer (not a member)
    task_data = {
        "title": "Invalid Task",
        "assigned_to": str(test_viewer.id)
    }

    response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )

    assert response.status_code == 400
    assert "not a project member" in response.json()["detail"].lower()


async def test_update_task_status_values(admin_client: AsyncClient):
    """Test all valid task status values."""
    # Create project and task
    project_data = {"name": "Status Test Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    task_data = {"title": "Status Task"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Test all valid statuses
    statuses = ["pending", "in_progress", "completed", "blocked"]

    for status_value in statuses:
        update_data = {"status": status_value}
        response = await admin_client.patch(
            f"/api/v1/tasks/{task_id}",
            json=update_data
        )
        assert response.status_code == 200
        assert response.json()["status"] == status_value


async def test_update_task_priority_values(admin_client: AsyncClient):
    """Test all valid task priority values."""
    # Create project and task
    project_data = {"name": "Priority Test Project"}
    project_response = await admin_client.post("/api/v1/projects", json=project_data)
    project_id = project_response.json()["id"]

    task_data = {"title": "Priority Task"}
    task_response = await admin_client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json=task_data
    )
    task_id = task_response.json()["id"]

    # Test all valid priorities
    priorities = ["low", "medium", "high", "urgent"]

    for priority_value in priorities:
        update_data = {"priority": priority_value}
        response = await admin_client.patch(
            f"/api/v1/tasks/{task_id}",
            json=update_data
        )
        assert response.status_code == 200
        assert response.json()["priority"] == priority_value
