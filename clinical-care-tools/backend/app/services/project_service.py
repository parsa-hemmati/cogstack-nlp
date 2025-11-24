"""
Project management service.

Provides CRUD operations for projects and project membership:
- get_all_projects: Retrieve all projects for a user
- get_project_by_id: Retrieve specific project
- create_project: Create new project and add creator as owner
- update_project: Update existing project
- delete_project: Delete project (soft delete)
- add_project_member: Add user to project with role
- remove_project_member: Remove user from project
- check_project_access: Verify user has access to project
"""

from typing import List, Optional
import uuid

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.project import Project, ProjectMember, ProjectMemberRole
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectMemberAdd


async def get_all_projects(
    db: AsyncSession,
    user_id: str
) -> List[Project]:
    """
    Retrieve all projects where user is a member.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        List of projects

    Example:
        projects = await get_all_projects(db, current_user.id)
        for project in projects:
            print(f"{project.name} - {len(project.members)} members")
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return []

    result = await db.execute(
        select(Project)
        .join(ProjectMember)
        .where(ProjectMember.user_id == user_uuid)
        .order_by(Project.created_at.desc())
    )
    return list(result.scalars().all())


async def get_project_by_id(
    db: AsyncSession,
    project_id: str
) -> Optional[Project]:
    """
    Retrieve project by ID.

    Args:
        db: Database session
        project_id: Project ID (UUID string)

    Returns:
        Project if found, None otherwise

    Example:
        project = await get_project_by_id(db, "550e8400-e29b-41d4-a716-446655440000")
        if project:
            print(f"Found project: {project.name}")
    """
    try:
        project_uuid = uuid.UUID(project_id)
    except ValueError:
        return None

    result = await db.execute(
        select(Project).where(Project.id == project_uuid)
    )
    return result.scalar_one_or_none()


async def check_project_access(
    db: AsyncSession,
    project_id: str,
    user_id: str,
    required_roles: Optional[List[ProjectMemberRole]] = None
) -> bool:
    """
    Check if user has access to project with optional role requirement.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID
        required_roles: Optional list of required roles

    Returns:
        True if user has access, False otherwise

    Example:
        # Check if user is project member
        has_access = await check_project_access(db, project_id, user_id)

        # Check if user is owner or admin
        is_admin = await check_project_access(
            db, project_id, user_id,
            required_roles=[ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN]
        )
    """
    try:
        project_uuid = uuid.UUID(project_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        return False

    query = select(ProjectMember).where(
        and_(
            ProjectMember.project_id == project_uuid,
            ProjectMember.user_id == user_uuid
        )
    )

    result = await db.execute(query)
    member = result.scalar_one_or_none()

    if not member:
        return False

    if required_roles is None:
        return True

    return member.role in required_roles


async def create_project(
    db: AsyncSession,
    project_data: ProjectCreate,
    creator_id: str
) -> Project:
    """
    Create new project and add creator as owner.

    Args:
        db: Database session
        project_data: Project creation data
        creator_id: User ID of project creator

    Returns:
        Created project with creator as owner

    Example:
        project_data = ProjectCreate(
            name="Clinical Research Project",
            description="Research project for patient cohort analysis"
        )
        project = await create_project(db, project_data, current_user.id)
        print(f"Created project: {project.id}")
    """
    try:
        creator_uuid = uuid.UUID(creator_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid creator user ID"
        )

    # Create project
    new_project = Project(
        id=uuid.uuid4(),
        name=project_data.name,
        description=project_data.description,
        created_by=creator_uuid
    )

    db.add(new_project)
    await db.flush()  # Flush to get project ID

    # Add creator as owner
    owner_member = ProjectMember(
        project_id=new_project.id,
        user_id=creator_uuid,
        role=ProjectMemberRole.OWNER,
        added_by=creator_uuid
    )

    db.add(owner_member)
    await db.commit()
    await db.refresh(new_project)

    return new_project


async def update_project(
    db: AsyncSession,
    project_id: str,
    update_data: ProjectUpdate,
    user_id: str
) -> Project:
    """
    Update existing project.

    Requires user to be owner or admin.

    Args:
        db: Database session
        project_id: Project ID
        update_data: Project update data
        user_id: User ID making the update

    Returns:
        Updated project

    Raises:
        HTTPException: 404 if project not found, 403 if unauthorized

    Example:
        update_data = ProjectUpdate(name="Updated Project Name")
        project = await update_project(db, project_id, update_data, current_user.id)
    """
    # Check if user has permission (owner or admin)
    has_permission = await check_project_access(
        db, project_id, user_id,
        required_roles=[ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN]
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners and admins can update projects"
        )

    project = await get_project_by_id(db, project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )

    # Update only provided fields
    update_dict = update_data.model_dump(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)

    return project


async def add_project_member(
    db: AsyncSession,
    project_id: str,
    member_data: ProjectMemberAdd,
    added_by_user_id: str
) -> ProjectMember:
    """
    Add user to project with specified role.

    Requires adding user to be owner or admin.

    Args:
        db: Database session
        project_id: Project ID
        member_data: Member data (user_id, role)
        added_by_user_id: User ID adding the member

    Returns:
        Created ProjectMember

    Raises:
        HTTPException: 404 if project/user not found, 403 if unauthorized, 400 if already member

    Example:
        member_data = ProjectMemberAdd(
            user_id="550e8400-e29b-41d4-a716-446655440002",
            role="member"
        )
        member = await add_project_member(db, project_id, member_data, current_user.id)
    """
    # Check if adding user has permission
    has_permission = await check_project_access(
        db, project_id, added_by_user_id,
        required_roles=[ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN]
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners and admins can add members"
        )

    # Verify project exists
    project = await get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found"
        )

    # Verify user exists
    try:
        new_member_uuid = uuid.UUID(member_data.user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )

    result = await db.execute(
        select(User).where(User.id == new_member_uuid)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{member_data.user_id}' not found"
        )

    # Check if already member
    existing = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == uuid.UUID(project_id),
                ProjectMember.user_id == new_member_uuid
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a project member"
        )

    # Add member
    new_member = ProjectMember(
        project_id=uuid.UUID(project_id),
        user_id=new_member_uuid,
        role=member_data.role,
        added_by=uuid.UUID(added_by_user_id)
    )

    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return new_member


async def remove_project_member(
    db: AsyncSession,
    project_id: str,
    user_id: str,
    removed_by_user_id: str
) -> None:
    """
    Remove user from project.

    Requires removing user to be owner or admin.
    Cannot remove the last owner.

    Args:
        db: Database session
        project_id: Project ID
        user_id: User ID to remove
        removed_by_user_id: User ID removing the member

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized, 400 if last owner

    Example:
        await remove_project_member(db, project_id, user_id, current_user.id)
    """
    # Check if removing user has permission
    has_permission = await check_project_access(
        db, project_id, removed_by_user_id,
        required_roles=[ProjectMemberRole.OWNER, ProjectMemberRole.ADMIN]
    )

    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners and admins can remove members"
        )

    # Get member to remove
    try:
        project_uuid = uuid.UUID(project_id)
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid project or user ID"
        )

    result = await db.execute(
        select(ProjectMember).where(
            and_(
                ProjectMember.project_id == project_uuid,
                ProjectMember.user_id == user_uuid
            )
        )
    )
    member = result.scalar_one_or_none()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a project member"
        )

    # Prevent removing last owner
    if member.role == ProjectMemberRole.OWNER:
        owner_count = await db.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_uuid,
                    ProjectMember.role == ProjectMemberRole.OWNER
                )
            )
        )
        if len(list(owner_count.scalars().all())) == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last project owner"
            )

    await db.delete(member)
    await db.commit()
