"""
Task management service.

Provides CRUD operations for tasks within projects:
- get_tasks_by_project: Retrieve all tasks in a project
- get_task_by_id: Retrieve specific task
- create_task: Create new task in project
- update_task: Update existing task
- delete_task: Delete task
- check_task_access: Verify user can access task via project membership
"""

from typing import List, Optional
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.task import Task, TaskStatus, TaskPriority
from app.models.project import ProjectMemberRole
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.project_service import check_project_access, get_project_by_id


async def get_tasks_by_project(
    db: AsyncSession,
    project_id: str,
    user_id: str
) -> List[Task]:
    """
    Retrieve all tasks in a project.

    User must be a project member to view tasks.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID (for access check)

    Returns:
        List of tasks in project

    Raises:
        HTTPException: 403 if user is not project member

    Example:
        tasks = await get_tasks_by_project(db, project_id, current_user.id)
        for task in tasks:
            print(f"{task.title} - {task.status}")
    """
    # Check project access
    has_access = await check_project_access(db, project_id, user_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )

    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return []

    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_uuid)
        .order_by(Task.created_at.desc())
    )
    return list(result.scalars().all())


async def get_task_by_id(
    db: AsyncSession,
    task_id: str,
    user_id: str
) -> Optional[Task]:
    """
    Retrieve task by ID.

    User must be a member of the task's project to view it.

    Args:
        db: Database session
        task_id: Task ID (UUID string)
        user_id: User ID (for access check)

    Returns:
        Task if found and user has access, None otherwise

    Raises:
        HTTPException: 403 if user is not project member

    Example:
        task = await get_task_by_id(db, task_id, current_user.id)
        if task:
            print(f"Found task: {task.title}")
    """
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        return None

    result = await db.execute(
        select(Task).where(Task.id == task_uuid)
    )
    task = result.scalar_one_or_none()

    if not task:
        return None

    # Check project access
    has_access = await check_project_access(db, str(task.project_id), user_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this task"
        )

    return task


async def check_task_access(
    db: AsyncSession,
    task_id: str,
    user_id: str,
    required_roles: Optional[List[ProjectMemberRole]] = None
) -> bool:
    """
    Check if user has access to task with optional role requirement.

    Access is determined by project membership.

    Args:
        db: Database session
        task_id: Task ID
        user_id: User ID
        required_roles: Optional list of required project roles

    Returns:
        True if user has access, False otherwise

    Example:
        # Check if user can view task
        has_access = await check_task_access(db, task_id, user_id)

        # Check if user can modify task (owner or admin)
        can_modify = await check_task_access(
            db, task_id, user_id,
            required_roles=[ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN]
        )
    """
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        return False

    result = await db.execute(
        select(Task).where(Task.id == task_uuid)
    )
    task = result.scalar_one_or_none()

    if not task:
        return False

    # Check project access
    return await check_project_access(
        db,
        str(task.project_id),
        user_id,
        required_roles=required_roles
    )


async def create_task(
    db: AsyncSession,
    project_id: str,
    task_data: TaskCreate,
    creator_id: str
) -> Task:
    """
    Create new task in project.

    User must be a project member to create tasks.

    Args:
        db: Database session
        project_id: Project ID where task will be created
        task_data: Task creation data
        creator_id: User ID of task creator

    Returns:
        Created task

    Raises:
        HTTPException: 404 if project not found, 403 if unauthorized,
                      400 if assigned user not found

    Example:
        task_data = TaskCreate(
            title="Implement user authentication",
            description="Add JWT-based authentication system",
            assigned_to="550e8400-e29b-41d4-a716-446655440002",
            priority="high",
            due_date=datetime(2025, 12, 31, 23, 59, 59)
        )
        task = await create_task(db, project_id, task_data, current_user.id)
        print(f"Created task: {task.id}")
    """
    # Check project access
    has_access = await check_project_access(db, project_id, creator_id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this project"
        )

    # Verify project exists
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )

    # Validate assigned_to user if provided
    assigned_to_uuid = None
    if task_data.assigned_to:
        try:
            assigned_to_uuid = uuid.UUID(task_data.assigned_to)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assigned_to user ID"
            )

        # Verify assigned user is project member
        is_member = await check_project_access(db, project_id, task_data.assigned_to)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign task to user who is not a project member"
            )

    try:
        project_uuid = uuid.UUID(project_id)
        creator_uuid = uuid.UUID(creator_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project or creator ID"
        )

    # Create task
    new_task = Task(
        id=uuid.uuid4(),
        project_id=project_uuid,
        title=task_data.title,
        description=task_data.description,
        assigned_to=assigned_to_uuid,
        status=task_data.status,
        priority=task_data.priority,
        due_date=task_data.due_date,
        created_by=creator_uuid
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return new_task


async def update_task(
    db: AsyncSession,
    task_id: str,
    update_data: TaskUpdate,
    user_id: str
) -> Task:
    """
    Update existing task.

    User must be a project member to update tasks.
    Only owners and admins can reassign tasks or change status to completed.

    Args:
        db: Database session
        task_id: Task ID
        update_data: Task update data
        user_id: User ID making the update

    Returns:
        Updated task

    Raises:
        HTTPException: 404 if task not found, 403 if unauthorized

    Example:
        update_data = TaskUpdate(
            status="in_progress",
            priority="urgent"
        )
        task = await update_task(db, task_id, update_data, current_user.id)
    """
    # Get task and check access
    task = await get_task_by_id(db, task_id, user_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found"
        )

    # Validate assigned_to user if being updated
    if update_data.assigned_to is not None:
        try:
            assigned_to_uuid = uuid.UUID(update_data.assigned_to)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid assigned_to user ID"
            )

        # Verify assigned user is project member
        is_member = await check_project_access(
            db,
            str(task.project_id),
            update_data.assigned_to
        )
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot assign task to user who is not a project member"
            )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        # Handle assigned_to as UUID
        if field == "assigned_to" and value is not None:
            value = uuid.UUID(value)
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return task


async def delete_task(
    db: AsyncSession,
    task_id: str,
    user_id: str
) -> None:
    """
    Delete task.

    User must be project owner or admin to delete tasks.

    Args:
        db: Database session
        task_id: Task ID
        user_id: User ID deleting the task

    Raises:
        HTTPException: 404 if task not found, 403 if unauthorized

    Example:
        await delete_task(db, task_id, current_user.id)
    """
    # Check if user has permission (owner or admin)
    has_permission = await check_task_access(
        db, task_id, user_id,
        required_roles=[ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN]
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners and admins can delete tasks"
        )

    # Get task
    try:
        task_uuid = uuid.UUID(task_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid task ID"
        )

    result = await db.execute(
        select(Task).where(Task.id == task_uuid)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found"
        )

    await db.delete(task)
    await db.commit()
