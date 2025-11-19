"""
Timeline Service for aggregating patient timeline data.

This service orchestrates data from PostgreSQL (documents) and Elasticsearch (concepts)
to build a complete patient timeline view.
"""

from typing import List, Dict
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from collections import defaultdict

from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity
from app.models.user import User
from app.schemas.timeline import (
    PatientTimeline, TimelineFilters, TimelineDocument,
    TimelineConcept, DateRange, ConceptMention
)
from app.repositories.elasticsearch_timeline_repo import ElasticsearchTimelineRepository
from app.services.audit_service import AuditService


class TimelineService:
    """Service for retrieving and aggregating patient timeline data.

    Combines document metadata from PostgreSQL with clinical concepts
    from Elasticsearch to provide a comprehensive patient timeline.
    """

    def __init__(self, db: AsyncSession):
        """Initialize timeline service.

        Args:
            db: Async database session
        """
        self.db = db
        self.es_repo = ElasticsearchTimelineRepository()
        self.audit_service = AuditService()

    async def get_patient_timeline(
        self,
        patient_id: UUID,
        filters: TimelineFilters,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None
    ) -> PatientTimeline:
        """Get complete patient timeline with documents and concepts.

        Args:
            patient_id: UUID of the patient
            filters: Timeline filters (concepts, date_range, meta_annotations, document_types)
            user: Current user (for audit logging)
            ip_address: Client IP address (for audit logging)
            user_agent: Client user agent (for audit logging)

        Returns:
            PatientTimeline with documents, concepts, and applied filters

        Raises:
            HTTPException: If patient not found or access denied

        Security:
            - Logs PHI access to audit log (HIPAA requirement)
            - Caller must enforce RBAC before calling this method
        """
        # Audit log access (CRITICAL: HIPAA requirement)
        await self.audit_service.log_phi_access(
            db=self.db,
            user=user,
            patient_id=str(patient_id),
            action="VIEW_TIMELINE",
            details={
                "filters": filters.dict(exclude_none=True) if filters else {}
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Get documents from PostgreSQL
        documents = await self._get_documents(patient_id, filters)

        # Get concepts from Elasticsearch
        concept_mentions = await self.es_repo.query_concepts_by_patient(
            patient_id=str(patient_id),
            concept_filter=filters.concepts if filters else None,
            date_range=filters.date_range if filters else None,
            meta_annotations=filters.meta_annotations if filters else None
        )

        # Aggregate concepts
        concepts = self._aggregate_concepts(concept_mentions)

        # Calculate date range
        date_range = self._calculate_date_range(documents, concept_mentions)

        return PatientTimeline(
            patient_id=str(patient_id),
            documents=documents,
            concepts=concepts,
            date_range=date_range,
            filters_applied=filters
        )

    async def _get_documents(
        self,
        patient_id: UUID,
        filters: TimelineFilters | None
    ) -> List[TimelineDocument]:
        """Get documents for a patient from PostgreSQL.

        NOTE: Current implementation queries through extracted_entities table
        since Document model doesn't have patient_id field (Phase 3 design).

        Future improvement: Add patient_id, date, document_type, title, author
        to Document model in a migration.

        Args:
            patient_id: Patient UUID
            filters: Timeline filters (date_range, document_types)

        Returns:
            List of TimelineDocument objects sorted by date
        """
        # Query documents via extracted_entities (current schema limitation)
        # Get distinct document IDs for this patient
        stmt = (
            select(ExtractedEntity.document_id)
            .where(ExtractedEntity.patient_id == patient_id)
            .distinct()
        )

        result = await self.db.execute(stmt)
        doc_ids = [row[0] for row in result.fetchall()]

        if not doc_ids:
            return []

        # Get document details
        doc_query = select(Document).where(Document.id.in_(doc_ids))

        # Apply date range filter (using created_at as proxy for document date)
        if filters and filters.date_range:
            doc_query = doc_query.where(
                and_(
                    Document.created_at >= filters.date_range.start,
                    Document.created_at <= filters.date_range.end
                )
            )

        # TODO: Apply document_types filter when document_type field exists
        # if filters and filters.document_types:
        #     doc_query = doc_query.where(Document.document_type.in_(filters.document_types))

        # Sort by date (using created_at as proxy)
        doc_query = doc_query.order_by(Document.created_at.asc())

        result = await self.db.execute(doc_query)
        docs = result.scalars().all()

        # Convert to TimelineDocument schema
        timeline_docs = []
        for doc in docs:
            # Get concept CUIs for this document
            concept_stmt = (
                select(ExtractedEntity.cui)
                .where(
                    and_(
                        ExtractedEntity.document_id == doc.id,
                        ExtractedEntity.patient_id == patient_id,
                        ExtractedEntity.cui.isnot(None)  # Exclude PHI entities
                    )
                )
                .distinct()
            )
            concept_result = await self.db.execute(concept_stmt)
            concept_cuis = [row[0] for row in concept_result.fetchall()]

            timeline_doc = TimelineDocument(
                document_id=str(doc.id),
                title=doc.filename,  # Use filename as title (MVP approach)
                document_type=self._infer_document_type(doc.filename),  # Infer from filename
                date=doc.created_at,  # Use upload date as document date (MVP approach)
                author=None,  # Not available in current schema
                concepts=concept_cuis
            )
            timeline_docs.append(timeline_doc)

        return timeline_docs

    def _infer_document_type(self, filename: str) -> str:
        """Infer document type from filename.

        This is a temporary approach until document_type is added to Document model.

        Args:
            filename: Document filename

        Returns:
            Inferred document type
        """
        filename_lower = filename.lower()

        # Common document type patterns
        if "discharge" in filename_lower:
            return "discharge_summary"
        elif "lab" in filename_lower or "result" in filename_lower:
            return "lab_result"
        elif "letter" in filename_lower:
            return "letter"
        elif "note" in filename_lower or "clinic" in filename_lower:
            return "clinical_note"
        elif "report" in filename_lower:
            return "report"
        else:
            return "clinical_note"  # Default

    def _aggregate_concepts(
        self,
        mentions: List[ConceptMention]
    ) -> List[TimelineConcept]:
        """Aggregate concept mentions into timeline concepts.

        Groups mentions by concept CUI and calculates:
        - First mention date
        - Total mention count
        - All mentions chronologically
        - Marks first (earliest) mention with is_first_mention=True

        Args:
            mentions: List of concept mentions from Elasticsearch

        Returns:
            List of aggregated TimelineConcept objects
        """
        # Group by concept CUI
        concept_map: Dict[str, Dict] = {}

        for mention in mentions:
            cui = mention.concept_cui

            if cui not in concept_map:
                # Initialize new concept
                concept_map[cui] = {
                    "concept_cui": cui,
                    "concept_name": mention.concept_name,
                    "concept_type": mention.concept_type,
                    "first_mention_date": mention.date,
                    "mention_count": 0,
                    "mentions": []
                }

            # Update aggregation
            concept_map[cui]["mention_count"] += 1
            concept_map[cui]["mentions"].append(mention)

            # Update first mention date if earlier
            if mention.date < concept_map[cui]["first_mention_date"]:
                concept_map[cui]["first_mention_date"] = mention.date

        # Mark first mentions for each concept
        for concept_data in concept_map.values():
            # Sort mentions chronologically
            concept_data["mentions"].sort(key=lambda m: m.date)

            # Mark first mention (earliest by date)
            if concept_data["mentions"]:
                concept_data["mentions"][0].is_first_mention = True
                # All others remain False (default from schema)

        # Convert to TimelineConcept objects
        concepts = [
            TimelineConcept(**concept_data)
            for concept_data in concept_map.values()
        ]

        # Sort by first mention date
        concepts.sort(key=lambda c: c.first_mention_date)

        return concepts

    def _calculate_date_range(
        self,
        documents: List[TimelineDocument],
        mentions: List[ConceptMention]
    ) -> DateRange:
        """Calculate overall date range from documents and concepts.

        Args:
            documents: List of timeline documents
            mentions: List of concept mentions

        Returns:
            DateRange with min/max dates
        """
        dates = []

        # Add document dates
        dates.extend([doc.date for doc in documents])

        # Add concept mention dates
        dates.extend([mention.date for mention in mentions])

        if not dates:
            # No data: return current datetime
            now = datetime.utcnow()
            return DateRange(start=now, end=now)

        return DateRange(start=min(dates), end=max(dates))

    async def close(self):
        """Close resources (Elasticsearch connection).

        Should be called when service is no longer needed.
        """
        await self.es_repo.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
