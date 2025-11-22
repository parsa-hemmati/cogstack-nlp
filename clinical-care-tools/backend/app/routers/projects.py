"""
Project Management API Router.

Provides CRUD operations for projects with member-based access control.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectList,
    ProjectMemberAdd,
    ProjectMemberResponse
)
from app.services.project_service import ProjectService

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}}
)


@router.get("/", response_model=ProjectList)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    project_type: Optional[str] = Query(None, description="Filter by project type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectList:
    """
    List projects for the current user.

    Returns only projects where the user is a member.

    Args:
        page: Page number (1-indexed)
        per_page: Items per page (max 100)
        search: Optional search term for name/description
        project_type: Optional filter by type
        status: Optional filter by status

    Returns:
        Paginated list of user's projects
    """
    service = ProjectService(db)
    return await service.get_user_projects(
        user_id=UUID(current_user["id"]),
        page=page,
        per_page=per_page,
        search=search,
        project_type=project_type,
        status=status
    )


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectResponse:
    """
    Create a new project.

    The creating user is automatically added as the project owner.

    Args:
        project_data: Project creation data

    Returns:
        Created project with owner membership

    Raises:
        HTTPException: 400 if project name already exists
    """
    service = ProjectService(db)
    project = await service.create_project(
        project_data=project_data,
        created_by=UUID(current_user["id"])
    )

    # Format response
    members = [
        ProjectMemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            role=member.role,
            username=member.user.username if member.user else None,
            email=member.user.email if member.user else None,
            joined_at=member.joined_at,
            added_by=member.added_by
        )
        for member in project.members
    ]

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        dataset_id=project.dataset_id,
        medcat_model_id=project.medcat_model_id,
        configuration=project.configuration,
        created_at=project.created_at,
        created_by=project.created_by,
        updated_at=project.updated_at,
        updated_by=project.updated_by,
        members=members,
        tasks_count=0,
        documents_count=0
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectResponse:
    """
    Get project by ID.

    User must be a member of the project to view it.

    Args:
        project_id: Project ID

    Returns:
        Project details with members

    Raises:
        HTTPException:
            - 403 if user is not a project member
            - 404 if project not found
    """
    service = ProjectService(db)
    project = await service.get_project_by_id(
        project_id=project_id,
        user_id=UUID(current_user["id"])
    )

    # Format response
    members = [
        ProjectMemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            role=member.role,
            username=member.user.username if member.user else None,
            email=member.user.email if member.user else None,
            joined_at=member.joined_at,
            added_by=member.added_by
        )
        for member in project.members
    ]

    # Get task count
    from app.models.project import Task
    from sqlalchemy import select, func

    task_count_result = await db.execute(
        select(func.count(Task.id)).where(Task.project_id == project_id)
    )
    task_count = task_count_result.scalar() or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        dataset_id=project.dataset_id,
        medcat_model_id=project.medcat_model_id,
        configuration=project.configuration,
        created_at=project.created_at,
        created_by=project.created_by,
        updated_at=project.updated_at,
        updated_by=project.updated_by,
        members=members,
        tasks_count=task_count,
        documents_count=0  # Will be implemented later
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectResponse:
    """
    Update project information.

    Only the project owner can update the project.

    Args:
        project_id: Project ID to update
        project_data: Update data (only provided fields will be updated)

    Returns:
        Updated project

    Raises:
        HTTPException:
            - 400 if duplicate project name
            - 403 if user is not the project owner
            - 404 if project not found
    """
    service = ProjectService(db)
    project = await service.update_project(
        project_id=project_id,
        project_data=project_data,
        user_id=UUID(current_user["id"])
    )

    # Format response
    members = [
        ProjectMemberResponse(
            id=member.id,
            project_id=member.project_id,
            user_id=member.user_id,
            role=member.role,
            username=member.user.username if member.user else None,
            email=member.user.email if member.user else None,
            joined_at=member.joined_at,
            added_by=member.added_by
        )
        for member in project.members
    ]

    # Get task count
    from app.models.project import Task
    from sqlalchemy import select, func

    task_count_result = await db.execute(
        select(func.count(Task.id)).where(Task.project_id == project_id)
    )
    task_count = task_count_result.scalar() or 0

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        status=project.status,
        dataset_id=project.dataset_id,
        medcat_model_id=project.medcat_model_id,
        configuration=project.configuration,
        created_at=project.created_at,
        created_by=project.created_by,
        updated_at=project.updated_at,
        updated_by=project.updated_by,
        members=members,
        tasks_count=task_count,
        documents_count=0
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a project.

    Only the project owner can delete the project.
    This performs a hard delete, removing the project and all associated data.

    Args:
        project_id: Project ID to delete

    Raises:
        HTTPException:
            - 403 if user is not the project owner
            - 404 if project not found
    """
    service = ProjectService(db)
    await service.delete_project(
        project_id=project_id,
        user_id=UUID(current_user["id"])
    )
    return None


@router.post("/{project_id}/members", response_model=ProjectMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_project_member(
    project_id: UUID,
    member_data: ProjectMemberAdd,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectMemberResponse:
    """
    Add a member to a project.

    Only the project owner can add members.

    Args:
        project_id: Project ID
        member_data: Member to add (user_id and role)

    Returns:
        Created project membership

    Raises:
        HTTPException:
            - 400 if user is already a member
            - 403 if current user is not the project owner
            - 404 if project or user not found
    """
    service = ProjectService(db)
    member = await service.add_project_member(
        project_id=project_id,
        member_data=member_data,
        added_by=UUID(current_user["id"])
    )

    return ProjectMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role,
        username=member.user.username if member.user else None,
        email=member.user.email if member.user else None,
        joined_at=member.joined_at,
        added_by=member.added_by
    )


@router.delete("/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Remove a member from a project.

    Only the project owner can remove members.
    The project owner cannot be removed.

    Args:
        project_id: Project ID
        user_id: User ID to remove

    Raises:
        HTTPException:
            - 400 if trying to remove the project owner
            - 403 if current user is not the project owner
            - 404 if project or member not found
    """
    service = ProjectService(db)
    await service.remove_project_member(
        project_id=project_id,
        user_id=user_id,
        removed_by=UUID(current_user["id"])
    )
    return None