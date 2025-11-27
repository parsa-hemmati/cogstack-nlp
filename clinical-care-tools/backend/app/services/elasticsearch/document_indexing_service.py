"""Document indexing service for Elasticsearch.

Syncs documents from PostgreSQL to Elasticsearch for full-text search.
Supports single document indexing and bulk operations.
"""

from typing import List, Optional, Dict, Any
from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from app.models.document import Document
from app.services.elasticsearch.index_config import INDEX_NAME

logger = logging.getLogger(__name__)


class DocumentIndexingService:
    """Service to index documents to Elasticsearch."""

    def __init__(self, es_client: AsyncElasticsearch, db: AsyncSession):
        """
        Initialize document indexing service.

        Args:
            es_client: Async Elasticsearch client
            db: Async database session
        """
        self.es = es_client
        self.db = db

    async def index_document(self, document_id: str) -> bool:
        """
        Index single document to Elasticsearch.

        Args:
            document_id: UUID of document to index

        Returns:
            True if indexed successfully, False otherwise

        Raises:
            ValueError: If document not found
        """
        try:
            # Fetch document from database
            result = await self.db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Transform to Elasticsearch document
            es_doc = self._transform_document(document)

            # Index to Elasticsearch
            await self.es.index(
                index=INDEX_NAME,
                id=str(document.id),
                document=es_doc
            )

            logger.info(f"Indexed document {document_id} to Elasticsearch")
            return True

        except Exception as e:
            logger.error(f"Failed to index document {document_id}: {e}")
            raise

    async def update_document(self, document_id: str) -> bool:
        """
        Update document in Elasticsearch.

        Args:
            document_id: UUID of document to update

        Returns:
            True if updated successfully

        Note:
            This is essentially the same as indexing (upsert operation)
        """
        return await self.index_document(document_id)

    async def delete_document(self, document_id: str) -> bool:
        """
        Delete document from Elasticsearch.

        Args:
            document_id: UUID of document to delete

        Returns:
            True if deleted successfully, False if not found
        """
        try:
            await self.es.delete(
                index=INDEX_NAME,
                id=document_id
            )

            logger.info(f"Deleted document {document_id} from Elasticsearch")
            return True

        except Exception as e:
            if "not_found" in str(e).lower():
                logger.warning(f"Document {document_id} not found in Elasticsearch")
                return False

            logger.error(f"Failed to delete document {document_id}: {e}")
            raise

    async def index_documents_bulk(
        self,
        document_ids: Optional[List[str]] = None,
        batch_size: int = 1000
    ) -> Dict[str, int]:
        """
        Index multiple documents in bulk.

        Args:
            document_ids: List of document IDs to index (None = all documents)
            batch_size: Number of documents per batch (default: 1000)

        Returns:
            Dictionary with counts:
                - indexed: Number successfully indexed
                - failed: Number failed
                - total: Total processed

        Raises:
            Exception: If bulk indexing fails critically
        """
        try:
            # Build query
            query = select(Document)
            if document_ids:
                query = query.where(Document.id.in_(document_ids))

            # Execute query
            result = await self.db.execute(query)
            documents = result.scalars().all()

            if not documents:
                logger.warning("No documents found to index")
                return {"indexed": 0, "failed": 0, "total": 0}

            # Prepare bulk actions
            actions = [
                {
                    "_index": INDEX_NAME,
                    "_id": str(doc.id),
                    "_source": self._transform_document(doc)
                }
                for doc in documents
            ]

            # Bulk index
            success_count = 0
            failed_count = 0

            async for ok, result in async_bulk(
                self.es,
                actions,
                chunk_size=batch_size,
                raise_on_error=False
            ):
                if ok:
                    success_count += 1
                else:
                    failed_count += 1
                    logger.error(f"Failed to index document: {result}")

            logger.info(
                f"Bulk indexing complete: {success_count} indexed, "
                f"{failed_count} failed, {len(documents)} total"
            )

            return {
                "indexed": success_count,
                "failed": failed_count,
                "total": len(documents)
            }

        except Exception as e:
            logger.error(f"Bulk indexing failed: {e}")
            raise

    def _transform_document(self, document: Document) -> Dict[str, Any]:
        """
        Transform SQLAlchemy Document model to Elasticsearch document.

        Args:
            document: SQLAlchemy Document instance

        Returns:
            Dictionary suitable for Elasticsearch indexing
        """
        return {
            "document_id": str(document.id),
            "patient_id": str(document.patient_id),
            "title": document.title or "",
            "content": document.content or "",
            "document_type": document.document_type or "unknown",
            "author": document.author or "Unknown",
            "department": document.department or "Unknown",
            "date": document.date.isoformat() if document.date else None,
            "created_at": document.created_at.isoformat() if document.created_at else None,
            "updated_at": document.updated_at.isoformat() if document.updated_at else None,
        }

    async def reindex_all(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Reindex all documents (delete index and recreate).

        Args:
            batch_size: Batch size for bulk operations

        Returns:
            Dictionary with indexing statistics

        Warning:
            This deletes and recreates the entire index
        """
        from app.services.elasticsearch.index_config import create_index, delete_index

        try:
            logger.info("Starting full reindex...")

            # Delete existing index
            await delete_index(self.es, INDEX_NAME)

            # Create fresh index
            await create_index(self.es, INDEX_NAME)

            # Index all documents
            stats = await self.index_documents_bulk(batch_size=batch_size)

            logger.info(f"Full reindex complete: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Full reindex failed: {e}")
            raise
