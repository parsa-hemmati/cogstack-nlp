"""
Integration tests for Documents API.

Tests document upload with encryption and deduplication.
"""
import pytest
import hashlib
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.models.audit_log import AuditLog
from app.models.user import User


@pytest.mark.asyncio
async def test_upload_new_document(client, admin_token, db: AsyncSession):
    """Test uploading a new document."""
    content = b"This is a test clinical document with patient data."

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test_document.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "document_id" in data
    assert data["status"] == "pending"  # Processing not started yet
    assert data["is_duplicate"] is False
    assert data["filename"] == "test_document.rtf"

    # Verify document in database
    result = await db.execute(
        select(Document).where(Document.id == data["document_id"])
    )
    doc = result.scalar_one()

    assert doc.filename == "test_document.rtf"
    assert doc.processing_status == ProcessingStatus.PENDING
    assert doc.encrypted_content != content  # Should be encrypted
    assert doc.content_hash == hashlib.sha256(content).hexdigest()


@pytest.mark.asyncio
async def test_upload_duplicate_document(client, admin_token, db: AsyncSession, admin_user: User):
    """Test uploading duplicate document (same content)."""
    content = b"Duplicate document content for testing."
    content_hash = hashlib.sha256(content).hexdigest()

    # Create original document manually
    original_doc = Document(
        filename="original.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,  # Simplified for test
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(original_doc)
    await db.commit()
    await db.refresh(original_doc)

    # Try to upload duplicate
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("duplicate.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["is_duplicate"] is True
    assert data["document_id"] == str(original_doc.id)
    assert data["status"] == "completed"  # Original status


@pytest.mark.asyncio
async def test_upload_document_encrypted_in_database(
    client, admin_token, db: AsyncSession
):
    """Test document content is encrypted before storage."""
    plaintext = b"Sensitive patient information."

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("sensitive.rtf", plaintext, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify encryption in database
    result = await db.execute(
        select(Document).where(Document.id == data["document_id"])
    )
    doc = result.scalar_one()

    # Encrypted content should NOT equal plaintext
    assert doc.encrypted_content != plaintext
    # Should have IV prepended (12 bytes for AES-GCM)
    assert len(doc.encrypted_content) >= 12 + len(plaintext)


@pytest.mark.asyncio
async def test_upload_document_audit_logged(client, admin_token, db: AsyncSession, admin_user: User):
    """Test document upload is audit logged (HIPAA compliance)."""
    content = b"Document for audit logging test."

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("audit_test.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Verify audit log entry
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.action == "DOCUMENT_UPLOAD",
            AuditLog.resource_id == data["document_id"],
        )
    )
    audit_entry = result.scalar_one()

    assert audit_entry.user_id == admin_user.id
    assert audit_entry.action == "DOCUMENT_UPLOAD"
    assert audit_entry.resource_type == "document"
    assert audit_entry.success == "success"
    assert audit_entry.details["filename"] == "audit_test.rtf"


@pytest.mark.asyncio
async def test_upload_document_requires_authentication(client):
    """Test upload requires valid JWT token."""
    content = b"Test document."

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.rtf", content, "application/rtf")},
        # No Authorization header
    )

    assert response.status_code == 401  # Unauthorized


@pytest.mark.asyncio
async def test_upload_document_returns_hash(client, admin_token):
    """Test upload response includes content hash."""
    content = b"Document for hash verification."
    expected_hash = hashlib.sha256(content).hexdigest()

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("hash_test.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["content_hash"] == expected_hash


@pytest.mark.asyncio
async def test_upload_empty_document(client, admin_token):
    """Test uploading empty document fails gracefully."""
    content = b""

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("empty.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    # Should either succeed with empty content or return 400
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_upload_large_document(client, admin_token):
    """Test uploading large document (5MB)."""
    content = b"A" * (5 * 1024 * 1024)  # 5MB

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("large_doc.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["file_size"] == 5 * 1024 * 1024


@pytest.mark.asyncio
async def test_upload_document_sets_processing_status_pending(
    client, admin_token, db: AsyncSession
):
    """Test uploaded document has status=pending (ready for background processing)."""
    content = b"Document for status test."

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("status_test.rtf", content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "pending"

    # Verify in database
    result = await db.execute(
        select(Document).where(Document.id == data["document_id"])
    )
    doc = result.scalar_one()

    assert doc.processing_status == ProcessingStatus.PENDING
