"""
Unit tests for ExtractedEntity model.

Tests entity storage for PHI and clinical concepts extracted by MedCAT.
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.models.extracted_entity import ExtractedEntity, EntityType
from app.models.user import User


@pytest.mark.asyncio
async def test_extracted_entity_creation(db: AsyncSession, admin_user: User):
    """Test basic extracted entity creation."""
    # Create document first
    doc = Document(
        filename="test.rtf",
        content_type="application/rtf",
        content_hash="hash123",
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Create extracted entity
    entity = ExtractedEntity(
        document_id=doc.id,
        patient_id=None,  # Not linked yet
        entity_type=EntityType.CLINICAL,
        cui="C0011849",  # SNOMED-CT: Diabetes mellitus
        pretty_name="Diabetes mellitus",
        start_char=10,
        end_char=28,
        accuracy=0.95,
        meta_anns={
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Definite",
        },
    )

    db.add(entity)
    await db.commit()
    await db.refresh(entity)

    assert entity.id is not None
    assert entity.cui == "C0011849"
    assert entity.entity_type == EntityType.CLINICAL
    assert entity.meta_anns["Negation"] == "Affirmed"
    assert entity.created_at is not None


@pytest.mark.asyncio
async def test_entity_relationship_to_document(db: AsyncSession, admin_user: User):
    """Test relationship between entity and document."""
    doc = Document(
        filename="clinical_note.rtf",
        content_type="application/rtf",
        content_hash="hash456",
        encrypted_content=b"Patient has hypertension",
        encryption_algorithm="aes-256-gcm",
        file_size=24,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    entity = ExtractedEntity(
        document_id=doc.id,
        entity_type=EntityType.CLINICAL,
        cui="C0020538",  # Hypertension
        pretty_name="Hypertension",
        start_char=12,
        end_char=24,
        accuracy=0.98,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)

    # Verify relationship
    assert entity.document_id == doc.id


@pytest.mark.asyncio
async def test_entity_type_phi_name(db: AsyncSession, admin_user: User):
    """Test PHI entity type: patient name."""
    doc = Document(
        filename="phi_doc.rtf",
        content_type="application/rtf",
        content_hash="hash789",
        encrypted_content=b"John Smith",
        encryption_algorithm="aes-256-gcm",
        file_size=10,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    entity = ExtractedEntity(
        document_id=doc.id,
        entity_type=EntityType.PHI_NAME,
        cui=None,  # PHI doesn't have CUI
        pretty_name="John Smith",
        start_char=0,
        end_char=10,
        accuracy=0.99,
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)

    assert entity.entity_type == EntityType.PHI_NAME
    assert entity.cui is None


@pytest.mark.asyncio
async def test_entity_meta_annotations_jsonb(db: AsyncSession, admin_user: User):
    """Test meta-annotations stored as JSONB."""
    doc = Document(
        filename="meta_test.rtf",
        content_type="application/rtf",
        content_hash="hash_meta",
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    entity = ExtractedEntity(
        document_id=doc.id,
        entity_type=EntityType.CLINICAL,
        cui="C0004238",
        pretty_name="Atrial fibrillation",
        start_char=0,
        end_char=20,
        accuracy=0.97,
        meta_anns={
            "Negation": "Negated",  # Patient DOES NOT have AFib
            "Temporality": "Historical",
            "Experiencer": "Patient",
            "Certainty": "Probable",
            "custom_field": "custom_value",  # JSONB allows flexible schema
        },
    )
    db.add(entity)
    await db.commit()
    await db.refresh(entity)

    # Verify JSONB storage
    assert entity.meta_anns["Negation"] == "Negated"
    assert entity.meta_anns["custom_field"] == "custom_value"
    assert len(entity.meta_anns) == 5


@pytest.mark.asyncio
async def test_entity_index_on_document_id(db: AsyncSession, admin_user: User):
    """Test index on document_id for fast entity retrieval."""
    doc = Document(
        filename="index_test.rtf",
        content_type="application/rtf",
        content_hash="hash_index",
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Create multiple entities for same document
    for i in range(5):
        entity = ExtractedEntity(
            document_id=doc.id,
            entity_type=EntityType.CLINICAL,
            cui=f"C000{i}",
            pretty_name=f"Concept {i}",
            start_char=i * 10,
            end_char=(i + 1) * 10,
            accuracy=0.9,
        )
        db.add(entity)
    await db.commit()

    # Query by document_id (should use index)
    result = await db.execute(
        select(ExtractedEntity).where(ExtractedEntity.document_id == doc.id)
    )
    entities = result.scalars().all()

    assert len(entities) == 5


@pytest.mark.asyncio
async def test_entity_index_on_entity_type(db: AsyncSession, admin_user: User):
    """Test index on entity_type for filtering PHI vs clinical entities."""
    doc = Document(
        filename="type_filter_test.rtf",
        content_type="application/rtf",
        content_hash="hash_type",
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    # Create mixed entity types
    clinical = ExtractedEntity(
        document_id=doc.id,
        entity_type=EntityType.CLINICAL,
        cui="C0011849",
        pretty_name="Diabetes",
        start_char=0,
        end_char=8,
        accuracy=0.95,
    )
    phi_name = ExtractedEntity(
        document_id=doc.id,
        entity_type=EntityType.PHI_NAME,
        pretty_name="John Doe",
        start_char=10,
        end_char=18,
        accuracy=0.99,
    )
    db.add_all([clinical, phi_name])
    await db.commit()

    # Query by entity_type (should use index)
    result = await db.execute(
        select(ExtractedEntity).where(
            ExtractedEntity.entity_type == EntityType.PHI_NAME
        )
    )
    phi_entities = result.scalars().all()

    assert len(phi_entities) >= 1
    assert all(e.entity_type == EntityType.PHI_NAME for e in phi_entities)


@pytest.mark.asyncio
async def test_entity_all_phi_types(db: AsyncSession, admin_user: User):
    """Test all PHI entity types."""
    doc = Document(
        filename="all_phi.rtf",
        content_type="application/rtf",
        content_hash="hash_all_phi",
        encrypted_content=b"test",
        encryption_algorithm="aes-256-gcm",
        file_size=4,
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    phi_types = [
        (EntityType.PHI_NAME, "John Smith"),
        (EntityType.PHI_NHS_NUMBER, "1234567890"),
        (EntityType.PHI_DOB, "1980-01-01"),
        (EntityType.PHI_ADDRESS, "123 Main St"),
    ]

    for entity_type, value in phi_types:
        entity = ExtractedEntity(
            document_id=doc.id,
            entity_type=entity_type,
            pretty_name=value,
            start_char=0,
            end_char=len(value),
            accuracy=0.98,
        )
        db.add(entity)

    await db.commit()

    # Verify all types saved
    result = await db.execute(
        select(ExtractedEntity).where(ExtractedEntity.document_id == doc.id)
    )
    entities = result.scalars().all()

    assert len(entities) == 4
    types_found = {e.entity_type for e in entities}
    assert EntityType.PHI_NAME in types_found
    assert EntityType.PHI_NHS_NUMBER in types_found
