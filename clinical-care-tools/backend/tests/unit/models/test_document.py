"""
Unit tests for Document model.

Tests document creation, SHA-256 hash generation, content storage.
"""

import pytest
import uuid
import hashlib
from datetime import datetime

from app.models.document import Document, ProcessingStatus
from app.models.user import User
from app.models.project import Project


pytestmark = pytest.mark.asyncio


async def test_create_document_with_required_fields(db_session, test_admin):
    """Test creating document with all required fields."""
    # Create project first
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create document
    content = b"This is test document content"
    content_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        id=uuid.uuid4(),
        filename="test_document.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,  # Will be encrypted in real usage
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )

    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    assert document.id is not None
    assert document.filename == "test_document.rtf"
    assert document.content_type == "application/rtf"
    assert document.content_hash == content_hash
    assert document.encrypted_content == content
    assert document.encryption_algorithm == "AES-256-GCM"
    assert document.file_size == len(content)
    assert document.uploaded_by == test_admin.id
    assert document.project_id == project.id
    assert document.processing_status == ProcessingStatus.PENDING
    assert document.created_at is not None


async def test_document_sha256_hash_generation(db_session, test_admin):
    """Test that SHA-256 hash is correctly calculated."""
    project = Project(
        id=uuid.uuid4(),
        name="Hash Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Test content with known hash
    content = b"Hello, World!"
    expected_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        id=uuid.uuid4(),
        filename="hash_test.rtf",
        content_type="application/rtf",
        content_hash=expected_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )

    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    assert document.content_hash == expected_hash
    assert len(document.content_hash) == 64  # SHA-256 produces 64 hex characters


async def test_document_with_different_processing_statuses(db_session, test_admin):
    """Test all processing status values."""
    project = Project(
        id=uuid.uuid4(),
        name="Status Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    statuses = [
        ProcessingStatus.PENDING,
        ProcessingStatus.PROCESSING,
        ProcessingStatus.COMPLETED,
        ProcessingStatus.FAILED
    ]

    for status in statuses:
        content = f"Content for {status}".encode()
        content_hash = hashlib.sha256(content).hexdigest()

        document = Document(
            id=uuid.uuid4(),
            filename=f"test_{status}.rtf",
            content_type="application/rtf",
            content_hash=content_hash,
            encrypted_content=content,
            encryption_algorithm="AES-256-GCM",
            file_size=len(content),
            uploaded_by=test_admin.id,
            project_id=project.id,
            processing_status=status
        )

        db_session.add(document)
        await db_session.commit()
        await db_session.refresh(document)

        assert document.processing_status == status


async def test_document_content_stored_as_bytea(db_session, test_admin):
    """Test that content is stored as binary (BYTEA in PostgreSQL)."""
    project = Project(
        id=uuid.uuid4(),
        name="BYTEA Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Binary content with non-ASCII characters
    content = b"\x00\x01\x02\x03\x04\x05\xFF\xFE\xFD"
    content_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        id=uuid.uuid4(),
        filename="binary_test.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )

    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    # Verify binary content is preserved
    assert document.encrypted_content == content
    assert isinstance(document.encrypted_content, bytes)


async def test_document_cascade_delete_with_project(db_session, test_admin):
    """Test that document is deleted when project is deleted."""
    project = Project(
        id=uuid.uuid4(),
        name="Delete Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    content = b"Test content"
    content_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        id=uuid.uuid4(),
        filename="delete_test.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )

    db_session.add(document)
    await db_session.commit()

    document_id = document.id

    # Delete project
    await db_session.delete(project)
    await db_session.commit()

    # Verify document was cascade deleted
    from sqlalchemy import select
    result = await db_session.execute(
        select(Document).where(Document.id == document_id)
    )
    deleted_document = result.scalar_one_or_none()

    assert deleted_document is None


async def test_document_with_large_content(db_session, test_admin):
    """Test document with large content (simulating RTF file)."""
    project = Project(
        id=uuid.uuid4(),
        name="Large File Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Simulate 50KB RTF file
    content = b"X" * (50 * 1024)
    content_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        id=uuid.uuid4(),
        filename="large_document.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )

    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    assert document.file_size == 50 * 1024
    assert len(document.encrypted_content) == 50 * 1024


async def test_document_timestamps_auto_set(db_session, test_admin):
    """Test that created_at timestamp is automatically set."""
    project = Project(
        id=uuid.uuid4(),
        name="Timestamp Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    content = b"Timestamp test"
    content_hash = hashlib.sha256(content).hexdigest()

    before_create = datetime.utcnow()

    document = Document(
        id=uuid.uuid4(),
        filename="timestamp_test.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )

    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)

    after_create = datetime.utcnow()

    assert document.created_at is not None
    assert before_create <= document.created_at <= after_create
