"""
Unit tests for Task model.

Tests:
- Task creation with required fields
- Task belongs to project relationship
- Task assigned to user relationship
- Task status transitions
- Task priority levels
- Timestamp auto-setting
"""

import pytest
import uuid
from datetime import datetime, timedelta

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import Project, ProjectMember
from app.models.user import User


pytestmark = pytest.mark.asyncio


async def test_create_task_with_required_fields(db_session, test_admin):
    """Test creating task with all required fields."""
    # Create project first
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create task
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        title="Implement user authentication",
        description="Add JWT-based authentication system",
        assigned_to=test_admin.id,
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        created_by=test_admin.id
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Assert
    assert task.id is not None
    assert task.project_id == project.id
    assert task.title == "Implement user authentication"
    assert task.description == "Add JWT-based authentication system"
    assert task.assigned_to == test_admin.id
    assert task.status == TaskStatus.PENDING
    assert task.priority == TaskPriority.HIGH
    assert isinstance(task.created_at, datetime)
    assert isinstance(task.updated_at, datetime)


async def test_create_task_with_minimal_fields(db_session, test_admin):
    """Test creating task with only required fields."""
    # Create project
    project = Project(
        id=uuid.uuid4(),
        name="Minimal Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create task (minimal fields)
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        title="Simple Task",
        created_by=test_admin.id
    )

    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Assert
    assert task.title == "Simple Task"
    assert task.description is None  # Optional
    assert task.assigned_to is None  # Optional (unassigned)
    assert task.status == TaskStatus.PENDING  # Default
    assert task.priority == TaskPriority.MEDIUM  # Default
    assert task.due_date is None  # Optional


async def test_task_belongs_to_project(db_session, test_admin):
    """Test that task belongs to project."""
    # Create project
    project = Project(
        id=uuid.uuid4(),
        name="Project with Tasks",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create task
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        title="Task 1",
        created_by=test_admin.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Assert relationship
    assert task.project_id == project.id
    assert task.project.name == "Project with Tasks"


async def test_task_assigned_to_user(db_session, test_admin, test_clinician):
    """Test that task can be assigned to user."""
    # Create project
    project = Project(
        id=uuid.uuid4(),
        name="Assignment Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create task assigned to clinician
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        title="Assigned Task",
        assigned_to=test_clinician.id,
        created_by=test_admin.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Assert
    assert task.assigned_to == test_clinician.id
    assert task.assigned_user.username == test_clinician.username


async def test_task_status_enum_values(db_session, test_admin):
    """Test all task status enum values."""
    project = Project(
        id=uuid.uuid4(),
        name="Status Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Test all valid statuses
    statuses = [
        TaskStatus.PENDING,
        TaskStatus.IN_PROGRESS,
        TaskStatus.COMPLETED,
        TaskStatus.BLOCKED
    ]

    for status in statuses:
        task = Task(
            id=uuid.uuid4(),
            project_id=project.id,
            title=f"Task {status}",
            status=status,
            created_by=test_admin.id
        )
        db_session.add(task)

    await db_session.commit()

    # Verify all tasks created
    from sqlalchemy import select
    result = await db_session.execute(
        select(Task).where(Task.project_id == project.id)
    )
    tasks = list(result.scalars().all())
    assert len(tasks) == 4

    task_statuses = [t.status for t in tasks]
    assert set(task_statuses) == set(statuses)


async def test_task_priority_enum_values(db_session, test_admin):
    """Test all task priority enum values."""
    project = Project(
        id=uuid.uuid4(),
        name="Priority Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Test all valid priorities
    priorities = [
        TaskPriority.LOW,
        TaskPriority.MEDIUM,
        TaskPriority.HIGH,
        TaskPriority.URGENT
    ]

    for priority in priorities:
        task = Task(
            id=uuid.uuid4(),
            project_id=project.id,
            title=f"Task {priority}",
            priority=priority,
            created_by=test_admin.id
        )
        db_session.add(task)

    await db_session.commit()

    # Verify all tasks created
    from sqlalchemy import select
    result = await db_session.execute(
        select(Task).where(Task.project_id == project.id)
    )
    tasks = list(result.scalars().all())
    assert len(tasks) == 4

    task_priorities = [t.priority for t in tasks]
    assert set(task_priorities) == set(priorities)


async def test_task_timestamps_auto_set(db_session, test_admin):
    """Test that created_at and updated_at are automatically set."""
    project = Project(
        id=uuid.uuid4(),
        name="Timestamp Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    before_create = datetime.utcnow()

    # Create task
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        title="Timestamp Task",
        created_by=test_admin.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    after_create = datetime.utcnow()

    # Assert
    assert task.created_at is not None
    assert task.updated_at is not None
    assert before_create <= task.created_at <= after_create
    assert before_create <= task.updated_at <= after_create
    assert task.created_at == task.updated_at  # Initially the same


async def test_task_with_due_date(db_session, test_admin):
    """Test task with due date."""
    project = Project(
        id=uuid.uuid4(),
        name="Due Date Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create task with due date
    due_date = datetime.utcnow() + timedelta(days=7)
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        title="Task with Deadline",
        due_date=due_date,
        created_by=test_admin.id
    )
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)

    # Assert
    assert task.due_date is not None
    assert task.due_date.date() == due_date.date()


async def test_multiple_tasks_same_project(db_session, test_admin):
    """Test that project can have multiple tasks."""
    project = Project(
        id=uuid.uuid4(),
        name="Multi-Task Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create 5 tasks
    for i in range(5):
        task = Task(
            id=uuid.uuid4(),
            project_id=project.id,
            title=f"Task {i+1}",
            created_by=test_admin.id
        )
        db_session.add(task)

    await db_session.commit()

    # Verify all tasks created
    from sqlalchemy import select
    result = await db_session.execute(
        select(Task).where(Task.project_id == project.id)
    )
    tasks = list(result.scalars().all())
    assert len(tasks) == 5


async def test_task_title_required(db_session, test_admin):
    """Test that task title is required."""
    project = Project(
        id=uuid.uuid4(),
        name="Required Field Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create task without title
    task = Task(
        id=uuid.uuid4(),
        project_id=project.id,
        # Missing title field
        created_by=test_admin.id
    )
    db_session.add(task)

    # Act & Assert
    with pytest.raises(Exception):  # Will raise database constraint error
        await db_session.commit()
