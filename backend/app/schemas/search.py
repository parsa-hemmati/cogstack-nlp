"""
Search schemas for API requests/responses.

Defines Pydantic models for full-text search functionality, including:
- Search requests with filters and pagination
- Search responses with documents, highlights, and facets
- Saved searches for reusable queries
- Search analytics for performance tracking
"""
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class SortBy(str, Enum):
    """Sort options for search results."""
    RELEVANCE = "relevance"  # BM25 score (default)
    DATE = "date"           # Document date (newest first)
    TITLE = "title"         # Alphabetical by title


class DocumentSearchFilters(BaseModel):
    """Filters for document search requests."""

    document_types: Optional[List[str]] = Field(
        None,
        description="Filter by document types (rtf, txt, docx, pdf)"
    )
    authors: Optional[List[str]] = Field(
        None,
        description="Filter by document authors (user IDs)"
    )
    departments: Optional[List[str]] = Field(
        None,
        description="Filter by departments (Cardiology, Neurology, etc.)"
    )
    date_from: Optional[date] = Field(
        None,
        description="Filter documents from this date onwards (inclusive)"
    )
    date_to: Optional[date] = Field(
        None,
        description="Filter documents up to this date (inclusive)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_types": ["rtf", "txt"],
                "authors": ["user-123"],
                "departments": ["Cardiology"],
                "date_from": "2025-01-01",
                "date_to": "2025-12-31"
            }
        }


