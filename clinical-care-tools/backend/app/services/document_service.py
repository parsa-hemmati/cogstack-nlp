"""
Document Service

Business logic for document management including upload, storage, and retrieval.
Implements AES-256 encryption for PHI protection.
"""

import hashlib
from typing import List, Optional, Tuple
from datetime import datetime
from uuid import UUID
import io

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from fastapi import UploadFile, HTTPException
import structlog

from app.models.document import Document
from app.models.user import User
from app.models.project import Project
from app.schemas.document import (
    DocumentUpload, DocumentResponse, DocumentFilter,
    DocumentWithContent, FileType
)
from app.utils.encryption import encrypt_document, decrypt_document
from app.services.audit_service import AuditService

logger = structlog.get_logger()


class DocumentService:
    """
    Service for managing clinical documents with encryption.

    Provides methods for:
    - Uploading and encrypting documents
    - Retrieving and decrypting documents
    - Document deduplication by content hash
    - Audit logging for PHI access
    """

    def __init__(self, db: AsyncSession, audit_service: AuditService):
        """
        Initialize document service.

        Args:
            db: Database session
            audit_service: Audit logging service
        """
        self.db = db
        self.audit = audit_service

    async def upload_document(
        self,
        file: UploadFile,
        project_id: UUID,
        user: User,
        document_type: Optional[str] = None,
        document_date: Optional[datetime] = None,
        author: Optional[str] = None
    ) -> DocumentResponse:
        """
        Upload and encrypt a document.

        Args:
            file: Uploaded file
            project_id: Project to associate with
            user: User uploading the document
            document_type: Type of document
            document_date: Date on the document
            author: Document author

        Returns:
            DocumentResponse with created document

        Raises:
            HTTPException: If upload fails
        """
        try:
            # Validate file type
            file_extension = file.filename.split('.')[-1].lower()
            if file_extension not in ['rtf', 'txt', 'pdf']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file type: {file_extension}"
                )

            # Read file content
            content = await file.read()

            # Validate file size (10MB max)
            max_size_mb = 10
            max_size_bytes = max_size_mb * 1024 * 1024
            if len(content) > max_size_bytes:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds maximum of {max_size_mb}MB"
                )

            if len(content) == 0:
                raise HTTPException(
                    status_code=400,
                    detail="File content cannot be empty"
                )

            # Check for duplicate by content hash
            content_hash = self._compute_content_hash(content)
            existing = await self._find_duplicate(content_hash, project_id)
            if existing:
                raise HTTPException(
                    status_code=409,
                    detail=f"Duplicate document already exists: {existing.filename}"
                )

            # Verify project exists
            project = await self.db.get(Project, project_id)
            if not project:
                raise HTTPException(
                    status_code=404,
                    detail=f"Project {project_id} not found"
                )

            # Create document record
            document = Document(
                project_id=project_id,
                uploaded_by=user.id,
                filename=file.filename,
                file_type=file_extension,
                file_size=len(content),
                content_hash=content_hash,
                document_type=document_type,
                document_date=document_date,
                author=author,
                medcat_status="pending",
                contains_phi=True,  # Always true for clinical documents
                phi_types=["NHS_NUMBER", "NAME", "ADDRESS", "DOB"]  # Default assumption
            )

            # Encrypt content
            encrypted_blob, key_id = encrypt_document(content, str(document.id))
            document.content = encrypted_blob
            document.encryption_key_id = key_id

            # Save to database
            self.db.add(document)
            await self.db.commit()
            await self.db.refresh(document)

            # Audit log
            await self.audit.log_document_upload(
                user_id=user.id,
                document_id=document.id,
                filename=file.filename,
                file_size=len(content)
            )

            logger.info(
                "Document uploaded successfully",
                document_id=str(document.id),
                filename=file.filename,
                user_id=str(user.id)
            )

            return DocumentResponse.model_validate(document)

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("Document upload failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Document upload failed: {str(e)}"
            )

    async def get_document(
        self,
        document_id: UUID,
        user: User,
        include_content: bool = False
    ) -> DocumentResponse | DocumentWithContent:
        """
        Get document by ID with optional content decryption.

        Args:
            document_id: Document ID
            user: User requesting the document
            include_content: Whether to include decrypted content

        Returns:
            DocumentResponse or DocumentWithContent

        Raises:
            HTTPException: If document not found or access denied
        """
        # Get document
        document = await self.db.get(Document, document_id)
        if not document:
            raise HTTPException(
                status_code=404,
                detail=f"Document {document_id} not found"
            )

        # NOTE: Check user permissions (RBAC)

        # Audit log PHI access
        await self.audit.log_phi_access(
            user_id=user.id,
            resource_type="document",
            resource_id=document_id,
            action="view"
        )

        if include_content:
            # Decrypt content
            try:
                decrypted_content = decrypt_document(
                    document.content,
                    document.encryption_key_id
                )
                # Convert bytes to string
                content_str = decrypted_content.decode('utf-8', errors='replace')

                return DocumentWithContent(
                    **DocumentResponse.model_validate(document).model_dump(),
                    content=content_str
                )
            except Exception as e:
                logger.error(
                    "Document decryption failed",
                    document_id=str(document_id),
                    error=str(e)
                )
                raise HTTPException(
                    status_code=500,
                    detail="Failed to decrypt document content"
                )
        else:
            return DocumentResponse.model_validate(document)

    async def list_documents(
        self,
        user: User,
        project_id: Optional[UUID] = None,
        filter: Optional[DocumentFilter] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[DocumentResponse], int]:
        """
        List documents with filtering and pagination.

        Args:
            user: User requesting documents
            project_id: Filter by project
            filter: Additional filter criteria
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (documents, total_count)

        Raises:
            HTTPException: If query fails
        """
        try:
            # Build query
            query = select(Document)

            # Apply filters
            conditions = []
            if project_id:
                conditions.append(Document.project_id == project_id)

            if filter:
                if filter.medcat_status:
                    conditions.append(Document.medcat_status == filter.medcat_status.value)
                if filter.document_type:
                    conditions.append(Document.document_type == filter.document_type)
                if filter.contains_phi is not None:
                    conditions.append(Document.contains_phi == filter.contains_phi)
                if filter.start_date:
                    conditions.append(Document.uploaded_at >= filter.start_date)
                if filter.end_date:
                    conditions.append(Document.uploaded_at <= filter.end_date)

            if conditions:
                query = query.where(and_(*conditions))

            # Get total count
            count_query = select(func.count()).select_from(Document)
            if conditions:
                count_query = count_query.where(and_(*conditions))
            total_count = await self.db.scalar(count_query)

            # Apply pagination
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
            query = query.order_by(Document.uploaded_at.desc())

            # Execute query
            result = await self.db.execute(query)
            documents = result.scalars().all()

            # Audit log
            await self.audit.log_phi_access(
                user_id=user.id,
                resource_type="document_list",
                resource_id=None,
                action="list"
            )

            return (
                [DocumentResponse.model_validate(doc) for doc in documents],
                total_count
            )

        except Exception as e:
            logger.error("Document list query failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list documents: {str(e)}"
            )

    async def delete_document(
        self,
        document_id: UUID,
        user: User,
        soft_delete: bool = True
    ) -> bool:
        """
        Delete document (soft delete by default).

        Args:
            document_id: Document ID
            user: User deleting the document
            soft_delete: Whether to soft delete (mark as deleted) or hard delete

        Returns:
            True if deleted successfully

        Raises:
            HTTPException: If document not found or deletion fails
        """
        try:
            # Get document
            document = await self.db.get(Document, document_id)
            if not document:
                raise HTTPException(
                    status_code=404,
                    detail=f"Document {document_id} not found"
                )

            # NOTE: Check user permissions

            if soft_delete:
                # Mark as deleted (would need to add deleted_at field)
                document.medcat_status = "deleted"
                await self.db.commit()
            else:
                # Hard delete
                await self.db.delete(document)
                await self.db.commit()

            # Audit log
            await self.audit.log_document_deletion(
                user_id=user.id,
                document_id=document_id,
                soft_delete=soft_delete
            )

            logger.info(
                "Document deleted",
                document_id=str(document_id),
                soft_delete=soft_delete
            )

            return True

        except HTTPException:
            await self.db.rollback()
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error("Document deletion failed", error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {str(e)}"
            )

    async def update_processing_status(
        self,
        document_id: UUID,
        status: str,
        error: Optional[str] = None
    ) -> None:
        """
        Update document processing status.

        Args:
            document_id: Document ID
            status: New status
            error: Error message if failed
        """
        document = await self.db.get(Document, document_id)
        if document:
            document.medcat_status = status
            if status == "complete":
                document.medcat_processed_at = datetime.utcnow()
            if error:
                document.medcat_error = error
            await self.db.commit()

    def _compute_content_hash(self, content: bytes) -> str:
        """
        Compute SHA-256 hash of content for deduplication.

        Args:
            content: Document content

        Returns:
            Hex string of hash
        """
        hash_obj = hashlib.sha256()
        hash_obj.update(content)
        return hash_obj.hexdigest()

    async def _find_duplicate(
        self,
        content_hash: str,
        project_id: UUID
    ) -> Optional[Document]:
        """
        Find duplicate document by content hash.

        Args:
            content_hash: SHA-256 hash of content
            project_id: Project ID

        Returns:
            Document if duplicate found, None otherwise
        """
        query = select(Document).where(
            and_(
                Document.content_hash == content_hash,
                Document.project_id == project_id,
                Document.medcat_status != "deleted"
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()