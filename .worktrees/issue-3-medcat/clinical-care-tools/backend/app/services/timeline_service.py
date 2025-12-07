"""Timeline service for retrieving patient timeline data."""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.annotation import Annotation
from app.models.document import Document
from app.schemas.timeline import (
    ConceptOccurrence,
    TimelineConcept,
    TimelineDocument,
    TimelineResponse,
)

logger = logging.getLogger(__name__)


class TimelineService:
    """
    Service for retrieving and processing patient timeline data.

    Combines documents and NLP-extracted concepts into chronological timeline.
    """

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def get_patient_timeline(
        self,
        patient_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_types: Optional[list[str]] = None,
        concept_types: Optional[list[str]] = None,
        include_negated: bool = False,
        include_family: bool = False,
    ) -> TimelineResponse:
        """
        Get comprehensive timeline for patient.

        Args:
            patient_id: Patient UUID
            start_date: Filter start date
            end_date: Filter end date
            document_types: Filter document types
            concept_types: Filter concept types (condition, medication, procedure)
            include_negated: Include negated concepts (default: False)
            include_family: Include family history (default: False)

        Returns:
            TimelineResponse with documents, concepts, date range, and metadata
        """
        logger.info(
            f"Fetching timeline for patient {patient_id} "
            f"(start={start_date}, end={end_date}, "
            f"doc_types={document_types}, concept_types={concept_types})"
        )

        # Get documents
        documents = await self._get_timeline_documents(
            patient_id, start_date, end_date, document_types
        )

        # Get concepts
        concepts = await self._get_timeline_concepts(
            patient_id,
            start_date,
            end_date,
            concept_types,
            include_negated,
            include_family,
        )

        # Calculate date range
        date_range = self._calculate_date_range(documents)

        logger.info(
            f"Timeline retrieved: {len(documents)} documents, {len(concepts)} concepts"
        )

        return TimelineResponse(
            patient_id=str(patient_id),
            timeline={
                "documents": [doc.model_dump() for doc in documents],
                "concepts": [concept.model_dump() for concept in concepts],
                "date_range": date_range,
            },
            metadata={
                "document_count": len(documents),
                "concept_count": len(concepts),
                "generated_at": datetime.utcnow().isoformat() + "Z",
            },
        )

    async def _get_timeline_documents(
        self,
        patient_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        document_types: Optional[list[str]],
    ) -> list[TimelineDocument]:
        """
        Get documents for timeline.

        Args:
            patient_id: Patient UUID
            start_date: Filter start date
            end_date: Filter end date
            document_types: Filter document types

        Returns:
            List of TimelineDocument objects
        """
        # Build query
        query = (
            select(
                Document.id,
                Document.title,
                Document.document_type,
                Document.document_date,
                Document.author,
                func.count(Annotation.id).label("annotation_count"),
            )
            .outerjoin(Annotation, Annotation.document_id == Document.id)
            .where(
                and_(
                    Document.patient_id == patient_id,
                    Document.status == "completed",  # Only completed documents
                )
            )
            .group_by(
                Document.id,
                Document.title,
                Document.document_type,
                Document.document_date,
                Document.author,
            )
            .order_by(Document.document_date.asc())
        )

        # Apply date filters
        if start_date:
            query = query.where(Document.document_date >= start_date)
        if end_date:
            query = query.where(Document.document_date <= end_date)

        # Apply document type filter
        if document_types:
            query = query.where(Document.document_type.in_(document_types))

        # Execute query
        result = await self.db.execute(query)
        rows = result.all()

        # Convert to TimelineDocument objects
        timeline_docs = []
        for row in rows:
            timeline_docs.append(
                TimelineDocument(
                    id=str(row.id),
                    title=row.title,
                    type=row.document_type.value,  # Enum to string
                    date=row.document_date.isoformat() + "Z",
                    author=row.author,
                    annotation_count=row.annotation_count or 0,
                )
            )

        return timeline_docs

    async def _get_timeline_concepts(
        self,
        patient_id: UUID,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        concept_types: Optional[list[str]],
        include_negated: bool,
        include_family: bool,
    ) -> list[TimelineConcept]:
        """
        Get aggregated concepts for timeline.

        Groups annotations by CUI and aggregates first/last mentioned dates.

        Args:
            patient_id: Patient UUID
            start_date: Filter start date
            end_date: Filter end date
            concept_types: Filter concept types
            include_negated: Include negated concepts
            include_family: Include family history

        Returns:
            List of TimelineConcept objects with aggregated data
        """
        # Build query
        query = (
            select(
                Annotation.cui,
                Annotation.preferred_name,
                Annotation.concept_type,
                func.min(Document.document_date).label("first_mentioned"),
                func.max(Document.document_date).label("last_mentioned"),
                Annotation.negation,
                Annotation.temporality,
                Annotation.experiencer,
                func.count(Annotation.id).label("occurrence_count"),
            )
            .join(Document, Annotation.document_id == Document.id)
            .where(
                and_(
                    Document.patient_id == patient_id,
                    Document.status == "completed",
                )
            )
            .group_by(
                Annotation.cui,
                Annotation.preferred_name,
                Annotation.concept_type,
                Annotation.negation,
                Annotation.temporality,
                Annotation.experiencer,
            )
            .order_by(func.min(Document.document_date).asc())
        )

        # Apply meta-annotation filters
        if not include_negated:
            query = query.where(Annotation.negation == "Affirmed")
        if not include_family:
            query = query.where(Annotation.experiencer == "Patient")

        # Apply date filters
        if start_date:
            query = query.where(Document.document_date >= start_date)
        if end_date:
            query = query.where(Document.document_date <= end_date)

        # Apply concept type filter
        if concept_types:
            query = query.where(Annotation.concept_type.in_(concept_types))

        # Execute query
        result = await self.db.execute(query)
        rows = result.all()

        # Convert to TimelineConcept objects
        timeline_concepts = []
        for row in rows:
            timeline_concepts.append(
                TimelineConcept(
                    id=row.cui,  # Use CUI as ID
                    cui=row.cui,
                    name=row.preferred_name,
                    type=row.concept_type,
                    first_mentioned=row.first_mentioned.isoformat() + "Z",
                    last_mentioned=row.last_mentioned.isoformat() + "Z",
                    occurrences=[],  # Populated on-demand if needed
                    meta_annotations={
                        "negation": row.negation or "Unknown",
                        "temporality": row.temporality or "Unknown",
                        "experiencer": row.experiencer or "Unknown",
                    },
                )
            )

        return timeline_concepts

    async def get_concept_occurrences(
        self,
        patient_id: UUID,
        cui: str,
    ) -> list[ConceptOccurrence]:
        """
        Get all occurrences of a specific concept for a patient.

        Args:
            patient_id: Patient UUID
            cui: Concept CUI to retrieve occurrences for

        Returns:
            List of ConceptOccurrence objects
        """
        query = (
            select(
                Annotation.id,
                Annotation.document_id,
                Document.document_date,
                Annotation.text,
                Annotation.start_char,
                Annotation.end_char,
            )
            .join(Document, Annotation.document_id == Document.id)
            .where(
                and_(
                    Document.patient_id == patient_id,
                    Annotation.cui == cui,
                    Document.status == "completed",
                )
            )
            .order_by(Document.document_date.asc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        occurrences = []
        for row in rows:
            occurrences.append(
                ConceptOccurrence(
                    document_id=str(row.document_id),
                    date=row.document_date.isoformat() + "Z",
                    context=row.text,  # Simplified - full context would need text extraction
                    start_char=row.start_char,
                    end_char=row.end_char,
                )
            )

        return occurrences

    def _calculate_date_range(
        self, documents: list[TimelineDocument]
    ) -> dict[str, Optional[str]]:
        """
        Calculate earliest and latest dates from documents.

        Args:
            documents: List of timeline documents

        Returns:
            Dictionary with earliest and latest dates (ISO 8601)
        """
        if not documents:
            return {"earliest": None, "latest": None}

        # Documents are already sorted by date (ascending)
        earliest = documents[0].date
        latest = documents[-1].date

        return {"earliest": earliest, "latest": latest}
