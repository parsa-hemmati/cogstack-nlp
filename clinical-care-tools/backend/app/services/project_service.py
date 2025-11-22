"""
Project Service for Clinical Care Tools.

Handles project management operations with member-based access control.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, or_, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.project import Project, ProjectMember, Task
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectList,
    ProjectMemberAdd,
    ProjectMemberResponse
)


class ProjectService:
    """Service for handling project management operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize project service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_project(
        self,
        project_data: ProjectCreate,
        created_by: UUID
    ) -> Project:
        """
        Create a new project.

        Args:
            project_data: Project creation data
            created_by: ID of user creating the project

        Returns:
            Created project object with creator as owner

        Raises:
            HTTPException: If project name already exists
        """
        # Check if project name already exists
        result = await self.db.execute(
            select(Project).where(Project.name == project_data.name)
        )
        existing_project = result.scalar_one_or_none()

        if existing_project:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project name already exists"
            )

        # Create new project
        new_project = Project(
            name=project_data.name,
            description=project_data.description,
            project_type=project_data.project_type,
            status=project_data.status,
            configuration=project_data.configuration,
            dataset_id=project_data.dataset_id,
            medcat_model_id=project_data.medcat_model_id,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            updated_at=datetime.now(timezone.utc),
            updated_by=created_by
        )

        self.db.add(new_project)
        await self.db.flush()  # Get project ID before creating member

        # Add creator as owner
        owner_member = ProjectMember(
            project_id=new_project.id,
            user_id=created_by,
            role="owner",
            added_by=created_by,
            joined_at=datetime.now(timezone.utc)
        )
        self.db.add(owner_member)

        # Audit log
        await self._audit_log(
            action="PROJECT_CREATED",
            user_id=created_by,
            resource_type="project",
            resource_id=new_project.id,
            details={"name": project_data.name, "type": project_data.project_type}
        )

        await self.db.commit()

        # Load with members
        await self.db.refresh(new_project)
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(Project.id == new_project.id)
        )
        return result.scalar_one()

    async def get_user_projects(
        self,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        search: Optional[str] = None,
        project_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> ProjectList:
        """
        Get projects for a specific user.

        Args:
            user_id: User ID
            page: Page number (1-indexed)
            per_page: Items per page
            search: Search term for name/description
            project_type: Filter by project type
            status: Filter by status

        Returns:
            Paginated project list
        """
        # Base query - get projects where user is a member
        query = (
            select(Project)
            .join(ProjectMember)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(ProjectMember.user_id == user_id)
        )

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Project.name.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%")
                )
            )

        if project_type:
            query = query.where(Project.project_type == project_type)

        if status:
            query = query.where(Project.status == status)

        # Get total count
        count_query = (
            select(func.count(Project.id))
            .join(ProjectMember)
            .where(ProjectMember.user_id == user_id)
        )

        if search or project_type or status:
            # Apply same filters to count query
            if search:
                count_query = count_query.where(
                    or_(
                        Project.name.ilike(f"%{search}%"),
                        Project.description.ilike(f"%{search}%")
                    )
                )
            if project_type:
                count_query = count_query.where(Project.project_type == project_type)
            if status:
                count_query = count_query.where(Project.status == status)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(Project.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        projects = result.scalars().all()

        # Get counts for each project
        project_responses = []
        for project in projects:
            # Get task count
            task_count_result = await self.db.execute(
                select(func.count(Task.id)).where(Task.project_id == project.id)
            )
            task_count = task_count_result.scalar() or 0

            # Format members
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

            project_response = ProjectResponse(
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
            project_responses.append(project_response)

        # Calculate pages
        pages = (total + per_page - 1) // per_page if total > 0 else 0

        return ProjectList(
            items=project_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )

    async def get_project_by_id(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Project:
        """
        Get project by ID if user is a member.

        Args:
            project_id: Project ID
            user_id: User ID requesting the project

        Returns:
            Project object

        Raises:
            HTTPException: If project not found or user not a member
        """
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check if user is a member
        is_member = any(member.user_id == user_id for member in project.members)
        if not is_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project"
            )

        return project

    async def update_project(
        self,
        project_id: UUID,
        project_data: ProjectUpdate,
        user_id: UUID
    ) -> Project:
        """
        Update project information.

        Args:
            project_id: Project ID to update
            project_data: Update data
            user_id: ID of user performing update

        Returns:
            Updated project object

        Raises:
            HTTPException: If project not found, user not owner, or duplicate name
        """
        # Get project and verify ownership
        project = await self._get_project_as_owner(project_id, user_id)

        # Check for duplicate name if being changed
        if project_data.name and project_data.name != project.name:
            existing = await self.db.execute(
                select(Project).where(Project.name == project_data.name)
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Project name already exists"
                )

        # Update fields
        update_dict = project_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc)
        update_dict["updated_by"] = user_id

        # Apply updates
        for field, value in update_dict.items():
            setattr(project, field, value)

        # Audit log
        await self._audit_log(
            action="PROJECT_UPDATED",
            user_id=user_id,
            resource_type="project",
            resource_id=project_id,
            details={"updated_fields": list(update_dict.keys())}
        )

        await self.db.commit()
        await self.db.refresh(project)

        # Reload with members
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.members).selectinload(ProjectMember.user))
            .where(Project.id == project_id)
        )
        return result.scalar_one()

    async def delete_project(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Delete a project (hard delete).

        Args:
            project_id: Project ID to delete
            user_id: ID of user performing deletion

        Raises:
            HTTPException: If project not found or user not owner
        """
        # Get project and verify ownership
        project = await self._get_project_as_owner(project_id, user_id)

        # Audit log before deletion
        await self._audit_log(
            action="PROJECT_DELETED",
            user_id=user_id,
            resource_type="project",
            resource_id=project_id,
            details={"name": project.name}
        )

        # Delete project (cascade will delete members, tasks, etc.)
        await self.db.delete(project)
        await self.db.commit()

    async def add_project_member(
        self,
        project_id: UUID,
        member_data: ProjectMemberAdd,
        added_by: UUID
    ) -> ProjectMember:
        """
        Add a member to a project.

        Args:
            project_id: Project ID
            member_data: Member data (user_id and role)
            added_by: ID of user adding the member

        Returns:
            Created project member

        Raises:
            HTTPException: If project not found, user not owner, or member already exists
        """
        # Get project and verify ownership
        project = await self._get_project_as_owner(project_id, added_by)

        # Check if user already a member
        existing = await self.db.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == member_data.user_id
                )
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this project"
            )

        # Verify user exists
        user_result = await self.db.execute(
            select(User).where(User.id == member_data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Create member
        new_member = ProjectMember(
            project_id=project_id,
            user_id=member_data.user_id,
            role=member_data.role,
            added_by=added_by,
            joined_at=datetime.now(timezone.utc)
        )
        self.db.add(new_member)

        # Audit log
        await self._audit_log(
            action="PROJECT_MEMBER_ADDED",
            user_id=added_by,
            resource_type="project",
            resource_id=project_id,
            details={"user_id": str(member_data.user_id), "role": member_data.role}
        )

        await self.db.commit()
        await self.db.refresh(new_member)

        # Load with user relation
        result = await self.db.execute(
            select(ProjectMember)
            .options(selectinload(ProjectMember.user))
            .where(ProjectMember.id == new_member.id)
        )
        return result.scalar_one()

    async def remove_project_member(
        self,
        project_id: UUID,
        user_id: UUID,
        removed_by: UUID
    ) -> None:
        """
        Remove a member from a project.

        Args:
            project_id: Project ID
            user_id: User ID to remove
            removed_by: ID of user removing the member

        Raises:
            HTTPException: If project not found, user not owner, member not found, or trying to remove owner
        """
        # Get project and verify ownership
        project = await self._get_project_as_owner(project_id, removed_by)

        # Find member
        result = await self.db.execute(
            select(ProjectMember).where(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id
                )
            )
        )
        member = result.scalar_one_or_none()

        if not member:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in project"
            )

        # Cannot remove project owner
        if member.role == "owner":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove project owner"
            )

        # Audit log
        await self._audit_log(
            action="PROJECT_MEMBER_REMOVED",
            user_id=removed_by,
            resource_type="project",
            resource_id=project_id,
            details={"user_id": str(user_id)}
        )

        # Remove member
        await self.db.delete(member)
        await self.db.commit()

    async def _get_project_as_owner(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> Project:
        """
        Get project and verify user is owner.

        Args:
            project_id: Project ID
            user_id: User ID to verify as owner

        Returns:
            Project object

        Raises:
            HTTPException: If project not found or user not owner
        """
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.members))
            .where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Check if user is owner
        is_owner = any(
            member.user_id == user_id and member.role == "owner"
            for member in project.members
        )

        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only project owner can perform this action"
            )

        return project

    async def _audit_log(
        self,
        action: str,
        user_id: UUID,
        resource_type: str,
        resource_id: UUID,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Create audit log entry.

        Args:
            action: Action performed
            user_id: User performing action
            resource_type: Type of resource
            resource_id: ID of resource
            details: Additional details
        """
        audit_entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            details=details or {},
            ip_address="system",
            user_agent="system",
            created_at=datetime.now(timezone.utc)
        )
        self.db.add(audit_entry)