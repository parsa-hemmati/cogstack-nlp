"""
Full-Text Search API Endpoints

Handles document full-text search with Elasticsearch.
"""
import io
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.clients.elasticsearch_client import get_es_client
from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.saved_search import SavedSearch
from app.models.user import User
from app.schemas.search import (
    ExportFormat,
    QueryAnalytics,
    QueryValidationResult,
    SearchAnalyticsAggregateResponse,
    SearchExportRequest,
    SearchRequest,
    SearchResponse,
    SearchSuggestion,
    SearchSuggestionsResponse,
    SavedSearchCreate,
    SavedSearchResponse,
    SlowQueryAnalytics,
    TrendDataPoint,
)
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.export_service import ExportService
from app.services.search_service import SearchService
from app.middleware.rate_limit import rate_limit_search_dependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(rate_limit_search_dependency)])
async def search_documents(
    search_request: SearchRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Full-text search for documents.

    **Authorization**: Requires valid JWT token (any authenticated user)

    **Workflow**:
    1. Validate search request (Pydantic validation)
    2. Execute Elasticsearch query with filters
    3. Apply pagination and sorting
    4. Track analytics (search_analytics table)
    5. Log audit trail (HIPAA compliance)
    6. Return results with highlights and facets

    **Search Features**:
    - Keyword search (multi_match on title and content)
    - Field boosting (title^10, content^1)
    - Filters: document_types, authors, departments, date_range
    - Sorting: relevance (BM25), date, title
    - Pagination: page, page_size (max 100)
    - Highlighting: <em> tags on matching terms
    - Facets: document_types, authors, departments aggregations

    **Performance**: Target <500ms for typical queries

    Args:
        search_request: SearchRequest with query, filters, pagination
        request: FastAPI request (for IP address)
        current_user: Authenticated user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        SearchResponse with documents, facets, and metadata

    Raises:
        HTTPException 400: Invalid request (validation error)
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error
    """
    try:
        # Get Elasticsearch client
        es_client = get_es_client()

        # Create SearchService
        search_service = SearchService(es_client=es_client, db_session=db)

        # Execute search
        response = await search_service.search_documents(
            request=search_request,
            user=current_user,
            ip_address=request.client.host if request.client else None
        )

        logger.info(
            f"Search executed: user={current_user.username}, "
            f"query='{search_request.query}', results={response.total_results}"
        )

        return response

    except ValueError as e:
        # Pydantic validation errors
        logger.warning(f"Search validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Elasticsearch or database errors
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during search"
        )


# ============================================================================
# Search Suggestions Endpoint (PRD Sprint 3 - Autocomplete)
# ============================================================================


@router.get("/suggestions", response_model=SearchSuggestionsResponse, status_code=status.HTTP_200_OK)
async def get_search_suggestions(
    q: str = Query(..., min_length=1, max_length=100, description="Query prefix for autocomplete"),
    limit: int = Query(10, ge=1, le=20, description="Maximum number of suggestions"),
    sources: Optional[str] = Query(
        None,
        description="Comma-separated sources to include: history, popular, concept, document"
    ),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get search suggestions for autocomplete (PRD Sprint 3).

    **Authorization**: Requires valid JWT token (any authenticated user)

    **Sources**:
    - **history**: User's recent search queries
    - **popular**: Most frequently searched terms
    - **concept**: Medical concepts matching prefix
    - **document**: Document titles/content matching prefix

    **Ranking**: Suggestions are ranked by:
    1. Exact prefix match (highest)
    2. Source priority: history > popular > concept > document
    3. Recency (for history) or frequency (for popular)

    **Performance**: Target <100ms response time

    Args:
        q: Query prefix (minimum 1 character)
        limit: Maximum suggestions to return (1-20, default 10)
        sources: Comma-separated sources to include (default: all)
        current_user: Authenticated user
        db: Database session

    Returns:
        SearchSuggestionsResponse with ranked suggestions

    Raises:
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error

    Example:
        ```bash
        curl -X GET "http://localhost:8000/api/v1/search/suggestions?q=diab&limit=5" \\
          -H "Authorization: Bearer $TOKEN"
        ```

    Response:
        ```json
        {
          "query": "diab",
          "suggestions": [
            {"text": "diabetes mellitus", "score": 0.95, "source": "popular"},
            {"text": "diabetic neuropathy", "score": 0.85, "source": "concept"}
          ],
          "total": 2
        }
        ```
    """
    try:
        suggestions = []
        query_lower = q.lower().strip()

        # Parse requested sources
        requested_sources = None
        if sources:
            requested_sources = [s.strip().lower() for s in sources.split(",")]

        # 1. Search user's history (most recent first)
        if not requested_sources or "history" in requested_sources:
            try:
                # Get recent searches from saved_searches that match prefix
                history_stmt = (
                    select(SavedSearch)
                    .where(SavedSearch.user_id == current_user.id)
                    .where(SavedSearch.query.ilike(f"{query_lower}%"))
                    .order_by(SavedSearch.last_executed_at.desc())
                    .limit(limit)
                )
                history_result = await db.execute(history_stmt)
                history_searches = history_result.scalars().all()

                for idx, search in enumerate(history_searches):
                    score = 1.0 - (idx * 0.05)  # Decrease score by position
                    suggestions.append(SearchSuggestion(
                        text=search.query,
                        score=min(max(score, 0.5), 1.0),
                        source="history",
                        metadata={"search_id": str(search.id), "execution_count": search.execution_count}
                    ))
            except Exception as e:
                logger.warning(f"Failed to get history suggestions: {e}")

        # 2. Get popular queries (from search_analytics)
        if not requested_sources or "popular" in requested_sources:
            try:
                analytics_service = AnalyticsService()
                top_queries = await analytics_service.get_top_queries(
                    db=db,
                    limit=limit,
                    prefix=query_lower
                )

                for idx, query_data in enumerate(top_queries):
                    # Don't duplicate if already in history
                    if not any(s.text.lower() == query_data.get("query", "").lower() for s in suggestions):
                        score = 0.8 - (idx * 0.03)
                        suggestions.append(SearchSuggestion(
                            text=query_data.get("query", ""),
                            score=min(max(score, 0.4), 0.8),
                            source="popular",
                            metadata={"count": query_data.get("count", 0)}
                        ))
            except Exception as e:
                logger.warning(f"Failed to get popular suggestions: {e}")

        # 3. Medical concepts (would query MedCAT or concept database)
        # This is a simplified implementation - in production would query UMLS/SNOMED
        if not requested_sources or "concept" in requested_sources:
            # Common medical terms for demonstration
            common_concepts = [
                ("diabetes mellitus", "C0011849"),
                ("diabetic nephropathy", "C0011881"),
                ("diabetic neuropathy", "C0011882"),
                ("diabetic retinopathy", "C0011884"),
                ("hypertension", "C0020538"),
                ("hyperlipidemia", "C0020473"),
                ("atrial fibrillation", "C0004238"),
                ("atrial flutter", "C0004239"),
                ("myocardial infarction", "C0027051"),
                ("chronic kidney disease", "C0403447"),
                ("chronic obstructive pulmonary disease", "C0024117"),
                ("heart failure", "C0018801"),
                ("stroke", "C0038454"),
            ]

            for concept_name, cui in common_concepts:
                if concept_name.lower().startswith(query_lower) and len(suggestions) < limit * 2:
                    if not any(s.text.lower() == concept_name.lower() for s in suggestions):
                        suggestions.append(SearchSuggestion(
                            text=concept_name,
                            score=0.7,
                            source="concept",
                            metadata={"cui": cui}
                        ))

        # Sort by score and limit
        suggestions.sort(key=lambda x: x.score, reverse=True)
        suggestions = suggestions[:limit]

        logger.info(
            f"Search suggestions: user={current_user.username}, "
            f"query='{q}', suggestions={len(suggestions)}"
        )

        return SearchSuggestionsResponse(
            query=q,
            suggestions=suggestions,
            total=len(suggestions)
        )

    except Exception as e:
        logger.error(f"Search suggestions error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error getting suggestions"
        )


@router.post("/validate", response_model=QueryValidationResult, status_code=status.HTTP_200_OK)
async def validate_search_query(
    query: str = Query(..., min_length=1, max_length=1000, description="Query to validate"),
    current_user: User = Depends(get_current_user),
):
    """
    Validate search query syntax.

    **Authorization**: Requires valid JWT token (any authenticated user)

    **Validation checks**:
    - Boolean operator syntax (AND, OR, NOT)
    - Parentheses matching
    - Quote matching
    - Reserved character escaping

    Args:
        query: Search query to validate
        current_user: Authenticated user

    Returns:
        QueryValidationResult with validation status and suggestions

    Example:
        ```bash
        curl -X POST "http://localhost:8000/api/v1/search/validate?query=diabetes+AND+OR" \\
          -H "Authorization: Bearer $TOKEN"
        ```
    """
    try:
        errors = []
        suggestions = []
        parsed_query = None

        # Check for consecutive boolean operators
        import re
        consecutive_ops = re.search(r'\b(AND|OR|NOT)\s+(AND|OR)\b', query, re.IGNORECASE)
        if consecutive_ops:
            errors.append(f"Consecutive operators '{consecutive_ops.group()}' not allowed")
            suggestions.append(f"Try removing one of the operators")

        # Check for unmatched parentheses
        open_parens = query.count('(')
        close_parens = query.count(')')
        if open_parens != close_parens:
            errors.append(f"Unmatched parentheses: {open_parens} '(' and {close_parens} ')'")
            suggestions.append("Ensure each '(' has a matching ')'")

        # Check for unmatched quotes
        quote_count = query.count('"')
        if quote_count % 2 != 0:
            errors.append(f"Unmatched quotes: {quote_count} '\"' found")
            suggestions.append("Ensure each '\"' has a matching '\"'")

        # Check for leading/trailing operators
        stripped = query.strip()
        if re.match(r'^(AND|OR)\b', stripped, re.IGNORECASE):
            errors.append("Query cannot start with AND or OR")
            suggestions.append("Remove the leading operator")
        if re.search(r'\b(AND|OR|NOT)$', stripped, re.IGNORECASE):
            errors.append("Query cannot end with AND, OR, or NOT")
            suggestions.append("Add a search term after the operator")

        valid = len(errors) == 0
        if valid:
            parsed_query = query.strip()

        logger.info(
            f"Query validated: user={current_user.username}, "
            f"query='{query[:50]}...', valid={valid}"
        )

        return QueryValidationResult(
            valid=valid,
            query=query,
            parsed_query=parsed_query,
            errors=errors,
            suggestions=suggestions
        )

    except Exception as e:
        logger.error(f"Query validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error validating query"
        )


# ============================================================================
# Saved Searches Endpoints
# ============================================================================


@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def create_saved_search(
    search_data: SavedSearchCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new saved search.

    **Authorization**: Requires valid JWT token (any authenticated user)

    **Workflow**:
    1. Validate saved search data (Pydantic validation)
    2. Check for duplicate name (per user)
    3. Create saved search in database
    4. Log audit trail (SEARCH_SAVED action)
    5. Return created saved search

    Args:
        search_data: SavedSearchCreate with name, query, filters
        request: FastAPI request (for IP address)
        current_user: Authenticated user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        SavedSearchResponse with created search details

    Raises:
        HTTPException 409: Duplicate search name for this user
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error
    """
    try:
        # Create SavedSearch model
        saved_search = SavedSearch(
            user_id=current_user.id,
            name=search_data.name,
            description=search_data.description,
            query=search_data.query,
            filters=search_data.filters or {},
            is_shared=search_data.is_shared,
            execution_count=0
        )

        # Add to database
        db.add(saved_search)
        await db.commit()
        await db.refresh(saved_search)

        # Log audit trail
        await AuditService.log_action(
            db=db,
            user=current_user,
            action="SEARCH_SAVED",
            resource_type="saved_search",
            resource_id=str(saved_search.id),
            details={
                "name": saved_search.name,
                "query": saved_search.query,
                "is_shared": saved_search.is_shared
            },
            ip_address=request.client.host if request.client else None
        )

        logger.info(
            f"Saved search created: user={current_user.username}, "
            f"name='{saved_search.name}', id={saved_search.id}"
        )

        return SavedSearchResponse.model_validate(saved_search)

    except IntegrityError as e:
        # Duplicate name constraint violation
        await db.rollback()
        logger.warning(
            f"Duplicate saved search name: user={current_user.username}, "
            f"name='{search_data.name}'"
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Saved search with name '{search_data.name}' already exists"
        )
    except Exception as e:
        # Database or other errors
        await db.rollback()
        logger.error(f"Error creating saved search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error creating saved search"
        )


@router.get("/saved", response_model=List[SavedSearchResponse], status_code=status.HTTP_200_OK)
async def list_saved_searches(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all saved searches for the current user.

    **Authorization**: Requires valid JWT token (any authenticated user)

    **Workflow**:
    1. Query saved searches for current user
    2. Sort by created_at descending (newest first)
    3. Return list of saved searches

    Args:
        current_user: Authenticated user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        List[SavedSearchResponse] with user's saved searches (newest first)

    Raises:
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error
    """
    try:
        # Query saved searches for current user
        result = await db.execute(
            select(SavedSearch)
            .where(SavedSearch.user_id == current_user.id)
            .order_by(SavedSearch.created_at.desc())
        )
        saved_searches = result.scalars().all()

        logger.info(
            f"Listed saved searches: user={current_user.username}, "
            f"count={len(saved_searches)}"
        )

        return [SavedSearchResponse.model_validate(s) for s in saved_searches]

    except Exception as e:
        # Database errors
        logger.error(f"Error listing saved searches: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error listing saved searches"
        )


@router.delete("/saved/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    search_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a saved search.

    **Authorization**: Requires valid JWT token (any authenticated user)
    **Ownership**: User can only delete their own saved searches

    **Workflow**:
    1. Find saved search by ID
    2. Verify ownership (user_id matches current_user.id)
    3. Delete from database
    4. Log audit trail (SEARCH_DELETED action)
    5. Return 204 No Content

    Args:
        search_id: UUID of saved search to delete
        request: FastAPI request (for IP address)
        current_user: Authenticated user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        None (204 No Content)

    Raises:
        HTTPException 404: Saved search not found
        HTTPException 403: User does not own this saved search
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error
    """
    try:
        # Find saved search
        saved_search = await db.get(SavedSearch, search_id)

        if not saved_search:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Saved search with ID {search_id} not found"
            )

        # Verify ownership
        if saved_search.user_id != current_user.id:
            logger.warning(
                f"User {current_user.username} attempted to delete "
                f"saved search {search_id} owned by user {saved_search.user_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this saved search"
            )

        # Delete saved search
        search_name = saved_search.name
        await db.delete(saved_search)
        await db.commit()

        # Log audit trail
        await AuditService.log_action(
            db=db,
            user=current_user,
            action="SEARCH_DELETED",
            resource_type="saved_search",
            resource_id=str(search_id),
            details={
                "name": search_name,
                "deleted_at": "now"
            },
            ip_address=request.client.host if request.client else None
        )

        logger.info(
            f"Saved search deleted: user={current_user.username}, "
            f"name='{search_name}', id={search_id}"
        )

        return None

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Database or other errors
        await db.rollback()
        logger.error(f"Error deleting saved search: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error deleting saved search"
        )


# ============================================================================
# Export Endpoint
# ============================================================================


@router.post("/export", dependencies=[Depends(rate_limit_search_dependency)])
async def export_search_results(
    export_request: SearchExportRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Export search results to CSV, JSON, or FHIR format.

    **Authorization**: Requires valid JWT token (any authenticated user)

    **Workflow**:
    1. Execute search with query and filters (no pagination - get all results)
    2. Export results to requested format (CSV, JSON, or FHIR)
    3. Log audit trail (SEARCH_EXPORTED action)
    4. Return file as StreamingResponse

    **Export Formats**:
    - **CSV**: Comma-separated values with metadata header
    - **JSON**: Structured JSON with query metadata
    - **FHIR R4**: DocumentReference bundle for EHR integration

    Args:
        export_request: SearchExportRequest with query, filters, format
        request: FastAPI request (for IP address)
        current_user: Authenticated user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        StreamingResponse with file download

    Raises:
        HTTPException 400: Invalid request (validation error)
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error
    """
    try:
        # Get Elasticsearch client
        es_client = get_es_client()

        # Create SearchService
        search_service = SearchService(es_client=es_client, db_session=db)

        # Execute search (get all results, no pagination)
        search_request = SearchRequest(
            query=export_request.query,
            filters=export_request.filters,
            page=1,
            page_size=10000,  # Maximum results for export
            sort="relevance"
        )

        response = await search_service.search_documents(
            request=search_request,
            user=current_user,
            ip_address=request.client.host if request.client else None
        )

        # Create ExportService
        export_service = ExportService(db_session=db)

        # Export results based on format
        if export_request.format == ExportFormat.CSV:
            export_bytes = await export_service.export_to_csv(
                results=response.documents,
                query=export_request.query,
                user_id=current_user.id,
                ip_address=request.client.host if request.client else None
            )
            media_type = "text/csv"
            filename = f"search_results_{export_request.query[:20]}.csv"

        elif export_request.format == ExportFormat.JSON:
            export_bytes = await export_service.export_to_json(
                results=response.documents,
                query=export_request.query,
                user_id=current_user.id,
                ip_address=request.client.host if request.client else None
            )
            media_type = "application/json"
            filename = f"search_results_{export_request.query[:20]}.json"

        elif export_request.format == ExportFormat.FHIR:
            export_bytes = await export_service.export_to_fhir(
                results=response.documents,
                query=export_request.query,
                user_id=current_user.id,
                ip_address=request.client.host if request.client else None
            )
            media_type = "application/fhir+json"
            filename = f"search_results_{export_request.query[:20]}_fhir.json"

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported export format: {export_request.format}"
            )

        # Create StreamingResponse
        export_stream = io.BytesIO(export_bytes)

        logger.info(
            f"Search results exported: user={current_user.username}, "
            f"query='{export_request.query}', format={export_request.format}, "
            f"results={len(response.documents)}"
        )

        return StreamingResponse(
            export_stream,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ValueError as e:
        # Pydantic validation errors
        logger.warning(f"Export validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Elasticsearch or database errors
        logger.error(f"Export error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during export"
        )


# ============================================================================
# Analytics Endpoint
# ============================================================================


@router.get("/analytics", response_model=SearchAnalyticsAggregateResponse, status_code=status.HTTP_200_OK)
async def get_search_analytics(
    start_date: Optional[str] = Query(None, description="Start date for analytics (ISO format YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date for analytics (ISO format YYYY-MM-DD)"),
    user_id: Optional[str] = Query(None, description="Filter by specific user ID"),
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get aggregated search analytics (admin only).

    **Authorization**: Requires admin role (403 for non-admin users)

    **Workflow**:
    1. Validate date range parameters
    2. Call AnalyticsService methods to aggregate data:
       - Top queries (most frequently searched)
       - Zero result queries (queries with no results)
       - Slow queries (queries exceeding 2000ms threshold)
       - Search trends (daily search volume)
    3. Return aggregated analytics response

    **Use Cases**:
    - Query performance monitoring (identify slow queries)
    - Search quality tracking (find zero-result queries)
    - User behavior analysis (popular queries, search trends)
    - System optimization (improve slow queries, add missing content)

    Args:
        start_date: Optional start date for filtering (ISO format YYYY-MM-DD)
        end_date: Optional end date for filtering (ISO format YYYY-MM-DD)
        user_id: Optional user ID filter
        current_user: Authenticated admin user (injected by FastAPI)
        db: Database session (injected by FastAPI)

    Returns:
        SearchAnalyticsAggregateResponse with aggregated analytics

    Raises:
        HTTPException 400: Invalid date format
        HTTPException 403: User is not admin
        HTTPException 401: Unauthorized (no valid JWT token)
        HTTPException 500: Internal server error
    """
    try:
        # Parse date parameters if provided
        start_datetime = None
        end_datetime = None

        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid start_date format: {start_date}. Expected ISO format (YYYY-MM-DD)"
                )

        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid end_date format: {end_date}. Expected ISO format (YYYY-MM-DD)"
                )

        # Validate date range
        if start_datetime and end_datetime and start_datetime > end_datetime:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="start_date must be before or equal to end_date"
            )

        # Parse user_id if provided
        user_id_uuid = None
        if user_id:
            try:
                user_id_uuid = UUID(user_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid user_id format: {user_id}. Expected UUID"
                )

        # Create AnalyticsService
        analytics_service = AnalyticsService()

        # Get top queries
        top_queries_data = await analytics_service.get_top_queries(
            db=db,
            limit=10,
            start_date=start_datetime,
            end_date=end_datetime,
            user_id=user_id_uuid
        )
        top_queries = [QueryAnalytics(**item) for item in top_queries_data]

        # Get zero result queries
        zero_result_data = await analytics_service.get_zero_result_queries(
            db=db,
            limit=10,
            start_date=start_datetime,
            end_date=end_datetime
        )
        zero_result_queries = [QueryAnalytics(**item) for item in zero_result_data]

        # Get slow queries
        slow_queries_data = await analytics_service.get_slow_queries(
            db=db,
            limit=10,
            threshold_ms=2000,
            start_date=start_datetime,
            end_date=end_datetime
        )
        slow_queries = [SlowQueryAnalytics(**item) for item in slow_queries_data]

        # Get search trends (if date range specified)
        trends = []
        if start_datetime and end_datetime:
            trends_data = await analytics_service.get_search_trends(
                db=db,
                start_date=start_datetime,
                end_date=end_datetime
            )
            trends = [TrendDataPoint(**item) for item in trends_data]

        logger.info(
            f"Analytics retrieved: user={current_user.username}, "
            f"top_queries={len(top_queries)}, zero_result={len(zero_result_queries)}, "
            f"slow_queries={len(slow_queries)}, trends={len(trends)}"
        )

        return SearchAnalyticsAggregateResponse(
            top_queries=top_queries,
            zero_result_queries=zero_result_queries,
            slow_queries=slow_queries,
            trends=trends
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Database or other errors
        logger.error(f"Analytics error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error retrieving analytics"
        )
