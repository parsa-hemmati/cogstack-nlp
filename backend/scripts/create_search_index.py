#!/usr/bin/env python3
"""
Elasticsearch Index Creation Script

Purpose: Create 'documents' index with clinical_analyzer for full-text search
Usage: python backend/scripts/create_search_index.py
Requirements: Elasticsearch running at http://localhost:9200
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from elasticsearch import AsyncElasticsearch


async def create_documents_index():
    """Create Elasticsearch documents index with mapping"""

    # Get Elasticsearch URL from environment or use default
    es_url = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')

    print(f"🔗 Connecting to Elasticsearch at {es_url}")
    es = AsyncElasticsearch([es_url])

    try:
        # Check Elasticsearch health
        health = await es.cluster.health()
        print(f"✅ Elasticsearch cluster health: {health['status']}")

        # Read mapping from JSON file
        backend_dir = Path(__file__).parent.parent
        mapping_file = backend_dir / 'elasticsearch' / 'documents-mapping.json'

        print(f"📄 Reading mapping from {mapping_file}")
        with open(mapping_file, 'r') as f:
            mapping = json.load(f)

        # Delete existing index if exists (idempotent operation)
        index_name = 'documents'
        if await es.indices.exists(index=index_name):
            print(f"⚠️  Index '{index_name}' already exists. Deleting...")
            await es.indices.delete(index=index_name)
            print(f"🗑️  Deleted existing index '{index_name}'")

        # Create index with mapping
        print(f"🔨 Creating index '{index_name}' with mapping...")
        await es.indices.create(index=index_name, body=mapping)
        print(f"✅ Created index '{index_name}'")

        # Verify index created
        index_info = await es.indices.get(index=index_name)
        settings = index_info[index_name]['settings']
        mappings = index_info[index_name]['mappings']

        print(f"\n📊 Index Information:")
        print(f"  - Shards: {settings['index']['number_of_shards']}")
        print(f"  - Replicas: {settings['index']['number_of_replicas']}")
        print(f"  - Refresh interval: {settings['index'].get('refresh_interval', 'default')}")
        print(f"  - Fields: {len(mappings['properties'])} properties defined")
        print(f"  - Analyzer: clinical_analyzer configured")

        print(f"\n🎉 Success! Index '{index_name}' is ready for document indexing.")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        await es.close()


if __name__ == '__main__':
    asyncio.run(create_documents_index())
