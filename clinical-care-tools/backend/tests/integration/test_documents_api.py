"""
Integration tests for Documents API endpoints.

Tests:
- POST /api/v1/documents/upload (upload document with encryption and deduplication)
- Document content encryption
- SHA-256 content hash deduplication
- Audit logging for uploads
- Permission checks (project access)
"""

import pytest
import hashlib
from httpx import AsyncClient
from io import BytesIO

from app.models.document import Document, ProcessingStatus
from app.models.project import Project
from app.models.audit_log import AuditLog
from sqlalchemy import select


pytestmark = pytest.mark.asyncio


async def test_upload_document_returns_201(admin_client: AsyncClient, db_session, test_admin):
    """Test that uploading new document returns 201 with processing status."""
    # Create project first
    project = Project(
        name="Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Create RTF file content
    rtf_content = b"{\\rtf1\\ansi Patient clinical notes: Diabetes diagnosis.}"

    # Upload document
    files = {
        "file": ("test_document.rtf", BytesIO(rtf_content), "application/rtf")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)

    assert response.status_code == 201, \
        "Uploading new document should return 201"

    result = response.json()
    assert "document_id" in result
    assert result["status"] == "pending"
    assert result["filename"] == "test_document.rtf"
    assert result["file_size"] == len(rtf_content)
    assert result["content_type"] == "application/rtf"


async def test_upload_document_encrypts_content(admin_client: AsyncClient, db_session, test_admin):
    """Test that uploaded document content is encrypted in database."""
    # Create project
    project = Project(
        name="Encryption Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Original content
    original_content = b"{\\rtf1\\ansi Sensitive patient data: medical history.}"

    # Upload document
    files = {
        "file": ("patient_data.rtf", BytesIO(original_content), "application/rtf")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201

    document_id = response.json()["document_id"]

    # Verify document in database
    result = await db_session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one()

    # Encrypted content should NOT equal original content
    assert document.encrypted_content != original_content, \
        "Document content should be encrypted"

    # Encrypted content should be longer (includes IV and auth tag)
    assert len(document.encrypted_content) > len(original_content)

    # Encryption algorithm should be set
    assert document.encryption_algorithm == "AES-256-GCM"


async def test_upload_document_stores_content_hash(admin_client: AsyncClient, db_session, test_admin):
    """Test that SHA-256 content hash is stored for deduplication."""
    # Create project
    project = Project(
        name="Hash Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Content and expected hash
    content = b"{\\rtf1\\ansi Test document content.}"
    expected_hash = hashlib.sha256(content).hexdigest()

    # Upload document
    files = {
        "file": ("test.rtf", BytesIO(content), "application/rtf")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201

    document_id = response.json()["document_id"]

    # Verify hash in database
    result = await db_session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one()

    assert document.content_hash == expected_hash
    assert len(document.content_hash) == 64  # SHA-256 hex string


async def test_upload_duplicate_document_returns_existing(admin_client: AsyncClient, db_session, test_admin):
    """Test that uploading duplicate document returns existing document ID."""
    # Create project
    project = Project(
        name="Dedup Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Same content for both uploads
    content = b"{\\rtf1\\ansi Duplicate document content.}"

    # Upload first document
    files1 = {
        "file": ("first.rtf", BytesIO(content), "application/rtf")
    }
    data1 = {
        "project_id": str(project.id)
    }

    response1 = await admin_client.post("/api/v1/documents/upload", files=files1, data=data1)
    assert response1.status_code == 201

    first_document_id = response1.json()["document_id"]

    # Upload second document with same content
    files2 = {
        "file": ("second.rtf", BytesIO(content), "application/rtf")
    }
    data2 = {
        "project_id": str(project.id)
    }

    response2 = await admin_client.post("/api/v1/documents/upload", files=files2, data=data2)

    # Should return 200 (not 201) for duplicate
    assert response2.status_code == 200, \
        "Uploading duplicate should return 200"

    result = response2.json()
    assert result["status"] == "duplicate"
    assert result["document_id"] == first_document_id
    assert "message" in result

    # Verify only one document in database
    count_result = await db_session.execute(
        select(Document).where(Document.content_hash == hashlib.sha256(content).hexdigest())
    )
    documents = count_result.scalars().all()
    assert len(documents) == 1


async def test_upload_document_creates_audit_log(admin_client: AsyncClient, db_session, test_admin):
    """Test that uploading document creates audit log entry."""
    # Create project
    project = Project(
        name="Audit Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Upload document
    content = b"{\\rtf1\\ansi Audit test content.}"
    files = {
        "file": ("audit_test.rtf", BytesIO(content), "application/rtf")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201

    document_id = response.json()["document_id"]

    # Check audit log
    result = await db_session.execute(
        select(AuditLog)
        .where(AuditLog.action == "UPLOAD_DOCUMENT")
        .where(AuditLog.resource_id == document_id)
        .where(AuditLog.user_id == str(test_admin.id))
    )
    audit_log = result.scalar_one_or_none()

    assert audit_log is not None, \
        "Audit log should be created for document upload"
    assert audit_log.resource_type == "document"


async def test_upload_document_without_auth_returns_401(client: AsyncClient):
    """Test that uploading without authentication returns 401."""
    content = b"{\\rtf1\\ansi Test.}"
    files = {
        "file": ("test.rtf", BytesIO(content), "application/rtf")
    }
    data = {
        "project_id": "550e8400-e29b-41d4-a716-446655440000"
    }

    response = await client.post("/api/v1/documents/upload", files=files, data=data)

    assert response.status_code == 401


async def test_upload_document_to_nonexistent_project_returns_404(admin_client: AsyncClient):
    """Test that uploading to non-existent project returns 404."""
    content = b"{\\rtf1\\ansi Test.}"
    files = {
        "file": ("test.rtf", BytesIO(content), "application/rtf")
    }
    data = {
        "project_id": "00000000-0000-0000-0000-000000000000"  # Non-existent
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)

    assert response.status_code == 404
    assert "Project not found" in response.json()["detail"]


async def test_upload_unsupported_file_type_returns_400(admin_client: AsyncClient, db_session, test_admin):
    """Test that uploading unsupported file type returns 400."""
    # Create project
    project = Project(
        name="File Type Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Upload non-RTF file
    content = b"<html><body>Not an RTF file</body></html>"
    files = {
        "file": ("test.html", BytesIO(content), "text/html")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)

    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


async def test_upload_document_sets_metadata_correctly(admin_client: AsyncClient, db_session, test_admin):
    """Test that document metadata is correctly stored."""
    # Create project
    project = Project(
        name="Metadata Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Upload document
    content = b"{\\rtf1\\ansi Metadata test.}"
    filename = "metadata_test.rtf"
    files = {
        "file": (filename, BytesIO(content), "application/rtf")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)
    assert response.status_code == 201

    document_id = response.json()["document_id"]

    # Verify metadata
    result = await db_session.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one()

    assert document.filename == filename
    assert document.content_type == "application/rtf"
    assert document.file_size == len(content)
    assert document.uploaded_by == test_admin.id
    assert document.project_id == project.id
    assert document.processing_status == ProcessingStatus.PENDING
    assert document.created_at is not None


async def test_upload_empty_file_returns_400(admin_client: AsyncClient, db_session, test_admin):
    """Test that uploading empty file returns 400."""
    # Create project
    project = Project(
        name="Empty File Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # Upload empty file
    files = {
        "file": ("empty.rtf", BytesIO(b""), "application/rtf")
    }
    data = {
        "project_id": str(project.id)
    }

    response = await admin_client.post("/api/v1/documents/upload", files=files, data=data)

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
