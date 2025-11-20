"""
Search Indexer Service

Batch indexes documents from PostgreSQL to Elasticsearch for full-text search.
Decrypts document content, extracts concepts from extracted_entities, and uses bulk API for performance.
"""

import logging
from datetime import datetime
from typing import List, Dict
from uuid import UUID

from elasticsearch import AsyncElasticsearch, helpers
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity, EntityType
from app.services.encryption_service import EncryptionService

logger = logging.getLogger(__name__)


class SearchIndexer:
    """
    Service for batch indexing documents to Elasticsearch.

    Responsibilities:
    - Query unindexed documents from PostgreSQL (indexed=False)
    - Decrypt document content using EncryptionService
    - Extract concepts from extracted_entities table
    - Batch index to Elasticsearch using async_bulk()
    - Mark documents as indexed=True after successful indexing
    - Handle errors gracefully (log and continue)

    Usage:
        indexer = SearchIndexer(es_client=get_es_client(), db_session=db)
        count = await indexer.index_documents_batch(batch_size=1000)
        print(f"Indexed {count} documents")
    """

    def __init__(self, es_client: AsyncElasticsearch, db_session: AsyncSession):
        """
        Initialize SearchIndexer.

        Args:
            es_client: Elasticsearch async client
            db_session: SQLAlchemy async database session
        """
        self.es = es_client
        self.db = db_session
        self.encryption_service = EncryptionService.from_env()

    async def _get_unindexed_documents(self, batch_size: int = 1000) -> List[Document]:
        """
        Get documents that haven't been indexed yet.

        Args:
            batch_size: Maximum number of documents to retrieve

        Returns:
            List of unindexed documents (indexed=False)
        """
        stmt = (
            select(Document)
            .where(Document.indexed == False)
            .limit(batch_size)
            .order_by(Document.created_at.asc())  # Oldest first
        )

        result = await self.db.execute(stmt)
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} unindexed documents")
        return list(documents)

    def _decrypt_content(self, encrypted_content: bytes) -> str:
        """
        Decrypt document content using EncryptionService.

        Args:
            encrypted_content: Encrypted content from documents.encrypted_content

        Returns:
            Decrypted plaintext as string
        """
        plaintext_bytes = self.encryption_service.decrypt(encrypted_content)
        return plaintext_bytes.decode('utf-8')

    async def _extract_concepts(self, document_id: UUID) -> List[Dict]:
        """
        Extract clinical concepts from document's extracted_entities.

        Args:
            document_id: Document UUID

        Returns:
            List of concept dictionaries with cui, name, type fields
        """
        stmt = (
            select(ExtractedEntity)
            .where(ExtractedEntity.document_id == document_id)
            .where(ExtractedEntity.entity_type == EntityType.CLINICAL)
        )

        result = await self.db.execute(stmt)
        entities = result.scalars().all()

        concepts = [
            {
                "cui": entity.cui,
                "name": entity.pretty_name,
                "type": entity.entity_type.value
            }
            for entity in entities
            if entity.cui  # Skip entities without CUI
        ]

        logger.debug(f"Extracted {len(concepts)} concepts from document {document_id}")
        return concepts

    async def index_documents_batch(self, batch_size: int = 1000) -> int:
        """
        Index a batch of documents to Elasticsearch.

        Process:
        1. Query unindexed documents (indexed=False)
        2. For each document:
           - Decrypt content
           - Extract concepts from extracted_entities
           - Create Elasticsearch document
        3. Bulk index to Elasticsearch
        4. Mark documents as indexed=True
        5. Commit database changes

        Args:
            batch_size: Number of documents to index per batch (default 1000)

        Returns:
            Number of documents successfully indexed
        """
        try:
            # Get unindexed documents
            documents = await self._get_unindexed_documents(batch_size)

            if not documents:
                logger.info("No unindexed documents found")
                return 0

            # Prepare bulk indexing actions
            actions = []

            for doc in documents:
                try:
                    # Decrypt content
                    content = self._decrypt_content(doc.encrypted_content)

                    # Extract concepts
                    concepts = await self._extract_concepts(doc.id)

                    # Create Elasticsearch document
                    es_doc = {
                        "_index": "documents",
                        "_id": str(doc.id),
                        "_source": {
                            "document_id": str(doc.id),
                            "title": doc.filename,
                            "content": content,
                            "document_type": doc.content_type,
                            "author": str(doc.uploaded_by),
                            "date": doc.created_at.isoformat() if doc.created_at else None,
                            "patient_id": None,  # Future: link to patient
                            "concepts": concepts,
                            "indexed_at": datetime.utcnow().isoformat()
                        }
                    }

                    actions.append(es_doc)

                except Exception as e:
                    logger.error(f"Error preparing document {doc.id} for indexing: {e}")
                    continue

            if not actions:
                logger.warning("No documents could be prepared for indexing")
                return 0

            # Bulk index to Elasticsearch
            logger.info(f"Bulk indexing {len(actions)} documents to Elasticsearch...")
            success_count, errors = await helpers.async_bulk(
                self.es,
                actions,
                raise_on_error=False,  # Don't raise on individual errors
                stats_only=True
            )

            logger.info(f"Successfully indexed {success_count} documents")

            if errors:
                logger.error(f"Encountered {len(errors)} errors during bulk indexing")

            # Mark successfully indexed documents
            indexed_doc_ids = {action["_id"] for action in actions}
            for doc in documents:
                if str(doc.id) in indexed_doc_ids:
                    doc.indexed = True
                    doc.last_indexed_at = datetime.utcnow()

            # Commit database changes
            await self.db.commit()

            return success_count

        except Exception as e:
            logger.error(f"Error during batch indexing: {e}")
            await self.db.rollback()
            return 0
