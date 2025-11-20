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
    query_type: Optional[str] = Query("standard", description="Query type: standard, boolean, wildcard, fuzzy, proximity, range, regex"),
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
    Search documents with advanced query support.

    Features:
    - Multi-field search (title, content, author)
    - Advanced query types:
      - standard: Basic multi-field search with fuzziness
      - boolean: AND/OR/NOT operators (e.g., "diabetes AND hypertension")
      - wildcard: Pattern matching with * and ? (e.g., "diabet*")
      - fuzzy: Typo tolerance with ~ (e.g., "diabets~")
      - proximity: Terms within distance (e.g., "heart NEAR/3 failure")
      - range: Numeric/date ranges (e.g., "age:[18 TO 65]")
      - regex: Regular expressions (e.g., "/diabet.*/")
    - Faceted filtering (document type, department, date range)
    - Result highlighting
    - Relevance ranking (BM25)

    Examples:
        GET /api/v1/search?q=diabetes+mellitus&query_type=standard
        GET /api/v1/search?q=diabetes+AND+hypertension&query_type=boolean
        GET /api/v1/search?q=diabet*&query_type=wildcard
        GET /api/v1/search?q=/heart.%2B(failure|disease)/&query_type=regex

    Returns:
        SearchResponse with results, facets, and metadata
    """
    try:
        # Build search query
        search_query = SearchQuery(
            q=q,
            query_type=query_type,
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


@router.get("/search/query-help")
async def get_query_help(
    query_type: Optional[str] = Query(None, description="Get help for specific query type"),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Get query syntax help and examples.

    Provides documentation and examples for each query type.

    Args:
        query_type: Optional specific query type to get help for

    Returns:
        Query syntax documentation and examples
    """
    query_help = {
        "standard": {
            "description": "Basic multi-field search with automatic fuzziness and relevance ranking",
            "syntax": "Simple keywords or phrases",
            "examples": [
                {"query": "diabetes mellitus", "description": "Search for both terms"},
                {"query": '"heart failure"', "description": "Exact phrase search"},
                {"query": "cardio", "description": "Partial word matching with fuzziness"}
            ],
            "use_case": "General document search with typo tolerance"
        },
        "boolean": {
            "description": "Advanced search with AND, OR, NOT operators",
            "syntax": "term1 AND term2, term1 OR term2, term1 NOT term2",
            "examples": [
                {"query": "diabetes AND hypertension", "description": "Both conditions must be present"},
                {"query": "diabetes OR hypertension", "description": "Either condition"},
                {"query": "diabetes NOT family", "description": "Diabetes but exclude family history"},
                {"query": '"heart failure" AND (diabetes OR hypertension)', "description": "Complex boolean logic"}
            ],
            "use_case": "Precise searches requiring specific term combinations"
        },
        "wildcard": {
            "description": "Pattern matching with * (any characters) and ? (single character)",
            "syntax": "term*, te?m, *term*",
            "examples": [
                {"query": "diabet*", "description": "Matches diabetes, diabetic, diabetology"},
                {"query": "wom?n", "description": "Matches woman, women"},
                {"query": "*cardia*", "description": "Matches cardiac, myocardial, tachycardia"},
                {"query": "bp_*:>140", "description": "Field wildcards for bp_systolic, bp_diastolic"}
            ],
            "use_case": "Finding variations of medical terms or partial matches",
            "warning": "Leading wildcards (*term) can be slow on large datasets"
        },
        "fuzzy": {
            "description": "Typo-tolerant search with edit distance",
            "syntax": "term~, term~2, \"phrase\"~n",
            "examples": [
                {"query": "diabets~", "description": "Finds diabetes with typo tolerance"},
                {"query": "diabets~1", "description": "Allow 1 character difference"},
                {"query": '"heart failure"~2', "description": "Phrase with up to 2 words between"},
                {"query": "diagnosis:cardiak~", "description": "Field-specific fuzzy search"}
            ],
            "use_case": "Handling misspellings and typos in medical documentation"
        },
        "proximity": {
            "description": "Find terms within specified word distance",
            "syntax": "term1 NEAR term2, term1 NEAR/n term2, term1 W/n term2",
            "examples": [
                {"query": "diabetes NEAR complications", "description": "Within 5 words (default)"},
                {"query": "heart NEAR/3 failure", "description": "Within 3 words"},
                {"query": "blood W/2 pressure", "description": "Within 2 words"},
                {"query": "myocardial ADJ infarction", "description": "Adjacent terms"}
            ],
            "use_case": "Finding related concepts that appear near each other"
        },
        "range": {
            "description": "Search numeric or date ranges",
            "syntax": "field:[min TO max], field:>value, field:<=value",
            "examples": [
                {"query": "age:[18 TO 65]", "description": "Age between 18 and 65 (inclusive)"},
                {"query": "bp_systolic:>140", "description": "Systolic BP greater than 140"},
                {"query": "date:[2023-01-01 TO 2023-12-31]", "description": "Documents from 2023"},
                {"query": "glucose:{4.0 TO 7.0}", "description": "Exclusive range (not including endpoints)"},
                {"query": "date:[2023-01-01 TO *]", "description": "From date to present"}
            ],
            "use_case": "Filtering by numeric values or date ranges"
        },
        "regex": {
            "description": "Regular expression pattern matching",
            "syntax": "/pattern/, /pattern/flags, field:/pattern/",
            "examples": [
                {"query": "/diabet.*/", "description": "Regex for diabetes variations"},
                {"query": "/heart.+(failure|disease)/", "description": "Complex pattern with groups"},
                {"query": "/[Cc]ardio.*/", "description": "Case variations"},
                {"query": "diagnosis:/^[A-Z]\\d{2}\\.\\d/", "description": "ICD-10 code pattern"},
                {"query": "/diabet.*/i", "description": "Case-insensitive regex"}
            ],
            "use_case": "Complex pattern matching for codes or structured data",
            "warning": "Regex queries can be very expensive. Use with caution."
        }
    }

    if query_type:
        # Return help for specific query type
        if query_type in query_help:
            return {
                "query_type": query_type,
                **query_help[query_type]
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown query type: {query_type}"
            )

    # Return all query types
    return {
        "available_query_types": list(query_help.keys()),
        "query_types": query_help,
        "tips": [
            "Start with 'standard' for general searches",
            "Use 'boolean' for precise term combinations",
            "Use 'fuzzy' when dealing with potential typos",
            "Use 'proximity' for related concepts",
            "Use 'range' for numeric or date filtering",
            "Combine query types with filters for best results"
        ]
    }


