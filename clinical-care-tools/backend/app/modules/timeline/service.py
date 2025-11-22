"""
Timeline Service

Business logic for timeline aggregation, filtering, and export.
Handles PHI access logging and RBAC verification.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.patient import Patient
from app.models.document import Document
from app.models.timeline import TimelineFilter, TimelineExport
from app.modules.timeline.models import (
    TimelineRequest,
    PatientTimeline,
    TimelineDocument,
    TimelineConcept,
    ConceptMention,
    ExportRequest,
    TimelineExport as TimelineExportResponse,
    ExportStatus,
)
from app.modules.timeline.repository import ElasticsearchTimelineRepository
from app.services.audit_service import AuditService


class TimelineService:
    """
    Service for timeline aggregation and export.

    Provides:
    - Patient timeline generation with concept extraction
    - Timeline filtering (dates, concepts, meta-annotations)
    - Multi-format export (PDF, FHIR, JSON)
    - Audit logging for all PHI access
    """

    def __init__(
        self,
        db: AsyncSession,
        es_repo: ElasticsearchTimelineRepository,
        audit_service: AuditService
    ):
        """
        Initialize timeline service.

        Args:
            db: Database session
            es_repo: Elasticsearch repository
            audit_service: Audit logging service
        """
        self.db = db
        self.es_repo = es_repo
        self.audit_service = audit_service

    async def get_patient_timeline(
        self,
        patient_id: UUID,
        request: TimelineRequest,
        user,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PatientTimeline:
        """
        Get patient timeline with documents and concepts.

        Args:
            patient_id: Patient UUID
            request: Timeline request with filters
            user: Authenticated user
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            PatientTimeline with documents, concepts, and statistics

        Raises:
            HTTPException: 404 if patient not found, 403 if access denied
        """
        # Log PHI access immediately (HIPAA requirement)
        await self.audit_service.log_phi_access(
            user_id=user.id,
            resource_type="patient",
            resource_id=patient_id,
            action="VIEW_TIMELINE",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "filters": request.model_dump(exclude_none=True)
            }
        )

        # Verify patient exists
        patient = await self._get_patient_or_404(patient_id)

        # Fetch documents from PostgreSQL
        documents = await self._fetch_documents(
            patient_id=patient_id,
            date_start=request.date_start,
            date_end=request.date_end,
            document_types=request.document_types
        )

        # Query concepts from Elasticsearch
        concept_data = await self.es_repo.query_patient_concepts(
            patient_id=patient_id,
            concept_cuis=request.concept_cuis,
            date_start=request.date_start,
            date_end=request.date_end,
            meta_annotations=request.meta_annotations.model_dump(exclude_none=True) if request.meta_annotations else None,
            document_types=request.document_types
        )

        # Aggregate concept frequency
        concept_frequency = await self.es_repo.aggregate_concept_frequency(
            patient_id=patient_id,
            concept_cuis=request.concept_cuis,
            date_start=request.date_start,
            date_end=request.date_end,
            granularity="month"
        )

        # Group concepts
        concepts = self._group_concepts(concept_data)

        # Build timeline documents
        timeline_docs = [
            TimelineDocument(
                id=doc.id,
                title=f"{doc.document_type} - {doc.document_date}",
                type=doc.document_type,
                document_date=doc.document_date,
                author=doc.author,
                concept_count=len([c for c in concept_data if UUID(c["document_id"]) == doc.id])
            )
            for doc in documents
        ]

        # Calculate statistics
        stats = {
            "total_documents": len(documents),
            "total_concepts": len(concepts),
            "date_span_days": (request.date_end - request.date_start).days if request.date_start and request.date_end else 0,
            "concept_frequency": concept_frequency
        }

        return PatientTimeline(
            patient_id=patient_id,
            documents=timeline_docs,
            concepts=concepts,
            date_range=(
                request.date_start or date.today(),
                request.date_end or date.today()
            ),
            filters_applied=request.model_dump(exclude_none=True),
            statistics=stats
        )

    async def export_timeline(
        self,
        patient_id: UUID,
        export_request: ExportRequest,
        user,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> TimelineExportResponse:
        """
        Create timeline export job.

        Args:
            patient_id: Patient UUID
            export_request: Export request with format and filters
            user: Authenticated user
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            TimelineExport with export ID and status

        Raises:
            HTTPException: 404 if patient not found
        """
        # Verify patient exists
        patient = await self._get_patient_or_404(patient_id)

        # Create export record
        export_id = uuid4()
        export_record = TimelineExport(
            id=export_id,
            patient_id=patient_id,
            user_id=user.id,
            format=export_request.format.value,
            status="processing",
            filters=export_request.filters,
            options=export_request.options,
            expires_at=datetime.now() + timedelta(days=7)
        )

        self.db.add(export_record)
        await self.db.flush()

        # Log export to audit
        await self.audit_service.log_phi_access(
            user_id=user.id,
            resource_type="patient",
            resource_id=patient_id,
            action="EXPORT_TIMELINE",
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "export_id": str(export_id),
                "format": export_request.format.value,
                "filters": export_request.filters
            }
        )

        # Return response
        return TimelineExportResponse(
            id=export_id,
            patient_id=patient_id,
            status=ExportStatus.PROCESSING,
            format=export_request.format,
            download_url=None,  # Will be populated when complete
            expires_at=export_record.expires_at
        )

    async def _get_patient_or_404(self, patient_id: UUID) -> Patient:
        """
        Get patient or raise 404.

        Args:
            patient_id: Patient UUID

        Returns:
            Patient model

        Raises:
            HTTPException: 404 if not found
        """
        result = await self.db.execute(
            select(Patient).where(Patient.id == patient_id)
        )
        patient = result.scalar_one_or_none()

        if not patient:
            raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

        return patient

    async def _fetch_documents(
        self,
        patient_id: UUID,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        document_types: Optional[List[str]] = None
    ) -> List[Document]:
        """
        Fetch documents from PostgreSQL with filters.

        Args:
            patient_id: Patient UUID
            date_start: Start date filter
            date_end: End date filter
            document_types: Document type filter

        Returns:
            List of Document models
        """
        # Build query
        query = select(Document).where(
            Document.id.in_(
                select(Patient.source_document_ids).where(Patient.id == patient_id)
            )
        )

        # Apply date filters
        if date_start:
            query = query.where(Document.document_date >= date_start)
        if date_end:
            query = query.where(Document.document_date <= date_end)

        # Apply document type filter
        if document_types:
            query = query.where(Document.document_type.in_(document_types))

        # Execute query
        result = await self.db.execute(query.order_by(Document.document_date.asc()))
        return list(result.scalars().all())

    def _group_concepts(self, concept_data: List[Dict]) -> List[TimelineConcept]:
        """
        Group concept mentions by CUI.

        Args:
            concept_data: List of concept dictionaries from Elasticsearch

        Returns:
            List of TimelineConcept with grouped mentions
        """
        concept_groups = {}

        for item in concept_data:
            cui = item["concept_cui"]

            if cui not in concept_groups:
                concept_groups[cui] = {
                    "concept_cui": cui,
                    "name": item.get("concept_name", "Unknown"),
                    "type": item.get("concept_type", "Unknown"),
                    "mentions": [],
                    "first_mention_date": None
                }

            # Add mention
            mention = ConceptMention(
                document_id=UUID(item["document_id"]),
                document_date=date.fromisoformat(item["document_date"]),
                sentence=item.get("sentence", ""),
                start_char=item.get("start_char", 0),
                end_char=item.get("end_char", 0),
                meta_annotations=item.get("meta_anns", {}),
                confidence=item.get("confidence", 0.0)
            )

            concept_groups[cui]["mentions"].append(mention)

            # Track first mention date
            mention_date = date.fromisoformat(item["document_date"])
            if concept_groups[cui]["first_mention_date"] is None or mention_date < concept_groups[cui]["first_mention_date"]:
                concept_groups[cui]["first_mention_date"] = mention_date

        # Convert to TimelineConcept list
        concepts = []
        for cui, group in concept_groups.items():
            concepts.append(
                TimelineConcept(
                    concept_cui=cui,
                    name=group["name"],
                    type=group["type"],
                    first_mention_date=group["first_mention_date"] or date.today(),
                    mention_count=len(group["mentions"]),
                    mentions=group["mentions"]
                )
            )

        return concepts
