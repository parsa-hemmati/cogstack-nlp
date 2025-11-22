"""
Document Router

API endpoints for document management, upload, and NLP processing.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.dependencies import get_current_user, require_role
from app.models.user import User
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, DocumentWithContent,
    DocumentFilter, DocumentProcessRequest, DocumentEntitiesResponse,
    ExtractedEntityResponse
)
from app.services.document_service import DocumentService
from app.services.audit_service import AuditService
from app.services.nlp_service import NLPService
from app.services.phi_classifier import PHIClassifier
from app.services.phi_extraction_service import PHIExtractionService
from app.services.patient_service import PatientService
from app.clients.cogstack_client import CogStackClient
from app.config import Settings

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["documents"]
)

settings = Settings()


async def get_document_service(db: AsyncSession = Depends(get_async_db)) -> DocumentService:
    """Get document service instance."""
    audit_service = AuditService(db)
    return DocumentService(db, audit_service)


async def get_nlp_service(db: AsyncSession = Depends(get_async_db)) -> NLPService:
    """Get NLP service instance."""
    cogstack_client = CogStackClient(settings)
    audit_service = AuditService(db)
    document_service = await get_document_service(db)
    return NLPService(db, cogstack_client, audit_service, document_service)


async def get_patient_service(db: AsyncSession = Depends(get_async_db)) -> PatientService:
    """Get patient service instance."""
    audit_service = AuditService(db)
    phi_classifier = PHIClassifier()
    phi_extraction_service = PHIExtractionService(db, phi_classifier, audit_service)
    return PatientService(db, audit_service, phi_extraction_service)


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: UUID = Form(...),
    document_type: Optional[str] = Form(None),
    author: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Upload and encrypt a clinical document.

    Accepts RTF, TXT, and PDF files up to 10MB.
    Documents are encrypted with AES-256 before storage.

    Args:
        file: File to upload
        project_id: Project to associate with
        document_type: Type of document (optional)
        author: Document author (optional)
        current_user: Authenticated user
        service: Document service

    Returns:
        Created document response

    Raises:
        HTTPException: 400 if invalid file, 409 if duplicate
    """
    return await service.upload_document(
        file=file,
        project_id=project_id,
        user=current_user,
        document_type=document_type,
        author=author
    )


@router.get("/", response_model=DocumentListResponse)
async def list_documents(
    project_id: Optional[UUID] = None,
    medcat_status: Optional[str] = None,
    document_type: Optional[str] = None,
    contains_phi: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
) -> DocumentListResponse:
    """
    List documents with filtering and pagination.

    Args:
        project_id: Filter by project
        medcat_status: Filter by processing status
        document_type: Filter by document type
        contains_phi: Filter by PHI presence
        page: Page number
        page_size: Items per page
        current_user: Authenticated user
        service: Document service

    Returns:
        Paginated list of documents
    """
    filter = DocumentFilter(
        medcat_status=medcat_status,
        document_type=document_type,
        contains_phi=contains_phi
    )

    documents, total = await service.list_documents(
        user=current_user,
        project_id=project_id,
        filter=filter,
        page=page,
        page_size=page_size
    )

    return DocumentListResponse(
        documents=documents,
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
) -> DocumentResponse:
    """
    Get document metadata by ID.

    Args:
        document_id: Document ID
        current_user: Authenticated user
        service: Document service

    Returns:
        Document metadata (without content)

    Raises:
        HTTPException: 404 if not found
    """
    return await service.get_document(
        document_id=document_id,
        user=current_user,
        include_content=False
    )


