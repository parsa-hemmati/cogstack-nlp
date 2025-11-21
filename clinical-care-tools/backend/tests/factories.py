"""Test factories for creating test data.

Uses factory pattern to create consistent test data across tests.
"""

import factory
from factory import Faker, SubFactory, LazyAttribute
from datetime import datetime, timedelta
import random
from typing import Optional, Dict, Any

from app.models.user import User
from app.models.patient import Patient
from app.models.document import Document
from app.core.database import async_session_maker


class AsyncSQLAlchemyModelFactory(factory.alchemy.SQLAlchemyModelFactory):
    """Base factory for async SQLAlchemy models."""

    class Meta:
        abstract = True
        sqlalchemy_session_persistence = "commit"

    @classmethod
    async def create(cls, **kwargs):
        """Create an instance asynchronously."""
        async with async_session_maker() as session:
            instance = cls.build(**kwargs)
            session.add(instance)
            await session.commit()
            await session.refresh(instance)
            return instance

    @classmethod
    async def create_batch(cls, size: int, **kwargs):
        """Create multiple instances asynchronously."""
        async with async_session_maker() as session:
            instances = []
            for _ in range(size):
                instance = cls.build(**kwargs)
                session.add(instance)
                instances.append(instance)
            await session.commit()
            for instance in instances:
                await session.refresh(instance)
            return instances


class UserFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User

    id = factory.Faker("uuid4")
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@test.com")
    full_name = factory.Faker("name")
    hashed_password = "$2b$12$test.hash"  # Pre-hashed password
    role = factory.Faker(
        "random_element",
        elements=["clinician", "researcher", "admin", "viewer"]
    )
    is_active = True
    is_locked = False
    failed_login_attempts = 0
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)


class PatientFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test patients."""

    class Meta:
        model = Patient

    id = factory.Faker("uuid4")
    patient_id = factory.Sequence(lambda n: f"NHS-{1000000000 + n}")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    date_of_birth = factory.Faker("date_of_birth", minimum_age=18, maximum_age=90)
    gender = factory.Faker("random_element", elements=["Male", "Female", "Other"])
    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)

    @factory.lazy_attribute
    def metadata(self):
        """Generate realistic patient metadata."""
        return {
            "address": {
                "line1": Faker("street_address").generate(),
                "city": Faker("city").generate(),
                "postcode": Faker("postcode").generate(),
                "country": "UK"
            },
            "contact": {
                "phone": Faker("phone_number").generate(),
                "email": Faker("email").generate()
            },
            "emergency_contact": {
                "name": Faker("name").generate(),
                "relationship": random.choice(["Spouse", "Parent", "Child", "Sibling"]),
                "phone": Faker("phone_number").generate()
            }
        }


class DocumentFactory(AsyncSQLAlchemyModelFactory):
    """Factory for creating test documents."""

    class Meta:
        model = Document

    id = factory.Faker("uuid4")
    document_id = factory.Sequence(lambda n: f"DOC-{2024000000 + n}")
    patient_id = factory.SubFactory(PatientFactory)

    title = factory.Faker(
        "random_element",
        elements=[
            "Clinical Note",
            "Discharge Summary",
            "Consultation Report",
            "Lab Results",
            "Radiology Report",
            "Prescription Record",
            "Progress Note",
            "Emergency Department Note",
            "Surgical Report",
            "Pathology Report"
        ]
    )

    document_type = factory.Faker(
        "random_element",
        elements=[
            "clinical_note",
            "discharge_summary",
            "consultation",
            "lab_report",
            "radiology_report",
            "prescription",
            "progress_note",
            "emergency_note",
            "surgical_report",
            "pathology_report"
        ]
    )

    author = factory.Faker("name", locale="en_GB")

    department = factory.Faker(
        "random_element",
        elements=[
            "Cardiology",
            "Endocrinology",
            "Neurology",
            "Oncology",
            "Emergency",
            "General Medicine",
            "Surgery",
            "Radiology",
            "Pathology",
            "Psychiatry"
        ]
    )

    created_at = factory.Faker("date_time_this_year")
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)
    date = factory.LazyAttribute(lambda obj: obj.created_at.date().isoformat())

    @factory.lazy_attribute
    def content(self):
        """Generate realistic medical document content."""
        templates = [
            "Patient presents with {condition1} and {condition2}. "
            "Physical examination reveals {finding}. "
            "Laboratory results show {lab_result}. "
            "Assessment: {assessment}. "
            "Plan: {plan}.",

            "Chief complaint: {symptom}. "
            "History of present illness: Patient reports {duration} history of {condition1}. "
            "Past medical history significant for {condition2}. "
            "Current medications include {medication}. "
            "Impression: {diagnosis}.",

            "Follow-up visit for {condition1}. "
            "Patient reports {improvement} since last visit. "
            "Current symptoms include {symptom}. "
            "Vital signs: BP {bp}, HR {hr}, Temp {temp}. "
            "Continue current treatment with {medication}.",
        ]

        template = random.choice(templates)

        return template.format(
            condition1=random.choice([
                "diabetes mellitus type 2",
                "hypertension",
                "atrial fibrillation",
                "heart failure",
                "chronic kidney disease",
                "COPD",
                "asthma",
                "hypothyroidism"
            ]),
            condition2=random.choice([
                "hyperlipidemia",
                "obesity",
                "depression",
                "anxiety",
                "osteoarthritis",
                "GERD",
                "anemia",
                "vitamin D deficiency"
            ]),
            symptom=random.choice([
                "chest pain",
                "shortness of breath",
                "fatigue",
                "dizziness",
                "palpitations",
                "headache",
                "abdominal pain",
                "joint pain"
            ]),
            finding=random.choice([
                "mild bilateral crackles",
                "regular heart rhythm",
                "no acute distress",
                "alert and oriented x3",
                "soft, non-tender abdomen",
                "normal breath sounds",
                "2+ pitting edema",
                "normal neurological exam"
            ]),
            lab_result=random.choice([
                "HbA1c 8.2%",
                "creatinine 1.4 mg/dL",
                "hemoglobin 11.5 g/dL",
                "TSH 5.2 mIU/L",
                "cholesterol 245 mg/dL",
                "glucose 156 mg/dL",
                "potassium 4.2 mmol/L",
                "sodium 138 mmol/L"
            ]),
            assessment=random.choice([
                "Stable condition",
                "Mild exacerbation",
                "Good control",
                "Requires adjustment",
                "Improving",
                "Unchanged",
                "Worsening symptoms",
                "Partial response to treatment"
            ]),
            plan=random.choice([
                "Continue current medications",
                "Increase dosage",
                "Add new medication",
                "Lifestyle modifications",
                "Follow-up in 3 months",
                "Refer to specialist",
                "Order additional tests",
                "Monitor closely"
            ]),
            diagnosis=random.choice([
                "Well-controlled diabetes",
                "Uncontrolled hypertension",
                "Stable angina",
                "Acute exacerbation",
                "Rule out malignancy",
                "Likely viral etiology",
                "Consistent with diagnosis",
                "Further workup needed"
            ]),
            duration=random.choice([
                "2 week", "1 month", "3 month", "6 month", "1 year", "2 year"
            ]),
            improvement=random.choice([
                "significant improvement",
                "mild improvement",
                "no change",
                "slight worsening",
                "complete resolution"
            ]),
            medication=random.choice([
                "metformin 1000mg BID",
                "lisinopril 10mg daily",
                "atorvastatin 40mg daily",
                "aspirin 81mg daily",
                "levothyroxine 50mcg daily",
                "omeprazole 20mg daily",
                "warfarin 5mg daily",
                "insulin glargine 20 units"
            ]),
            bp=random.choice(["120/80", "135/85", "140/90", "128/82", "110/70"]),
            hr=random.choice(["72", "68", "84", "76", "88", "64"]),
            temp=random.choice(["98.6", "99.2", "98.4", "97.8", "99.0"])
        )

    @factory.lazy_attribute
    def metadata(self):
        """Generate document metadata."""
        return {
            "version": 1,
            "status": random.choice(["draft", "final", "amended"]),
            "confidentiality": random.choice(["normal", "restricted", "confidential"]),
            "language": "en",
            "format": "text/plain",
            "size_bytes": random.randint(1000, 50000),
            "checksum": Faker("sha256").generate(),
            "tags": random.sample(
                ["urgent", "follow-up", "reviewed", "pending", "important"],
                k=random.randint(0, 3)
            )
        }


class MedCATEntityFactory:
    """Factory for creating MedCAT entity responses."""

    @staticmethod
    def create_entity(**kwargs) -> Dict[str, Any]:
        """Create a MedCAT entity."""
        defaults = {
            "cui": f"C{random.randint(1000000, 9999999)}",
            "pretty_name": random.choice([
                "Diabetes Mellitus",
                "Hypertension",
                "Atrial Fibrillation",
                "Heart Failure",
                "Chronic Kidney Disease"
            ]),
            "source_value": kwargs.get("pretty_name", "diabetes").lower(),
            "start": random.randint(0, 100),
            "end": random.randint(101, 200),
            "context_similarity": round(random.uniform(0.7, 1.0), 3),
            "meta_anns": {
                "Negation": random.choice(["Affirmed", "Negated"]),
                "Temporality": random.choice(["Current", "Historical", "Future/Hypothetical"]),
                "Experiencer": random.choice(["Patient", "Family", "Other"]),
                "Certainty": random.choice(["Certain", "Uncertain", "Possible"])
            },
            "types": ["Disease", "Symptom"],
            "snomed": f"{random.randint(100000000, 999999999)}"
        }
        defaults.update(kwargs)
        return defaults

    @staticmethod
    def create_batch(size: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple entities."""
        return [MedCATEntityFactory.create_entity(**kwargs) for _ in range(size)]