@router.post("/search/validate")
async def validate_search_query(
    q: str = Query(..., description="Query to validate"),
    query_type: str = Query("standard", description="Query type to validate"),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """
    Validate a search query without executing it.

    Useful for providing real-time feedback in search UI.

    Args:
        q: Query string to validate
        query_type: Type of query to validate

    Returns:
        Validation result with parsed structure or error details
    """
    try:
        # Try to build the query to validate syntax
        filters = {}

        if query_type == "boolean":
            query_dict = SearchQueryBuilder.build_boolean_query(q, filters)
        elif query_type == "wildcard":
            query_dict = SearchQueryBuilder.build_wildcard_query(q, filters)
        elif query_type == "fuzzy":
            query_dict = SearchQueryBuilder.build_fuzzy_query(q, filters)
        elif query_type == "proximity":
            query_dict = SearchQueryBuilder.build_proximity_query(q, filters)
        elif query_type == "range":
            query_dict = SearchQueryBuilder.build_range_query(q, filters)
        elif query_type == "regex":
            query_dict = SearchQueryBuilder.build_regex_query(q, filters)
        elif query_type == "standard":
            query_dict = SearchQueryBuilder.build_query(q)
        else:
            return {
                "valid": False,
                "error": f"Unknown query type: {query_type}",
                "query": q
            }

        # Query is valid if we got here
        return {
            "valid": True,
            "query": q,
            "query_type": query_type,
            "elasticsearch_query": query_dict,
            "message": "Query syntax is valid"
        }

    except Exception as e:
        return {
            "valid": False,
            "query": q,
            "query_type": query_type,
            "error": str(e),
            "message": "Query syntax is invalid",
            "suggestion": "Check the query syntax using /search/query-help endpoint"
        }


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
