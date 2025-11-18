"""Elasticsearch client and utilities."""

import logging
from typing import Any, Dict, List, Optional

from elasticsearch import AsyncElasticsearch, NotFoundError

logger = logging.getLogger(__name__)

# Elasticsearch client instance
_es_client: Optional[AsyncElasticsearch] = None


def get_elasticsearch_client() -> AsyncElasticsearch:
    """
    Get or create Elasticsearch client.

    Returns:
        AsyncElasticsearch client
    """
    global _es_client

    if _es_client is None:
        # TODO: Get URL from settings
        _es_client = AsyncElasticsearch(
            hosts=["http://localhost:9200"],
            request_timeout=30,
        )
        logger.info("Elasticsearch client created")

    return _es_client


async def close_elasticsearch_client() -> None:
    """Close Elasticsearch client."""
    global _es_client

    if _es_client:
        await _es_client.close()
        _es_client = None
        logger.info("Elasticsearch client closed")


class ElasticsearchService:
    """Service for Elasticsearch operations."""

    def __init__(self, index_name: str = "clinical_documents"):
        """
        Initialize Elasticsearch service.

        Args:
            index_name: Name of the Elasticsearch index
        """
        self.index_name = index_name
        self.client = get_elasticsearch_client()

    async def create_index(self, mappings: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create Elasticsearch index with mappings.

        Args:
            mappings: Index mappings

        Returns:
            True if successful
        """
        if mappings is None:
            mappings = self._get_default_mappings()

        try:
            await self.client.indices.create(
                index=self.index_name,
                body={"mappings": mappings},
            )
            logger.info(f"Created index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {e}")
            return False

    async def index_document(
        self,
        doc_id: str,
        document: Dict[str, Any],
    ) -> bool:
        """
        Index a document in Elasticsearch.

        Args:
            doc_id: Document ID
            document: Document content

        Returns:
            True if successful
        """
        try:
            await self.client.index(
                index=self.index_name,
                id=doc_id,
                document=document,
            )
            logger.info(f"Indexed document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to index document: {e}")
            return False

    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document content or None
        """
        try:
            result = await self.client.get(index=self.index_name, id=doc_id)
            return result["_source"]
        except NotFoundError:
            return None
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

    async def search(
        self,
        query: Dict[str, Any],
        size: int = 20,
        from_: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Search documents.

        Args:
            query: Elasticsearch query
            size: Number of results
            from_: Starting offset

        Returns:
            List of matching documents
        """
        try:
            result = await self.client.search(
                index=self.index_name,
                body={"query": query, "size": size, "from": from_},
            )

            return [hit["_source"] for hit in result["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def delete_document(self, doc_id: str) -> bool:
        """
        Delete document by ID.

        Args:
            doc_id: Document ID

        Returns:
            True if successful
        """
        try:
            await self.client.delete(index=self.index_name, id=doc_id)
            logger.info(f"Deleted document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False

    def _get_default_mappings(self) -> Dict[str, Any]:
        """
        Get default index mappings for clinical documents.

        Returns:
            Elasticsearch mappings
        """
        return {
            "properties": {
                "patient_id": {"type": "keyword"},
                "document_id": {"type": "keyword"},
                "document_type": {"type": "keyword"},
                "document_date": {"type": "date"},
                "author": {"type": "text"},
                "title": {"type": "text"},
                "content": {
                    "type": "text",
                    "analyzer": "english",
                },
                "entities": {
                    "type": "nested",
                    "properties": {
                        "cui": {"type": "keyword"},
                        "name": {"type": "text"},
                        "type": {"type": "keyword"},
                        "start": {"type": "integer"},
                        "end": {"type": "integer"},
                        "confidence": {"type": "float"},
                        "negation": {"type": "keyword"},
                        "temporality": {"type": "keyword"},
                        "experiencer": {"type": "keyword"},
                        "certainty": {"type": "keyword"},
                    },
                },
                "processed_at": {"type": "date"},
            }
        }
