"""Search API endpoints.

Provides:
- Full-text document search with faceting
- Autocomplete suggestions
- Search analytics (admin only)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from elasticsearch import AsyncElasticsearch
import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_current_active_user, require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.elasticsearch.search_service import (
    SearchService,
    SearchQuery,
    SearchResponse
)
from app.services.audit_service import AuditAction, log_audit
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Dependency to get Elasticsearch client
async def get_es_client() -> AsyncElasticsearch:
    """Get Elasticsearch client."""
    client = AsyncElasticsearch(
        hosts=[settings.ELASTICSEARCH_URL],
        verify_certs=False  # For development
    )
    try:
        yield client
    finally:
        await client.close()


# Dependency to get Redis client
async def get_redis_client() -> redis.Redis:
    """Get Redis client for caching."""
    client = redis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=False
    )
    try:
        yield client
    finally:
        await client.close()


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., description="Search query", min_length=1),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    date_from: Optional[str] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[str] = Query(None, description="End date (ISO format)"),
    department: Optional[str] = Query(None, description="Filter by department"),
    author: Optional[str] = Query(None, description="Filter by author"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    current_user: User = Depends(get_current_active_user),
    es_client: AsyncElasticsearch = Depends(get_es_client),
    redis_client: redis.Redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    """
    Search documents with full-text query.

    Features:
    - Multi-field search (title, content, author)
    - Faceted filtering (document type, department, date range)
    - Result highlighting
    - Relevance ranking (BM25)

    Example:
        GET /api/v1/search?q=diabetes+mellitus&document_type=discharge_summary&page=1&page_size=20

    Returns:
        SearchResponse with results, facets, and metadata
    """
    try:
        # Build search query
        search_query = SearchQuery(
            q=q,
            document_type=document_type,
            date_from=date_from,
            date_to=date_to,
            department=department,
            author=author,
            page=page,
            page_size=page_size
        )

        # Execute search
        search_service = SearchService(es_client, redis_client, db)
        response = await search_service.search(
            query=search_query,
            user_id=str(current_user.id)
        )

        # Audit log search (HIPAA compliance)
        await log_audit(
            db=db,
            user_id=current_user.id,
            action=AuditAction.SEARCH,
            resource_type="document",
            details={
                "query": q,
                "filters": {
                    "document_type": document_type,
                    "date_from": date_from,
                    "date_to": date_to,
                    "department": department,
                    "author": author
                },
                "total_results": response.total_results,
                "execution_time_ms": response.execution_time_ms
            }
        )

        return response

    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/search/suggest")
async def get_search_suggestions(
    q: str = Query(..., description="Partial query", min_length=2),
    size: int = Query(5, ge=1, le=10, description="Max suggestions"),
    current_user: User = Depends(get_current_active_user),
    es_client: AsyncElasticsearch = Depends(get_es_client),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> dict:
    """
    Get autocomplete suggestions for search query.

    Features:
    - Phrase-based suggestions
    - Redis caching (1 hour TTL)
    - Fast response (<200ms)

    Example:
        GET /api/v1/search/suggest?q=diab&size=5

    Returns:
        {"query": "diab", "suggestions": ["diabetes", "diabetic ketoacidosis", ...]}
    """
    try:
        # Get suggestions
        search_service = SearchService(es_client, redis_client)
        suggestions = await search_service.get_suggestions(
            partial_query=q,
            size=size
        )

        return {
            "query": q,
            "suggestions": suggestions
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Suggestions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Suggestions failed: {str(e)}"
        )


@router.get("/search/analytics")
async def get_search_analytics(
    date_from: str = Query(..., description="Start date (ISO format)"),
    date_to: str = Query(..., description="End date (ISO format)"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    es_client: AsyncElasticsearch = Depends(get_es_client),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Get search analytics (admin only).

    Features:
    - Top queries
    - Zero-result queries
    - Search volume metrics
    - Average response time

    Example:
        GET /api/v1/search/analytics?date_from=2023-11-01&date_to=2023-11-30&limit=50

    Returns:
        Analytics dictionary with top queries, zero-result queries, and metrics
    """
    try:
        search_service = SearchService(es_client, None, db)
        analytics = await search_service.get_analytics(
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )

        # Audit log analytics access
        await log_audit(
            db=db,
            user_id=current_user.id,
            action=AuditAction.VIEW,
            resource_type="search_analytics",
            details={
                "date_from": date_from,
                "date_to": date_to
            }
        )

        return analytics

    except Exception as e:
        logger.error(f"Analytics failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analytics failed: {str(e)}"
        )
