"""
Task Management API endpoints.

Provides:
- GET /api/v1/projects/{project_id}/tasks - List all tasks in project
- POST /api/v1/projects/{project_id}/tasks - Create new task
- PATCH /api/v1/tasks/{task_id} - Update task
- DELETE /api/v1/tasks/{task_id} - Delete task

All endpoints require authentication, project membership, and create audit logs.
"""

from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services import task_service
from app.services.audit_service import log_action


router = APIRouter()


@router.get(
    "/projects/{project_id}/tasks",
    response_model=List[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all tasks in project",
    description="Retrieve all tasks in a project. Requires project membership."
)
async def get_project_tasks(
    project_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[TaskResponse]:
    """
    Retrieve all tasks in a project.

    **Permission**: Project member

    **Path Parameters**:
    - project_id: Project ID (UUID)

    **Returns**: List of tasks in project

    **Example**:
    ```bash
    curl -X GET http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/tasks \
      -H "Authorization: Bearer <token>"
    ```
    """
    tasks = await task_service.get_tasks_by_project(
        db, project_id, str(current_user.id)
    )
    return [TaskResponse.model_validate(task) for task in tasks]


@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new task",
    description="Create new task in project. Requires project membership."
)
async def create_task(
    project_id: str,
    task_data: TaskCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TaskResponse:
    """
    Create new task in project.

    **Permission**: Project member

    **Path Parameters**:
    - project_id: Project ID (UUID)

    **Request Body**:
    - title: Task title (required, max 200 characters)
    - description: Task description (optional)
    - assigned_to: User ID to assign task to (optional, must be project member)
    - status: Task status (default: pending)
    - priority: Task priority (default: medium)
    - due_date: Task deadline (optional, ISO 8601 datetime)

    **Returns**: Created task

    **Audit**: Creates CREATE_TASK audit log entry

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/tasks \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{
        "title": "Implement user authentication",
        "description": "Add JWT-based authentication system",
        "assigned_to": "550e8400-e29b-41d4-a716-446655440002",
        "priority": "high",
        "due_date": "2025-12-31T23:59:59"
      }'
    ```
    """
    # Create task
    new_task = await task_service.create_task(
        db, project_id, task_data, str(current_user.id)
    )

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="CREATE_TASK",
        resource_type="task",
        resource_id=str(new_task.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "project_id": str(new_task.project_id),
            "task_title": new_task.title,
            "assigned_to": str(new_task.assigned_to) if new_task.assigned_to else None,
            "priority": new_task.priority.value,
            "status": new_task.status.value
        }
    )

    return TaskResponse.model_validate(new_task)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task",
    description="Update existing task. Requires project membership."
)
async def update_task(
    task_id: str,
    update_data: TaskUpdate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> TaskResponse:
    """
    Update existing task.

    **Permission**: Project member

    **Path Parameters**:
    - task_id: Task ID (UUID)

    **Request Body** (all fields optional):
    - title: New task title
    - description: New task description
    - assigned_to: User ID to assign task to (must be project member)
    - status: New task status (pending, in_progress, completed, blocked)
    - priority: New task priority (low, medium, high, urgent)
    - due_date: New task deadline

    **Returns**: Updated task

    **Audit**: Creates UPDATE_TASK audit log entry

    **Example**:
    ```bash
    curl -X PATCH http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440003 \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{
        "status": "in_progress",
        "priority": "urgent"
      }'
    ```
    """
    # Update task
    updated_task = await task_service.update_task(
        db, task_id, update_data, str(current_user.id)
    )

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="UPDATE_TASK",
        resource_type="task",
        resource_id=str(updated_task.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "project_id": str(updated_task.project_id),
            "updated_fields": update_data.model_dump(exclude_unset=True)
        }
    )

    return TaskResponse.model_validate(updated_task)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete task. Requires owner or admin role in project."
)
async def delete_task(
    task_id: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """
    Delete task.

    **Permission**: Project owner or admin

    **Path Parameters**:
    - task_id: Task ID (UUID)

    **Returns**: 204 No Content on success

    **Audit**: Creates DELETE_TASK audit log entry

    **Example**:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/tasks/550e8400-e29b-41d4-a716-446655440003 \
      -H "Authorization: Bearer <token>"
    ```
    """
    # Get task before deleting (for audit log)
    task = await task_service.get_task_by_id(db, task_id, str(current_user.id))

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID '{task_id}' not found"
        )

    # Delete task
    await task_service.delete_task(db, task_id, str(current_user.id))

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="DELETE_TASK",
        resource_type="task",
        resource_id=task_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "project_id": str(task.project_id),
            "task_title": task.title
        }
    )
