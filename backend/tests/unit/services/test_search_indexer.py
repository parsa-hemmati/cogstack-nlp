"""
Unit Tests for SearchIndexer Service

Tests batch indexing of documents from PostgreSQL to Elasticsearch.
Follows TDD approach: Write tests first, then implement.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_get_unindexed_documents_returns_unindexed_only():
    """Test that _get_unindexed_documents returns only documents where indexed=False"""
    from app.services.search_indexer import SearchIndexer

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()

    # Mock query result: 2 unindexed documents
    mock_doc1 = MagicMock()
    mock_doc1.id = uuid.uuid4()
    mock_doc1.indexed = False

    mock_doc2 = MagicMock()
    mock_doc2.id = uuid.uuid4()
    mock_doc2.indexed = False

    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_doc1, mock_doc2]

    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Act
    result = await indexer._get_unindexed_documents(batch_size=10)

    # Assert
    assert len(result) == 2
    assert result[0].indexed is False
    assert result[1].indexed is False


@pytest.mark.asyncio
async def test_decrypt_content_returns_plaintext():
    """Test that _decrypt_content decrypts document content"""
    from app.services.search_indexer import SearchIndexer

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()
    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Mock encrypted content
    encrypted_content = b"fake_encrypted_content"
    expected_plaintext = b"Patient has diabetes mellitus"

    # Mock encryption service
    with patch('app.services.search_indexer.EncryptionService') as mock_enc:
        mock_enc.from_env.return_value.decrypt.return_value = expected_plaintext

        # Act
        result = indexer._decrypt_content(encrypted_content)

        # Assert
        assert result == expected_plaintext.decode('utf-8')
        mock_enc.from_env.return_value.decrypt.assert_called_once_with(encrypted_content)


@pytest.mark.asyncio
async def test_extract_concepts_from_entities():
    """Test that _extract_concepts extracts concepts from document entities"""
    from app.services.search_indexer import SearchIndexer
    from app.models.extracted_entity import EntityType

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()

    doc_id = uuid.uuid4()

    # Mock extracted entities
    entity1 = MagicMock()
    entity1.cui = "C0011849"
    entity1.pretty_name = "Diabetes mellitus"
    entity1.entity_type = EntityType.CLINICAL

    entity2 = MagicMock()
    entity2.cui = "C0020538"
    entity2.pretty_name = "Hypertension"
    entity2.entity_type = EntityType.CLINICAL

    mock_db.execute.return_value.scalars.return_value.all.return_value = [entity1, entity2]

    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Act
    result = await indexer._extract_concepts(doc_id)

    # Assert
    assert len(result) == 2
    assert result[0]['cui'] == "C0011849"
    assert result[0]['name'] == "Diabetes mellitus"
    assert result[0]['type'] == EntityType.CLINICAL.value
    assert result[1]['cui'] == "C0020538"
    assert result[1]['name'] == "Hypertension"


@pytest.mark.asyncio
async def test_index_documents_batch_indexes_to_elasticsearch():
    """Test that index_documents_batch indexes documents to Elasticsearch"""
    from app.services.search_indexer import SearchIndexer

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()

    doc_id = uuid.uuid4()
    mock_doc = MagicMock()
    mock_doc.id = doc_id
    mock_doc.filename = "test.rtf"
    mock_doc.content_type = "application/rtf"
    mock_doc.encrypted_content = b"encrypted"
    mock_doc.uploaded_by = uuid.uuid4()
    mock_doc.created_at = datetime.now()
    mock_doc.indexed = False

    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Mock methods
    indexer._decrypt_content = MagicMock(return_value="Patient has diabetes")
    indexer._extract_concepts = AsyncMock(return_value=[
        {"cui": "C0011849", "name": "Diabetes mellitus", "type": "clinical"}
    ])

    # Mock Elasticsearch bulk helper
    with patch('app.services.search_indexer.helpers.async_bulk') as mock_bulk:
        mock_bulk.return_value = (1, [])  # 1 success, 0 errors

        # Act
        count = await indexer.index_documents_batch(batch_size=10)

        # Assert
        assert count == 1
        mock_bulk.assert_called_once()


@pytest.mark.asyncio
async def test_index_documents_batch_marks_documents_as_indexed():
    """Test that index_documents_batch marks documents as indexed=True"""
    from app.services.search_indexer import SearchIndexer

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()

    doc_id = uuid.uuid4()
    mock_doc = MagicMock()
    mock_doc.id = doc_id
    mock_doc.filename = "test.rtf"
    mock_doc.content_type = "application/rtf"
    mock_doc.encrypted_content = b"encrypted"
    mock_doc.uploaded_by = uuid.uuid4()
    mock_doc.created_at = datetime.now()
    mock_doc.indexed = False

    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Mock methods
    indexer._decrypt_content = MagicMock(return_value="Patient has diabetes")
    indexer._extract_concepts = AsyncMock(return_value=[])

    # Mock Elasticsearch bulk helper
    with patch('app.services.search_indexer.helpers.async_bulk') as mock_bulk:
        mock_bulk.return_value = (1, [])

        # Act
        await indexer.index_documents_batch(batch_size=10)

        # Assert
        assert mock_doc.indexed is True
        assert mock_doc.last_indexed_at is not None
        mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_index_documents_batch_handles_errors_gracefully():
    """Test that index_documents_batch handles Elasticsearch errors gracefully"""
    from app.services.search_indexer import SearchIndexer

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()

    doc_id = uuid.uuid4()
    mock_doc = MagicMock()
    mock_doc.id = doc_id
    mock_doc.filename = "test.rtf"
    mock_doc.content_type = "application/rtf"
    mock_doc.encrypted_content = b"encrypted"
    mock_doc.uploaded_by = uuid.uuid4()
    mock_doc.created_at = datetime.now()
    mock_doc.indexed = False

    mock_db.execute.return_value.scalars.return_value.all.return_value = [mock_doc]

    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Mock methods
    indexer._decrypt_content = MagicMock(return_value="Patient has diabetes")
    indexer._extract_concepts = AsyncMock(return_value=[])

    # Mock Elasticsearch bulk helper with error
    with patch('app.services.search_indexer.helpers.async_bulk') as mock_bulk:
        mock_bulk.side_effect = Exception("Elasticsearch connection error")

        # Act
        count = await indexer.index_documents_batch(batch_size=10)

        # Assert
        assert count == 0  # No documents indexed due to error
        # Document should NOT be marked as indexed
        assert mock_doc.indexed is False


@pytest.mark.asyncio
async def test_index_documents_batch_with_empty_result():
    """Test that index_documents_batch handles empty result gracefully"""
    from app.services.search_indexer import SearchIndexer

    # Arrange
    mock_db = AsyncMock()
    mock_es = MagicMock()

    # No unindexed documents
    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    indexer = SearchIndexer(es_client=mock_es, db_session=mock_db)

    # Act
    count = await indexer.index_documents_batch(batch_size=10)

    # Assert
    assert count == 0
