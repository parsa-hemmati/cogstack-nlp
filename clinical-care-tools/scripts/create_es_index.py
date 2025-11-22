#!/usr/bin/env python3
"""
Create Elasticsearch Index for Clinical Concepts.

This script creates the 'clinical_concepts' index in Elasticsearch with proper
mappings for storing MedCAT-extracted medical concepts.

Usage:
    python scripts/create_es_index.py [--recreate]

Options:
    --recreate    Delete existing index and recreate (WARNING: data loss)

Requirements:
    - Elasticsearch 8.x running at localhost:9200 (or ELASTICSEARCH_URL env var)
    - elasticsearch Python package installed: pip install elasticsearch==8.11.1
"""

import sys
import os
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import RequestError


# Elasticsearch connection
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")

# Index name
INDEX_NAME = "clinical_concepts"

# Index mapping
INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "clinical_text_analyzer": {
                    "type": "standard",
                    "stopwords": "_english_"
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "patient_id": {
                "type": "keyword",
                "index": True
            },
            "document_id": {
                "type": "keyword",
                "index": True
            },
            "concept_cui": {
                "type": "keyword",
                "index": True
            },
            "concept_name": {
                "type": "text",
                "analyzer": "clinical_text_analyzer",
                "fields": {
                    "keyword": {
                        "type": "keyword",
                        "ignore_above": 256
                    }
                }
            },
            "concept_type": {
                "type": "keyword",
                "index": True
            },
            "date": {
                "type": "date",
                "format": "strict_date_optional_time||yyyy-MM-dd||epoch_millis"
            },
            "sentence": {
                "type": "text",
                "analyzer": "clinical_text_analyzer"
            },
            "start_char": {
                "type": "integer"
            },
            "end_char": {
                "type": "integer"
            },
            "meta_annotations": {
                "type": "nested",
                "properties": {
                    "Negation": {
                        "type": "keyword",
                        "index": True
                    },
                    "Experiencer": {
                        "type": "keyword",
                        "index": True
                    },
                    "Temporality": {
                        "type": "keyword",
                        "index": True
                    },
                    "Certainty": {
                        "type": "keyword",
                        "index": True
                    }
                }
            },
            "confidence": {
                "type": "float"
            }
        }
    }
}


def create_index(es: Elasticsearch, recreate: bool = False):
    """
    Create Elasticsearch index with mapping.

    Args:
        es: Elasticsearch client instance
        recreate: If True, delete existing index before creating

    Returns:
        True if successful, False otherwise
    """
    # Check if index exists
    index_exists = es.indices.exists(index=INDEX_NAME)

    if index_exists and recreate:
        print(f"⚠️  Deleting existing index '{INDEX_NAME}'...")
        es.indices.delete(index=INDEX_NAME)
        print(f"✅ Index '{INDEX_NAME}' deleted")
        index_exists = False

    if index_exists:
        print(f"⚠️  Index '{INDEX_NAME}' already exists")
        print(f"    Use --recreate to delete and recreate (WARNING: data loss)")
        return False

    # Create index
    print(f"📝 Creating index '{INDEX_NAME}'...")

    try:
        es.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
        print(f"✅ Index '{INDEX_NAME}' created successfully")

        # Verify mapping
        mapping = es.indices.get_mapping(index=INDEX_NAME)
        properties = mapping[INDEX_NAME]["mappings"]["properties"]

        print(f"\n📊 Index Mapping Summary:")
        print(f"   - Fields: {len(properties)}")
        print(f"   - Keyword fields: patient_id, document_id, concept_cui, concept_type")
        print(f"   - Text fields: concept_name, sentence")
        print(f"   - Date field: date")
        print(f"   - Nested object: meta_annotations")
        print(f"   - Numeric fields: start_char, end_char, confidence")

        return True

    except RequestError as e:
        print(f"❌ Error creating index: {e.info}")
        return False


def main():
    """Main entry point for script."""
    # Check for --recreate flag
    recreate = "--recreate" in sys.argv

    if recreate:
        print("⚠️  WARNING: --recreate flag detected")
        print("    This will DELETE all existing data in the index")
        response = input("    Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Aborted")
            return

    # Connect to Elasticsearch
    print(f"🔌 Connecting to Elasticsearch at {ES_URL}...")

    try:
        es = Elasticsearch([ES_URL])

        # Check connection
        if not es.ping():
            print(f"❌ Cannot connect to Elasticsearch at {ES_URL}")
            print("   Make sure Elasticsearch is running:")
            print("   - docker-compose up -d elasticsearch")
            print("   - curl http://localhost:9200/_cluster/health")
            sys.exit(1)

        print(f"✅ Connected to Elasticsearch")

        # Get cluster info
        info = es.info()
        print(f"   Version: {info['version']['number']}")
        print(f"   Cluster: {info['cluster_name']}")

        # Create index
        success = create_index(es, recreate=recreate)

        if success:
            print(f"\n✅ Elasticsearch index setup complete!")
            print(f"\n📚 Next steps:")
            print(f"   1. Run data migration: python scripts/migrate_concepts_to_es.py")
            print(f"   2. Verify index: curl http://localhost:9200/{INDEX_NAME}/_count?pretty")
            print(f"   3. Test timeline API: GET /api/v1/timeline/{{patient_id}}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