class SearchRequest(BaseModel):
    """Request schema for document search."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query (keywords, phrases, or boolean expressions)"
    )
    filters: Optional[DocumentSearchFilters] = Field(
        None,
        description="Optional filters for search results"
    )
    page: int = Field(
        1,
        ge=1,
        description="Page number for pagination (1-indexed)"
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Number of results per page (max 100)"
    )
    sort: SortBy = Field(
        SortBy.RELEVANCE,
        description="Sort order for results"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace-only")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "diabetes mellitus type 2",
                "filters": {
                    "document_types": ["rtf"],
                    "date_from": "2025-01-01"
                },
                "page": 1,
                "page_size": 20,
                "sort": "relevance"
            }
        }


class Highlight(BaseModel):
    """Highlighted text snippet from search results."""

    field: str = Field(
        ...,
        description="Field name where highlight was found (title, content)"
    )
    snippets: List[str] = Field(
        ...,
        description="List of highlighted text snippets with <em> tags"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "field": "content",
                "snippets": [
                    "Patient diagnosed with <em>diabetes</em> mellitus type 2",
                    "Current medications include metformin for <em>diabetes</em>"
                ]
            }
        }


class SearchResultDocument(BaseModel):
    """Single document in search results."""

    document_id: UUID = Field(..., description="Unique document identifier")
    title: str = Field(..., description="Document title (filename)")
    document_type: str = Field(..., description="Document type (rtf, txt, docx, pdf)")
    author: Optional[str] = Field(None, description="Document author (user ID or name)")
    date: Optional[datetime] = Field(None, description="Document date")
    department: Optional[str] = Field(None, description="Department (Cardiology, Neurology, etc.)")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="BM25 relevance score (0.0 to 1.0, normalized)"
    )
    highlights: List[Highlight] = Field(
        default_factory=list,
        description="Highlighted text snippets matching query"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "clinical_note_001.rtf",
                "document_type": "rtf",
                "author": "Dr. Smith",
                "date": "2025-11-18T12:00:00Z",
                "department": "Cardiology",
                "relevance_score": 0.95,
                "highlights": [
                    {
                        "field": "content",
                        "snippets": ["Patient with <em>diabetes</em> mellitus"]
                    }
                ]
            }
        }


class FacetValue(BaseModel):
    """Single value in a facet aggregation."""

    value: str = Field(..., description="Facet value (e.g., 'rtf', 'Dr. Smith')")
    count: int = Field(..., ge=0, description="Number of documents with this value")

    class Config:
        json_schema_extra = {
            "example": {
                "value": "rtf",
                "count": 150
            }
        }


class Facets(BaseModel):
    """Facet aggregations for search results."""

    document_types: List[FacetValue] = Field(
        default_factory=list,
        description="Document type facets (rtf, txt, docx, pdf)"
    )
    authors: List[FacetValue] = Field(
        default_factory=list,
        description="Author facets (user IDs or names)"
    )
    departments: List[FacetValue] = Field(
        default_factory=list,
        description="Department facets (Cardiology, Neurology, etc.)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "document_types": [
                    {"value": "rtf", "count": 150},
                    {"value": "txt", "count": 75}
                ],
                "authors": [
                    {"value": "Dr. Smith", "count": 100}
                ],
                "departments": [
                    {"value": "Cardiology", "count": 80},
                    {"value": "Neurology", "count": 60}
                ]
            }
        }


class SearchResponse(BaseModel):
    """Response schema for document search."""

    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., ge=0, description="Total number of matching documents")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of results per page")
    documents: List[SearchResultDocument] = Field(
        default_factory=list,
        description="List of matching documents with highlights"
    )
    facets: Facets = Field(
        ...,
        description="Facet aggregations for filtering"
    )
    execution_time_ms: int = Field(
        ...,
        ge=0,
        description="Query execution time in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "diabetes mellitus",
                "total_results": 42,
                "page": 1,
                "page_size": 20,
                "documents": [
                    {
                        "document_id": "550e8400-e29b-41d4-a716-446655440000",
                        "title": "clinical_note_001.rtf",
                        "document_type": "rtf",
                        "author": "Dr. Smith",
                        "date": "2025-11-18T12:00:00Z",
                        "department": "Cardiology",
                        "relevance_score": 0.95,
                        "highlights": [
                            {
                                "field": "content",
                                "snippets": ["<em>diabetes</em> mellitus type 2"]
                            }
                        ]
                    }
                ],
                "facets": {
                    "document_types": [{"value": "rtf", "count": 30}],
                    "authors": [{"value": "Dr. Smith", "count": 20}],
                    "departments": [{"value": "Cardiology", "count": 15}]
                },
                "execution_time_ms": 125
            }
        }


class SavedSearchCreate(BaseModel):
    """Request schema for creating a saved search."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Name for the saved search"
    )
    description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional description of the search"
    )
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query to save"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Search filters as JSON object"
    )
    is_shared: bool = Field(
        False,
        description="Whether to share this search with other users"
    )

    @field_validator('name', 'query')
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Validate string is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace-only")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Diabetes Patients - Cardiology",
                "description": "Search for diabetes patients in cardiology department",
                "query": "diabetes mellitus",
                "filters": {
                    "document_types": ["rtf"],
                    "departments": ["Cardiology"]
                },
                "is_shared": True
            }
        }


class SavedSearchResponse(BaseModel):
    """Response schema for saved search."""

    id: UUID = Field(..., description="Saved search ID")
    user_id: UUID = Field(..., description="User who created the search")
    name: str = Field(..., description="Search name")
    description: Optional[str] = Field(None, description="Search description")
    query: str = Field(..., description="Search query")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Search filters")
    is_shared: bool = Field(..., description="Whether search is shared")
    execution_count: int = Field(..., ge=0, description="Number of times executed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "name": "Diabetes Patients - Cardiology",
                "description": "Search for diabetes patients in cardiology",
                "query": "diabetes mellitus",
                "filters": {"departments": ["Cardiology"]},
                "is_shared": True,
                "execution_count": 15,
                "created_at": "2025-11-18T12:00:00Z",
                "updated_at": "2025-11-18T14:30:00Z"
            }
        }


