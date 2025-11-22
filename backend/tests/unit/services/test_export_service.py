"""
Unit tests for ExportService.

Tests export_to_csv(), export_to_json(), export_to_fhir() methods.
"""
import json
from datetime import datetime
from uuid import UUID, uuid4

import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.services.export_service import ExportService
from app.schemas.search import SearchResultDocument, Highlight


@pytest.fixture
def sample_search_results():
    """Sample search results for testing."""
    return [
        SearchResultDocument(
            document_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            title="clinical_note_001.rtf",
            document_type="rtf",
            author="Dr. Smith",
            date=datetime(2025, 1, 15, 12, 30),
            department="Cardiology",
            relevance_score=0.95,
            highlights=[
                Highlight(
                    field="content",
                    snippets=["Patient with <em>diabetes</em> mellitus"]
                )
            ]
        ),
        SearchResultDocument(
            document_id=UUID("660e8400-e29b-41d4-a716-446655440001"),
            title="discharge_summary_002.txt",
            document_type="txt",
            author="Dr. Jones",
            date=datetime(2025, 1, 16, 10, 15),
            department="Neurology",
            relevance_score=0.87,
            highlights=[]
        ),
    ]


@pytest.fixture
def export_service():
    """Create ExportService instance."""
    mock_db = AsyncMock()
    return ExportService(db_session=mock_db)


@pytest.mark.asyncio
async def test_export_to_csv_generates_valid_csv(export_service, sample_search_results):
    """Test export_to_csv() generates valid CSV with headers."""
    # Act
    csv_bytes = await export_service.export_to_csv(
        results=sample_search_results,
        query="diabetes"
    )

    # Assert
    assert csv_bytes is not None
    csv_str = csv_bytes.decode('utf-8')

    # Check headers
    lines = csv_str.strip().split('\n')
    assert len(lines) == 4, "Should have metadata comment + header + 2 result rows"

    # First line is metadata comment
    assert lines[0].startswith('#'), "First line should be metadata comment"
    assert "Query: diabetes" in lines[0]

    header = lines[1]  # Header is second line
    assert "document_id" in header
    assert "title" in header
    assert "document_type" in header
    assert "author" in header
    assert "date" in header
    assert "department" in header
    assert "relevance_score" in header

    # Check data (lines 2 and 3 are data rows)
    assert "550e8400-e29b-41d4-a716-446655440000" in lines[2]
    assert "clinical_note_001.rtf" in lines[2]
    assert "Dr. Smith" in lines[2]
    assert "Cardiology" in lines[2]

    assert "660e8400-e29b-41d4-a716-446655440001" in lines[3]
    assert "discharge_summary_002.txt" in lines[3]
    assert "Dr. Jones" in lines[3]
    assert "Neurology" in lines[3]


@pytest.mark.asyncio
async def test_export_to_csv_handles_empty_results(export_service):
    """Test export_to_csv() handles empty results."""
    # Act
    csv_bytes = await export_service.export_to_csv(
        results=[],
        query="no results"
    )

    # Assert
    assert csv_bytes is not None
    csv_str = csv_bytes.decode('utf-8')
    lines = csv_str.strip().split('\n')
    assert len(lines) == 2, "Should have metadata comment + header only"
    assert lines[0].startswith('#'), "First line should be metadata comment"
    assert "document_id" in lines[1], "Second line should be header"


@pytest.mark.asyncio
async def test_export_to_csv_handles_none_values(export_service):
    """Test export_to_csv() handles None values in results."""
    # Arrange
    results = [
        SearchResultDocument(
            document_id=uuid4(),
            title="test.rtf",
            document_type="rtf",
            author=None,  # None value
            date=None,    # None value
            department=None,  # None value
            relevance_score=0.75,
            highlights=[]
        )
    ]

    # Act
    csv_bytes = await export_service.export_to_csv(results=results, query="test")

    # Assert
    assert csv_bytes is not None
    csv_str = csv_bytes.decode('utf-8')
    assert "test.rtf" in csv_str


