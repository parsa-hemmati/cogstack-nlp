"""
Unit tests for Document Deduplication Service.

Tests SHA-256 hash-based deduplication with Redis cache.
"""
import hashlib
import pytest
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.services.deduplication_service import DeduplicationService


@pytest.fixture
def dedup_service():
    """Create deduplication service with mocked Redis."""
    service = DeduplicationService()
    return service


@pytest.fixture
def sample_content():
    """Sample document content for testing."""
    return b"This is a sample clinical document with patient information."


def test_compute_hash_same_content_same_hash(sample_content):
    """Test that same content produces same hash."""
    hash1 = DeduplicationService.compute_hash(sample_content)
    hash2 = DeduplicationService.compute_hash(sample_content)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 produces 64 hex characters


def test_compute_hash_different_content_different_hash():
    """Test that different content produces different hashes."""
    content1 = b"Patient A has diabetes."
    content2 = b"Patient B has hypertension."

    hash1 = DeduplicationService.compute_hash(content1)
    hash2 = DeduplicationService.compute_hash(content2)

    assert hash1 != hash2


def test_compute_hash_deterministic(sample_content):
    """Test that hash computation is deterministic (not random)."""
    hashes = [DeduplicationService.compute_hash(sample_content) for _ in range(10)]

    # All hashes should be identical
    assert len(set(hashes)) == 1


@pytest.mark.asyncio
async def test_check_duplicate_cache_hit(dedup_service):
    """Test cache hit for duplicate document (fast path)."""
    content_hash = "abc123def456"
    existing_doc_id = uuid4()

    # Mock Redis get() to return cached document ID
    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.get = AsyncMock(return_value=str(existing_doc_id).encode())

        result = await dedup_service.check_duplicate(content_hash)

        assert result == existing_doc_id
        mock_redis.get.assert_called_once_with(f"doc_hash:{content_hash}")


@pytest.mark.asyncio
async def test_check_duplicate_cache_miss_database_hit(dedup_service, db: AsyncSession, admin_user):
    """Test cache miss but database hit (updates cache)."""
    content = b"Duplicate document"
    content_hash = hashlib.sha256(content).hexdigest()

    # Create document in database
    doc = Document(
        filename="original.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Mock Redis: cache miss (get returns None)
    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        result = await dedup_service.check_duplicate_db(content_hash, db)

        assert result == doc.id
        # Cache should be updated
        mock_redis.setex.assert_called_once_with(
            f"doc_hash:{content_hash}",
            30 * 24 * 60 * 60,  # 30 days
            str(doc.id),
        )


@pytest.mark.asyncio
async def test_check_duplicate_no_duplicate(dedup_service, db: AsyncSession):
    """Test no duplicate found (cache miss + database miss)."""
    content_hash = "nonexistent_hash_12345"

    # Mock Redis: cache miss
    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)

        result = await dedup_service.check_duplicate_db(content_hash, db)

        assert result is None


@pytest.mark.asyncio
async def test_update_cache_after_database_lookup(dedup_service):
    """Test cache is updated after successful database lookup."""
    content_hash = "test_hash_xyz"
    doc_id = uuid4()
    ttl_seconds = 30 * 24 * 60 * 60  # 30 days

    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.setex = AsyncMock()

        await dedup_service.update_cache(content_hash, doc_id)

        mock_redis.setex.assert_called_once_with(
            f"doc_hash:{content_hash}",
            ttl_seconds,
            str(doc_id),
        )


@pytest.mark.asyncio
async def test_check_duplicate_cache_ttl_30_days(dedup_service):
    """Test cache entries have 30-day TTL."""
    content_hash = "test_hash"
    doc_id = uuid4()

    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.setex = AsyncMock()

        await dedup_service.update_cache(content_hash, doc_id)

        # Verify TTL is 30 days (in seconds)
        expected_ttl = 30 * 24 * 60 * 60
        mock_redis.setex.assert_called_once()
        args = mock_redis.setex.call_args[0]
        assert args[1] == expected_ttl


def test_compute_hash_empty_content():
    """Test hash computation for empty content."""
    content = b""
    content_hash = DeduplicationService.compute_hash(content)

    # SHA-256 of empty string is known value
    expected_hash = hashlib.sha256(b"").hexdigest()
    assert content_hash == expected_hash


def test_compute_hash_large_content():
    """Test hash computation for large document (5MB)."""
    content = b"A" * (5 * 1024 * 1024)  # 5MB

    content_hash = DeduplicationService.compute_hash(content)

    assert len(content_hash) == 64
    assert content_hash == hashlib.sha256(content).hexdigest()


@pytest.mark.asyncio
async def test_deduplication_workflow_new_document(dedup_service, db: AsyncSession):
    """Test complete workflow for new document (no duplicate)."""
    content = b"Brand new document content"
    content_hash = DeduplicationService.compute_hash(content)

    # Mock Redis: cache miss
    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)

        # Check for duplicate
        result = await dedup_service.check_duplicate_db(content_hash, db)

        assert result is None  # No duplicate found


@pytest.mark.asyncio
async def test_deduplication_workflow_duplicate_document(
    dedup_service, db: AsyncSession, admin_user
):
    """Test complete workflow for duplicate document."""
    content = b"Duplicate document content"
    content_hash = DeduplicationService.compute_hash(content)

    # Create original document
    doc = Document(
        filename="original.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=content,
        encryption_algorithm="aes-256-gcm",
        file_size=len(content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Mock Redis: cache miss (first check)
    with patch.object(
        dedup_service, "redis", new_callable=AsyncMock
    ) as mock_redis:
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()

        # Check for duplicate
        result = await dedup_service.check_duplicate_db(content_hash, db)

        assert result == doc.id  # Duplicate found!
