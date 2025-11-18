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
from sqlalchemy.orm import aliased

from app.models.extracted_entity import ExtractedEntity
from app.models.patient import Patient
from app.schemas.patient_search import (
    MetaAnnotationFilters,
    PatientSearchRequest,
    PatientSearchResponse,
    PatientSearchResult,
)

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
        query: str,
        filters: MetaAnnotationFilters,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "relevance",
    ) -> PatientSearchResponse:
        """
        Search for patients by clinical concept.

        Args:
            query: Search query (concept name or CUI)
            filters: Meta-annotation filters
            page: Page number (1-indexed)
            page_size: Results per page
            sort_by: Sort order (relevance | name | last_updated)

        Returns:
            PatientSearchResponse with results, pagination, and query time

        Example:
            >>> response = await service.search(
            ...     query="diabetes",
            ...     filters=MetaAnnotationFilters(negation="Affirmed"),
            ...     page=1,
            ...     page_size=20,
            ...     sort_by="relevance"
            ... )
            >>> print(f"Found {response.total_count} patients in {response.query_time_ms}ms")
        """
        start_time = time.time()

        # Build query with filters
        query_stmt, count_stmt = self._build_query(query, filters, sort_by)

        # Get total count (for pagination)
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query_stmt = query_stmt.offset(offset).limit(page_size)

        # Execute search query
        result = await self.db.execute(query_stmt)
        rows = result.all()

        # Convert rows to PatientSearchResult objects
        results = []
        for row in rows:
            patient = row.Patient
            concept_doc_count = row.concept_document_count
            total_doc_count = row.total_document_count

            # Calculate age from date of birth
            age = self._calculate_age(patient.date_of_birth) if patient.date_of_birth else 0

            results.append(
                PatientSearchResult(
                    patient_id=patient.id,
                    nhs_number=self._mask_nhs_number(patient.nhs_number),
                    full_name=patient.full_name or "Unknown",
                    date_of_birth=patient.date_of_birth or date(1900, 1, 1),
                    age=age,
                    document_count=total_doc_count,
                    concept_document_count=concept_doc_count,
                    last_updated=patient.last_seen_at or datetime.utcnow(),
                )
            )

        # Calculate query time
        query_time_ms = int((time.time() - start_time) * 1000)

        return PatientSearchResponse(
            results=results,
            total_count=total_count,
            page=page,
            page_size=page_size,
            query_time_ms=query_time_ms,
        )

    def _build_query(
        self,
        query: str,
        filters: MetaAnnotationFilters,
        sort_by: str,
    ) -> Tuple:
        """
        Build SQL query with JOINs and filters.

        Args:
            query: Search query (concept name or CUI)
            filters: Meta-annotation filters
            sort_by: Sort order

        Returns:
            Tuple of (query_statement, count_statement)
        """
        # Subquery: Count documents per patient containing the concept
        concept_docs_subq = (
            select(
                ExtractedEntity.patient_id,
                func.count(func.distinct(ExtractedEntity.document_id)).label("concept_document_count"),
            )
            .where(self._build_concept_filter(query))
            .where(self._build_meta_annotation_filters(filters))
            .group_by(ExtractedEntity.patient_id)
            .subquery()
        )

        # Subquery: Total documents per patient
        total_docs_subq = (
            select(
                ExtractedEntity.patient_id,
                func.count(func.distinct(ExtractedEntity.document_id)).label("total_document_count"),
            )
            .group_by(ExtractedEntity.patient_id)
            .subquery()
        )

        # Main query: JOIN patients with document counts
        query_stmt = (
            select(
                Patient,
                concept_docs_subq.c.concept_document_count,
                total_docs_subq.c.total_document_count,
            )
            .join(concept_docs_subq, Patient.id == concept_docs_subq.c.patient_id)
            .join(total_docs_subq, Patient.id == total_docs_subq.c.patient_id)
        )

        # Apply sorting
        if sort_by == "relevance":
            query_stmt = query_stmt.order_by(concept_docs_subq.c.concept_document_count.desc())
        elif sort_by == "name":
            query_stmt = query_stmt.order_by(Patient.full_name)
        elif sort_by == "last_updated":
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

    def _build_meta_annotation_filters(self, filters: MetaAnnotationFilters):
        """
        Build WHERE clause for meta-annotation filters.

        Args:
            filters: Meta-annotation filter values

        Returns:
            SQLAlchemy filter condition (AND of all non-"Any" filters)
        """
        conditions = []

        # Negation filter
        if filters.negation and filters.negation != "Any":
            conditions.append(
                ExtractedEntity.meta_anns["Negation"].astext == filters.negation
            )

        # Temporality filter
        if filters.temporality and filters.temporality != "Any":
            conditions.append(
                ExtractedEntity.meta_anns["Temporality"].astext == filters.temporality
            )

        # Experiencer filter
        if filters.experiencer and filters.experiencer != "Any":
            conditions.append(
                ExtractedEntity.meta_anns["Experiencer"].astext == filters.experiencer
            )

        # Certainty filter
        if filters.certainty and filters.certainty != "Any":
            conditions.append(
                ExtractedEntity.meta_anns["Certainty"].astext == filters.certainty
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
            nhs_number: Full NHS number (e.g., "123-456-7890")

        Returns:
            Masked NHS number (e.g., "XXX-XXX-7890")

        Example:
            >>> service._mask_nhs_number("123-456-7890")
            'XXX-XXX-7890'
            >>> service._mask_nhs_number("1234567890")
            'XXXXXX7890'
        """
        if not nhs_number:
            return "XXX-XXX-XXXX"

        # Check if NHS number has dashes (formatted)
        if "-" in nhs_number:
            # Format: "123-456-7890" → "XXX-XXX-7890"
            parts = nhs_number.split("-")
            if len(parts) == 3:
                return f"XXX-XXX-{parts[2]}"
            else:
                # Fallback: show last 4 digits
                return "XXX-XXX-" + nhs_number[-4:]
        else:
            # Format: "1234567890" → "XXXXXX7890"
            return "X" * (len(nhs_number) - 4) + nhs_number[-4:]

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
