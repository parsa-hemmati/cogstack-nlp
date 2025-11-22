#!/usr/bin/env python3
"""
Migrate Clinical Concepts from PostgreSQL to Elasticsearch.

This script reads extracted_entities from the PostgreSQL database and bulk inserts
them into the Elasticsearch 'clinical_concepts' index.

Usage:
    python scripts/migrate_concepts_to_es.py [--batch-size 1000] [--dry-run]

Options:
    --batch-size N    Bulk insert batch size (default: 1000)
    --dry-run         Show what would be migrated without actually inserting

Requirements:
    - PostgreSQL database with extracted_entities table
    - Elasticsearch 8.x with clinical_concepts index created
    - pip install elasticsearch==8.11.1 psycopg2-binary sqlalchemy tqdm
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tqdm import tqdm


# Configuration
ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/clinical_care_tools")
INDEX_NAME = "clinical_concepts"
DEFAULT_BATCH_SIZE = 1000


def fetch_concepts_from_db(db_session, batch_size: int = 1000):
    """
    Fetch extracted concepts from PostgreSQL database.

    Args:
        db_session: SQLAlchemy session
        batch_size: Number of records to fetch per batch

    Yields:
        List of concept dictionaries
    """
    # Query to fetch extracted entities
    # Assumes extracted_entities table structure from MedCAT Trainer
    query = text("""
        SELECT
            ee.id,
            ee.patient_id,
            ee.document_id,
            ee.cui AS concept_cui,
            ee.name AS concept_name,
            ee.type AS concept_type,
            d.document_date AS date,
            ee.context AS sentence,
            ee.start_char,
            ee.end_char,
            ee.meta_anns AS meta_annotations,
            ee.confidence
        FROM extracted_entities ee
        JOIN documents d ON ee.document_id = d.id
        WHERE ee.cui IS NOT NULL
        ORDER BY ee.id
    """)

    offset = 0

    while True:
        # Fetch batch
        batch_query = query.limit(batch_size).offset(offset)
        result = db_session.execute(batch_query)
        rows = result.fetchall()

        if not rows:
            break

        yield rows

        offset += batch_size


def transform_concept_for_es(row) -> Dict[str, Any]:
    """
    Transform database row to Elasticsearch document format.

    Args:
        row: SQLAlchemy row result

    Returns:
        Dictionary formatted for Elasticsearch indexing
    """
    # Parse meta-annotations (assuming JSON format in database)
    meta_anns = row.meta_annotations if row.meta_annotations else {}

    # Ensure meta_annotations has correct structure
    if isinstance(meta_anns, dict):
        # Normalize keys
        normalized_meta_anns = {
            "Negation": meta_anns.get("Negation", meta_anns.get("negation", "Affirmed")),
            "Experiencer": meta_anns.get("Experiencer", meta_anns.get("experiencer", "Patient")),
            "Temporality": meta_anns.get("Temporality", meta_anns.get("temporality", "Current")),
            "Certainty": meta_anns.get("Certainty", meta_anns.get("certainty", "Confirmed"))
        }
    else:
        # Default meta-annotations
        normalized_meta_anns = {
            "Negation": "Affirmed",
            "Experiencer": "Patient",
            "Temporality": "Current",
            "Certainty": "Confirmed"
        }

    # Format date
    date_str = row.date.isoformat() if row.date else datetime.now().date().isoformat()

    return {
        "_index": INDEX_NAME,
        "_id": str(row.id),  # Use entity ID as Elasticsearch document ID
        "_source": {
            "patient_id": str(row.patient_id),
            "document_id": str(row.document_id),
            "concept_cui": row.concept_cui,
            "concept_name": row.concept_name,
            "concept_type": row.concept_type or "Unknown",
            "date": date_str,
            "sentence": row.sentence or "",
            "start_char": row.start_char or 0,
            "end_char": row.end_char or 0,
            "meta_annotations": normalized_meta_anns,
            "confidence": float(row.confidence) if row.confidence else 0.0
        }
    }


def migrate_concepts(es: Elasticsearch, db_session, batch_size: int = 1000, dry_run: bool = False):
    """
    Migrate concepts from PostgreSQL to Elasticsearch.

    Args:
        es: Elasticsearch client
        db_session: SQLAlchemy session
        batch_size: Bulk insert batch size
        dry_run: If True, don't actually insert data

    Returns:
        Total number of documents migrated
    """
    total_migrated = 0

    print(f"🔍 Counting total concepts to migrate...")

    # Count total records
    count_query = text("""
        SELECT COUNT(*)
        FROM extracted_entities
        WHERE cui IS NOT NULL
    """)
    result = db_session.execute(count_query)
    total_concepts = result.scalar()

    print(f"📊 Found {total_concepts:,} concepts to migrate")

    if dry_run:
        print(f"🏃 DRY RUN MODE: No data will be inserted")
        # Show sample data
        query = text("""
            SELECT
                ee.patient_id,
                ee.cui AS concept_cui,
                ee.name AS concept_name,
                d.document_date AS date
            FROM extracted_entities ee
            JOIN documents d ON ee.document_id = d.id
            WHERE ee.cui IS NOT NULL
            LIMIT 5
        """)
        result = db_session.execute(query)
        rows = result.fetchall()

        print(f"\n📝 Sample concepts:")
        for row in rows:
            print(f"   - {row.concept_name} (CUI: {row.concept_cui}) - Patient: {row.patient_id} - Date: {row.date}")

        return 0

    # Migrate in batches
    with tqdm(total=total_concepts, desc="Migrating concepts", unit="docs") as pbar:
        for batch_rows in fetch_concepts_from_db(db_session, batch_size):
            # Transform to ES format
            es_docs = [transform_concept_for_es(row) for row in batch_rows]

            # Bulk insert
            try:
                success, failed = bulk(es, es_docs, raise_on_error=False, stats_only=True)

                total_migrated += success

                if failed > 0:
                    print(f"\n⚠️  {failed} documents failed to index")

                pbar.update(len(batch_rows))

            except Exception as e:
                print(f"\n❌ Error during bulk insert: {e}")
                raise

    return total_migrated


def main():
    """Main entry point for script."""
    # Parse arguments
    batch_size = DEFAULT_BATCH_SIZE
    dry_run = False

    for arg in sys.argv[1:]:
        if arg.startswith("--batch-size="):
            batch_size = int(arg.split("=")[1])
        elif arg == "--dry-run":
            dry_run = True

    print(f"🚀 Clinical Concepts Migration")
    print(f"   Batch size: {batch_size}")
    print(f"   Dry run: {dry_run}")
    print()

    # Connect to Elasticsearch
    print(f"🔌 Connecting to Elasticsearch at {ES_URL}...")

    try:
        es = Elasticsearch([ES_URL])

        if not es.ping():
            print(f"❌ Cannot connect to Elasticsearch at {ES_URL}")
            print("   Make sure Elasticsearch is running:")
            print("   - docker-compose up -d elasticsearch")
            sys.exit(1)

        print(f"✅ Connected to Elasticsearch")

        # Check if index exists
        if not es.indices.exists(index=INDEX_NAME):
            print(f"❌ Index '{INDEX_NAME}' does not exist")
            print(f"   Create it first: python scripts/create_es_index.py")
            sys.exit(1)

        print(f"✅ Index '{INDEX_NAME}' exists")

    except Exception as e:
        print(f"❌ Elasticsearch error: {e}")
        sys.exit(1)

    # Connect to PostgreSQL
    print(f"🔌 Connecting to PostgreSQL at {DATABASE_URL.split('@')[1]}...")

    try:
        engine = create_engine(DATABASE_URL)
        Session = sessionmaker(bind=engine)
        db_session = Session()

        # Test connection
        db_session.execute(text("SELECT 1"))
        print(f"✅ Connected to PostgreSQL")

    except Exception as e:
        print(f"❌ PostgreSQL error: {e}")
        print(f"   Make sure PostgreSQL is running and DATABASE_URL is correct")
        print(f"   DATABASE_URL={DATABASE_URL}")
        sys.exit(1)

    # Migrate data
    try:
        print()
        total_migrated = migrate_concepts(es, db_session, batch_size, dry_run)

        print()
        print(f"✅ Migration complete!")
        print(f"   Migrated: {total_migrated:,} documents")

        if not dry_run:
            # Refresh index
            es.indices.refresh(index=INDEX_NAME)

            # Get document count
            count = es.count(index=INDEX_NAME)
            print(f"   Index count: {count['count']:,} documents")

            print(f"\n📚 Next steps:")
            print(f"   1. Verify index: curl http://localhost:9200/{INDEX_NAME}/_count?pretty")
            print(f"   2. Test search: curl -X POST 'http://localhost:9200/{INDEX_NAME}/_search?pretty' -H 'Content-Type: application/json' -d'{{\"query\":{{\"match_all\":{{}}}}}}'")
            print(f"   3. Test timeline API: GET /api/v1/timeline/{{patient_id}}")

    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)
    finally:
        db_session.close()


if __name__ == "__main__":
    main()
