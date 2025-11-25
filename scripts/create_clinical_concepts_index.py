#!/usr/bin/env python3
"""
Create clinical_concepts Elasticsearch index for Timeline View.

This script creates the Elasticsearch index for storing clinical concepts
with temporal and meta-annotation data for fast timeline queries.

Usage:
    python scripts/create_clinical_concepts_index.py

Environment Variables:
    ELASTICSEARCH_URL: Elasticsearch connection URL (default: http://localhost:9200)
"""

import json
import os
import sys
from pathlib import Path

try:
    from elasticsearch import Elasticsearch
except ImportError:
    print("ERROR: elasticsearch package not installed")
    print("Install with: pip install elasticsearch")
    sys.exit(1)


def create_index():
    """Create clinical_concepts index with mappings."""

    # Get Elasticsearch URL from environment
    es_url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

    # Connect to Elasticsearch
    print(f"Connecting to Elasticsearch at {es_url}...")
    es = Elasticsearch([es_url])

    # Check connection
    try:
        if not es.ping():
            print(f"ERROR: Cannot connect to Elasticsearch at {es_url}")
            sys.exit(1)
        print("✅ Connected to Elasticsearch")
    except Exception as e:
        print(f"ERROR: Failed to connect to Elasticsearch: {e}")
        sys.exit(1)

    # Load mapping from JSON file
    mapping_file = Path(__file__).parent.parent / "backend" / "elasticsearch" / "clinical_concepts_mapping.json"

    if not mapping_file.exists():
        print(f"ERROR: Mapping file not found: {mapping_file}")
        sys.exit(1)

    with open(mapping_file) as f:
        mapping = json.load(f)

    # Check if index already exists
    index_name = "clinical_concepts"

    if es.indices.exists(index=index_name):
        print(f"ℹ️  Index '{index_name}' already exists")

        # Ask user if they want to delete and recreate
        response = input("Delete and recreate? (y/N): ").strip().lower()

        if response == 'y':
            print(f"Deleting existing index '{index_name}'...")
            es.indices.delete(index=index_name)
            print("✅ Index deleted")
        else:
            print("Keeping existing index. Exiting.")
            return

    # Create index
    print(f"Creating index '{index_name}'...")
    es.indices.create(index=index_name, body=mapping)
    print("✅ Index created successfully")

    # Verify index was created
    index_info = es.indices.get(index=index_name)
    print(f"\nIndex settings:")
    print(f"  Shards: {index_info[index_name]['settings']['index']['number_of_shards']}")
    print(f"  Replicas: {index_info[index_name]['settings']['index']['number_of_replicas']}")
    print(f"  Refresh interval: {index_info[index_name]['settings']['index']['refresh_interval']}")

    print(f"\nIndex mappings:")
    mappings = index_info[index_name]['mappings']['properties']
    print(f"  Fields: {list(mappings.keys())}")

    print(f"\n✅ clinical_concepts index is ready for use")


if __name__ == "__main__":
    create_index()
