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
    SearchAnalyticsAggregateResponse,
    SearchExportRequest,
    SearchRequest,
    SearchResponse,
    SavedSearchCreate,
    SavedSearchResponse,
    SlowQueryAnalytics,
    TrendDataPoint,
)
from app.services.analytics_service import AnalyticsService
from app.services.audit_service import AuditService
from app.services.export_service import ExportService
from app.services.search_service import SearchService
from app.middleware.rate_limit import rate_limit_search

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK, dependencies=[Depends(rate_limit_search)])
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
        audit_service = AuditService(db)
        await audit_service.log_action(
            user_id=current_user.id,
            action="SEARCH_SAVED",
            resource_type="saved_search",
            resource_id=str(saved_search.id),
            metadata={
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
        audit_service = AuditService(db)
        await audit_service.log_action(
            user_id=current_user.id,
            action="SEARCH_DELETED",
            resource_type="saved_search",
            resource_id=str(search_id),
            metadata={
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


@router.post("/export", dependencies=[Depends(rate_limit_search)])
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
