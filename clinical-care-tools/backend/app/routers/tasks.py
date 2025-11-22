"""
Task Management API Router.

Provides CRUD operations for tasks with project member access control.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskList,
    TaskStatusUpdate,
    TaskAssign
)
from app.services.task_service import TaskService

router = APIRouter(
    prefix="/api/v1",
    tags=["tasks"],
    responses={404: {"description": "Not found"}}
)


@router.get("/projects/{project_id}/tasks", response_model=TaskList)
async def list_project_tasks(
    project_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    assigned_to: Optional[UUID] = Query(None, description="Filter by assigned user"),
    task_type: Optional[str] = Query(None, description="Filter by task type"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskList:
    """
    List tasks for a project.

    User must be a member of the project to view tasks.

    Args:
        project_id: Project ID
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        status: Optional filter by status
        priority: Optional filter by priority
        assigned_to: Optional filter by assigned user
        task_type: Optional filter by task type

    Returns:
        Paginated list of project tasks

    Raises:
        HTTPException:
            - 403 if user is not a project member
            - 404 if project not found
    """
    service = TaskService(db)
    return await service.get_project_tasks(
        project_id=project_id,
        user_id=UUID(current_user["id"]),
        page=page,
        per_page=per_page,
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        task_type=task_type
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: UUID,
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Create a new task in a project.

    User must be a member of the project to create tasks.
    The assigned user must also be a project member.

    Args:
        project_id: Project ID
        task_data: Task creation data

    Returns:
        Created task

    Raises:
        HTTPException:
            - 400 if assigned user is not a project member
            - 403 if current user is not a project member
            - 404 if project not found
    """
    service = TaskService(db)
    task = await service.create_task(
        project_id=project_id,
        task_data=task_data,
        created_by=UUID(current_user["id"])
    )

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assigned_username=task.assignee.username if task.assignee else None,
        assigned_email=task.assignee.email if task.assignee else None,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        configuration=task.configuration,
        created_at=task.created_at,
        created_by=task.created_by,
        updated_at=task.updated_at,
        updated_by=task.updated_by
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Get task by ID.

    User must be a member of the task's project to view it.

    Args:
        task_id: Task ID

    Returns:
        Task details

    Raises:
        HTTPException:
            - 403 if user is not a project member
            - 404 if task not found
    """
    service = TaskService(db)
    task = await service.get_task_by_id(
        task_id=task_id,
        user_id=UUID(current_user["id"])
    )

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assigned_username=task.assignee.username if task.assignee else None,
        assigned_email=task.assignee.email if task.assignee else None,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        configuration=task.configuration,
        created_at=task.created_at,
        created_by=task.created_by,
        updated_at=task.updated_at,
        updated_by=task.updated_by
    )


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Update task information.

    User must be a member of the task's project to update it.

    Args:
        task_id: Task ID to update
        task_data: Update data (only provided fields will be updated)

    Returns:
        Updated task

    Raises:
        HTTPException:
            - 403 if user is not a project member
            - 404 if task not found
    """
    service = TaskService(db)
    task = await service.update_task(
        task_id=task_id,
        task_data=task_data,
        user_id=UUID(current_user["id"])
    )

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assigned_username=task.assignee.username if task.assignee else None,
        assigned_email=task.assignee.email if task.assignee else None,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        configuration=task.configuration,
        created_at=task.created_at,
        created_by=task.created_by,
        updated_at=task.updated_at,
        updated_by=task.updated_by
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a task.

    User must be a member of the task's project to delete it.

    Args:
        task_id: Task ID to delete

    Raises:
        HTTPException:
            - 403 if user is not a project member
            - 404 if task not found
    """
    service = TaskService(db)
    await service.delete_task(
        task_id=task_id,
        user_id=UUID(current_user["id"])
    )
    return None


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
async def update_task_status(
    task_id: UUID,
    status_data: TaskStatusUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Update task status.

    User must be a member of the task's project to update status.
    Setting status to 'complete' will automatically set completed_at timestamp.

    Args:
        task_id: Task ID
        status_data: New status

    Returns:
        Updated task

    Raises:
        HTTPException:
            - 403 if user is not a project member
            - 404 if task not found
    """
    service = TaskService(db)
    task = await service.update_task_status(
        task_id=task_id,
        status_data=status_data,
        user_id=UUID(current_user["id"])
    )

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assigned_username=task.assignee.username if task.assignee else None,
        assigned_email=task.assignee.email if task.assignee else None,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        configuration=task.configuration,
        created_at=task.created_at,
        created_by=task.created_by,
        updated_at=task.updated_at,
        updated_by=task.updated_by
    )


@router.patch("/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: UUID,
    assign_data: TaskAssign,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """
    Assign or reassign a task to a user.

    User must be a member of the task's project to assign it.
    The assigned user must also be a project member.

    Args:
        task_id: Task ID
        assign_data: User to assign to

    Returns:
        Updated task

    Raises:
        HTTPException:
            - 400 if assigned user is not a project member
            - 403 if current user is not a project member
            - 404 if task not found
    """
    service = TaskService(db)
    task = await service.assign_task(
        task_id=task_id,
        assign_data=assign_data,
        user_id=UUID(current_user["id"])
    )

    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        assigned_to=task.assigned_to,
        assigned_username=task.assignee.username if task.assignee else None,
        assigned_email=task.assignee.email if task.assignee else None,
        name=task.name,
        description=task.description,
        task_type=task.task_type,
        status=task.status,
        priority=task.priority,
        due_date=task.due_date,
        completed_at=task.completed_at,
        configuration=task.configuration,
        created_at=task.created_at,
        created_by=task.created_by,
        updated_at=task.updated_at,
        updated_by=task.updated_by
    )