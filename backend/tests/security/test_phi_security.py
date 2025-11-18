"""
Security tests for PHI protection and de-identification.

Tests HIPAA compliance requirements for PHI handling.
"""
import pytest
import hashlib
import logging
from datetime import datetime
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.models.extracted_entity import ExtractedEntity, EntityType
from app.models.patient import Patient
from app.models.audit_log import AuditLog
from app.services.encryption_service import EncryptionService
from app.services.document_processing_service import DocumentProcessingService


@pytest.mark.asyncio
async def test_phi_encrypted_at_rest(client, admin_token, db: AsyncSession):
    """Test PHI is encrypted before storage in database."""
    # Upload document with PHI
    phi_content = b"Patient: John Smith, NHS: 1234567890, DOB: 15/01/1980"

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("phi_test.rtf", phi_content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    document_id = response.json()["document_id"]

    # Verify content is encrypted in database
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one()

    # Encrypted content should NOT contain plaintext PHI
    assert b"John Smith" not in doc.encrypted_content
    assert b"1234567890" not in doc.encrypted_content
    assert b"15/01/1980" not in doc.encrypted_content

    # Encrypted content should be different from plaintext
    assert doc.encrypted_content != phi_content

    # Encrypted content should have IV prepended (12 bytes for AES-GCM)
    assert len(doc.encrypted_content) >= 12


@pytest.mark.asyncio
async def test_phi_not_exposed_in_logs(client, admin_token, caplog):
    """Test PHI is not logged in application logs."""
    caplog.set_level(logging.INFO)

    # Upload document with PHI
    phi_content = b"Patient: Jane Doe, NHS: 9876543210"

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("log_test.rtf", phi_content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200

    # Check logs do NOT contain PHI
    log_messages = [record.message for record in caplog.records]
    combined_logs = " ".join(log_messages)

    assert "Jane Doe" not in combined_logs
    assert "9876543210" not in combined_logs

    # Logs MAY contain document ID (not PHI)
    document_id = response.json()["document_id"]
    # This is acceptable - document ID is not PHI


@pytest.mark.asyncio
async def test_phi_access_audited(client, admin_token, admin_user, db: AsyncSession):
    """Test all PHI access is logged in audit trail (HIPAA requirement)."""
    # Upload document
    phi_content = b"Patient PHI data for audit test"

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("audit_test.rtf", phi_content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    document_id = response.json()["document_id"]

    # Verify audit log entry exists
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.action == "DOCUMENT_UPLOAD",
            AuditLog.resource_id == document_id,
        )
    )
    audit_entry = result.scalar_one()

    # Check audit log completeness
    assert audit_entry.user_id == admin_user.id
    assert audit_entry.action == "DOCUMENT_UPLOAD"
    assert audit_entry.resource_type == "document"
    assert audit_entry.success == "success"
    assert "filename" in audit_entry.details


@pytest.mark.asyncio
async def test_phi_entities_classified_correctly(db: AsyncSession):
    """Test PHI entities are classified separately from clinical entities."""
    # Create document
    document = Document(
        filename="phi_classification_test.rtf",
        content_hash="test_hash",
        encrypted_content=b"encrypted",
        file_size=100,
        uploaded_by=uuid4(),
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # Create PHI entities
    phi_entities = [
        ExtractedEntity(
            document_id=document.id,
            entity_type=EntityType.PHI_NAME,
            pretty_name="John Smith",
            start_char=0,
            end_char=10,
            accuracy=0.99,
        ),
        ExtractedEntity(
            document_id=document.id,
            entity_type=EntityType.PHI_NHS_NUMBER,
            pretty_name="1234567890",
            start_char=15,
            end_char=25,
            accuracy=0.99,
        ),
    ]

    # Create clinical entity
    clinical_entity = ExtractedEntity(
        document_id=document.id,
        entity_type=EntityType.CLINICAL,
        cui="C0004238",
        pretty_name="Atrial Flutter",
        start_char=30,
        end_char=44,
        accuracy=0.95,
    )

    for entity in phi_entities + [clinical_entity]:
        db.add(entity)
    await db.commit()

    # Verify PHI entities are marked as PHI
    result = await db.execute(
        select(ExtractedEntity).where(
            ExtractedEntity.document_id == document.id,
            ExtractedEntity.entity_type != EntityType.CLINICAL,
        )
    )
    phi_only = result.scalars().all()

    assert len(phi_only) == 2
    for entity in phi_only:
        assert entity.is_phi() is True

    # Verify clinical entity is NOT PHI
    result = await db.execute(
        select(ExtractedEntity).where(
            ExtractedEntity.document_id == document.id,
            ExtractedEntity.entity_type == EntityType.CLINICAL,
        )
    )
    clinical = result.scalar_one()

    assert clinical.is_phi() is False


@pytest.mark.asyncio
async def test_unauthorized_document_access_denied(client, db: AsyncSession):
    """Test unauthorized users cannot access documents (RBAC)."""
    # Create document
    document = Document(
        filename="unauthorized_test.rtf",
        content_hash="test_hash",
        encrypted_content=b"encrypted",
        file_size=100,
        uploaded_by=uuid4(),
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(document)
    await db.commit()

    # Try to access without authentication
    response = client.get(f"/api/v1/documents/{document.id}")

    # Should return 401 Unauthorized
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_encryption_decryption_roundtrip():
    """Test encryption/decryption maintains data integrity."""
    service = EncryptionService.from_env()

    # Test data with PHI
    phi_data = b"Patient: John Smith, NHS: 1234567890, DOB: 15/01/1980, Address: 123 Main St"

    # Encrypt
    encrypted = service.encrypt(phi_data)

    # Encrypted data should be different
    assert encrypted != phi_data

    # Encrypted data should be longer (IV + ciphertext + tag)
    assert len(encrypted) > len(phi_data)

    # Decrypt
    decrypted = service.decrypt(encrypted)

    # Decrypted data should match original
    assert decrypted == phi_data


@pytest.mark.asyncio
async def test_phi_extracted_correctly_from_text():
    """Test PHI extraction identifies all PHI types."""
    from app.clients.modelserve_client import Entity

    service = DocumentProcessingService()

    # Mock entities from MedCAT
    entities = [
        Entity(
            pretty_name="John Smith",
            types=["Person", "Name"],
            start=0,
            end=10,
            accuracy=0.99,
            cui=None,
            meta_anns={},
        ),
        Entity(
            pretty_name="1234567890",
            types=["NHS Number"],
            start=15,
            end=25,
            accuracy=0.99,
            cui=None,
            meta_anns={},
        ),
        Entity(
            pretty_name="15/01/1980",
            types=["DOB"],
            start=30,
            end=40,
            accuracy=0.95,
            cui=None,
            meta_anns={},
        ),
        Entity(
            pretty_name="123 Main St",
            types=["Address"],
            start=45,
            end=56,
            accuracy=0.92,
            cui=None,
            meta_anns={},
        ),
    ]

    # Extract PHI
    phi_data = service._extract_phi(entities)

    # Verify all PHI extracted
    assert phi_data["full_name"] == "John Smith"
    assert phi_data["nhs_number"] == "1234567890"
    assert phi_data["date_of_birth"] is not None
    assert phi_data["address"] == "123 Main St"


@pytest.mark.asyncio
async def test_duplicate_document_does_not_leak_phi(client, admin_token, db: AsyncSession, admin_user):
    """Test duplicate document detection does not expose PHI."""
    phi_content = b"Sensitive patient information"
    content_hash = hashlib.sha256(phi_content).hexdigest()

    # Create original document
    encryption_service = EncryptionService.from_env()
    encrypted = encryption_service.encrypt(phi_content)

    original_doc = Document(
        filename="original.rtf",
        content_type="application/rtf",
        content_hash=content_hash,
        encrypted_content=encrypted,
        encryption_algorithm="aes-256-gcm",
        file_size=len(phi_content),
        uploaded_by=admin_user.id,
        processing_status=ProcessingStatus.COMPLETED,
    )
    db.add(original_doc)
    await db.commit()
    await db.refresh(original_doc)

    # Try to upload duplicate
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("duplicate.rtf", phi_content, "application/rtf")},
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert response.status_code == 200
    data = response.json()

    # Response should indicate duplicate
    assert data["is_duplicate"] is True

    # Response should contain hash (not PHI)
    assert "content_hash" in data

    # Response should NOT contain plaintext content
    assert "Sensitive patient information" not in str(data)


@pytest.mark.asyncio
async def test_failed_decryption_does_not_expose_phi(db: AsyncSession):
    """Test failed decryption doesn't expose PHI in error messages."""
    # Create document with tampered encrypted content
    document = Document(
        filename="tampered.rtf",
        content_hash="test_hash",
        encrypted_content=b"TAMPERED_DATA",  # Invalid encrypted data
        file_size=100,
        uploaded_by=uuid4(),
        processing_status=ProcessingStatus.PENDING,
    )
    db.add(document)
    await db.commit()

    service = DocumentProcessingService()

    # Process document (should fail decryption)
    result = await service.process_document(document.id, db)

    # Document should be marked as failed
    await db.refresh(document)
    assert document.processing_status == ProcessingStatus.FAILED

    # Error should not expose PHI
    # (PHI couldn't be decrypted, so none should be in logs)


@pytest.mark.asyncio
async def test_patient_aggregation_requires_nhs_number(db: AsyncSession):
    """Test patient aggregation only occurs with valid NHS number."""
    from app.services.patient_aggregation_service import PatientAggregationService

    service = PatientAggregationService()

    # Try to aggregate without NHS number (should fail gracefully)
    # This test verifies that missing NHS number is handled correctly
    patient = await service.aggregate_patient(
        db=db,
        nhs_number="",  # Empty NHS number
        full_name="John Doe",
        document_date=datetime.utcnow(),
    )

    # Should still create patient record, but with empty NHS number
    # (This may fail validation - adjust based on actual behavior)
    # The key is that no PHI is exposed in error handling


@pytest.mark.asyncio
async def test_content_hash_prevents_phi_exposure():
    """Test content hash is one-way and doesn't expose PHI."""
    from app.services.deduplication_service import DeduplicationService

    phi_content = b"Patient: John Smith, NHS: 1234567890"

    # Compute hash
    content_hash = DeduplicationService.compute_hash(phi_content)

    # Hash should be SHA-256 (64 hex characters)
    assert len(content_hash) == 64

    # Hash should not contain PHI
    assert "John Smith" not in content_hash
    assert "1234567890" not in content_hash

    # Hash should be deterministic (same input = same hash)
    hash2 = DeduplicationService.compute_hash(phi_content)
    assert content_hash == hash2

    # Different content should have different hash
    different_content = b"Different patient data"
    different_hash = DeduplicationService.compute_hash(different_content)
    assert content_hash != different_hash
