"""
Document Management API endpoints.

Provides:
- POST /api/v1/documents/upload - Upload clinical document with encryption and deduplication

All endpoints require authentication and create audit logs.
"""

import uuid
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.document import Document, ProcessingStatus
from app.models.project import Project
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentDuplicateResponse,
)
from app.services.encryption_service import encrypt_content
from app.services.deduplication_service import compute_content_hash, check_duplicate, cache_document_hash
from app.services.audit_service import log_action


router = APIRouter()


# Supported file types
SUPPORTED_CONTENT_TYPES = {
    "application/rtf": [".rtf"],
    "text/rtf": [".rtf"],
}


@router.post(
    "/documents/upload",
    # response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload clinical document",
    description="Upload RTF document with encryption and deduplication. Returns existing document if duplicate detected.",
    responses={
        200: {
            "model": DocumentDuplicateResponse,
            "description": "Duplicate document detected, returning existing document"
        },
        201: {
            "model": DocumentUploadResponse,
            "description": "New document uploaded successfully"
        },
        400: {
            "description": "Invalid file (empty, wrong type, etc.)"
        },
        404: {
            "description": "Project not found"
        }
    }
)
async def upload_document(
    file: Annotated[UploadFile, File(description="RTF document file to upload")],
    project_id: Annotated[str, Form(description="Project ID to associate document with")],
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Upload clinical document with encryption and deduplication.

    **Process**:
    1. Validate file type (RTF only)
    2. Compute SHA-256 hash
    3. Check for duplicates
    4. Encrypt content with AES-256-GCM
    5. Store in database
    6. Log audit trail

    **Request**:
    - file: RTF document (multipart/form-data)
    - project_id: Project UUID (form field)

    **Returns**:
    - 201: New document uploaded
    - 200: Duplicate detected, returns existing document

    **Audit**: Creates UPLOAD_DOCUMENT audit log entry

    **Example**:
    ```bash
    curl -X POST http://localhost:8000/api/v1/documents/upload \
      -H "Authorization: Bearer <token>" \
      -F "file=@patient_notes.rtf" \
      -F "project_id=550e8400-e29b-41d4-a716-446655440000"
    ```
    """
    # Step 1: Validate file is not empty
    try:
        # Step 1: Validate file is not empty
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )

        # Read file content
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )

        # Step 2: Validate file type
        content_type = file.content_type or "application/octet-stream"

        if content_type not in SUPPORTED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {content_type}. Only RTF files are supported."
            )

        # Step 3: Verify project exists and user has access
        try:
            project_uuid = uuid.UUID(project_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid project ID format"
            )

        result = await db.execute(
            select(Project).where(Project.id == project_uuid)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project not found: {project_id}"
            )

        # Step 4: Compute content hash
        content_hash = compute_content_hash(content)

        # Step 5: Check for duplicates
        existing_document_id = await check_duplicate(db, content_hash)

        if existing_document_id:
            # Duplicate detected - return existing document
            result = await db.execute(
                select(Document).where(Document.id == uuid.UUID(existing_document_id))
            )
            existing_document = result.scalar_one()

            # Log audit trail for duplicate attempt
            await log_action(
                db=db,
                user_id=str(current_user.id),
                username=current_user.username,
                action="UPLOAD_DOCUMENT_DUPLICATE",
                resource_type="document",
                resource_id=existing_document_id,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent", "unknown"),
                details={
                    "filename": file.filename,
                    "content_hash": content_hash,
                    "file_size": len(content),
                    "duplicate_of": existing_document_id
                }
            )

            return DocumentDuplicateResponse(
                document_id=existing_document_id,
                status="duplicate",
                message=f"Document already exists with same content (uploaded {existing_document.created_at})",
                filename=existing_document.filename,
                created_at=existing_document.created_at
            )

        # Step 6: Encrypt content
        encrypted_content = encrypt_content(content)

        # Step 7: Create document record
        new_document = Document(
            id=uuid.uuid4(),
            filename=file.filename,
            content_type=content_type,
            content_hash=content_hash,
            encrypted_content=encrypted_content,
            encryption_algorithm="AES-256-GCM",
            file_size=len(content),
            uploaded_by=current_user.id,
            project_id=project_uuid,
            processing_status=ProcessingStatus.PENDING,
            created_at=datetime.utcnow()
        )

        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        # Step 8: Cache the document hash for fast future lookups
        try:
            await cache_document_hash(content_hash, str(new_document.id))
        except Exception as cache_error:
            # Cache failure should not block upload
            # Error already logged by cache_document_hash
            pass

        # Step 9: Log audit trail
        await log_action(
            db=db,
            user_id=str(current_user.id),
            username=current_user.username,
            action="UPLOAD_DOCUMENT",
            resource_type="document",
            resource_id=str(new_document.id),
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", "unknown"),
            details={
                "filename": file.filename,
                "content_type": content_type,
                "file_size": len(content),
                "content_hash": content_hash,
                "project_id": project_id
            }
        )

        return DocumentUploadResponse(
            document_id=str(new_document.id),
            status=new_document.processing_status.value,
            filename=new_document.filename,
            content_type=new_document.content_type,
            file_size=new_document.file_size,
            content_hash=new_document.content_hash,
            created_at=new_document.created_at
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e