class SearchAnalyticsResponse(BaseModel):
    """Response schema for search analytics."""

    id: UUID = Field(..., description="Analytics record ID")
    user_id: UUID = Field(..., description="User who performed the search")
    query: str = Field(..., description="Search query executed")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filters applied")
    results_count: int = Field(..., ge=0, description="Number of results returned")
    execution_time_ms: int = Field(..., ge=0, description="Query execution time (ms)")
    clicked_documents: List[UUID] = Field(
        default_factory=list,
        description="Documents clicked from results"
    )
    created_at: datetime = Field(..., description="Search execution timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e8400-e29b-41d4-a716-446655440000",
                "query": "diabetes mellitus",
                "filters": {"document_types": ["rtf"]},
                "results_count": 42,
                "execution_time_ms": 125,
                "clicked_documents": [
                    "770e8400-e29b-41d4-a716-446655440000",
                    "880e8400-e29b-41d4-a716-446655440000"
                ],
                "created_at": "2025-11-18T12:00:00Z"
            }
        }


class QueryAnalytics(BaseModel):
    """Analytics for a specific query."""

    query: str = Field(..., description="Search query")
    count: int = Field(..., ge=0, description="Number of times searched")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "diabetes mellitus",
                "count": 42
            }
        }


class SlowQueryAnalytics(BaseModel):
    """Analytics for slow queries."""

    query: str = Field(..., description="Search query")
    execution_time_ms: int = Field(..., ge=0, description="Maximum execution time (ms)")
    avg_execution_time_ms: int = Field(..., ge=0, description="Average execution time (ms)")
    count: int = Field(..., ge=0, description="Number of times searched")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "complex boolean query",
                "execution_time_ms": 2500,
                "avg_execution_time_ms": 2200,
                "count": 5
            }
        }


class TrendDataPoint(BaseModel):
    """Single data point in search trends."""

    date: str = Field(..., description="Date (YYYY-MM-DD)")
    count: int = Field(..., ge=0, description="Number of searches on this date")

    class Config:
        json_schema_extra = {
            "example": {
                "date": "2025-11-18",
                "count": 42
            }
        }


class SearchAnalyticsAggregateResponse(BaseModel):
    """Aggregated search analytics response."""

    top_queries: List[QueryAnalytics] = Field(
        default_factory=list,
        description="Most frequently searched queries"
    )
    zero_result_queries: List[QueryAnalytics] = Field(
        default_factory=list,
        description="Queries that returned no results"
    )
    slow_queries: List[SlowQueryAnalytics] = Field(
        default_factory=list,
        description="Queries exceeding performance threshold"
    )
    trends: List[TrendDataPoint] = Field(
        default_factory=list,
        description="Search volume trends by date"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "top_queries": [
                    {"query": "diabetes mellitus", "count": 42},
                    {"query": "hypertension", "count": 35}
                ],
                "zero_result_queries": [
                    {"query": "rare disease xyz", "count": 5}
                ],
                "slow_queries": [
                    {
                        "query": "complex boolean query",
                        "execution_time_ms": 2500,
                        "avg_execution_time_ms": 2200,
                        "count": 5
                    }
                ],
                "trends": [
                    {"date": "2025-11-18", "count": 42},
                    {"date": "2025-11-19", "count": 38}
                ]
            }
        }


class ExportFormat(str, Enum):
    """Export format options."""
    CSV = "csv"
    JSON = "json"
    FHIR = "fhir"


class SearchExportRequest(BaseModel):
    """Request schema for search export."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query to execute"
    )
    filters: Optional[DocumentSearchFilters] = Field(
        None,
        description="Optional filters for search results"
    )
    format: ExportFormat = Field(
        ...,
        description="Export format (csv, json, or fhir)"
    )

    @field_validator('query')
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate query is not empty or whitespace-only."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty or whitespace-only")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "diabetes mellitus",
                "filters": {
                    "document_types": ["rtf"],
                    "date_from": "2025-01-01"
                },
                "format": "csv"
            }
        }
