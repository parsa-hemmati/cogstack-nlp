#!/usr/bin/env python3
"""
Script to create Elasticsearch index for document search.

Usage:
    python scripts/create_es_index.py

Environment variables:
    ELASTICSEARCH_URL: Elasticsearch connection URL (default: http://localhost:9200)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from elasticsearch import AsyncElasticsearch
from app.services.elasticsearch.index_config import create_index, INDEX_NAME, DOCUMENTS_INDEX_CONFIG
from app.core.config import settings


async def main():
    """Create Elasticsearch index."""
    print(f"Creating Elasticsearch index '{INDEX_NAME}'...")
    print(f"Connecting to: {settings.ELASTICSEARCH_URL}")

    # Create Elasticsearch client
    es_client = AsyncElasticsearch(
        hosts=[settings.ELASTICSEARCH_URL],
        verify_certs=False  # For local development
    )

    try:
        # Create index
        created = await create_index(es_client, INDEX_NAME, DOCUMENTS_INDEX_CONFIG)

        if created:
            print(f"✅ Index '{INDEX_NAME}' created successfully!")

            # Print mapping
            mapping = await es_client.indices.get_mapping(index=INDEX_NAME)
            print("\nIndex mapping:")
            import json
            print(json.dumps(mapping[INDEX_NAME]["mappings"], indent=2))
        else:
            print(f"ℹ️  Index '{INDEX_NAME}' already exists")

    except Exception as e:
        print(f"❌ Error creating index: {e}")
        sys.exit(1)

    finally:
        await es_client.close()


if __name__ == "__main__":
    asyncio.run(main())
