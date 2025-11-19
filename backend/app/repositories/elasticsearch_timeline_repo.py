"""
Elasticsearch Timeline Repository for clinical concept queries.

This module provides async repository methods for querying the clinical_concepts
Elasticsearch index with temporal and meta-annotation filtering.
"""

from elasticsearch import AsyncElasticsearch
from typing import List, Optional, Dict, Any
from datetime import datetime
import os

from app.schemas.timeline import ConceptMention, DateRange, MetaAnnotations


class ElasticsearchTimelineRepository:
    """Repository for querying clinical concepts from Elasticsearch.

    Provides methods for:
    - Querying concepts by patient with temporal and meta-annotation filters
    - Aggregating concept frequency by date
    - Supporting timeline visualizations
    """

    def __init__(self, es_url: Optional[str] = None):
        """Initialize Elasticsearch client.

        Args:
            es_url: Elasticsearch URL (default: from ELASTICSEARCH_URL env var or localhost:9200)
        """
        if es_url is None:
            es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
        self.es = AsyncElasticsearch([es_url])
        self.index_name = "clinical_concepts"

    async def query_concepts_by_patient(
        self,
        patient_id: str,
        concept_filter: Optional[List[str]] = None,
        date_range: Optional[DateRange] = None,
        meta_annotations: Optional[Dict[str, Any]] = None,
        size: int = 1000
    ) -> List[ConceptMention]:
        """Query concepts for a patient with optional filters.

        Args:
            patient_id: UUID of the patient
            concept_filter: List of concept CUIs to filter by (AND logic)
            date_range: Date range filter (inclusive)
            meta_annotations: Meta-annotation filters (key-value pairs)
                Example: {"Negation": "Affirmed", "Experiencer": "Patient"}
                Supports list values: {"Temporality": ["Current", "Recent"]}
            size: Maximum number of results (default 1000)

        Returns:
            List of ConceptMention objects sorted by date (ascending)

        Example:
            >>> repo = ElasticsearchTimelineRepository()
            >>> mentions = await repo.query_concepts_by_patient(
            ...     patient_id="patient-123",
            ...     concept_filter=["C0011849"],  # Diabetes
            ...     meta_annotations={"Negation": "Affirmed", "Experiencer": "Patient"}
            ... )
        """
        # Build Elasticsearch query
        query: Dict[str, Any] = {
            "bool": {
                "must": [
                    {"term": {"patient_id": patient_id}}
                ]
            }
        }

        # Add concept filter
        if concept_filter:
            query["bool"]["must"].append({
                "terms": {"concept_cui": concept_filter}
            })

        # Add date range filter
        if date_range:
            query["bool"]["must"].append({
                "range": {
                    "date": {
                        "gte": date_range.start.isoformat(),
                        "lte": date_range.end.isoformat()
                    }
                }
            })

        # Add meta-annotation filters
        if meta_annotations:
            for key, value in meta_annotations.items():
                if isinstance(value, list):
                    # List values: OR logic (match any value)
                    query["bool"]["must"].append({
                        "terms": {f"meta_annotations.{key}": value}
                    })
                else:
                    # Single value: exact match
                    query["bool"]["must"].append({
                        "term": {f"meta_annotations.{key}": value}
                    })

        # Execute query
        result = await self.es.search(
            index=self.index_name,
            query=query,
            sort=[{"date": "asc"}],
            size=size
        )

        # Parse results into ConceptMention objects
        mentions = []
        for hit in result["hits"]["hits"]:
            source = hit["_source"]

            # Parse meta_annotations into MetaAnnotations object
            meta_anns = MetaAnnotations(
                Negation=source["meta_annotations"]["Negation"],
                Temporality=source["meta_annotations"]["Temporality"],
                Experiencer=source["meta_annotations"]["Experiencer"],
                Certainty=source["meta_annotations"]["Certainty"]
            )

            # Create ConceptMention
            mention = ConceptMention(
                document_id=source["document_id"],
                date=datetime.fromisoformat(source["date"].replace("Z", "+00:00")),
                sentence=source["sentence"],
                meta_annotations=meta_anns,
                confidence=source["confidence"]
            )
            mentions.append(mention)

        return mentions

    async def aggregate_concepts_by_date(
        self,
        patient_id: str,
        granularity: str = "month",
        concept_filter: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Aggregate concept frequency by date for timeline visualizations.

        Args:
            patient_id: UUID of the patient
            granularity: Time bucket size ("day", "week", "month", "quarter", "year")
            concept_filter: Optional list of concept CUIs to filter by

        Returns:
            List of date buckets with concept counts
            Example:
                [
                    {
                        "key": "2023-01-01T00:00:00.000Z",
                        "doc_count": 15,
                        "concept_counts": {
                            "buckets": [
                                {"key": "C0011849", "doc_count": 5},
                                {"key": "C0020538", "doc_count": 3}
                            ]
                        }
                    }
                ]

        Example:
            >>> repo = ElasticsearchTimelineRepository()
            >>> buckets = await repo.aggregate_concepts_by_date(
            ...     patient_id="patient-123",
            ...     granularity="month"
            ... )
        """
        # Build query
        query: Dict[str, Any] = {
            "term": {"patient_id": patient_id}
        }

        # Add concept filter if provided
        if concept_filter:
            query = {
                "bool": {
                    "must": [
                        {"term": {"patient_id": patient_id}},
                        {"terms": {"concept_cui": concept_filter}}
                    ]
                }
            }

        # Build aggregation
        aggs = {
            "concepts_by_time": {
                "date_histogram": {
                    "field": "date",
                    "calendar_interval": granularity,
                    "min_doc_count": 1  # Only return buckets with data
                },
                "aggs": {
                    "concept_counts": {
                        "terms": {
                            "field": "concept_cui",
                            "size": 50  # Top 50 concepts per time bucket
                        }
                    }
                }
            }
        }

        # Execute query
        result = await self.es.search(
            index=self.index_name,
            query=query,
            aggs=aggs,
            size=0  # We only want aggregations, not documents
        )

        # Return aggregation buckets
        return result["aggregations"]["concepts_by_time"]["buckets"]

    async def close(self):
        """Close Elasticsearch connection.

        Should be called when repository is no longer needed.
        """
        await self.es.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
