"""
Unit tests for Document model.

Tests document storage with encryption, hashing, and processing status.
"""
import hashlib
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.models.user import User


@pytest.mark.asyncio
async def test_document_creation(db: AsyncSession, admin_user: User):
    """Test basic document creation with all fields."""
    content = b"This is a test clinical document."
    content_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        filename="test_document.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,  # Will be encrypted in service layer
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        project_id=None,  # No projects yet
        processing_status=ProcessingStatus.PENDING,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    assert document.id is not None
    assert document.filename == "test_document.rtf"
    assert document.content_hash == content_hash
    assert document.processing_status == ProcessingStatus.PENDING
    assert document.created_at is not None


@pytest.mark.asyncio
async def test_document_sha256_hash_generation(db: AsyncSession, admin_user: User):
    """Test that SHA-256 hash is correctly computed for content."""
    content = b"Test clinical note with PHI."
    expected_hash = hashlib.sha256(content).hexdigest()

    document = Document(
        filename="clinical_note.rtf",
        content_type="application/rtf",
        content_hash=expected_hash,
        encrypted_content=content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Verify hash stored correctly
    assert document.content_hash == expected_hash
    assert len(document.content_hash) == 64  # SHA-256 produces 64 hex characters


@pytest.mark.asyncio
async def test_document_content_stored_as_bytea(db: AsyncSession, admin_user: User):
    """Test that encrypted content is stored as BYTEA (binary)."""
    content = b"\x00\x01\x02\x03\x04\x05Binary encrypted content"

    document = Document(
        filename="encrypted.rtf",
        content_type="application/rtf",
        content_hash=hashlib.sha256(content).hexdigest(),
        encrypted_content=content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Verify binary content stored and retrieved correctly
    assert document.encrypted_content == content
    assert isinstance(document.encrypted_content, bytes)


@pytest.mark.asyncio
async def test_document_unique_hash_constraint(db: AsyncSession, admin_user: User):
    """Test that duplicate content_hash is detected (deduplication)."""
    content = b"Duplicate document content"
    content_hash = hashlib.sha256(content).hexdigest()

    # Create first document
    doc1 = Document(
        filename="original.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(doc1)
    await db.commit()

    # Try to create duplicate
    doc2 = Document(
        filename="duplicate.rtf",
        content_type="application/rtf",
        content_hash=content_hash,  # Same hash!
        encrypted_content=content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(doc2)

    # Should raise IntegrityError due to unique constraint
    with pytest.raises(Exception):  # IntegrityError or similar
        await db.commit()


@pytest.mark.asyncio
async def test_document_processing_status_enum(db: AsyncSession, admin_user: User):
    """Test processing status transitions."""
    document = Document(
        filename="processing_test.rtf",
        content_type="application/rtf",
        content_hash=hashlib.sha256(b"test").hexdigest(),
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Verify initial status
    assert document.processing_status == ProcessingStatus.PENDING

    # Update to processing
    document.processing_status = ProcessingStatus.PROCESSING
    await db.commit()
    await db.refresh(document)
    assert document.processing_status == ProcessingStatus.PROCESSING

    # Update to completed
    document.processing_status = ProcessingStatus.COMPLETED
    await db.commit()
    await db.refresh(document)
    assert document.processing_status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_document_uploaded_by_relationship(db: AsyncSession, admin_user: User):
    """Test relationship to user who uploaded the document."""
    document = Document(
        filename="user_test.rtf",
        content_type="application/rtf",
        content_hash=hashlib.sha256(b"test").hexdigest(),
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Verify uploaded_by points to admin_user
    assert document.uploaded_by == admin_user.id


@pytest.mark.asyncio
async def test_document_index_on_content_hash(db: AsyncSession, admin_user: User):
    """Test that content_hash is indexed for fast deduplication lookups."""
    # Create multiple documents
    for i in range(10):
        content = f"Document {i}".encode()
        doc = Document(
            filename=f"doc_{i}.rtf",
            content_type="application/rtf",
            content_hash=hashlib.sha256(content).hexdigest(),
            encrypted_content=content,
            encryption_algorithm="aes-256-gcm",
            file_size=len(content),
            uploaded_by=admin_user.id,
            processing_status=ProcessingStatus.PENDING,
        )
        db.add(doc)

    await db.commit()

    # Query by content_hash (should use index)
    search_hash = hashlib.sha256(b"Document 5").hexdigest()
    result = await db.execute(
        select(Document).where(Document.content_hash == search_hash)
    )
    doc = result.scalar_one_or_none()

    assert doc is not None
    assert doc.filename == "doc_5.rtf"


@pytest.mark.asyncio
async def test_document_processing_failed_status(db: AsyncSession, admin_user: User):
    """Test failed processing status for error handling."""
    document = Document(
        filename="failed_doc.rtf",
        content_type="application/rtf",
        content_hash=hashlib.sha256(b"test").hexdigest(),
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.FAILED,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    assert document.processing_status == ProcessingStatus.FAILED
