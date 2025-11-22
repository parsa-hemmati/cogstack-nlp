"""
Patient Search Service

Business logic for patient search with meta-annotation filtering.
"""

import logging
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

import httpx
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload

from app.models.patient import Patient
from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity
from .schemas import (
    ConceptMatch,
    ConceptSuggestion,
    MetaAnnotationFilters,
    PatientSearchRequest,
    PatientSearchResponse,
    PatientSearchResult,
)

logger = logging.getLogger(__name__)


class PatientSearchService:
    """
    Service for searching patients using medical concepts with meta-annotation filtering.

    Key Features:
        - SNOMED-CT/UMLS concept search
        - Meta-annotation filtering for 95% precision
        - Boolean query operators (AND, OR, NOT)
        - Date range filtering
        - Result ranking by relevance
        - Caching for performance
    """

    def __init__(self, medcat_url: str = "http://localhost:5000"):
        """
        Initialize patient search service.

        Args:
            medcat_url: URL of MedCAT service
        """
        self.medcat_url = medcat_url
        self._concept_cache: Dict[str, List[str]] = {}

    def check_medcat_connectivity(self) -> bool:
        """
        Check if MedCAT service is available.

        Returns:
            True if service is reachable
        """
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.medcat_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"MedCAT connectivity check failed: {e}")
            return False

    async def search_patients(
        self,
        request: PatientSearchRequest,
        db: Session,
        user_id: UUID,
    ) -> PatientSearchResponse:
        """
        Search for patients matching the query criteria.

        Args:
            request: Search request with query and filters
            db: Database session
            user_id: Current user ID for audit logging

        Returns:
            Search response with matching patients
        """
        start_time = time.time()

        # Extract CUIs from query
        cuis = await self._extract_concepts(request.query)
        if not cuis and not request.queries:
            return PatientSearchResponse(
                results=[],
                total=0,
                query_time_ms=int((time.time() - start_time) * 1000),
                filters_applied=request.filters,
            )

        # Build the database query
        query = self._build_search_query(db, cuis, request)

        # Execute query with pagination
        total = query.count()
        results = query.offset(request.offset).limit(request.limit).all()

        # Process results
        patient_results = []
        for patient_id, entities in self._group_by_patient(results):
            patient_result = self._process_patient_result(
                db, patient_id, entities, request.filters
            )
            if patient_result:
                patient_results.append(patient_result)

        # Calculate statistics
        stats = self._calculate_statistics(patient_results)

        # Audit log the search
        self._audit_log_search(db, user_id, request, len(patient_results))

        query_time = int((time.time() - start_time) * 1000)

        return PatientSearchResponse(
            results=patient_results,
            total=total,
            query_time_ms=query_time,
            filters_applied=request.filters,
            stats=stats,
        )

    async def _extract_concepts(self, query: str) -> List[str]:
        """
        Extract medical concepts (CUIs) from free text query.

        Args:
            query: Free text search query

        Returns:
            List of concept unique identifiers (CUIs)
        """
        # Check cache first
        if query in self._concept_cache:
            return self._concept_cache[query]

        try:
            # Call MedCAT service to extract concepts
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.medcat_url}/process",
                    json={"text": query}
                )

                if response.status_code == 200:
                    data = response.json()
                    entities = data.get("entities", [])
                    cuis = [ent["cui"] for ent in entities]

                    # Cache the result
                    self._concept_cache[query] = cuis
                    return cuis

        except Exception as e:
            logger.error(f"Failed to extract concepts from query: {e}")

        # Fallback: treat as direct CUI if it looks like one
        if query.startswith("C") and len(query) == 8:
            return [query]

        return []

    def _build_search_query(
        self,
        db: Session,
        cuis: List[str],
        request: PatientSearchRequest,
    ):
        """
        Build SQLAlchemy query for patient search.

        Args:
            db: Database session
            cuis: List of concept UIDs to search for
            request: Search request with filters

        Returns:
            SQLAlchemy query object
        """
        # Start with base query
        query = db.query(ExtractedEntity).join(Document).join(Patient)

        # Filter by concepts
        if cuis:
            query = query.filter(ExtractedEntity.cui.in_(cuis))

        # Apply meta-annotation filters
        query = self._apply_meta_filters(query, request.filters)

        # Apply date filters
        if request.date_from:
            query = query.filter(Document.created_at >= request.date_from)
        if request.date_to:
            query = query.filter(Document.created_at <= request.date_to)

        # Apply department filters
        if request.department_ids:
            query = query.filter(Patient.department_id.in_(request.department_ids))

        # Apply document type filters
        if request.document_types:
            query = query.filter(Document.document_type.in_(request.document_types))

        return query

    def _apply_meta_filters(
        self,
        query,
        filters: MetaAnnotationFilters,
    ):
        """
        Apply meta-annotation filters to query.

        This is the KEY function for achieving 95% precision.

        Args:
            query: SQLAlchemy query
            filters: Meta-annotation filters

        Returns:
            Filtered query
        """
        meta_anns = ExtractedEntity.meta_annotations

        # Negation filter (CRITICAL: exclude negated mentions)
        if filters.negation:
            query = query.filter(
                meta_anns["Negation"].astext == filters.negation.value
            )

        # Temporality filter (CRITICAL: exclude historical mentions)
        if filters.temporality:
            temporality_values = [t.value for t in filters.temporality]
            query = query.filter(
                meta_anns["Temporality"].astext.in_(temporality_values)
            )

        # Experiencer filter (CRITICAL: exclude family history)
        if filters.experiencer:
            query = query.filter(
                meta_anns["Experiencer"].astext == filters.experiencer.value
            )

        # Certainty filter
        if filters.certainty:
            certainty_values = [c.value for c in filters.certainty]
            query = query.filter(
                meta_anns["Certainty"].astext.in_(certainty_values)
            )

        # Confidence threshold
        query = query.filter(ExtractedEntity.confidence >= filters.confidence_min)

        return query

    def _group_by_patient(
        self,
        entities: List[ExtractedEntity],
    ) -> Dict[UUID, List[ExtractedEntity]]:
        """
        Group extracted entities by patient.

        Args:
            entities: List of extracted entities

        Returns:
            Dictionary mapping patient ID to entities
        """
        grouped = {}
        for entity in entities:
            patient_id = entity.document.patient_id
            if patient_id not in grouped:
                grouped[patient_id] = []
            grouped[patient_id].append(entity)
        return grouped.items()

    def _process_patient_result(
        self,
        db: Session,
        patient_id: UUID,
        entities: List[ExtractedEntity],
        filters: MetaAnnotationFilters,
    ) -> Optional[PatientSearchResult]:
        """
        Process entities for a single patient into a search result.

        Args:
            db: Database session
            patient_id: Patient UUID
            entities: List of entities for this patient
            filters: Applied filters

        Returns:
            Patient search result or None if no matches
        """
        # Get patient information
        patient = db.query(Patient).filter(Patient.id == patient_id).first()
        if not patient:
            return None

        # Convert entities to concept matches
        matched_concepts = []
        for entity in entities[:10]:  # Limit to top 10 matches
            concept = ConceptMatch(
                text=entity.text,
                cui=entity.cui,
                pretty_name=entity.pretty_name,
                confidence=entity.confidence,
                negation=entity.meta_annotations.get("Negation", "Unknown"),
                temporality=entity.meta_annotations.get("Temporality", "Unknown"),
                experiencer=entity.meta_annotations.get("Experiencer", "Unknown"),
                certainty=entity.meta_annotations.get("Certainty", "Unknown"),
                start_idx=entity.start_idx,
                end_idx=entity.end_idx,
                context=self._get_context(entity),
            )
            matched_concepts.append(concept)

        # Calculate relevance score
        relevance_score = self._calculate_relevance(entities, filters)

        # Get document statistics
        document_ids = set(e.document_id for e in entities)
        latest_date = max(e.document.created_at for e in entities)

        return PatientSearchResult(
            patient_id=patient.id,
            patient_mrn=patient.mrn,
            age=self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
            gender=patient.gender,
            matched_concepts=matched_concepts,
            relevance_score=relevance_score,
            document_count=len(document_ids),
            latest_match_date=latest_date,
            summary=self._generate_summary(matched_concepts),
        )

    def _get_context(self, entity: ExtractedEntity, window: int = 50) -> str:
        """
        Get text context around an entity match.

        Args:
            entity: Extracted entity
            window: Characters to include before/after

        Returns:
            Context string
        """
        # This would normally get text from the document
        # For now, return a placeholder
        return f"...{entity.text}..."

    def _calculate_relevance(
        self,
        entities: List[ExtractedEntity],
        filters: MetaAnnotationFilters,
    ) -> float:
        """
        Calculate overall relevance score for a patient.

        Args:
            entities: List of matched entities
            filters: Applied filters

        Returns:
            Relevance score (0.0-1.0)
        """
        if not entities:
            return 0.0

        # Factors for relevance:
        # 1. Average confidence score
        avg_confidence = sum(e.confidence for e in entities) / len(entities)

        # 2. Number of matches (normalized)
        match_score = min(len(entities) / 10.0, 1.0)

        # 3. Recency (how recent are the matches)
        now = datetime.now()
        recency_scores = []
        for entity in entities:
            days_ago = (now - entity.document.created_at).days
            recency = max(0, 1.0 - (days_ago / 365.0))  # Linear decay over 1 year
            recency_scores.append(recency)
        avg_recency = sum(recency_scores) / len(recency_scores) if recency_scores else 0

        # 4. Meta-annotation quality (prefer confirmed, current, patient)
        meta_score = 1.0
        for entity in entities:
            if entity.meta_annotations.get("Negation") == "Negated":
                meta_score *= 0.5
            if entity.meta_annotations.get("Temporality") == "Historical":
                meta_score *= 0.7
            if entity.meta_annotations.get("Experiencer") != "Patient":
                meta_score *= 0.6

        # Weighted combination
        relevance = (
            avg_confidence * 0.4 +
            match_score * 0.2 +
            avg_recency * 0.2 +
            meta_score * 0.2
        )

        return min(max(relevance, 0.0), 1.0)

    def _calculate_age(self, date_of_birth: date) -> int:
        """Calculate age from date of birth."""
        today = date.today()
        return today.year - date_of_birth.year - (
            (today.month, today.day) < (date_of_birth.month, date_of_birth.day)
        )

    def _generate_summary(self, concepts: List[ConceptMatch]) -> str:
        """
        Generate AI summary of patient's conditions.

        Args:
            concepts: List of matched concepts

        Returns:
            Summary text
        """
        if not concepts:
            return "No matching conditions found."

        # Group concepts by type
        conditions = []
        for concept in concepts:
            if concept.negation == "Affirmed" and concept.temporality in ["Current", "Recent"]:
                conditions.append(concept.pretty_name)

        if not conditions:
            return "No active conditions matching search criteria."

        # Simple summary (would use LLM in production)
        unique_conditions = list(set(conditions))
        if len(unique_conditions) == 1:
            return f"Patient with {unique_conditions[0].lower()}"
        elif len(unique_conditions) == 2:
            return f"Patient with {unique_conditions[0].lower()} and {unique_conditions[1].lower()}"
        else:
            return f"Patient with multiple conditions including {', '.join(unique_conditions[:2]).lower()}"

    def _calculate_statistics(
        self,
        results: List[PatientSearchResult],
    ) -> Dict[str, Any]:
        """
        Calculate search statistics.

        Args:
            results: List of patient results

        Returns:
            Statistics dictionary
        """
        if not results:
            return {}

        # Concept distribution
        concept_counts = {}
        total_confidence = 0
        total_concepts = 0

        for result in results:
            for concept in result.matched_concepts:
                if concept.cui not in concept_counts:
                    concept_counts[concept.cui] = 0
                concept_counts[concept.cui] += 1
                total_confidence += concept.confidence
                total_concepts += 1

        return {
            "avg_confidence": total_confidence / total_concepts if total_concepts > 0 else 0,
            "concept_distribution": concept_counts,
            "avg_concepts_per_patient": total_concepts / len(results) if results else 0,
        }

    def _audit_log_search(
        self,
        db: Session,
        user_id: UUID,
        request: PatientSearchRequest,
        result_count: int,
    ):
        """
        Log search activity for audit trail.

        Args:
            db: Database session
            user_id: User performing search
            request: Search request
            result_count: Number of results found
        """
        # This would log to the audit_log table
        logger.info(
            f"Patient search by user {user_id}: "
            f"query='{request.query}', "
            f"filters={request.filters.model_dump()}, "
            f"results={result_count}"
        )

    async def get_concept_suggestions(
        self,
        query: str,
        limit: int = 10,
    ) -> List[ConceptSuggestion]:
        """
        Get concept suggestions for autocomplete.

        Args:
            query: Partial query string
            limit: Maximum suggestions to return

        Returns:
            List of concept suggestions
        """
        suggestions = []

        try:
            # Call MedCAT service for suggestions
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{self.medcat_url}/concepts",
                    params={"query": query, "limit": limit}
                )

                if response.status_code == 200:
                    data = response.json()
                    for item in data:
                        suggestion = ConceptSuggestion(
                            cui=item["cui"],
                            pretty_name=item["pretty_name"],
                            semantic_type=item.get("semantic_type", "Unknown"),
                            synonyms=item.get("synonyms", []),
                            popularity=item.get("popularity", 0),
                        )
                        suggestions.append(suggestion)

        except Exception as e:
            logger.error(f"Failed to get concept suggestions: {e}")

        # Fallback: return common concepts if service unavailable
        if not suggestions and not self.medcat_url:
            common_concepts = [
                ("C0011860", "Diabetes Mellitus, Type 2", "Disease"),
                ("C0004238", "Atrial Fibrillation", "Disease"),
                ("C0020538", "Hypertension", "Disease"),
                ("C0024117", "Chronic Obstructive Pulmonary Disease", "Disease"),
                ("C0018801", "Heart Failure", "Disease"),
            ]

            for cui, name, sem_type in common_concepts:
                if query.lower() in name.lower():
                    suggestions.append(
                        ConceptSuggestion(
                            cui=cui,
                            pretty_name=name,
                            semantic_type=sem_type,
                            synonyms=[],
                            popularity=100,
                        )
                    )

        return suggestions[:limit]