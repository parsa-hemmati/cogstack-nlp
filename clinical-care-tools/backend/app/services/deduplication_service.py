"""
Document Deduplication Service.

Uses SHA-256 content hashing with Redis caching for fast duplicate detection.
Prevents duplicate document uploads and saves storage space.

Features:
- SHA-256 content hashing for unique document identification
- Redis cache for fast duplicate lookups (sub-millisecond)
- Database fallback when cache misses
- 30-day TTL on cache entries
- Graceful degradation if Redis unavailable

Usage:
    >>> from app.services.deduplication_service import check_duplicate, compute_content_hash
    >>>
    >>> # Compute content hash
    >>> content = b"Patient medical record..."
    >>> content_hash = compute_content_hash(content)
    >>>
    >>> # Check for duplicate
    >>> existing_doc_id = await check_duplicate(db, content_hash)
    >>> if existing_doc_id:
    ...     print(f"Duplicate! Existing document: {existing_doc_id}")
    ... else:
    ...     print("New document, proceed with upload")

Performance:
- Cache hit: ~1ms (Redis lookup)
- Cache miss + DB hit: ~10-50ms (PostgreSQL query + cache update)
- Cache miss + DB miss: ~10-50ms (PostgreSQL query only)
"""

import hashlib
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import redis_client
from app.models.document import Document


logger = logging.getLogger(__name__)


class DuplicationError(Exception):
    """Raised when deduplication check fails."""
    pass


def compute_content_hash(content: bytes) -> str:
    """
    Compute SHA-256 hash of document content.

    Args:
        content: Raw document content (bytes)

    Returns:
        str: 64-character hexadecimal SHA-256 hash

    Example:
        >>> content = b"Patient data..."
        >>> hash_value = compute_content_hash(content)
        >>> len(hash_value)
        64
    """
    return hashlib.sha256(content).hexdigest()


async def check_duplicate(db: AsyncSession, content_hash: str) -> Optional[str]:
    """
    Check if document with given hash already exists.

    Checks Redis cache first for fast lookup, falls back to database if cache miss.
    Updates cache after database lookup with 30-day TTL.

    Args:
        db: Database session
        content_hash: SHA-256 hash of document content (64-char hex string)

    Returns:
        Optional[str]: Document ID if duplicate found, None otherwise

    Raises:
        DuplicationError: If check fails critically (database error)

    Example:
        >>> existing_id = await check_duplicate(db, "abc123...")
        >>> if existing_id:
        ...     print(f"Duplicate of document {existing_id}")
    """
    try:
        # Step 1: Check Redis cache (fast path)
        cache_key = f"doc_hash:{content_hash}"

        try:
            cached_doc_id = await redis_client.get(cache_key)
            if cached_doc_id:
                logger.debug(f"Cache hit for hash {content_hash[:16]}...")
                return cached_doc_id
        except Exception as redis_error:
            # Redis failure should not block deduplication
            logger.warning(f"Redis cache check failed, falling back to database: {redis_error}")

        # Step 2: Check database (cache miss)
        logger.debug(f"Cache miss for hash {content_hash[:16]}..., checking database")

        result = await db.execute(
            select(Document.id).where(Document.content_hash == content_hash)
        )
        document = result.scalar_one_or_none()

        if document:
            document_id = str(document)
            logger.info(f"Duplicate found in database: {document_id}")

            # Step 3: Update cache for future lookups (30-day TTL)
            try:
                await cache_document_hash(content_hash, document_id)
            except Exception as cache_error:
                # Cache update failure should not block deduplication
                logger.warning(f"Failed to update cache: {cache_error}")

            return document_id

        # No duplicate found
        logger.debug(f"No duplicate found for hash {content_hash[:16]}...")
        return None

    except Exception as e:
        logger.error(f"Deduplication check failed for hash {content_hash[:16]}...: {e}")
        raise DuplicationError(f"Failed to check for duplicates: {str(e)}")


async def cache_document_hash(content_hash: str, document_id: str, ttl_days: int = 30) -> None:
    """
    Cache document hash to ID mapping in Redis.

    Args:
        content_hash: SHA-256 hash of document content
        document_id: Document UUID
        ttl_days: Time-to-live in days (default: 30)

    Raises:
        Exception: If Redis cache update fails (caller should handle gracefully)

    Example:
        >>> await cache_document_hash("abc123...", "550e8400-...")
    """
    cache_key = f"doc_hash:{content_hash}"
    ttl_seconds = ttl_days * 24 * 60 * 60

    try:
        await redis_client.setex(cache_key, ttl_seconds, document_id)
        logger.debug(f"Cached hash {content_hash[:16]}... -> {document_id} (TTL: {ttl_days} days)")
    except Exception as e:
        logger.error(f"Failed to cache document hash {content_hash[:16]}...: {e}")
        raise


async def invalidate_document_cache(content_hash: str) -> None:
    """
    Invalidate cached document hash (e.g., when document is deleted).

    Args:
        content_hash: SHA-256 hash of document content

    Example:
        >>> await invalidate_document_cache("abc123...")
    """
    cache_key = f"doc_hash:{content_hash}"

    try:
        await redis_client.delete(cache_key)
        logger.info(f"Invalidated cache for hash {content_hash[:16]}...")
    except Exception as e:
        logger.warning(f"Failed to invalidate cache for hash {content_hash[:16]}...: {e}")


# Statistics and monitoring helpers

async def get_cache_stats() -> dict:
    """
    Get deduplication cache statistics.

    Returns:
        dict: Cache statistics (keys count, memory usage, etc.)

    Example:
        >>> stats = await get_cache_stats()
        >>> print(f"Cached documents: {stats['doc_hash_count']}")
    """
    try:
        # Count keys matching doc_hash:* pattern
        keys = await redis_client.keys("doc_hash:*")
        doc_hash_count = len(keys) if keys else 0

        # Get Redis info
        info = await redis_client.info("memory")

        return {
            "doc_hash_count": doc_hash_count,
            "memory_used_mb": info.get("used_memory", 0) / (1024 * 1024),
            "memory_peak_mb": info.get("used_memory_peak", 0) / (1024 * 1024),
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "doc_hash_count": 0,
            "memory_used_mb": 0,
            "memory_peak_mb": 0,
            "error": str(e)
        }


# Module-level docstring test
if __name__ == "__main__":
    import asyncio

    async def example():
        print("Deduplication Service Example")
        print("-" * 50)

        # Compute hash
        content = b"Patient clinical notes for John Doe..."
        content_hash = compute_content_hash(content)
        print(f"Content hash: {content_hash}")
        print(f"Hash length: {len(content_hash)} characters")

    asyncio.run(example())