class ElasticsearchDocumentFactory:
    """Factory for creating Elasticsearch documents."""

    @staticmethod
    def create_document(**kwargs) -> Dict[str, Any]:
        """Create an Elasticsearch document."""
        doc_factory = DocumentFactory.build()

        defaults = {
            "_id": doc_factory.document_id,
            "_source": {
                "document_id": doc_factory.document_id,
                "patient_id": doc_factory.patient_id.id if hasattr(doc_factory.patient_id, 'id') else str(doc_factory.patient_id),
                "title": doc_factory.title,
                "content": doc_factory.content,
                "document_type": doc_factory.document_type,
                "author": doc_factory.author,
                "department": doc_factory.department,
                "date": doc_factory.date,
                "created_at": doc_factory.created_at.isoformat(),
                "metadata": doc_factory.metadata,
                "entities": MedCATEntityFactory.create_batch(random.randint(3, 10))
            },
            "_score": round(random.uniform(0.5, 10.0), 2)
        }

        # Update with any provided kwargs
        if kwargs:
            defaults["_source"].update(kwargs)

        return defaults

    @staticmethod
    def create_search_response(
        total: int = 10,
        size: int = 10,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a complete Elasticsearch search response."""
        actual_size = min(size, total)

        return {
            "took": random.randint(5, 50),
            "timed_out": False,
            "_shards": {
                "total": 5,
                "successful": 5,
                "skipped": 0,
                "failed": 0
            },
            "hits": {
                "total": {
                    "value": total,
                    "relation": "eq"
                },
                "max_score": 10.0,
                "hits": [
                    ElasticsearchDocumentFactory.create_document(**kwargs)
                    for _ in range(actual_size)
                ]
            },
            "aggregations": {
                "document_type": {
                    "buckets": [
                        {"key": "clinical_note", "doc_count": random.randint(10, 50)},
                        {"key": "discharge_summary", "doc_count": random.randint(5, 30)},
                        {"key": "consultation", "doc_count": random.randint(5, 25)}
                    ]
                },
                "department": {
                    "buckets": [
                        {"key": "Cardiology", "doc_count": random.randint(10, 40)},
                        {"key": "Endocrinology", "doc_count": random.randint(8, 35)},
                        {"key": "Emergency", "doc_count": random.randint(5, 30)}
                    ]
                },
                "date_histogram": {
                    "buckets": [
                        {
                            "key_as_string": "2023-01-01",
                            "key": 1672531200000,
                            "doc_count": random.randint(5, 20)
                        },
                        {
                            "key_as_string": "2023-02-01",
                            "key": 1675209600000,
                            "doc_count": random.randint(5, 20)
                        }
                    ]
                }
            }
        }