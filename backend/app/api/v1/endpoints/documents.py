"""
Documents API endpoints.

Handles document upload with encryption and deduplication.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.document import Document, ProcessingStatus
from app.models.user import User
from app.schemas.document import DocumentUploadResponse
from app.services.audit_service import AuditService
from app.services.deduplication_service import DeduplicationService
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_200_OK)
async def upload_document(
    file: UploadFile = File(..., description="RTF document file"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload clinical document with encryption and deduplication.

    Workflow:
    1. Read file content
    2. Compute SHA-256 hash
    3. Check for duplicates (Redis + Database)
    4. If duplicate: Return existing document ID
    5. If new: Encrypt content with AES-256-GCM
    6. Store in database with status=pending
    7. Log upload action (HIPAA audit trail)
    8. Return document ID and status

    Returns:
        DocumentUploadResponse with document_id, status, is_duplicate flag

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/documents/upload" \\
          -H "Authorization: Bearer $TOKEN" \\
          -F "file=@clinical_note_001.rtf"
        ```
    """
    # Initialize services
    encryption_service = EncryptionService.from_env()
    deduplication_service = DeduplicationService()
    audit_service = AuditService()

    # Read file content
    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file not allowed",
        )

    # Compute SHA-256 hash for deduplication
    content_hash = DeduplicationService.compute_hash(content)

    # Check for duplicates (two-tier: Redis + Database)
    duplicate_id = await deduplication_service.check_duplicate_db(content_hash, db)

    if duplicate_id:
        # Duplicate found - return existing document
        from sqlalchemy import select

        result = await db.execute(select(Document).where(Document.id == duplicate_id))
        existing_doc = result.scalar_one()

        # Audit log: duplicate upload attempt
        await audit_service.log_action(
            db=db,
            user=current_user,
            action="DOCUMENT_UPLOAD_DUPLICATE",
            resource_type="document",
            resource_id=str(duplicate_id),
            details={
                "filename": file.filename,
                "content_hash": content_hash,
                "original_filename": existing_doc.filename,
            },
        )

        return DocumentUploadResponse(
            document_id=duplicate_id,
            filename=existing_doc.filename,
            file_size=existing_doc.file_size,
            content_hash=content_hash,
            status=existing_doc.processing_status.value,
            is_duplicate=True,
            message="Duplicate document detected",
            created_at=existing_doc.created_at,
        )

    # New document - encrypt content
    encrypted_content = encryption_service.encrypt(content)

    # Create document record
    document = Document(
        filename=file.filename or "unknown.rtf",
        content_type=file.content_type or "application/rtf",
        content_hash=content_hash,
        encrypted_content=encrypted_content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=current_user.id,
        project_id=None,  # TODO: Add project support in future
        processing_status=ProcessingStatus.PENDING,
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Update deduplication cache
    await deduplication_service.update_cache(content_hash, document.id)

    # Audit log: successful upload
    await audit_service.log_action(
        db=db,
        user=current_user,
        action="DOCUMENT_UPLOAD",
        resource_type="document",
        resource_id=str(document.id),
        details={
            "filename": file.filename,
            "file_size": len(content),
            "content_hash": content_hash,
        },
    )

    logger.info(
        f"Document uploaded: {document.id} (user={current_user.id}, "
        f"size={len(content)} bytes, hash={content_hash[:16]}...)"
    )

    return DocumentUploadResponse(
        document_id=document.id,
        filename=document.filename,
        file_size=document.file_size,
        content_hash=content_hash,
        status=document.processing_status.value,
        is_duplicate=False,
        message="Document uploaded successfully",
        created_at=document.created_at,
    )
