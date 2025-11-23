"""
Unit tests for Project model.

Tests:
- Project creation with required fields
- Project-user relationship (many-to-many via project_members)
- Project member roles
- Cascade delete behavior
"""

import pytest
import uuid
from datetime import datetime

from app.models.project import Project, ProjectMember
from app.models.user import User


pytestmark = pytest.mark.asyncio


async def test_create_project_with_required_fields(db_session):
    """Test creating project with all required fields."""
    # Arrange
    creator_id = uuid.uuid4()

    # Act
    project = Project(
        id=uuid.uuid4(),
        name="Clinical Research Project",
        description="Research project for patient cohort analysis",
        created_by=creator_id
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Assert
    assert project.id is not None
    assert project.name == "Clinical Research Project"
    assert project.description == "Research project for patient cohort analysis"
    assert project.created_by == creator_id
    assert isinstance(project.created_at, datetime)
    assert isinstance(project.updated_at, datetime)


async def test_create_project_with_minimal_fields(db_session):
    """Test creating project with only required fields."""
    # Arrange
    creator_id = uuid.uuid4()

    # Act
    project = Project(
        id=uuid.uuid4(),
        name="Minimal Project",
        created_by=creator_id
    )

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Assert
    assert project.id is not None
    assert project.name == "Minimal Project"
    assert project.description is None  # Optional field
    assert project.created_by == creator_id


async def test_project_user_relationship(db_session, test_admin, test_clinician):
    """Test many-to-many relationship between projects and users."""
    # Arrange
    project = Project(
        id=uuid.uuid4(),
        name="Multi-user Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Act: Add admin as owner
    member1 = ProjectMember(
        project_id=project.id,
        user_id=test_admin.id,
        role="owner",
        added_by=test_admin.id
    )
    db_session.add(member1)

    # Add clinician as member
    member2 = ProjectMember(
        project_id=project.id,
        user_id=test_clinician.id,
        role="member",
        added_by=test_admin.id
    )
    db_session.add(member2)

    await db_session.commit()
    await db_session.refresh(project)

    # Assert
    assert len(project.members) == 2

    # Check owner membership
    owner_member = next(m for m in project.members if m.role == "owner")
    assert owner_member.user_id == test_admin.id
    assert owner_member.added_by == test_admin.id

    # Check regular membership
    regular_member = next(m for m in project.members if m.role == "member")
    assert regular_member.user_id == test_clinician.id
    assert regular_member.added_by == test_admin.id


async def test_project_member_roles(db_session, test_admin):
    """Test different project member roles."""
    # Arrange
    project = Project(
        id=uuid.uuid4(),
        name="Role Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Act: Test all valid roles
    valid_roles = ["owner", "admin", "member", "viewer"]

    for role in valid_roles:
        user_id = uuid.uuid4()
        member = ProjectMember(
            project_id=project.id,
            user_id=user_id,
            role=role,
            added_by=test_admin.id
        )
        db_session.add(member)

    await db_session.commit()
    await db_session.refresh(project)

    # Assert
    assert len(project.members) == 4
    roles_in_project = [m.role for m in project.members]
    assert set(roles_in_project) == set(valid_roles)


async def test_project_timestamps_auto_set(db_session):
    """Test that created_at and updated_at are automatically set."""
    # Arrange
    before_create = datetime.utcnow()

    # Act
    project = Project(
        id=uuid.uuid4(),
        name="Timestamp Test",
        created_by=uuid.uuid4()
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    after_create = datetime.utcnow()

    # Assert
    assert project.created_at is not None
    assert project.updated_at is not None
    assert before_create <= project.created_at <= after_create
    assert before_create <= project.updated_at <= after_create
    assert project.created_at == project.updated_at  # Initially the same


async def test_project_member_added_at_auto_set(db_session, test_admin):
    """Test that ProjectMember.added_at is automatically set."""
    # Arrange
    project = Project(
        id=uuid.uuid4(),
        name="Member Timestamp Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    before_add = datetime.utcnow()

    # Act
    member = ProjectMember(
        project_id=project.id,
        user_id=test_admin.id,
        role="owner",
        added_by=test_admin.id
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(member)

    after_add = datetime.utcnow()

    # Assert
    assert member.added_at is not None
    assert before_add <= member.added_at <= after_add


async def test_multiple_projects_same_user(db_session, test_admin):
    """Test that a user can be member of multiple projects."""
    # Arrange & Act
    projects = []
    for i in range(3):
        project = Project(
            id=uuid.uuid4(),
            name=f"Project {i+1}",
            created_by=test_admin.id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

        member = ProjectMember(
            project_id=project.id,
            user_id=test_admin.id,
            role="owner",
            added_by=test_admin.id
        )
        db_session.add(member)
        projects.append(project)

    await db_session.commit()

    # Assert
    for project in projects:
        await db_session.refresh(project)
        assert len(project.members) == 1
        assert project.members[0].user_id == test_admin.id


async def test_project_name_required(db_session):
    """Test that project name is required."""
    # Arrange
    project = Project(
        id=uuid.uuid4(),
        created_by=uuid.uuid4()
        # Missing name field
    )

    db_session.add(project)

    # Act & Assert
    with pytest.raises(Exception):  # Will raise database constraint error
        await db_session.commit()
