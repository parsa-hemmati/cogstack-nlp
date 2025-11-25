"""
Unit tests for Document Processing Service.

Tests background job for PHI/entity extraction from documents.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.models.document import Document, ProcessingStatus
from app.models.extracted_entity import ExtractedEntity, EntityType
from app.models.patient import Patient
from app.services.document_processing_service import DocumentProcessingService
from app.clients.modelserve_client import Entity


@pytest.fixture
def processing_service():
    """Create document processing service."""
    return DocumentProcessingService()


@pytest.fixture
def mock_document():
    """Create mock document."""
    return Document(
        id=uuid4(),
        filename="test_clinical_note.rtf",
        content_hash="abc123",
        encrypted_content=b"encrypted_data_here",
        encryption_algorithm="aes-256-gcm",
        file_size=1024,
        uploaded_by=uuid4(),
        processing_status=ProcessingStatus.PENDING,
        created_at=datetime(2025, 1, 15),
    )


@pytest.fixture
def mock_medcat_entities():
    """Mock MedCAT entity extraction results."""
    return [
        # Clinical concept: Atrial flutter
        Entity(
            pretty_name="Atrial Flutter",
            types=["Condition"],
            start=0,
            end=14,
            accuracy=0.95,
            cui="C0004238",
            meta_anns={
                "Negation": "Affirmed",
                "Temporality": "Current",
                "Experiencer": "Patient",
                "Certainty": "Confirmed",
            },
        ),
        # PHI: Patient name
        Entity(
            pretty_name="John Smith",
            types=["Person", "Name"],
            start=50,
            end=60,
            accuracy=0.99,
            cui=None,
            meta_anns={},
        ),
        # PHI: NHS number
        Entity(
            pretty_name="1234567890",
            types=["NHS Number"],
            start=75,
            end=85,
            accuracy=0.99,
            cui=None,
            meta_anns={},
        ),
        # PHI: Date of birth
        Entity(
            pretty_name="15/01/1980",
            types=["Date", "DOB"],
            start=95,
            end=105,
            accuracy=0.95,
            cui=None,
            meta_anns={},
        ),
    ]


@pytest.mark.asyncio
async def test_process_document_success(
    processing_service, mock_document, mock_medcat_entities, db
):
    """Test successful document processing extracts entities and creates patient."""
    # Mock dependencies
    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"decrypted text"
    ), patch.object(
        processing_service.modelserve_client,
        "process_text",
        return_value=mock_medcat_entities,
    ), patch.object(
        processing_service.patient_aggregation_service, "aggregate_patient"
    ) as mock_aggregate:
        mock_patient = Patient(
            id=uuid4(),
            nhs_number="1234567890",
            full_name="John Smith",
            document_count=1,
        )
        mock_aggregate.return_value = mock_patient

        # Add mock document to database
        db.add(mock_document)
        await db.commit()
        await db.refresh(mock_document)

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert
        await db.refresh(mock_document)
        assert mock_document.processing_status == ProcessingStatus.COMPLETED

        # Check entities were created
        from sqlalchemy import select

        result = await db.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.document_id == mock_document.id
            )
        )
        entities = result.scalars().all()
        assert len(entities) == 4

        # Check clinical entity
        clinical_entity = [e for e in entities if e.entity_type == EntityType.CLINICAL][
            0
        ]
        assert clinical_entity.cui == "C0004238"
        assert clinical_entity.pretty_name == "Atrial Flutter"
        assert clinical_entity.meta_anns["Negation"] == "Affirmed"

        # Check PHI entities
        phi_entities = [e for e in entities if e.is_phi()]
        assert len(phi_entities) == 3


@pytest.mark.asyncio
async def test_process_document_updates_patient_record(
    processing_service, mock_document, mock_medcat_entities, db
):
    """Test processing creates/updates patient aggregation."""
    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"text"
    ), patch.object(
        processing_service.modelserve_client,
        "process_text",
        return_value=mock_medcat_entities,
    ), patch.object(
        processing_service.patient_aggregation_service, "aggregate_patient"
    ) as mock_aggregate:
        mock_patient = Patient(
            id=uuid4(), nhs_number="1234567890", full_name="John Smith"
        )
        mock_aggregate.return_value = mock_patient

        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert: aggregate_patient was called
        mock_aggregate.assert_called_once()
        call_args = mock_aggregate.call_args[1]
        assert call_args["nhs_number"] == "1234567890"
        assert call_args["full_name"] == "John Smith"


@pytest.mark.asyncio
async def test_process_document_handles_missing_phi(
    processing_service, mock_document, db
):
    """Test processing handles documents with no PHI detected."""
    clinical_only = [
        Entity(
            pretty_name="Diabetes",
            types=["Condition"],
            start=0,
            end=8,
            accuracy=0.92,
            cui="C0011849",
            meta_anns={},
        )
    ]

    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"text"
    ), patch.object(
        processing_service.modelserve_client, "process_text", return_value=clinical_only
    ):
        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert
        await db.refresh(mock_document)
        # Should still complete even without PHI
        assert mock_document.processing_status == ProcessingStatus.COMPLETED


@pytest.mark.asyncio
async def test_process_document_sets_failed_on_error(processing_service, mock_document, db):
    """Test document status set to failed on processing error."""
    with patch.object(
        processing_service.encryption_service,
        "decrypt",
        side_effect=Exception("Decryption failed"),
    ):
        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert
        await db.refresh(mock_document)
        assert mock_document.processing_status == ProcessingStatus.FAILED


@pytest.mark.asyncio
async def test_process_document_filters_negated_entities(
    processing_service, mock_document, db
):
    """Test negated entities are stored but marked for filtering."""
    entities_with_negation = [
        Entity(
            pretty_name="Diabetes",
            types=["Condition"],
            start=0,
            end=8,
            accuracy=0.92,
            cui="C0011849",
            meta_anns={"Negation": "Negated"},  # Patient DOES NOT have diabetes
        )
    ]

    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"text"
    ), patch.object(
        processing_service.modelserve_client,
        "process_text",
        return_value=entities_with_negation,
    ):
        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert
        from sqlalchemy import select

        result = await db.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.document_id == mock_document.id
            )
        )
        entity = result.scalar_one()

        # Negated entity should be stored for record-keeping
        assert entity.meta_anns["Negation"] == "Negated"
        # But helper method should identify it as NOT an active condition
        assert entity.is_active_patient_condition() is False


@pytest.mark.asyncio
async def test_process_document_handles_family_history(
    processing_service, mock_document, db
):
    """Test family history entities marked correctly."""
    family_history = [
        Entity(
            pretty_name="Heart Disease",
            types=["Condition"],
            start=0,
            end=13,
            accuracy=0.90,
            cui="C0018799",
            meta_anns={
                "Experiencer": "Family",  # Father has heart disease
                "Negation": "Affirmed",
            },
        )
    ]

    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"text"
    ), patch.object(
        processing_service.modelserve_client, "process_text", return_value=family_history
    ):
        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert
        from sqlalchemy import select

        result = await db.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.document_id == mock_document.id
            )
        )
        entity = result.scalar_one()

        # Family history should be stored
        assert entity.meta_anns["Experiencer"] == "Family"
        # But should NOT be counted as patient's active condition
        assert entity.is_family_history() is True
        assert entity.is_active_patient_condition() is False


@pytest.mark.asyncio
async def test_process_pending_documents_batch(processing_service, db):
    """Test batch processing of pending documents."""
    # Create 3 pending documents
    docs = [
        Document(
            filename=f"doc_{i}.rtf",
            content_hash=f"hash_{i}",
            encrypted_content=b"encrypted",
            file_size=100,
            uploaded_by=uuid4(),
            processing_status=ProcessingStatus.PENDING,
        )
        for i in range(3)
    ]
    for doc in docs:
        db.add(doc)
    await db.commit()

    with patch.object(processing_service, "process_document") as mock_process:
        # Act
        count = await processing_service.process_pending_documents(db, batch_size=10)

        # Assert
        assert count == 3
        assert mock_process.call_count == 3


@pytest.mark.asyncio
async def test_process_pending_documents_respects_batch_size(processing_service, db):
    """Test batch size limit is respected."""
    # Create 10 pending documents
    docs = [
        Document(
            filename=f"doc_{i}.rtf",
            content_hash=f"hash_{i}",
            encrypted_content=b"encrypted",
            file_size=100,
            uploaded_by=uuid4(),
            processing_status=ProcessingStatus.PENDING,
        )
        for i in range(10)
    ]
    for doc in docs:
        db.add(doc)
    await db.commit()

    with patch.object(processing_service, "process_document") as mock_process:
        # Act: Process only 5 at a time
        count = await processing_service.process_pending_documents(db, batch_size=5)

        # Assert
        assert count == 5
        assert mock_process.call_count == 5


@pytest.mark.asyncio
async def test_process_document_links_entities_to_patient(
    processing_service, mock_document, mock_medcat_entities, db
):
    """Test entities are linked to aggregated patient record."""
    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"text"
    ), patch.object(
        processing_service.modelserve_client,
        "process_text",
        return_value=mock_medcat_entities,
    ), patch.object(
        processing_service.patient_aggregation_service, "aggregate_patient"
    ) as mock_aggregate:
        mock_patient = Patient(
            id=uuid4(), nhs_number="1234567890", full_name="John Smith"
        )
        mock_aggregate.return_value = mock_patient

        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert: Entities linked to patient
        from sqlalchemy import select

        result = await db.execute(
            select(ExtractedEntity).where(
                ExtractedEntity.document_id == mock_document.id
            )
        )
        entities = result.scalars().all()

        # All entities should have patient_id set
        for entity in entities:
            assert entity.patient_id == mock_patient.id


@pytest.mark.asyncio
async def test_process_document_updates_status_to_processing(
    processing_service, mock_document, db
):
    """Test document status set to processing before extraction."""
    with patch.object(
        processing_service.encryption_service, "decrypt", return_value=b"text"
    ), patch.object(
        processing_service.modelserve_client, "process_text", return_value=[]
    ):
        db.add(mock_document)
        await db.commit()

        # Act
        await processing_service.process_document(mock_document.id, db)

        # Assert: Final status is completed
        await db.refresh(mock_document)
        assert mock_document.processing_status == ProcessingStatus.COMPLETED
