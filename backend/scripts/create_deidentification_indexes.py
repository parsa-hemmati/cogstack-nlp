#!/usr/bin/env python3
"""
Create Elasticsearch indexes for de-identification audit logging.

Indexes:
- deidentified_notes: Stores de-identified clinical notes
- phi_audit_log: Stores audit trail of all de-identification activities

Usage:
    python scripts/create_deidentification_indexes.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from elasticsearch import AsyncElasticsearch
from app.core.config import settings


async def create_deidentified_notes_index(es: AsyncElasticsearch) -> None:
    """
    Create deidentified_notes index.

    Stores de-identified clinical notes with metadata:
    - De-identified text (searchable)
    - Entities removed (nested)
    - Method used (removal, replacement, generalization)
    - Confidence score
    - Review flag
    """
    index_name = "deidentified_notes"

    mapping = {
        "mappings": {
            "properties": {
                "job_id": {"type": "keyword"},
                "note_id": {"type": "keyword"},
                "deidentified_text": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}
                    }
                },
                "entities_removed": {
                    "type": "nested",
                    "properties": {
                        "entity_type": {"type": "keyword"},
                        "text": {"type": "text"},  # Placeholder text like [NAME], Patient A
                        "confidence": {"type": "float"}
                    }
                },
                "method_used": {
                    "type": "keyword"
                },
                "confidence_score": {
                    "type": "float"
                },
                "review_required": {
                    "type": "boolean"
                },
                "created_at": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "max_result_window": 10000
            }
        }
    }

    # Check if index exists
    if await es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Skipping creation.")
        return

    # Create index
    await es.indices.create(index=index_name, body=mapping)
    print(f"Created index '{index_name}'")


async def create_phi_audit_log_index(es: AsyncElasticsearch) -> None:
    """
    Create phi_audit_log index.

    Stores HIPAA-compliant audit trail:
    - User ID (who accessed PHI)
    - Action (what was done)
    - Job/note IDs (which resources)
    - Timestamp (when)
    - IP address (from where)
    - Processing metrics
    - Error tracking
    """
    index_name = "phi_audit_log"

    mapping = {
        "mappings": {
            "properties": {
                "user_id": {"type": "keyword"},
                "action": {
                    "type": "keyword"
                },
                "job_id": {"type": "keyword"},
                "note_id": {"type": "keyword"},
                "entities_detected": {"type": "integer"},
                "entities_removed": {"type": "integer"},
                "method_used": {
                    "type": "keyword"
                },
                "ip_address": {
                    "type": "ip"
                },
                "user_agent": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}
                    }
                },
                "timestamp": {
                    "type": "date",
                    "format": "strict_date_optional_time||epoch_millis"
                },
                "processing_time_ms": {
                    "type": "integer"
                },
                "error": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword", "ignore_above": 256}
                    }
                }
            }
        },
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "index": {
                "max_result_window": 10000
            }
        }
    }

    # Check if index exists
    if await es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Skipping creation.")
        return

    # Create index
    await es.indices.create(index=index_name, body=mapping)
    print(f"Created index '{index_name}'")


async def main():
    """Create all de-identification indexes."""
    # Connect to Elasticsearch
    es = AsyncElasticsearch(
        hosts=[settings.ELASTICSEARCH_URL],
        verify_certs=False,
        ssl_show_warn=False
    )

    try:
        # Check connection
        if not await es.ping():
            print("ERROR: Cannot connect to Elasticsearch")
            sys.exit(1)

        print(f"Connected to Elasticsearch at {settings.ELASTICSEARCH_URL}")

        # Create indexes
        await create_deidentified_notes_index(es)
        await create_phi_audit_log_index(es)

        print("\nAll de-identification indexes created successfully!")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(main())
