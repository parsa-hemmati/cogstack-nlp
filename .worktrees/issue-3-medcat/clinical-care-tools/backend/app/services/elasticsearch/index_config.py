"""Elasticsearch index configuration for documents.

This module defines the index mapping for document full-text search with:
- Custom medical analyzer (lowercase + stop + snowball)
- Field boosting for relevance ranking
- Keyword sub-fields for faceting
- Optimized settings for 100K+ documents
"""

from typing import Dict, Any
from elasticsearch import AsyncElasticsearch
import logging

logger = logging.getLogger(__name__)

# Elasticsearch index name
INDEX_NAME = "documents"

# Index configuration with mapping and settings
DOCUMENTS_INDEX_CONFIG: Dict[str, Any] = {
    "settings": {
        "number_of_shards": 2,
        "number_of_replicas": 1,
        "refresh_interval": "5s",
        "analysis": {
            "analyzer": {
                "medical_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "document_id": {
                "type": "keyword"
            },
            "patient_id": {
                "type": "keyword"
            },
            "title": {
                "type": "text",
                "analyzer": "medical_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "content": {
                "type": "text",
                "analyzer": "medical_analyzer"
            },
            "document_type": {
                "type": "keyword"
            },
            "author": {
                "type": "text",
                "analyzer": "medical_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "department": {
                "type": "keyword"
            },
            "date": {
                "type": "date",
                "format": "strict_date_optional_time||epoch_millis"
            },
            "created_at": {
                "type": "date"
            },
            "updated_at": {
                "type": "date"
            }
        }
    }
}


async def create_index(
    es_client: AsyncElasticsearch,
    index_name: str = INDEX_NAME,
    config: Dict[str, Any] = DOCUMENTS_INDEX_CONFIG
) -> bool:
    """
    Create Elasticsearch index with specified configuration.

    Args:
        es_client: Async Elasticsearch client
        index_name: Name of index to create (default: "documents")
        config: Index configuration (settings + mappings)

    Returns:
        True if index created successfully, False if already exists

    Raises:
        elasticsearch.exceptions.ElasticsearchException: If index creation fails
    """
    try:
        # Check if index already exists
        exists = await es_client.indices.exists(index=index_name)

        if exists:
            logger.info(f"Index '{index_name}' already exists")
            return False

        # Create index
        await es_client.indices.create(index=index_name, body=config)
        logger.info(f"Index '{index_name}' created successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to create index '{index_name}': {e}")
        raise


async def delete_index(
    es_client: AsyncElasticsearch,
    index_name: str = INDEX_NAME
) -> bool:
    """
    Delete Elasticsearch index.

    Args:
        es_client: Async Elasticsearch client
        index_name: Name of index to delete

    Returns:
        True if index deleted successfully, False if doesn't exist

    Raises:
        elasticsearch.exceptions.ElasticsearchException: If deletion fails
    """
    try:
        # Check if index exists
        exists = await es_client.indices.exists(index=index_name)

        if not exists:
            logger.info(f"Index '{index_name}' does not exist")
            return False

        # Delete index
        await es_client.indices.delete(index=index_name)
        logger.info(f"Index '{index_name}' deleted successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to delete index '{index_name}': {e}")
        raise


async def get_index_mapping(
    es_client: AsyncElasticsearch,
    index_name: str = INDEX_NAME
) -> Dict[str, Any]:
    """
    Get current index mapping.

    Args:
        es_client: Async Elasticsearch client
        index_name: Name of index

    Returns:
        Index mapping dictionary

    Raises:
        elasticsearch.exceptions.NotFoundError: If index doesn't exist
    """
    try:
        mapping = await es_client.indices.get_mapping(index=index_name)
        return mapping[index_name]["mappings"]

    except Exception as e:
        logger.error(f"Failed to get mapping for index '{index_name}': {e}")
        raise
