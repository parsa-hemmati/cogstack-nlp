"""
Patient Search Service.

Business logic for searching patients by clinical concepts with meta-annotation filtering.
"""
import logging
import time
from datetime import date, datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, joinedload

from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity
from app.models.patient import Patient
from app.schemas.patient_search import (
    Annotation,
    ConceptHighlightResponse,
    Demographics,
    DocumentHighlight,
    MetaAnnotationDisplay,
    MetaAnnotations,
    PaginationInfo,
    PatientSearchRequest,
    PatientSearchResponse,
    PatientSearchResult,
    PerformanceInfo,
    SearchFilters,
)
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class PatientSearchService:
    """
    Patient search service with meta-annotation filtering.

    Features:
    - Search by concept name (case-insensitive) or SNOMED-CT CUI
    - Filter by meta-annotations (negation, temporality, experiencer, certainty)
    - Pagination support (page, page_size)
    - Multiple sort options (relevance, name, last_updated)
    - NHS number masking for privacy
    - Performance: <500ms for 10,000 patients (with indexes)

    Example:
        >>> service = PatientSearchService(db)
        >>> response = await service.search(
        ...     query="diabetes",
        ...     filters=MetaAnnotationFilters(negation="Affirmed"),
        ...     page=1,
        ...     page_size=20,
        ...     sort_by="relevance"
        ... )
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize patient search service.

        Args:
            db: Async database session
        """
        self.db = db

    async def search(
        self,
        concept: str,
        filters: SearchFilters,
        page: int = 1,
        page_size: int = 20,
        sort: str = "relevance",
    ) -> PatientSearchResponse:
        """
        Search for patients by clinical concept (PRD-compliant).

        Args:
            concept: Medical concept to search (name or CUI)
            filters: Search filters (temporal, negation, family history)
            page: Page number (1-indexed)
            page_size: Results per page
            sort: Sort order (relevance | name | lastUpdated)

        Returns:
            PatientSearchResponse with results, annotations, and query time

        Example:
            >>> response = await service.search(
            ...     concept="diabetes",
            ...     filters=SearchFilters(temporal="current", includeNegated=False),
            ...     page=1,
            ...     page_size=20,
            ...     sort="relevance"
            ... )
            >>> print(f"Found {response.total} patients in {response.queryTimeMs}ms")
        """
        start_time = time.time()

        # Build query with filters
        query_stmt, count_stmt = self._build_query(concept, filters, sort)

        # Get total count (for pagination)
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query_stmt = query_stmt.offset(offset).limit(page_size)

        # Execute search query
        result = await self.db.execute(query_stmt)
        rows = result.all()

        # Convert rows to PatientSearchResult objects with annotations
        results = []
        for row in rows:
            patient = row.Patient

            # Fetch annotations for this patient + concept
            annotations = await self._fetch_annotations(patient.id, concept, filters)

            # Calculate age from date of birth
            age = self._calculate_age(patient.date_of_birth) if patient.date_of_birth else 0

            results.append(
                PatientSearchResult(
                    mrn=self._mask_nhs_number(patient.nhs_number),
                    demographics=Demographics(
                        age=age,
                        gender=None,
                        department=None,
                    ),
                    annotations=annotations,
                    lastUpdated=patient.last_seen_at.isoformat() if patient.last_seen_at else datetime.utcnow().isoformat(),
                )
            )

        # Calculate query time
        query_time_ms = int((time.time() - start_time) * 1000)

        # Calculate total pages (ceiling division)
        total_pages = (total_count + page_size - 1) // page_size

        return PatientSearchResponse(
            results=results,
            pagination=PaginationInfo(
                page=page,
                pageSize=page_size,
                totalResults=total_count,
                totalPages=total_pages,
            ),
            performance=PerformanceInfo(
                searchTime=query_time_ms,
                source="live",  # Note: Caching detection not yet implemented (see CONTEXT.md technical debt)
            ),
        )

    async def _fetch_annotations(
        self,
        patient_id: UUID,
        concept: str,
        filters: SearchFilters,
    ) -> List[Annotation]:
        """
        Fetch annotations for a patient matching the concept and filters.

        Args:
            patient_id: Patient ID
            concept: Medical concept to search
            filters: Search filters

        Returns:
            List of Annotation objects with full details
        """
        # Build query to fetch annotations with document details
        stmt = (
            select(ExtractedEntity, Document)
            .join(Document, ExtractedEntity.document_id == Document.id)
            .where(ExtractedEntity.patient_id == patient_id)
            .where(self._build_concept_filter(concept))
            .where(self._build_meta_annotation_filters(filters))
            .order_by(Document.created_at.desc())
            .limit(20)  # Limit annotations per patient to avoid huge payloads
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        annotations = []
        for entity, document in rows:
            # Build meta-annotations object
            meta_anns_dict = entity.meta_anns or {}
            meta_annotations = MetaAnnotations(
                temporality=meta_anns_dict.get("Temporality"),
                negated=meta_anns_dict.get("Negation") == "Negated",
                experiencer=meta_anns_dict.get("Experiencer"),
                certainty=meta_anns_dict.get("Certainty"),
            )

            annotations.append(
                Annotation(
                    cui=entity.cui or "",
                    conceptName=entity.pretty_name,
                    sourceValue=entity.pretty_name,
                    documentId=str(document.id),
                    documentType=document.content_type,
                    documentDate=document.created_at.isoformat(),
                    startChar=entity.start_char,
                    endChar=entity.end_char,
                    confidence=entity.accuracy or 0.0,
                    metaAnnotations=meta_annotations,
                    snomedCT=None,
                    icd10=None,
                )
            )

        return annotations

    def _build_query(
        self,
        concept: str,
        filters: SearchFilters,
        sort: str,
    ) -> Tuple:
        """
        Build SQL query with JOINs and filters.

        Args:
            concept: Medical concept (name or CUI)
            filters: Search filters
            sort: Sort order

        Returns:
            Tuple of (query_statement, count_statement)
        """
        # Subquery: Count documents per patient containing the concept
        concept_docs_subq = (
            select(
                ExtractedEntity.patient_id,
                func.count(func.distinct(ExtractedEntity.document_id)).label("concept_document_count"),
            )
            .where(self._build_concept_filter(concept))
            .where(self._build_meta_annotation_filters(filters))
            .group_by(ExtractedEntity.patient_id)
            .subquery()
        )

        # Main query: JOIN patients with document counts
        query_stmt = select(Patient).join(
            concept_docs_subq, Patient.id == concept_docs_subq.c.patient_id
        )

        # Apply sorting (enum values are strings like "relevance", "name", "lastUpdated")
        sort_value = sort.value if hasattr(sort, "value") else sort
        if sort_value == "relevance":
            query_stmt = query_stmt.order_by(concept_docs_subq.c.concept_document_count.desc())
        elif sort_value == "name":
            query_stmt = query_stmt.order_by(Patient.full_name)
        elif sort_value == "lastUpdated":
            query_stmt = query_stmt.order_by(Patient.last_seen_at.desc())

        # Count query: Count distinct patients
        count_stmt = select(func.count(func.distinct(concept_docs_subq.c.patient_id))).select_from(
            concept_docs_subq
        )

        return query_stmt, count_stmt

    def _build_concept_filter(self, query: str):
        """
        Build WHERE clause for concept search (CUI or name).

        Args:
            query: Search query (CUI like "C0011849" or name like "diabetes")

        Returns:
            SQLAlchemy filter condition
        """
        # Check if query looks like a CUI (starts with C followed by digits)
        if query.startswith("C") and query[1:].isdigit():
            # Exact CUI match
            return ExtractedEntity.cui == query
        else:
            # Case-insensitive partial name match
            return ExtractedEntity.pretty_name.ilike(f"%{query}%")

    def _build_meta_annotation_filters(self, filters: SearchFilters):
        """
        Build WHERE clause for meta-annotation filters.

        Args:
            filters: Search filters with temporal, negation, family flags

        Returns:
            SQLAlchemy filter condition (AND of all filters)
        """
        conditions = []

        # Temporal filter (current, historical, future, any)
        if filters.temporal and filters.temporal.value != "any":
            # Map PRD temporal values to meta-annotation values
            temporal_map = {
                "current": ["Current", "Recent"],
                "historical": ["Historical"],
                "future": ["Future"],
            }
            allowed_values = temporal_map.get(filters.temporal.value, [])
            if allowed_values:
                conditions.append(
                    ExtractedEntity.meta_anns["Temporality"].astext.in_(allowed_values)
                )

        # Negation filter (includeNegated boolean)
        if not filters.includeNegated:
            # Exclude negated mentions
            conditions.append(
                or_(
                    ExtractedEntity.meta_anns["Negation"].astext == "Affirmed",
                    ExtractedEntity.meta_anns["Negation"].is_(None),
                )
            )

        # Family history filter (includeFamily boolean)
        if not filters.includeFamily:
            # Exclude family history
            conditions.append(
                or_(
                    ExtractedEntity.meta_anns["Experiencer"].astext == "Patient",
                    ExtractedEntity.meta_anns["Experiencer"].is_(None),
                )
            )

        # Combine all conditions with AND
        if conditions:
            return and_(*conditions)
        else:
            # No filters = return all
            return text("1=1")

    def _mask_nhs_number(self, nhs_number: str) -> str:
        """
        Mask NHS number for privacy.

        Args:
            nhs_number: Full NHS number (various formats: "123-456-7890", "123 456 7890", "1234567890")

        Returns:
            Masked NHS number (e.g., "XXX-XXX-7890")

        Example:
            >>> service._mask_nhs_number("123-456-7890")
            'XXX-XXX-7890'
            >>> service._mask_nhs_number("123 456 7890")
            'XXX-XXX-7890'
            >>> service._mask_nhs_number("1234567890")
            'XXX-XXX-7890'
        """
        if not nhs_number:
            return "XXX-XXX-XXXX"

        # Normalize to digits only (handles spaces, dashes, any format)
        digits = "".join(ch for ch in nhs_number if ch.isdigit())

        # Validate length
        if len(digits) < 4:
            # Too short or malformed, mask entirely
            return "XXX-XXX-XXXX"

        # UK NHS numbers are 10 digits, but be flexible
        if len(digits) >= 10:
            # Standard UK format: XXX-XXX-7890
            return f"XXX-XXX-{digits[-4:]}"
        else:
            # Shorter format: mask all but last 4
            return "X" * (len(digits) - 4) + digits[-4:]

    def _calculate_age(self, date_of_birth: date) -> int:
        """
        Calculate age from date of birth.

        Args:
            date_of_birth: Patient's date of birth

        Returns:
            Age in years

        Example:
            >>> service._calculate_age(date(2000, 1, 1))
            24  # (if today is 2024-11-18)
        """
        today = date.today()
        age = today.year - date_of_birth.year

        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (date_of_birth.month, date_of_birth.day):
            age -= 1

        return age

    # ========================================================================
    # Concept Highlights (Task 4.3)
    # ========================================================================

    async def get_concept_highlights(
        self,
        patient_id: UUID,
        cui: str,
        filters: Optional[SearchFilters] = None,
    ) -> ConceptHighlightResponse:
        """
        Retrieve documents containing specific concept for a patient.

        Returns document snippets with concept context (100 chars before/after),
        meta-annotations, and document metadata.

        Args:
            patient_id: Patient UUID
            cui: SNOMED-CT CUI or concept name
            filters: Optional meta-annotation filters

        Returns:
            ConceptHighlightResponse with document highlights

        Example:
            >>> service = PatientSearchService(db)
            >>> response = await service.get_concept_highlights(
            ...     patient_id=UUID("..."),
            ...     cui="C0004238",
            ...     filters=SearchFilters(includeNegated=False)
            ... )
            >>> response.totalCount
            5
            >>> response.documents[0].snippet
            '...patient presents with <b>atrial flutter</b> with...'
        """
        start_time = time.time()

        # Build base query
        query = (
            select(ExtractedEntity, Document)
            .join(Document, ExtractedEntity.document_id == Document.id)
            .where(ExtractedEntity.patient_id == patient_id)
        )

        # Filter by CUI or concept name
        if cui.startswith("C"):
            # SNOMED-CT CUI format
            query = query.where(ExtractedEntity.cui == cui)
        else:
            # Concept name (case-insensitive)
            query = query.where(func.lower(ExtractedEntity.pretty_name).contains(cui.lower()))

        # Apply meta-annotation filters if provided
        if filters:
            query = self._apply_meta_annotation_filters(query, filters)

        # Execute query
        result = await self.db.execute(query)
        rows = result.all()

        # Build document highlights
        highlights = []
        encryption_service = EncryptionService()

        for entity, document in rows:
            # Decrypt document content
            decrypted_content = encryption_service.decrypt(document.encrypted_content)

            # Extract snippet
            snippet = self._extract_snippet(
                text=decrypted_content,
                start_char=entity.start_char,
                end_char=entity.end_char,
            )

            # Build meta-annotations display
            meta_anns = entity.meta_anns or {}
            meta_display = MetaAnnotationDisplay(
                Negation=meta_anns.get("Negation", "Unknown"),
                Temporality=meta_anns.get("Temporality", "Unknown"),
                Experiencer=meta_anns.get("Experiencer", "Unknown"),
                Certainty=meta_anns.get("Certainty", "Unknown"),
            )

            # Build document highlight
            highlight = DocumentHighlight(
                documentId=str(document.id),
                title=document.title or "Untitled Document",
                date=document.document_date.isoformat() if document.document_date else datetime.now().date().isoformat(),
                snippet=snippet,
                metaAnnotations=meta_display,
                startChar=entity.start_char,
                endChar=entity.end_char,
            )
            highlights.append(highlight)

        query_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            f"Concept highlights retrieved for patient {patient_id}, "
            f"CUI {cui}, {len(highlights)} documents, {query_time_ms}ms"
        )

        return ConceptHighlightResponse(
            documents=highlights,
            totalCount=len(highlights),
        )

    def _extract_snippet(self, text: str, start_char: int, end_char: int) -> str:
        """
        Extract snippet with context (100 chars before + concept + 100 chars after).

        The concept is bolded in the snippet using <b></b> tags.

        Args:
            text: Full document text
            start_char: Character offset where concept starts
            end_char: Character offset where concept ends

        Returns:
            Text snippet with concept bolded

        Example:
            >>> service._extract_snippet("Patient presents with diabetes mellitus.", 23, 31)
            'Patient presents with <b>diabetes</b> mellitus.'
        """
        # Handle edge cases
        if start_char < 0 or end_char > len(text) or start_char >= end_char:
            return text[:200]  # Return first 200 chars as fallback

        # Extract 100 chars before, concept, 100 chars after
        snippet_start = max(0, start_char - 100)
        snippet_end = min(len(text), end_char + 100)
        snippet = text[snippet_start:snippet_end]

        # Calculate concept position within snippet
        concept_start_in_snippet = start_char - snippet_start
        concept_end_in_snippet = end_char - snippet_start

        # Bold the concept
        bolded_snippet = (
            snippet[:concept_start_in_snippet]
            + f"<b>{snippet[concept_start_in_snippet:concept_end_in_snippet]}</b>"
            + snippet[concept_end_in_snippet:]
        )

        # Add ellipsis if truncated
        if snippet_start > 0:
            bolded_snippet = "..." + bolded_snippet
        if snippet_end < len(text):
            bolded_snippet = bolded_snippet + "..."

        return bolded_snippet
