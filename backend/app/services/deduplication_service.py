"""
Document Deduplication Service.

Provides SHA-256 hash-based deduplication with Redis caching.
Prevents duplicate document storage and saves processing time.
"""
import hashlib
from typing import Optional
from uuid import UUID

from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import get_redis
from app.models.document import Document


class DeduplicationService:
    """
    Document deduplication service using SHA-256 hashing.

    Features:
    - SHA-256 content hashing for deduplication
    - Redis cache for fast lookups (avoids database queries)
    - 30-day TTL on cache entries
    - Two-tier lookup: Redis first, then database

    Workflow:
        1. Compute SHA-256 hash of document content
        2. Check Redis cache: key = "doc_hash:{hash}"
        3. If cache miss, check database
        4. If found in database, update cache
        5. If not found anywhere, document is new

    Example:
        >>> service = DeduplicationService()
        >>> hash = service.compute_hash(content)
        >>> doc_id = await service.check_duplicate(hash, db)
        >>> if doc_id:
        >>>     print(f"Duplicate of document {doc_id}")
    """

    CACHE_PREFIX = "doc_hash:"
    CACHE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days

    def __init__(self):
        """Initialize deduplication service."""
        self.redis: Optional[Redis] = None

    async def get_redis(self) -> Redis:
        """Get Redis client (lazy initialization)."""
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    @staticmethod
    def compute_hash(content: bytes) -> str:
        """
        Compute SHA-256 hash of document content.

        Args:
            content: Document content (bytes)

        Returns:
            64-character hex hash (SHA-256)

        Example:
            >>> hash = DeduplicationService.compute_hash(b"Patient data")
            >>> print(hash)  # 64 hex characters
        """
        return hashlib.sha256(content).hexdigest()

    async def check_duplicate(self, content_hash: str) -> Optional[UUID]:
        """
        Check if document with this hash already exists (Redis only).

        Args:
            content_hash: SHA-256 hash of document content

        Returns:
            Document ID if duplicate found in cache, None otherwise

        Example:
            >>> doc_id = await service.check_duplicate(hash)
        """
        redis = await self.get_redis()
        cache_key = f"{self.CACHE_PREFIX}{content_hash}"

        cached_id = await redis.get(cache_key)
        if cached_id:
            return UUID(cached_id.decode())

        return None

    async def check_duplicate_db(
        self, content_hash: str, db: AsyncSession
    ) -> Optional[UUID]:
        """
        Check if document with this hash exists (Redis + Database).

        Args:
            content_hash: SHA-256 hash of document content
            db: Database session

        Returns:
            Document ID if duplicate found, None otherwise

        Example:
            >>> doc_id = await service.check_duplicate_db(hash, db)
        """
        # First, check Redis cache (fast path)
        cached_id = await self.check_duplicate(content_hash)
        if cached_id:
            return cached_id

        # Cache miss, check database
        result = await db.execute(
            select(Document.id).where(Document.content_hash == content_hash).limit(1)
        )
        doc_id = result.scalar_one_or_none()

        if doc_id:
            # Update cache for future lookups
            await self.update_cache(content_hash, doc_id)

        return doc_id

    async def update_cache(self, content_hash: str, doc_id: UUID) -> None:
        """
        Update Redis cache with document hash -> ID mapping.

        Args:
            content_hash: SHA-256 hash of document
            doc_id: Document UUID

        Example:
            >>> await service.update_cache(hash, doc_id)
        """
        redis = await self.get_redis()
        cache_key = f"{self.CACHE_PREFIX}{content_hash}"

        await redis.setex(cache_key, self.CACHE_TTL_SECONDS, str(doc_id))

    async def invalidate_cache(self, content_hash: str) -> None:
        """
        Invalidate cache entry for a document hash.

        Used when document is deleted.

        Args:
            content_hash: SHA-256 hash to invalidate

        Example:
            >>> await service.invalidate_cache(hash)
        """
        redis = await self.get_redis()
        cache_key = f"{self.CACHE_PREFIX}{content_hash}"

        await redis.delete(cache_key)
