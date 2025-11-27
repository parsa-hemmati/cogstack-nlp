#!/usr/bin/env python3
"""
Seed test data for Timeline E2E tests

Creates 10 test patients with varied event counts:
- P12345: 50 events (light load)
- P12346: 100 events
- P12347: 200 events
- P12348: 500 events (medium load)
- P12349: 1000 events
- P12350: 2000 events
- P12351: 5000 events (heavy load)
- P12352: 10 events (minimal)
- P12353: 237 events (realistic)
- P_LARGE_TIMELINE: 5000 events (stress test)

Usage:
    python backend/scripts/seed_timeline_test_data.py
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path
import random

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from elasticsearch import AsyncElasticsearch
from app.core.config import settings


# Event types and sample concepts
EVENT_TYPES = ["diagnosis", "procedure", "medication", "lab", "visit"]

CONCEPTS_BY_TYPE = {
    "diagnosis": [
        ("Atrial Fibrillation", "C0004238"),
        ("Hypertension", "C0020538"),
        ("Diabetes Mellitus", "C0011849"),
        ("Heart Failure", "C0018802"),
        ("Chronic Kidney Disease", "C1561643"),
        ("COPD", "C0024117"),
        ("Asthma", "C0004096"),
        ("Depression", "C0011570"),
        ("Anxiety", "C0003467"),
        ("Osteoarthritis", "C0029408"),
    ],
    "procedure": [
        ("ECG", "C0013798"),
        ("Echocardiogram", "C0013516"),
        ("CT Scan", "C0040405"),
        ("MRI", "C0024485"),
        ("Blood Test", "C0018941"),
        ("X-Ray", "C0034571"),
        ("Endoscopy", "C0014245"),
        ("Biopsy", "C0005558"),
        ("Surgery", "C0543467"),
        ("Dialysis", "C0011946"),
    ],
    "medication": [
        ("Metformin", "C0025598"),
        ("Lisinopril", "C0065374"),
        ("Atorvastatin", "C0286651"),
        ("Metoprolol", "C0025859"),
        ("Amlodipine", "C0051474"),
        ("Omeprazole", "C0028978"),
        ("Albuterol", "C0001927"),
        ("Levothyroxine", "C0040165"),
        ("Warfarin", "C0043031"),
        ("Insulin", "C0021641"),
    ],
    "lab": [
        ("HbA1c", "C0019018"),
        ("Glucose", "C0017725"),
        ("Creatinine", "C0010294"),
        ("Sodium", "C0037473"),
        ("Potassium", "C0032821"),
        ("Hemoglobin", "C0019046"),
        ("WBC Count", "C0023508"),
        ("Platelet Count", "C0032181"),
        ("TSH", "C0040160"),
        ("INR", "C0525032"),
    ],
    "visit": [
        ("Cardiology Consultation", "C0087111"),
        ("Primary Care Visit", "C0033137"),
        ("Emergency Department", "C0562508"),
        ("Inpatient Admission", "C0184666"),
        ("Follow-up Visit", "C0420316"),
        ("Specialist Referral", "C0034927"),
        ("Telemedicine Visit", "C0162648"),
        ("Physical Therapy", "C0699718"),
        ("Radiology Visit", "C0034599"),
        ("Laboratory Visit", "C0022885"),
    ],
}

META_ANNOTATIONS = {
    "negation": ["Affirmed", "Negated"],
    "experiencer": ["Patient", "Family"],
    "temporality": ["Current", "Historical", "Future"],
    "certainty": ["Definite", "Probable", "Possible"],
}


async def create_event(
    patient_id: str,
    event_id: int,
    base_date: datetime,
    event_type: str = None,
) -> dict:
    """Create a single timeline event"""

    if event_type is None:
        event_type = random.choice(EVENT_TYPES)

    concept_name, concept_cui = random.choice(CONCEPTS_BY_TYPE[event_type])

    # Generate date (random in past year)
    days_offset = random.randint(0, 365)
    event_date = base_date - timedelta(days=days_offset)

    # Meta-annotations (90% affirmed, 10% negated)
    negation = random.choices(
        META_ANNOTATIONS["negation"], weights=[90, 10]
    )[0]
    experiencer = random.choices(
        META_ANNOTATIONS["experiencer"], weights=[95, 5]
    )[0]
    temporality = random.choices(
        META_ANNOTATIONS["temporality"], weights=[70, 25, 5]
    )[0]
    certainty = random.choices(
        META_ANNOTATIONS["certainty"], weights=[80, 15, 5]
    )[0]

    return {
        "patient_id": patient_id,
        "event_id": f"{patient_id}_event_{event_id}",
        "date": event_date.isoformat(),
        "event_type": event_type,
        "concept_name": concept_name,
        "concept_cui": concept_cui,
        "confidence": random.uniform(0.85, 0.99),
        "meta_annotations": {
            "negation": negation,
            "experiencer": experiencer,
            "temporality": temporality,
            "certainty": certainty,
        },
        "source_document": f"doc_{event_id}",
        "context": f"Clinical note documenting {concept_name.lower()}",
        "specialty": random.choice(["cardiology", "primary_care", "endocrinology", "nephrology", "pulmonology"]),
        "provider_id": f"prov_{random.randint(1, 10)}",
    }


async def seed_patient_timeline(es: AsyncElasticsearch, patient_id: str, event_count: int):
    """Seed timeline events for a patient"""

    print(f"Seeding {event_count} events for patient {patient_id}...")

    base_date = datetime.now()
    events = []

    for i in range(event_count):
        event = await create_event(patient_id, i, base_date)
        events.append({
            "_index": "timeline_events",
            "_id": event["event_id"],
            "_source": event,
        })

    # Bulk index
    if events:
        from elasticsearch.helpers import async_bulk

        success, failed = await async_bulk(
            es,
            events,
            raise_on_error=False,
        )

        print(f"  ✅ Indexed {success} events for {patient_id}")
        if failed:
            print(f"  ⚠️  Failed to index {len(failed)} events")


async def create_index(es: AsyncElasticsearch):
    """Create timeline_events index with proper mappings"""

    index_name = "timeline_events"

    # Check if index exists
    if await es.indices.exists(index=index_name):
        print(f"Index {index_name} already exists. Deleting...")
        await es.indices.delete(index=index_name)

    # Create index with mappings
    mappings = {
        "properties": {
            "patient_id": {"type": "keyword"},
            "event_id": {"type": "keyword"},
            "date": {"type": "date"},
            "event_type": {"type": "keyword"},
            "concept_name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "concept_cui": {"type": "keyword"},
            "confidence": {"type": "float"},
            "meta_annotations": {
                "properties": {
                    "negation": {"type": "keyword"},
                    "experiencer": {"type": "keyword"},
                    "temporality": {"type": "keyword"},
                    "certainty": {"type": "keyword"},
                }
            },
            "source_document": {"type": "keyword"},
            "context": {"type": "text"},
            "specialty": {"type": "keyword"},
            "provider_id": {"type": "keyword"},
        }
    }

    await es.indices.create(index=index_name, mappings=mappings)
    print(f"✅ Created index: {index_name}")


async def main():
    """Main seeding function"""

    print("🌱 Starting Timeline Test Data Seeding...\n")

    # Connect to Elasticsearch
    es = AsyncElasticsearch([settings.ELASTICSEARCH_URL])

    try:
        # Create index
        await create_index(es)

        # Test patient configurations
        patients = [
            ("P12345", 50),  # Light load
            ("P12346", 100),
            ("P12347", 200),
            ("P12348", 500),  # Medium load
            ("P12349", 1000),
            ("P12350", 2000),
            ("P12351", 5000),  # Heavy load
            ("P12352", 10),  # Minimal
            ("P12353", 237),  # Realistic
            ("P_LARGE_TIMELINE", 5000),  # Stress test
            ("P_MEDIUM", 500),  # Named patient for tests
            ("P_LARGE", 5000),  # Named patient for tests
        ]

        # Seed each patient
        for patient_id, event_count in patients:
            await seed_patient_timeline(es, patient_id, event_count)

        # Refresh index
        await es.indices.refresh(index="timeline_events")

        print("\n✅ Test data seeding complete!")
        print(f"   Total patients: {len(patients)}")
        print(f"   Total events: {sum(count for _, count in patients)}")

    finally:
        await es.close()


if __name__ == "__main__":
    asyncio.run(main())
