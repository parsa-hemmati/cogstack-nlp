"""Tests for DocumentIndexingService.

Tests ensure:
- Documents indexed successfully
- Updates propagated
- Deletions handled
- Bulk indexing works
- Error handling for failed operations
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.services.elasticsearch.document_indexing_service import DocumentIndexingService
from app.models.document import Document


@pytest.fixture
def mock_es_client():
    """Mock Elasticsearch client."""
    mock = AsyncMock()
    mock.index = AsyncMock()
    mock.delete = AsyncMock()
    mock.indices.exists = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock = AsyncMock()
    return mock


@pytest.fixture
def sample_document():
    """Create sample document for testing."""
    return Document(
        id=uuid4(),
        patient_id=uuid4(),
        title="Discharge Summary",
        content="Patient discharged with diabetes mellitus type 2",
        document_type="discharge_summary",
        author="Dr. Smith",
        department="Endocrinology",
        date=datetime(2023, 11, 15),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.fixture
def indexing_service(mock_es_client, mock_db_session):
    """Create DocumentIndexingService instance."""
    return DocumentIndexingService(mock_es_client, mock_db_session)


class TestDocumentIndexing:
    """Test single document indexing."""

    @pytest.mark.asyncio
    async def test_index_document_success(
        self,
        indexing_service,
        mock_db_session,
        mock_es_client,
        sample_document
    ):
        """Test successful document indexing."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_document)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Index document
        result = await indexing_service.index_document(str(sample_document.id))

        assert result is True

        # Verify Elasticsearch index called
        mock_es_client.index.assert_called_once()
        call_args = mock_es_client.index.call_args
        assert call_args.kwargs["id"] == str(sample_document.id)
        assert call_args.kwargs["document"]["title"] == "Discharge Summary"

    @pytest.mark.asyncio
    async def test_index_document_not_found(
        self,
        indexing_service,
        mock_db_session
    ):
        """Test indexing non-existent document raises ValueError."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=None)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Document .* not found"):
            await indexing_service.index_document(str(uuid4()))

    @pytest.mark.asyncio
    async def test_update_document(
        self,
        indexing_service,
        mock_db_session,
        sample_document
    ):
        """Test document update (same as indexing)."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = AsyncMock(return_value=sample_document)
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Update document
        result = await indexing_service.update_document(str(sample_document.id))

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        indexing_service,
        mock_es_client,
        sample_document
    ):
        """Test successful document deletion."""
        result = await indexing_service.delete_document(str(sample_document.id))

        assert result is True

        # Verify Elasticsearch delete called
        mock_es_client.delete.assert_called_once_with(
            index="documents",
            id=str(sample_document.id)
        )

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self,
        indexing_service,
        mock_es_client
    ):
        """Test deleting non-existent document returns False."""
        # Mock Elasticsearch raising not_found error
        mock_es_client.delete = AsyncMock(
            side_effect=Exception("not_found: Document not found")
        )

        result = await indexing_service.delete_document(str(uuid4()))

        assert result is False


class TestBulkIndexing:
    """Test bulk document indexing."""

    @pytest.mark.asyncio
    async def test_bulk_index_success(
        self,
        indexing_service,
        mock_db_session,
        sample_document
    ):
        """Test successful bulk indexing."""
        # Create sample documents
        documents = [sample_document for _ in range(5)]

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=documents)))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock async_bulk
        async def mock_bulk(*args, **kwargs):
            for _ in range(5):
                yield True, {"index": {"_id": "123"}}

        with patch("app.services.elasticsearch.document_indexing_service.async_bulk", side_effect=mock_bulk):
            stats = await indexing_service.index_documents_bulk()

        assert stats["indexed"] == 5
        assert stats["failed"] == 0
        assert stats["total"] == 5

    @pytest.mark.asyncio
    async def test_bulk_index_partial_failure(
        self,
        indexing_service,
        mock_db_session,
        sample_document
    ):
        """Test bulk indexing with some failures."""
        documents = [sample_document for _ in range(5)]

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=documents)))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock async_bulk with some failures
        async def mock_bulk(*args, **kwargs):
            yield True, {"index": {"_id": "1"}}
            yield True, {"index": {"_id": "2"}}
            yield False, {"index": {"error": "timeout"}}
            yield True, {"index": {"_id": "4"}}
            yield False, {"index": {"error": "timeout"}}

        with patch("app.services.elasticsearch.document_indexing_service.async_bulk", side_effect=mock_bulk):
            stats = await indexing_service.index_documents_bulk()

        assert stats["indexed"] == 3
        assert stats["failed"] == 2
        assert stats["total"] == 5

    @pytest.mark.asyncio
    async def test_bulk_index_no_documents(
        self,
        indexing_service,
        mock_db_session
    ):
        """Test bulk indexing with no documents returns zeros."""
        # Mock database query returning empty list
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        stats = await indexing_service.index_documents_bulk()

        assert stats["indexed"] == 0
        assert stats["failed"] == 0
        assert stats["total"] == 0

    @pytest.mark.asyncio
    async def test_bulk_index_with_specific_ids(
        self,
        indexing_service,
        mock_db_session,
        sample_document
    ):
        """Test bulk indexing specific document IDs."""
        documents = [sample_document]
        document_ids = [str(sample_document.id)]

        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=documents)))
        mock_db_session.execute = AsyncMock(return_value=mock_result)

        # Mock async_bulk
        async def mock_bulk(*args, **kwargs):
            yield True, {"index": {"_id": str(sample_document.id)}}

        with patch("app.services.elasticsearch.document_indexing_service.async_bulk", side_effect=mock_bulk):
            stats = await indexing_service.index_documents_bulk(document_ids=document_ids)

        assert stats["indexed"] == 1
        assert stats["total"] == 1


class TestDocumentTransformation:
    """Test document transformation for Elasticsearch."""

    def test_transform_document(self, indexing_service, sample_document):
        """Test document transformation to ES format."""
        es_doc = indexing_service._transform_document(sample_document)

        assert es_doc["document_id"] == str(sample_document.id)
        assert es_doc["patient_id"] == str(sample_document.patient_id)
        assert es_doc["title"] == "Discharge Summary"
        assert es_doc["content"] == "Patient discharged with diabetes mellitus type 2"
        assert es_doc["document_type"] == "discharge_summary"
        assert es_doc["author"] == "Dr. Smith"
        assert es_doc["department"] == "Endocrinology"
        assert es_doc["date"] == "2023-11-15T00:00:00"

    def test_transform_document_with_nulls(self, indexing_service):
        """Test document transformation handles null values."""
        doc = Document(
            id=uuid4(),
            patient_id=uuid4(),
            title=None,
            content=None,
            document_type=None,
            author=None,
            department=None,
            date=None
        )

        es_doc = indexing_service._transform_document(doc)

        assert es_doc["title"] == ""
        assert es_doc["content"] == ""
        assert es_doc["document_type"] == "unknown"
        assert es_doc["author"] == "Unknown"
        assert es_doc["department"] == "Unknown"
        assert es_doc["date"] is None
