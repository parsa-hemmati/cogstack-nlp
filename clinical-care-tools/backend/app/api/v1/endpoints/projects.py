"""
Project Management API endpoints.

Provides:
- GET /api/v1/projects - List all projects for current user
- POST /api/v1/projects - Create new project
- PATCH /api/v1/projects/{project_id} - Update project
- POST /api/v1/projects/{project_id}/members - Add member to project
- DELETE /api/v1/projects/{project_id}/members/{user_id} - Remove member

All endpoints require authentication and create audit logs.
"""

from typing import List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.project import ProjectMemberRole
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectMemberAdd,
    ProjectMemberResponse
)
from app.services import project_service
from app.services.audit_service import log_action


router = APIRouter()


@router.get(
    "/projects",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all projects",
    description="Retrieve all projects where current user is a member."
)
async def get_projects(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> List[ProjectResponse]:
    """
    Retrieve all projects for current user.

    **Returns**: List of projects where user is a member

    **Example**:
    ```bash
    curl -X GET http://localhost:8000/api/v1/projects \
      -H "Authorization: Bearer <token>"
    ```
    """
    projects = await project_service.get_all_projects(db, str(current_user.id))
    return [ProjectResponse.model_validate(project) for project in projects]


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new project",
    description="Create new project with current user as owner."
)
async def create_project(
    project_data: ProjectCreate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProjectResponse:
    """
    Create new project.

    **Request Body**:
    - name: Project name (required)
    - description: Project description (optional)

    **Returns**: Created project with creator as owner

    **Audit**: Creates CREATE_PROJECT audit log entry

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/projects \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Clinical Research Project",
        "description": "Research project for patient cohort analysis"
      }'
    ```
    """
    # Create project
    new_project = await project_service.create_project(
        db, project_data, str(current_user.id)
    )

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="CREATE_PROJECT",
        resource_type="project",
        resource_id=str(new_project.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "project_name": new_project.name,
            "project_description": new_project.description
        }
    )

    return ProjectResponse.model_validate(new_project)


@router.patch(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update project",
    description="Update existing project. Requires owner or admin role."
)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProjectResponse:
    """
    Update existing project.

    **Permission**: Owner or Admin

    **Path Parameters**:
    - project_id: Project ID (UUID)

    **Request Body** (all fields optional):
    - name: New project name
    - description: New project description

    **Returns**: Updated project

    **Audit**: Creates UPDATE_PROJECT audit log entry

    **Example**:
    ```bash
    curl -X PATCH http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000 \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Updated Project Name"
      }'
    ```
    """
    # Update project
    updated_project = await project_service.update_project(
        db, project_id, update_data, str(current_user.id)
    )

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="UPDATE_PROJECT",
        resource_type="project",
        resource_id=str(updated_project.id),
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "updated_fields": update_data.model_dump(exclude_unset=True)
        }
    )

    return ProjectResponse.model_validate(updated_project)


@router.post(
    "/projects/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add project member",
    description="Add user to project with specified role. Requires owner or admin role."
)
async def add_project_member(
    project_id: str,
    member_data: ProjectMemberAdd,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> ProjectMemberResponse:
    """
    Add user to project.

    **Permission**: Owner or Admin

    **Path Parameters**:
    - project_id: Project ID (UUID)

    **Request Body**:
    - user_id: User ID to add (UUID)
    - role: Member role (owner, admin, member, viewer)

    **Returns**: Created project membership

    **Audit**: Creates ADD_PROJECT_MEMBER audit log entry

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/members \
      -H "Authorization: Bearer <token>" \
      -H "Content-Type: application/json" \
      -d '{
        "user_id": "550e8400-e29b-41d4-a716-446655440002",
        "role": "member"
      }'
    ```
    """
    # Add member
    new_member = await project_service.add_project_member(
        db, project_id, member_data, str(current_user.id)
    )

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="ADD_PROJECT_MEMBER",
        resource_type="project",
        resource_id=project_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "added_user_id": str(new_member.user_id),
            "role": new_member.role
        }
    )

    return ProjectMemberResponse.model_validate(new_member)


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove project member",
    description="Remove user from project. Requires owner or admin role."
)
async def remove_project_member(
    project_id: str,
    user_id: str,
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> None:
    """
    Remove user from project.

    **Permission**: Owner or Admin

    **Path Parameters**:
    - project_id: Project ID (UUID)
    - user_id: User ID to remove (UUID)

    **Returns**: 204 No Content on success

    **Audit**: Creates REMOVE_PROJECT_MEMBER audit log entry

    **Example**:
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/projects/550e8400-e29b-41d4-a716-446655440000/members/550e8400-e29b-41d4-a716-446655440002 \
      -H "Authorization: Bearer <token>"
    ```
    """
    # Remove member
    await project_service.remove_project_member(
        db, project_id, user_id, str(current_user.id)
    )

    # Log audit trail
    await log_action(
        db=db,
        user_id=str(current_user.id),
        username=current_user.username,
        action="REMOVE_PROJECT_MEMBER",
        resource_type="project",
        resource_id=project_id,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        details={
            "removed_user_id": user_id
        }
    )
