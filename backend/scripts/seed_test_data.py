"""
Test Data Seeding Script for Timeline Performance Tests

Creates test patients with varying event counts:
- P_SMALL: 50 events (low complexity)
- P_MEDIUM: 1,000 events (medium complexity)
- P_LARGE: 10,000 events (high complexity)

Usage:
    python backend/scripts/seed_test_data.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
from uuid import uuid4, UUID

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.session import AsyncSessionLocal
from app.models.patient import Patient
from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity
from sqlalchemy import select


# Medical concepts (CUI codes) for realistic test data
MEDICAL_CONCEPTS = [
    ("C0011849", "Diabetes Mellitus", "condition"),
    ("C0020538", "Hypertension", "condition"),
    ("C0004238", "Atrial Fibrillation", "condition"),
    ("C0018801", "Heart Failure", "condition"),
    ("C0011860", "Type 2 Diabetes", "condition"),
    ("C0003873", "Rheumatoid Arthritis", "condition"),
    ("C0024530", "Malaria", "condition"),
    ("C0011847", "Diabetes Type 1", "condition"),
    ("C0011854", "Diabetic Neuropathy", "condition"),
    ("C0020456", "Hyperglycemia", "symptom"),
    ("C0020459", "Hypoglycemia", "symptom"),
    ("C0018802", "Congestive Heart Failure", "condition"),
    ("C0010068", "Coronary Artery Disease", "condition"),
    ("C0042373", "Vascular Disease", "condition"),
    ("C0028754", "Obesity", "condition"),
    ("C0003811", "Cardiac Arrhythmia", "condition"),
    ("C0152013", "Atrial Flutter", "condition"),
    ("C0002395", "Alzheimer's Disease", "condition"),
    ("C0011849", "Diabetes", "condition"),
    ("C0007222", "Cardiovascular Disease", "condition"),
]

# Meta-annotation values
NEGATION_VALUES = ["Affirmed", "Negated"]
EXPERIENCER_VALUES = ["Patient", "Family", "Other"]
TEMPORALITY_VALUES = ["Current", "Recent", "Past", "Future", "Hypothetical"]
CERTAINTY_VALUES = ["High", "Medium", "Low"]


async def create_patient(nhs_number: str, event_count: int) -> UUID:
    """
    Create a test patient with specified number of events.
    
    Args:
        nhs_number: NHS number for the patient
        event_count: Number of concept mentions to create
    
    Returns:
        UUID of created patient
    """
    async with AsyncSessionLocal() as session:
        # Check if patient exists
        result = await session.execute(
            select(Patient).where(Patient.nhs_number == nhs_number)
        )
        existing_patient = result.scalar_one_or_none()
        
        if existing_patient:
            print(f"Patient {nhs_number} already exists (ID: {existing_patient.id})")
            return existing_patient.id
        
        # Create patient
        patient = Patient(
            id=uuid4(),
            nhs_number=nhs_number,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(patient)
        await session.commit()
        
        print(f"Created patient {nhs_number} (ID: {patient.id})")
        
        # Create documents and entities
        concepts_per_document = min(20, max(1, event_count // 10))
        num_documents = (event_count + concepts_per_document - 1) // concepts_per_document
        
        print(f"Creating {num_documents} documents with ~{concepts_per_document} concepts each...")
        
        created_concepts = 0
        
        for doc_idx in range(num_documents):
            # Create document
            document_date = datetime.utcnow() - timedelta(days=random.randint(1, 1825))  # 0-5 years ago
            
            document = Document(
                id=uuid4(),
                patient_id=patient.id,
                document_type=random.choice([
                    "clinical_note",
                    "discharge_summary",
                    "lab_results",
                    "radiology_report",
                    "progress_note"
                ]),
                content_encrypted=b"ENCRYPTED_TEST_CONTENT",  # Placeholder
                encryption_key_id="test_key",
                content_hash="test_hash_" + str(doc_idx),
                created_at=document_date,
                updated_at=document_date,
                processing_status="completed"
            )
            session.add(document)
            
            # Create concepts for this document
            concepts_this_doc = min(concepts_per_document, event_count - created_concepts)
            
            for concept_idx in range(concepts_this_doc):
                concept = random.choice(MEDICAL_CONCEPTS)
                cui, name, type_ = concept
                
                # Create extracted entity
                entity = ExtractedEntity(
                    id=uuid4(),
                    document_id=document.id,
                    patient_id=patient.id,
                    cui=cui,
                    pretty_name=name,
                    concept_type=type_,
                    start_pos=random.randint(0, 1000),
                    end_pos=random.randint(1000, 2000),
                    confidence=round(random.uniform(0.7, 0.99), 2),
                    meta_negation=random.choice(NEGATION_VALUES),
                    meta_experiencer=random.choice(EXPERIENCER_VALUES),
                    meta_temporality=random.choice(TEMPORALITY_VALUES),
                    meta_certainty=random.choice(CERTAINTY_VALUES),
                    created_at=document_date
                )
                session.add(entity)
                created_concepts += 1
            
            if (doc_idx + 1) % 10 == 0:
                await session.commit()
                print(f"  Created {doc_idx + 1}/{num_documents} documents ({created_concepts} concepts)...")
        
        await session.commit()
        print(f"✓ Patient {nhs_number} complete: {num_documents} documents, {created_concepts} concepts")
        
        return patient.id


async def seed_test_patients():
    """
    Seed test patients with different complexity levels.
    """
    print("=" * 60)
    print("Timeline Module - Test Data Seeding")
    print("=" * 60)
    print()
    
    # Create test patients
    patients = [
        ("P_SMALL", 50),
        ("P_MEDIUM", 1000),
        ("P_LARGE", 10000),
    ]
    
    for nhs_number, event_count in patients:
        print(f"\n{nhs_number}: Creating patient with {event_count} events...")
        try:
            patient_id = await create_patient(nhs_number, event_count)
            print(f"✓ {nhs_number} ready (ID: {patient_id})")
        except Exception as e:
            print(f"✗ Error creating {nhs_number}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 60)
    print("Test data seeding complete!")
    print("=" * 60)
    print()
    print("Test patients:")
    print("  - P_SMALL (50 events) - Low complexity")
    print("  - P_MEDIUM (1,000 events) - Medium complexity")
    print("  - P_LARGE (10,000 events) - High complexity")
    print()
    print("These patients can be used for:")
    print("  - E2E tests: /patients/P_SMALL/timeline")
    print("  - Performance tests: Locust load testing")
    print("  - Frontend rendering tests: Various complexity levels")
    print()


if __name__ == "__main__":
    asyncio.run(seed_test_patients())