@router.get("/{document_id}/content", response_model=DocumentWithContent)
async def get_document_with_content(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service)
) -> DocumentWithContent:
    """
    Get document with decrypted content.

    Decrypts document content for viewing. This operation is audit logged.

    Args:
        document_id: Document ID
        current_user: Authenticated user
        service: Document service

    Returns:
        Document with decrypted content

    Raises:
        HTTPException: 404 if not found, 500 if decryption fails
    """
    return await service.get_document(
        document_id=document_id,
        user=current_user,
        include_content=True
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    soft_delete: bool = True,
    current_user: User = Depends(get_current_user),
    _: User = Depends(require_role(["admin", "project_owner"])),
    service: DocumentService = Depends(get_document_service)
) -> None:
    """
    Delete a document (soft delete by default).

    Args:
        document_id: Document ID
        soft_delete: Whether to soft delete or hard delete
        current_user: Authenticated user
        service: Document service

    Raises:
        HTTPException: 404 if not found, 403 if unauthorized
    """
    success = await service.delete_document(
        document_id=document_id,
        user=current_user,
        soft_delete=soft_delete
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )


@router.post("/{document_id}/process")
async def process_document(
    document_id: UUID,
    request: DocumentProcessRequest = DocumentProcessRequest(),
    current_user: User = Depends(get_current_user),
    nlp_service: NLPService = Depends(get_nlp_service),
    patient_service: PatientService = Depends(get_patient_service)
) -> dict:
    """
    Process document with NLP to extract entities.

    Extracts medical entities using SNOMED-CT and detects PHI using DeID model.
    Also attempts to aggregate patient information from extracted PHI.

    Args:
        document_id: Document to process
        request: Processing options
        current_user: Authenticated user
        nlp_service: NLP service
        patient_service: Patient service

    Returns:
        Processing results including entity counts

    Raises:
        HTTPException: 404 if document not found, 500 if processing fails
    """
    try:
        # Process document with NLP
        result = await nlp_service.process_document(
            document_id=document_id,
            user_id=current_user.id,
            force_reprocess=request.force_reprocess
        )

        # Try to aggregate patient from document
        if result["status"] == "success":
            patient = await patient_service.aggregate_patient_from_document(
                document_id=document_id,
                user_id=current_user.id
            )

            if patient:
                result["patient_id"] = str(patient.id)
                result["patient_matched"] = True
            else:
                result["patient_matched"] = False

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.get("/{document_id}/entities", response_model=DocumentEntitiesResponse)
async def get_document_entities(
    document_id: UUID,
    include_phi: bool = True,
    entity_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    nlp_service: NLPService = Depends(get_nlp_service)
) -> DocumentEntitiesResponse:
    """
    Get entities extracted from a document.

    Args:
        document_id: Document ID
        include_phi: Whether to include PHI entities
        entity_type: Filter by entity type
        current_user: Authenticated user
        nlp_service: NLP service

    Returns:
        Extracted entities from the document

    Raises:
        HTTPException: 404 if document not found
    """
    entities = await nlp_service.get_document_entities(
        document_id=document_id,
        include_phi=include_phi,
        entity_type=entity_type
    )

    # Convert to response format
    entity_responses = [
        ExtractedEntityResponse.model_validate(entity)
        for entity in entities
    ]

    phi_count = sum(1 for e in entities if e.is_phi)
    clinical_count = len(entities) - phi_count

    return DocumentEntitiesResponse(
        document_id=document_id,
        entities=entity_responses,
        total_entities=len(entities),
        phi_entities_count=phi_count,
        clinical_entities_count=clinical_count
    )


@router.post("/batch/process")
async def batch_process_documents(
    document_ids: list[UUID],
    current_user: User = Depends(get_current_user),
    nlp_service: NLPService = Depends(get_nlp_service)
) -> list[dict]:
    """
    Process multiple documents in batch.

    Args:
        document_ids: List of document IDs to process
        current_user: Authenticated user
        nlp_service: NLP service

    Returns:
        List of processing results

    Raises:
        HTTPException: 400 if too many documents (max 50)
    """
    if len(document_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 documents can be processed at once"
        )

    results = await nlp_service.batch_process_documents(
        document_ids=document_ids,
        user_id=current_user.id,
        batch_size=5
    )

    return results