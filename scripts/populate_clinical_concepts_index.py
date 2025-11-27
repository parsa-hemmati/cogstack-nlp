#!/usr/bin/env python3
"""
Populate clinical_concepts Elasticsearch index with existing patient concepts.

This script indexes all ExtractedEntity records from PostgreSQL into the
clinical_concepts Elasticsearch index for timeline visualization.

Usage:
    python scripts/populate_clinical_concepts_index.py

Prerequisites:
    - PostgreSQL running with ExtractedEntity records
    - Elasticsearch running with clinical_concepts index created
    - clinical_concepts index mapping exists (from Task 5.1.3)
"""
import asyncio
import sys
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from elasticsearch import AsyncElasticsearch
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.document import ExtractedEntity


async def populate_index():
    """
    Populate clinical_concepts index with all ExtractedEntity records.

    Extracts:
    - patient_id: UUID of patient
    - document_id: UUID of document
    - concept_cui: SNOMED-CT or UMLS CUI
    - concept_name: Human-readable concept name
    - concept_type: UMLS semantic type
    - date: Document date (ISO 8601)
    - meta_annotations: Negation, Temporality, Experiencer, Certainty
    - confidence: MedCAT confidence score (0.0-1.0)
    - sentence: Sentence containing the concept mention
    """
    # Connect to Elasticsearch
    es = AsyncElasticsearch(['http://localhost:9200'])

    try:
        # Check if index exists
        index_exists = await es.indices.exists(index='clinical_concepts')
        if not index_exists:
            print("❌ Error: clinical_concepts index does not exist")
            print("   Please run Task 5.1.3 script to create the index first")
            return

        print("✅ clinical_concepts index exists")

        # Get database session
        async for db in get_db():
            # Query all ExtractedEntity records with their documents
            result = await db.execute(
                select(ExtractedEntity)
                .options(joinedload(ExtractedEntity.document))
            )
            entities = result.scalars().all()

            if not entities:
                print("⚠️  No ExtractedEntity records found in database")
                return

            print(f"📊 Found {len(entities)} ExtractedEntity records to index")

            # Index each entity
            indexed_count = 0
            for entity in entities:
                # Skip if no document (orphaned entity)
                if not entity.document:
                    print(f"⚠️  Skipping entity {entity.id} (no document)")
                    continue

                # Prepare document for Elasticsearch
                doc = {
                    "patient_id": str(entity.patient_id),
                    "document_id": str(entity.document_id),
                    "concept_cui": entity.cui,
                    "concept_name": entity.pretty_name,
                    "concept_type": entity.types[0] if entity.types else "unknown",
                    "date": entity.document.date.isoformat(),
                    "meta_annotations": entity.meta_anns or {},
                    "confidence": entity.acc or 0.0,
                    "sentence": entity.context or ""
                }

                # Index document
                await es.index(
                    index="clinical_concepts",
                    document=doc
                )

                indexed_count += 1

                # Progress indicator every 100 records
                if indexed_count % 100 == 0:
                    print(f"   Indexed {indexed_count}/{len(entities)} records...")

            print(f"✅ Successfully indexed {indexed_count} records")

            # Verify count
            await es.indices.refresh(index='clinical_concepts')
            count_response = await es.count(index='clinical_concepts')
            es_count = count_response['count']

            print(f"\n📈 Verification:")
            print(f"   PostgreSQL entities: {len(entities)}")
            print(f"   Elasticsearch documents: {es_count}")

            if es_count >= indexed_count:
                print("✅ Index population successful!")
            else:
                print(f"⚠️  Count mismatch: expected {indexed_count}, got {es_count}")

            break  # Exit after first database session

    finally:
        # Close Elasticsearch connection
        await es.close()


if __name__ == "__main__":
    print("🚀 Starting clinical_concepts index population...\n")
    asyncio.run(populate_index())
    print("\n✅ Done!")
