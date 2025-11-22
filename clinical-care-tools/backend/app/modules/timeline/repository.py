"""
Elasticsearch Timeline Repository

Implements Elasticsearch queries for temporal concept aggregation and filtering.
Follows repository pattern for separation of concerns.
"""

from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch


class ElasticsearchTimelineRepository:
    """
    Repository for querying MedCAT annotations from Elasticsearch.

    Provides temporal concept aggregation and filtering capabilities
    for patient timeline visualization.
    """

    def __init__(self, es_client: AsyncElasticsearch, index_name: str = "medcat_annotations"):
        """
        Initialize repository with Elasticsearch client.

        Args:
            es_client: Async Elasticsearch client instance
            index_name: Name of the Elasticsearch index (default: medcat_annotations)
        """
        self.es_client = es_client
        self.index_name = index_name

    async def query_patient_concepts(
        self,
        patient_id: UUID,
        concept_cuis: Optional[List[str]] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        meta_annotations: Optional[Dict[str, Any]] = None,
        document_types: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Query patient concepts from Elasticsearch with filters.

        Args:
            patient_id: Patient UUID to filter by
            concept_cuis: List of concept CUIs to filter by (optional)
            date_start: Start date for document date range (optional)
            date_end: End date for document date range (optional)
            meta_annotations: Dict of meta-annotation filters (optional)
                - negation: str (e.g., "Affirmed")
                - experiencer: str (e.g., "Patient")
                - temporality: List[str] (e.g., ["Current", "Recent"])
                - certainty: List[str] (e.g., ["Confirmed"])
            document_types: List of document types to filter by (optional)
            limit: Maximum number of results (default: 1000)

        Returns:
            List of concept annotations with metadata
        """
        # Build bool query with must clauses
        must_clauses = []

        # Required: patient_id filter
        must_clauses.append({
            "term": {"patient_id": str(patient_id)}
        })

        # Optional: concept CUI filter
        if concept_cuis:
            must_clauses.append({
                "terms": {"concept_cui": concept_cuis}
            })

        # Optional: date range filter
        if date_start or date_end:
            range_filter = {}
            if date_start:
                range_filter["gte"] = date_start.isoformat()
            if date_end:
                range_filter["lte"] = date_end.isoformat()

            must_clauses.append({
                "range": {"document_date": range_filter}
            })

        # Optional: document type filter
        if document_types:
            must_clauses.append({
                "terms": {"document_type": document_types}
            })

        # Optional: meta-annotation filters
        if meta_annotations:
            # Negation filter (single value)
            if "negation" in meta_annotations:
                must_clauses.append({
                    "term": {"meta_anns.Negation": meta_annotations["negation"]}
                })

            # Experiencer filter (single value)
            if "experiencer" in meta_annotations:
                must_clauses.append({
                    "term": {"meta_anns.Experiencer": meta_annotations["experiencer"]}
                })

            # Temporality filter (multiple values)
            if "temporality" in meta_annotations:
                must_clauses.append({
                    "terms": {"meta_anns.Temporality": meta_annotations["temporality"]}
                })

            # Certainty filter (multiple values)
            if "certainty" in meta_annotations:
                must_clauses.append({
                    "terms": {"meta_anns.Certainty": meta_annotations["certainty"]}
                })

        # Build complete query
        query = {
            "bool": {
                "must": must_clauses
            }
        }

        # Execute search
        response = await self.es_client.search(
            index=self.index_name,
            body={
                "query": query,
                "size": limit,
                "sort": [
                    {"document_date": {"order": "asc"}},
                    {"start_char": {"order": "asc"}}
                ]
            }
        )

        # Extract and format results
        hits = response.get("hits", {}).get("hits", [])
        results = []

        for hit in hits:
            source = hit["_source"]
            results.append(source)

        return results

    async def aggregate_concept_frequency(
        self,
        patient_id: UUID,
        concept_cuis: Optional[List[str]] = None,
        date_start: Optional[date] = None,
        date_end: Optional[date] = None,
        granularity: str = "month",
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Aggregate concept frequency over time using date histogram.

        Args:
            patient_id: Patient UUID to filter by
            concept_cuis: List of concept CUIs to aggregate (optional, aggregates all if None)
            date_start: Start date for aggregation range (optional)
            date_end: End date for aggregation range (optional)
            granularity: Time granularity (day, week, month, year) (default: month)

        Returns:
            Dict mapping concept CUI to list of {date, count} dicts
            Example:
            {
                "C0011860": [
                    {"date": "2024-01-01", "count": 5},
                    {"date": "2024-02-01", "count": 3}
                ]
            }
        """
        # Build query filters (same as query_patient_concepts)
        must_clauses = [
            {"term": {"patient_id": str(patient_id)}}
        ]

        if concept_cuis:
            must_clauses.append({
                "terms": {"concept_cui": concept_cuis}
            })

        if date_start or date_end:
            range_filter = {}
            if date_start:
                range_filter["gte"] = date_start.isoformat()
            if date_end:
                range_filter["lte"] = date_end.isoformat()

            must_clauses.append({
                "range": {"document_date": range_filter}
            })

        query = {
            "bool": {
                "must": must_clauses
            }
        }

        # Build aggregation
        aggs = {
            "concepts": {
                "terms": {
                    "field": "concept_cui",
                    "size": 1000  # Max concepts to aggregate
                },
                "aggs": {
                    "date_histogram": {
                        "date_histogram": {
                            "field": "document_date",
                            "calendar_interval": granularity,
                            "format": "yyyy-MM-dd"
                        }
                    }
                }
            }
        }

        # Execute aggregation query
        response = await self.es_client.search(
            index=self.index_name,
            body={
                "query": query,
                "size": 0,  # Don't return documents, only aggregations
                "aggs": aggs
            }
        )

        # Parse aggregation results
        concept_buckets = response.get("aggregations", {}).get("concepts", {}).get("buckets", [])

        # Format results
        results = {}
        for concept_bucket in concept_buckets:
            concept_cui = concept_bucket["key"]
            date_buckets = concept_bucket.get("date_histogram", {}).get("buckets", [])

            # Convert to list of {date, count} dicts
            frequency_data = []
            for date_bucket in date_buckets:
                frequency_data.append({
                    "date": date_bucket["key_as_string"],
                    "count": date_bucket["doc_count"]
                })

            results[concept_cui] = frequency_data

        return results
