"""
Task Service for Clinical Care Tools.

Handles task management operations with project member access control.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from app.models.project import Project, ProjectMember, Task
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskList,
    TaskStatusUpdate,
    TaskAssign
)


class TaskService:
    """Service for handling task management operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize task service.

        Args:
            db: Database session
        """
        self.db = db

    async def create_task(
        self,
        project_id: UUID,
        task_data: TaskCreate,
        created_by: UUID
    ) -> Task:
        """
        Create a new task in a project.

        Args:
            project_id: Project ID
            task_data: Task creation data
            created_by: ID of user creating the task

        Returns:
            Created task object

        Raises:
            HTTPException: If user not a member or assigned user not a member
        """
        # Verify user is a project member
        await self._verify_project_member(project_id, created_by)

        # Verify assigned user is also a project member
        await self._verify_project_member(project_id, task_data.assigned_to)

        # Create new task
        new_task = Task(
            project_id=project_id,
            assigned_to=task_data.assigned_to,
            name=task_data.name,
            description=task_data.description,
            task_type=task_data.task_type,
            status="pending",
            priority=task_data.priority,
            due_date=task_data.due_date,
            configuration=task_data.configuration,
            created_at=datetime.now(timezone.utc),
            created_by=created_by,
            updated_at=datetime.now(timezone.utc),
            updated_by=created_by
        )

        self.db.add(new_task)

        # Audit log
        await self._audit_log(
            action="TASK_CREATED",
            user_id=created_by,
            resource_type="task",
            resource_id=new_task.id,
            details={
                "project_id": str(project_id),
                "name": task_data.name,
                "assigned_to": str(task_data.assigned_to)
            }
        )

        await self.db.commit()
        await self.db.refresh(new_task)

        # Load with assignee relation
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.id == new_task.id)
        )
        return result.scalar_one()

    async def get_project_tasks(
        self,
        project_id: UUID,
        user_id: UUID,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[UUID] = None,
        task_type: Optional[str] = None
    ) -> TaskList:
        """
        Get tasks for a project.

        Args:
            project_id: Project ID
            user_id: User requesting tasks (must be a member)
            page: Page number (1-indexed)
            per_page: Items per page
            status: Filter by status
            priority: Filter by priority
            assigned_to: Filter by assigned user
            task_type: Filter by task type

        Returns:
            Paginated task list

        Raises:
            HTTPException: If user not a project member
        """
        # Verify user is a project member
        await self._verify_project_member(project_id, user_id)

        # Base query
        query = (
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.project_id == project_id)
        )

        # Apply filters
        if status:
            query = query.where(Task.status == status)

        if priority:
            query = query.where(Task.priority == priority)

        if assigned_to:
            query = query.where(Task.assigned_to == assigned_to)

        if task_type:
            query = query.where(Task.task_type == task_type)

        # Get total count
        count_query = select(func.count(Task.id)).where(Task.project_id == project_id)
        if status or priority or assigned_to or task_type:
            # Apply same filters to count
            if status:
                count_query = count_query.where(Task.status == status)
            if priority:
                count_query = count_query.where(Task.priority == priority)
            if assigned_to:
                count_query = count_query.where(Task.assigned_to == assigned_to)
            if task_type:
                count_query = count_query.where(Task.task_type == task_type)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page).order_by(Task.created_at.desc())

        # Execute query
        result = await self.db.execute(query)
        tasks = result.scalars().all()

        # Format responses
        task_responses = []
        for task in tasks:
            task_response = TaskResponse(
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
            task_responses.append(task_response)

        # Calculate pages
        pages = (total + per_page - 1) // per_page if total > 0 else 0

        return TaskList(
            items=task_responses,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages
        )

    async def get_task_by_id(
        self,
        task_id: UUID,
        user_id: UUID
    ) -> Task:
        """
        Get task by ID if user is a project member.

        Args:
            task_id: Task ID
            user_id: User requesting the task

        Returns:
            Task object

        Raises:
            HTTPException: If task not found or user not a project member
        """
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )

        # Verify user is a project member
        await self._verify_project_member(task.project_id, user_id)

        return task

    async def update_task(
        self,
        task_id: UUID,
        task_data: TaskUpdate,
        user_id: UUID
    ) -> Task:
        """
        Update task information.

        Args:
            task_id: Task ID to update
            task_data: Update data
            user_id: ID of user performing update

        Returns:
            Updated task object

        Raises:
            HTTPException: If task not found or user not a project member
        """
        # Get task
        task = await self.get_task_by_id(task_id, user_id)

        # Update fields
        update_dict = task_data.model_dump(exclude_unset=True)
        update_dict["updated_at"] = datetime.now(timezone.utc)
        update_dict["updated_by"] = user_id

        # Apply updates
        for field, value in update_dict.items():
            setattr(task, field, value)

        # Audit log
        await self._audit_log(
            action="TASK_UPDATED",
            user_id=user_id,
            resource_type="task",
            resource_id=task_id,
            details={"updated_fields": list(update_dict.keys())}
        )

        await self.db.commit()
        await self.db.refresh(task)

        # Reload with assignee
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.id == task_id)
        )
        return result.scalar_one()

    async def delete_task(
        self,
        task_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Delete a task.

        Args:
            task_id: Task ID to delete
            user_id: ID of user performing deletion

        Raises:
            HTTPException: If task not found or user not a project member
        """
        # Get task and verify access
        task = await self.get_task_by_id(task_id, user_id)

        # Audit log
        await self._audit_log(
            action="TASK_DELETED",
            user_id=user_id,
            resource_type="task",
            resource_id=task_id,
            details={"name": task.name, "project_id": str(task.project_id)}
        )

        # Delete task
        await self.db.delete(task)
        await self.db.commit()

    async def update_task_status(
        self,
        task_id: UUID,
        status_data: TaskStatusUpdate,
        user_id: UUID
    ) -> Task:
        """
        Update task status.

        Args:
            task_id: Task ID
            status_data: New status
            user_id: User updating the status

        Returns:
            Updated task

        Raises:
            HTTPException: If task not found or user not a project member
        """
        # Get task
        task = await self.get_task_by_id(task_id, user_id)

        # Update status
        task.status = status_data.status
        task.updated_at = datetime.now(timezone.utc)
        task.updated_by = user_id

        # Set completed_at if status is complete
        if status_data.status == "complete":
            task.completed_at = datetime.now(timezone.utc)
        elif status_data.status in ["pending", "in_progress"]:
            task.completed_at = None

        # Audit log
        await self._audit_log(
            action="TASK_STATUS_UPDATED",
            user_id=user_id,
            resource_type="task",
            resource_id=task_id,
            details={"old_status": task.status, "new_status": status_data.status}
        )

        await self.db.commit()
        await self.db.refresh(task)

        # Reload with assignee
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.id == task_id)
        )
        return result.scalar_one()

    async def assign_task(
        self,
        task_id: UUID,
        assign_data: TaskAssign,
        user_id: UUID
    ) -> Task:
        """
        Assign or reassign a task to a user.

        Args:
            task_id: Task ID
            assign_data: User to assign to
            user_id: User performing the assignment

        Returns:
            Updated task

        Raises:
            HTTPException: If task not found, user not a member, or assigned user not a member
        """
        # Get task
        task = await self.get_task_by_id(task_id, user_id)

        # Verify assigned user is a project member
        await self._verify_project_member(task.project_id, assign_data.user_id)

        # Update assignment
        old_assignee = task.assigned_to
        task.assigned_to = assign_data.user_id
        task.updated_at = datetime.now(timezone.utc)
        task.updated_by = user_id

        # Audit log
        await self._audit_log(
            action="TASK_ASSIGNED",
            user_id=user_id,
            resource_type="task",
            resource_id=task_id,
            details={
                "old_assignee": str(old_assignee),
                "new_assignee": str(assign_data.user_id)
            }
        )

        await self.db.commit()
        await self.db.refresh(task)

        # Reload with assignee
        result = await self.db.execute(
            select(Task)
            .options(selectinload(Task.assignee))
            .where(Task.id == task_id)
        )
        return result.scalar_one()

    async def _verify_project_member(
        self,
        project_id: UUID,
        user_id: UUID
    ) -> None:
        """
        Verify user is a member of the project.

        Args:
            project_id: Project ID
            user_id: User ID to verify

        Raises:
            HTTPException: 403 if user is not a project member, 404 if project not found
        """
        # Check if user is a member
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
            # Check if project exists
            project_result = await self.db.execute(
                select(Project).where(Project.id == project_id)
            )
            if not project_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )

            # Check if it's about assignment
            user_result = await self.db.execute(
                select(User).where(User.id == user_id)
            )
            if user_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User is not a member of this project"
                )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this project"
            )

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