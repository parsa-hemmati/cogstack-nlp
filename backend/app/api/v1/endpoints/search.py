"""
Full-Text Search API Endpoints

Handles document full-text search with Elasticsearch.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.elasticsearch_client import get_es_client
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse, status_code=status.HTTP_200_OK)
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
