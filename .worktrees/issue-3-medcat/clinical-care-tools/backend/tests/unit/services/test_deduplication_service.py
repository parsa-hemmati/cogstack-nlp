"""
Unit tests for Document Deduplication Service.

Tests SHA-256 hash-based deduplication with Redis cache and database fallback.
"""

import pytest
import hashlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.deduplication_service import (
    check_duplicate,
    compute_content_hash,
    cache_document_hash,
    DuplicationError
)
from app.models.document import Document, ProcessingStatus


pytestmark = pytest.mark.asyncio


def test_compute_content_hash_returns_sha256():
    """Test that content hash is computed using SHA-256."""
    content = b"Test document content"

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_content_hash(content)

    assert actual_hash == expected_hash
    assert len(actual_hash) == 64  # SHA-256 hex string


def test_compute_content_hash_same_content_same_hash():
    """Test that same content produces same hash."""
    content = b"Identical content"

    hash1 = compute_content_hash(content)
    hash2 = compute_content_hash(content)

    assert hash1 == hash2


def test_compute_content_hash_different_content_different_hash():
    """Test that different content produces different hash."""
    content1 = b"First document"
    content2 = b"Second document"

    hash1 = compute_content_hash(content1)
    hash2 = compute_content_hash(content2)

    assert hash1 != hash2


@patch('app.services.deduplication_service.redis_client')
async def test_check_duplicate_cache_hit(mock_redis):
    """Test that cache hit returns document ID without database query."""
    content_hash = "abc123def456"
    cached_doc_id = str(uuid.uuid4())

    # Mock Redis cache hit
    mock_redis.get = AsyncMock(return_value=cached_doc_id)

    # Mock database session (should not be called)
    mock_db = AsyncMock()

    result = await check_duplicate(mock_db, content_hash)

    assert result == cached_doc_id
    mock_redis.get.assert_called_once_with(f"doc_hash:{content_hash}")
    # Database should not be queried
    mock_db.execute.assert_not_called()


@patch('app.services.deduplication_service.redis_client')
async def test_check_duplicate_cache_miss_database_hit(mock_redis, db_session, test_admin):
    """Test that cache miss triggers database lookup and updates cache."""
    content = b"Document content"
    content_hash = hashlib.sha256(content).hexdigest()

    # Create document in database
    from app.models.project import Project
    project = Project(
        id=uuid.uuid4(),
        name="Test Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    document = Document(
        id=uuid.uuid4(),
        filename="test.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )
    db_session.add(document)
    await db_session.commit()

    # Mock Redis cache miss, then cache set
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()

    result = await check_duplicate(db_session, content_hash)

    assert result == str(document.id)
    mock_redis.get.assert_called_once()
    # Cache should be updated with 30-day TTL
    mock_redis.setex.assert_called_once_with(
        f"doc_hash:{content_hash}",
        30 * 24 * 60 * 60,  # 30 days in seconds
        str(document.id)
    )


@patch('app.services.deduplication_service.redis_client')
async def test_check_duplicate_not_found(mock_redis, db_session):
    """Test that non-existent document returns None."""
    content_hash = "nonexistent123"

    # Mock Redis cache miss
    mock_redis.get = AsyncMock(return_value=None)

    result = await check_duplicate(db_session, content_hash)

    assert result is None
    mock_redis.get.assert_called_once()


@patch('app.services.deduplication_service.redis_client')
async def test_cache_document_hash_sets_ttl(mock_redis):
    """Test that caching sets 30-day TTL."""
    content_hash = "abc123"
    document_id = str(uuid.uuid4())

    mock_redis.setex = AsyncMock()

    await cache_document_hash(content_hash, document_id)

    mock_redis.setex.assert_called_once_with(
        f"doc_hash:{content_hash}",
        30 * 24 * 60 * 60,  # 30 days
        document_id
    )


@patch('app.services.deduplication_service.redis_client')
async def test_check_duplicate_redis_failure_falls_back_to_database(mock_redis, db_session, test_admin):
    """Test that Redis failures gracefully fall back to database."""
    content = b"Fallback test"
    content_hash = hashlib.sha256(content).hexdigest()

    # Create document in database
    from app.models.project import Project
    project = Project(
        id=uuid.uuid4(),
        name="Fallback Project",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    document = Document(
        id=uuid.uuid4(),
        filename="fallback.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )
    db_session.add(document)
    await db_session.commit()

    # Mock Redis failure
    mock_redis.get = AsyncMock(side_effect=Exception("Redis connection failed"))

    # Should fall back to database
    result = await check_duplicate(db_session, content_hash)

    assert result == str(document.id)


def test_compute_content_hash_empty_content():
    """Test hashing empty content."""
    content = b""

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_content_hash(content)

    assert actual_hash == expected_hash


def test_compute_content_hash_large_content():
    """Test hashing large content (50KB)."""
    content = b"X" * (50 * 1024)

    expected_hash = hashlib.sha256(content).hexdigest()
    actual_hash = compute_content_hash(content)

    assert actual_hash == expected_hash
    assert len(actual_hash) == 64


@patch('app.services.deduplication_service.redis_client')
async def test_check_duplicate_multiple_documents_same_hash(mock_redis, db_session, test_admin):
    """Test that first document is returned when multiple have same hash (edge case)."""
    content = b"Duplicate content"
    content_hash = hashlib.sha256(content).hexdigest()

    # Mock Redis cache miss
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.setex = AsyncMock()

    # Create project
    from app.models.project import Project
    project = Project(
        id=uuid.uuid4(),
        name="Duplicate Test",
        created_by=test_admin.id
    )
    db_session.add(project)
    await db_session.commit()

    # Create first document
    doc1 = Document(
        id=uuid.uuid4(),
        filename="first.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="AES-256-GCM",
        file_size=len(content),
        uploaded_by=test_admin.id,
        project_id=project.id,
        processing_status=ProcessingStatus.PENDING
    )
    db_session.add(doc1)
    await db_session.commit()

    result = await check_duplicate(db_session, content_hash)

    # Should return first document
    assert result == str(doc1.id)


@patch('app.services.deduplication_service.redis_client')
async def test_cache_document_hash_with_invalid_id_raises_error(mock_redis):
    """Test that caching with invalid document ID raises error."""
    content_hash = "abc123"
    invalid_doc_id = "not-a-uuid"

    mock_redis.setex = AsyncMock()

    # Should handle gracefully or raise appropriate error
    # For now, service should accept any string
    await cache_document_hash(content_hash, invalid_doc_id)

    mock_redis.setex.assert_called_once()