@pytest.mark.asyncio
async def test_export_to_json_generates_valid_json(export_service, sample_search_results):
    """Test export_to_json() serializes results to valid JSON."""
    # Act
    json_bytes = await export_service.export_to_json(
        results=sample_search_results,
        query="diabetes"
    )

    # Assert
    assert json_bytes is not None
    json_str = json_bytes.decode('utf-8')
    data = json.loads(json_str)

    # Check structure
    assert "query" in data
    assert "total_results" in data
    assert "documents" in data
    assert "exported_at" in data

    assert data["query"] == "diabetes"
    assert data["total_results"] == 2
    assert len(data["documents"]) == 2

    # Check first document
    doc1 = data["documents"][0]
    assert doc1["document_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert doc1["title"] == "clinical_note_001.rtf"
    assert doc1["author"] == "Dr. Smith"
    assert doc1["department"] == "Cardiology"
    assert doc1["relevance_score"] == 0.95


@pytest.mark.asyncio
async def test_export_to_json_handles_empty_results(export_service):
    """Test export_to_json() handles empty results."""
    # Act
    json_bytes = await export_service.export_to_json(
        results=[],
        query="no results"
    )

    # Assert
    assert json_bytes is not None
    data = json.loads(json_bytes.decode('utf-8'))
    assert data["total_results"] == 0
    assert data["documents"] == []


@pytest.mark.asyncio
async def test_export_to_fhir_creates_document_reference_bundle(export_service, sample_search_results):
    """Test export_to_fhir() creates FHIR R4 DocumentReference bundle."""
    # Act
    fhir_bytes = await export_service.export_to_fhir(
        results=sample_search_results,
        query="diabetes"
    )

    # Assert
    assert fhir_bytes is not None
    fhir_str = fhir_bytes.decode('utf-8')
    bundle = json.loads(fhir_str)

    # Check FHIR Bundle structure
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert "entry" in bundle
    assert len(bundle["entry"]) == 2

    # Check first DocumentReference
    entry1 = bundle["entry"][0]
    assert entry1["resource"]["resourceType"] == "DocumentReference"
    assert entry1["resource"]["status"] == "current"
    assert entry1["resource"]["type"]["text"] == "rtf"

    # Check metadata
    content = entry1["resource"]["content"][0]
    assert content["attachment"]["title"] == "clinical_note_001.rtf"


@pytest.mark.asyncio
async def test_export_to_fhir_handles_empty_results(export_service):
    """Test export_to_fhir() handles empty results."""
    # Act
    fhir_bytes = await export_service.export_to_fhir(
        results=[],
        query="no results"
    )

    # Assert
    assert fhir_bytes is not None
    bundle = json.loads(fhir_bytes.decode('utf-8'))
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] == 0
    assert bundle["entry"] == []


@pytest.mark.asyncio
async def test_export_creates_audit_log(export_service, sample_search_results):
    """Test export methods create audit logs."""
    # Arrange
    user_id = uuid4()
    mock_audit_service = AsyncMock()

    with patch('app.services.export_service.AuditService', return_value=mock_audit_service):
        # Act
        await export_service.export_to_csv(
            results=sample_search_results,
            query="diabetes",
            user_id=user_id,
            ip_address="127.0.0.1"
        )

        # Assert
        mock_audit_service.log_action.assert_called_once()
        call_args = mock_audit_service.log_action.call_args
        assert call_args.kwargs["action"] == "SEARCH_EXPORTED"
        assert call_args.kwargs["user_id"] == user_id
        assert call_args.kwargs["resource_type"] == "search_export"


@pytest.mark.asyncio
async def test_export_to_csv_includes_metadata_comment(export_service, sample_search_results):
    """Test CSV export includes metadata as comment."""
    # Act
    csv_bytes = await export_service.export_to_csv(
        results=sample_search_results,
        query="diabetes"
    )

    # Assert
    csv_str = csv_bytes.decode('utf-8')
    lines = csv_str.split('\n')

    # Check for metadata comment (should be first line starting with #)
    assert lines[0].startswith('#'), "First line should be metadata comment"
    assert "Query: diabetes" in lines[0]
    assert "Results: 2" in lines[0]


@pytest.mark.asyncio
async def test_export_formats_dates_correctly(export_service, sample_search_results):
    """Test exports format dates in ISO 8601 format."""
    # Act - CSV
    csv_bytes = await export_service.export_to_csv(
        results=sample_search_results,
        query="test"
    )
    csv_str = csv_bytes.decode('utf-8')
    assert "2025-01-15" in csv_str

    # Act - JSON
    json_bytes = await export_service.export_to_json(
        results=sample_search_results,
        query="test"
    )
    data = json.loads(json_bytes.decode('utf-8'))
    assert "2025-01-15T12:30:00" in data["documents"][0]["date"]

    # Act - FHIR
    fhir_bytes = await export_service.export_to_fhir(
        results=sample_search_results,
        query="test"
    )
    bundle = json.loads(fhir_bytes.decode('utf-8'))
    # FHIR dates are in ISO 8601 format
    assert "2025-01-15" in json.dumps(bundle)
