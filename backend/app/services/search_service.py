"""
Search Service

Handles document search using Elasticsearch with filtering, pagination,
highlighting, analytics tracking, and audit logging.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from elasticsearch import AsyncElasticsearch
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.search_analytics import SearchAnalytics
from app.models.user import User
from app.schemas.search import (
    SearchRequest,
    SearchResponse,
    SearchResultDocument,
    Highlight,
    Facets,
    FacetValue,
    SortBy
)
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class SearchService:
    """
    Service for full-text document search.

    Responsibilities:
    - Build Elasticsearch queries with multi_match on title/content
    - Apply filters (document_type, author, department, date_range)
    - Execute search with highlighting and facets
    - Parse ES response to SearchResponse
    - Track analytics in search_analytics table
    - Audit log all searches

    Usage:
        service = SearchService(es_client=get_es_client(), db_session=db)
        response = await service.search_documents(
            request=SearchRequest(query="diabetes"),
            user=current_user,
            ip_address="127.0.0.1"
        )
    """

    def __init__(self, es_client: AsyncElasticsearch, db_session: AsyncSession):
        """
        Initialize SearchService.

        Args:
            es_client: Elasticsearch async client
            db_session: SQLAlchemy async database session
        """
        self.es = es_client
        self.db = db_session

    async def search_documents(
        self,
        request: SearchRequest,
        user: User,
        ip_address: Optional[str] = None
    ) -> SearchResponse:
        """
        Search documents using Elasticsearch.

        Process:
        1. Build Elasticsearch query (multi_match on title/content)
        2. Apply filters (document_type, author, department, date_range)
        3. Add field boosting (title^10, content^1)
        4. Execute search with highlighting
        5. Parse ES response to SearchResponse
        6. Track analytics (search_analytics table)
        7. Audit log search

        Args:
            request: Search request with query, filters, pagination
            user: Authenticated user performing search
            ip_address: Client IP address for audit logging

        Returns:
            SearchResponse with documents, facets, and metadata
        """
        start_time = datetime.utcnow()

        # Build Elasticsearch query
        es_query = self._build_query(request)

        # Execute search
        es_response = await self.es.search(
            index="documents",
            body=es_query,
            from_=(request.page - 1) * request.page_size,
            size=request.page_size
        )

        execution_time_ms = es_response["took"]

        # Parse response
        search_response = self._parse_response(
            es_response=es_response,
            request=request,
            execution_time_ms=execution_time_ms
        )

        # Track analytics
        await self._track_analytics(
            request=request,
            user=user,
            results_count=search_response.total_results,
            execution_time_ms=execution_time_ms
        )

        # Audit log
        await self._log_audit_trail(
            request=request,
            user=user,
            ip_address=ip_address,
            results_count=search_response.total_results
        )

        return search_response

    def _build_query(self, request: SearchRequest) -> dict:
        """
        Build Elasticsearch query from search request.

        Args:
            request: Search request with query and filters

        Returns:
            Elasticsearch query dict
        """
        # Base multi_match query with field boosting
        must_clause = {
            "multi_match": {
                "query": request.query,
                "fields": ["title^10", "content^1"],  # title boosted 10x
                "type": "best_fields",
                "operator": "or"
            }
        }

        # Build filter clauses
        filter_clauses = []

        if request.filters:
            # Document type filter
            if request.filters.document_types:
                filter_clauses.append({
                    "terms": {"document_type": request.filters.document_types}
                })

            # Author filter
            if request.filters.authors:
                filter_clauses.append({
                    "terms": {"author": request.filters.authors}
                })

            # Department filter
            if request.filters.departments:
                filter_clauses.append({
                    "terms": {"department": request.filters.departments}
                })

            # Date range filter
            if request.filters.date_from or request.filters.date_to:
                date_range = {}
                if request.filters.date_from:
                    date_range["gte"] = request.filters.date_from.isoformat()
                if request.filters.date_to:
                    date_range["lte"] = request.filters.date_to.isoformat()

                filter_clauses.append({
                    "range": {"date": date_range}
                })

        # Combine query and filters
        query = {
            "bool": {
                "must": [must_clause],
                "filter": filter_clauses
            }
        }

        # Add sorting
        sort = self._build_sort(request.sort)

        # Add highlighting
        highlight = {
            "fields": {
                "title": {
                    "number_of_fragments": 1,
                    "fragment_size": 150
                },
                "content": {
                    "number_of_fragments": 3,
                    "fragment_size": 150
                }
            },
            "pre_tags": ["<em>"],
            "post_tags": ["</em>"]
        }

        # Add aggregations for facets
        aggs = {
            "document_types": {
                "terms": {"field": "document_type", "size": 20}
            },
            "authors": {
                "terms": {"field": "author", "size": 20}
            },
            "departments": {
                "terms": {"field": "department", "size": 20}
            }
        }

        return {
            "query": query,
            "highlight": highlight,
            "aggs": aggs,
            "sort": sort
        }

    def _build_sort(self, sort_by: SortBy) -> list:
        """
        Build Elasticsearch sort clause.

        Args:
            sort_by: Sort option (RELEVANCE, DATE, TITLE)

        Returns:
            Elasticsearch sort list
        """
        if sort_by == SortBy.DATE:
            return [{"date": {"order": "desc"}}]
        elif sort_by == SortBy.TITLE:
            return [{"title.raw": {"order": "asc"}}]
        else:  # SortBy.RELEVANCE (default)
            return ["_score"]

    def _parse_response(
        self,
        es_response: dict,
        request: SearchRequest,
        execution_time_ms: int
    ) -> SearchResponse:
        """
        Parse Elasticsearch response to SearchResponse.

        Args:
            es_response: Raw Elasticsearch response
            request: Original search request
            execution_time_ms: Query execution time

        Returns:
            SearchResponse with documents and facets
        """
        # Parse documents
        documents = []
        for hit in es_response["hits"]["hits"]:
            source = hit["_source"]

            # Parse highlights
            highlights = []
            if "highlight" in hit:
                for field, snippets in hit["highlight"].items():
                    highlights.append(Highlight(field=field, snippets=snippets))

            # Normalize relevance score to 0.0-1.0
            # Elasticsearch scores are unbounded, typical range 0-30
            # We normalize by dividing by 30 and capping at 1.0
            raw_score = hit.get("_score", 0.0)
            normalized_score = min(raw_score / 30.0, 1.0)

            doc = SearchResultDocument(
                document_id=UUID(source["document_id"]),
                title=source["title"],
                document_type=source["document_type"],
                author=source.get("author"),
                date=datetime.fromisoformat(source["date"]) if source.get("date") else None,
                department=source.get("department"),
                relevance_score=normalized_score,
                highlights=highlights
            )
            documents.append(doc)

        # Parse facets
        facets = self._parse_facets(es_response.get("aggregations", {}))

        # Get total results
        total_results = es_response["hits"]["total"]["value"]

        return SearchResponse(
            query=request.query,
            total_results=total_results,
            page=request.page,
            page_size=request.page_size,
            documents=documents,
            facets=facets,
            execution_time_ms=execution_time_ms
        )

    def _parse_facets(self, aggregations: dict) -> Facets:
        """
        Parse Elasticsearch aggregations to Facets.

        Args:
            aggregations: Elasticsearch aggregations dict

        Returns:
            Facets with document_types, authors, departments
        """
        def parse_terms_agg(agg_name: str) -> list[FacetValue]:
            """Parse terms aggregation to list of FacetValue."""
            if agg_name not in aggregations:
                return []
            buckets = aggregations[agg_name].get("buckets", [])
            return [
                FacetValue(value=bucket["key"], count=bucket["doc_count"])
                for bucket in buckets
            ]

        return Facets(
            document_types=parse_terms_agg("document_types"),
            authors=parse_terms_agg("authors"),
            departments=parse_terms_agg("departments")
        )

    async def _track_analytics(
        self,
        request: SearchRequest,
        user: User,
        results_count: int,
        execution_time_ms: int
    ) -> None:
        """
        Track search analytics in database.

        Args:
            request: Search request
            user: User who performed search
            results_count: Number of results returned
            execution_time_ms: Query execution time
        """
        analytics = SearchAnalytics(
            user_id=user.id,
            query=request.query,
            filters=request.filters.model_dump() if request.filters else {},
            results_count=results_count,
            execution_time_ms=execution_time_ms,
            clicked_documents=[]  # Will be updated when user clicks documents
        )

        self.db.add(analytics)
        await self.db.commit()
        await self.db.refresh(analytics)

        logger.info(
            f"Search analytics tracked: user={user.id}, query='{request.query}', "
            f"results={results_count}, time={execution_time_ms}ms"
        )

    async def _log_audit_trail(
        self,
        request: SearchRequest,
        user: User,
        ip_address: Optional[str],
        results_count: int
    ) -> None:
        """
        Log search to audit trail.

        Args:
            request: Search request
            user: User who performed search
            ip_address: Client IP address
            results_count: Number of results returned
        """
        await AuditService.log_action(
            db=self.db,
            user=user,
            action="SEARCH_EXECUTED",
            resource_type="search",
            details={
                "query": request.query,
                "filters": request.filters.model_dump() if request.filters else {},
                "results_count": results_count
            },
            ip_address=ip_address
        )

        logger.info(f"Search audit logged: user={user.username}, query='{request.query}'")
