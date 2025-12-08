"""
Document Processing Service.

Handles background processing of uploaded clinical documents:
1. Decrypt document content
2. Extract entities via CogStack-ModelServe (SNOMED + PHI)
3. Classify entities (PHI vs clinical)
4. Store entities in database
5. Aggregate patient demographics
6. Update document status

Triggered as FastAPI background task after document upload.

Usage:
    >>> from app.services.document_processing_service import process_document
    >>>
    >>> # Queue as background task (in upload endpoint)
    >>> background_tasks.add_task(process_document, document_id=doc.id, db=db)
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, ProcessingStatus
from app.models.extracted_entity import ExtractedEntity, EntityType
from app.models.patient import Patient
from app.services.encryption_service import decrypt_content, DecryptionError
from app.clients.modelserve_client import CogStackModelServeClient, ModelServeError
from app.services.phi_classifier import classify_entity, classify_entity
from app.services.alerting.alert_manager import AlertManager

logger = logging.getLogger(__name__)


class DocumentProcessingError(Exception):
    """Raised when document processing fails."""
    pass


async def process_document(
    document_id: UUID,
    db: AsyncSession
):
    """
    Process uploaded document in background.
    """
    try:
        logger.info(f"Starting processing for document {document_id}")

        # Step 1: Load document
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise DocumentProcessingError(f"Document not found: {document_id}")

        # Update status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        await db.commit()

        # Step 2: Decrypt content
        try:
            plaintext_content = decrypt_content(document.encrypted_content)
            logger.debug(f"Decrypted document {document_id} ({len(plaintext_content)} bytes)")
        except DecryptionError as e:
            logger.error(f"Decryption failed for document {document_id}: {e}")
            document.processing_status = ProcessingStatus.FAILED
            await db.commit()
            raise DocumentProcessingError(f"Decryption failed: {str(e)}")

        # Convert bytes to string (RTF files are text-based)
        try:
            text_content = plaintext_content.decode('utf-8', errors='ignore')
        except Exception as e:
            logger.error(f"UTF-8 decoding failed for document {document_id}: {e}")
            text_content = plaintext_content.decode('latin-1', errors='ignore')

        # Step 3: Extract entities via CogStack-ModelServe
        modelserve_client = CogStackModelServeClient()

        try:
            # Extract SNOMED clinical entities
            logger.debug(f"Extracting SNOMED entities from document {document_id}")
            snomed_entities = await modelserve_client.process_text(
                text_content,
                model_name="medcat_snomed"
            )
            logger.info(f"Extracted {len(snomed_entities)} SNOMED entities from document {document_id}")

            # Extract PHI entities
            logger.debug(f"Detecting PHI in document {document_id}")
            phi_entities = await modelserve_client.detect_phi(text_content)
            logger.info(f"Detected {len(phi_entities)} PHI entities in document {document_id}")

        except ModelServeError as e:
            logger.error(f"CogStack-ModelServe failed for document {document_id}: {e}")
            document.processing_status = ProcessingStatus.FAILED
            await db.commit()
            raise DocumentProcessingError(f"Entity extraction failed: {str(e)}")
        finally:
            await modelserve_client.close()

        # Step 4: Classify and store entities
        nhs_number = None  # For patient aggregation

        # Process SNOMED clinical entities
        for entity_data in snomed_entities:
            entity_category = classify_entity(entity_data)

            # Store entity
            await _store_entity(
                db=db,
                document_id=document_id,
                entity_data=entity_data,
                entity_category=entity_category
            )

        # Process PHI entities
        for entity_data in phi_entities:
            entity_category = classify_entity(entity_data)

            # Check if this is an NHS number for patient aggregation
            if entity_category == "phi_nhs_number":
                nhs_number = entity_data.get("pretty_name")
                logger.info(f"Found NHS number in document {document_id}: {nhs_number}")

            # Store entity
            await _store_entity(
                db=db,
                document_id=document_id,
                entity_data=entity_data,
                entity_category=entity_category
            )

        await db.commit()

        logger.info(
            f"Stored {len(snomed_entities) + len(phi_entities)} entities from document {document_id}"
        )

        # Step 5: Aggregate patient demographics (if NHS number found)
        patient = None
        if nhs_number:
            patient = await _aggregate_patient(
                db=db,
                document_id=document_id,
                nhs_number=nhs_number
            )

        # Step 6: Trigger Automated Alerting
        if patient:
            logger.info(f"Evaluating alerts for patient {patient.id}")
            try:
                alert_manager = AlertManager(db)
                alert_data = {
                    "text": text_content,
                    "concepts": [e.get("pretty_name", "") for e in snomed_entities]
                }
                await alert_manager.evaluate_and_notify(
                    data=alert_data,
                    patient_id=patient.id
                )
            except Exception as e:
                logger.error(f"Alert evaluation failed: {e}")
                # Do not fail document processing if alerting fails

        # Step 7: Update document status to completed
        document.processing_status = ProcessingStatus.COMPLETED
        await db.commit()

        logger.info(f"Successfully processed document {document_id}")

    except Exception as e:
        logger.error(f"Document processing failed for {document_id}: {e}")
        # Update status to failed
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()
            if document:
                document.processing_status = ProcessingStatus.FAILED
                await db.commit()
        except:
            pass  # Best effort status update

        raise


async def _store_entity(
    db: AsyncSession,
    document_id: UUID,
    entity_data: Dict[str, Any],
    entity_category: str
):
    """
    Store extracted entity in database.
    """
    # Map category string to EntityType enum
    entity_type_mapping = {
        "phi_name": EntityType.PHI_NAME,
        "phi_nhs_number": EntityType.PHI_NHS_NUMBER,
        "phi_dob": EntityType.PHI_DOB,
        "phi_date": EntityType.PHI_DATE,
        "phi_address": EntityType.PHI_ADDRESS,
        "phi_phone": EntityType.PHI_PHONE,
        "phi_email": EntityType.PHI_EMAIL,
        "clinical": EntityType.CLINICAL,
    }

    entity_type = entity_type_mapping.get(entity_category, EntityType.CLINICAL)

    # Create entity record
    entity = ExtractedEntity(
        document_id=document_id,
        entity_type=entity_type,
        cui=entity_data.get("cui", "UNKNOWN"),
        pretty_name=entity_data.get("pretty_name", ""),
        start_char=entity_data.get("start", 0),
        end_char=entity_data.get("end", 0),
        accuracy=entity_data.get("accuracy", entity_data.get("confidence", 0.0)),
        meta_anns=entity_data.get("meta_anns", {})
    )

    db.add(entity)


async def _aggregate_patient(
    db: AsyncSession,
    document_id: UUID,
    nhs_number: str
) -> Optional[Patient]:
    """
    Aggregate patient demographics from document.

    Returns:
        Patient object if found/created, None otherwise.
    """
    from datetime import datetime

    logger.info(f"Aggregating patient data for NHS number: {nhs_number}")

    # Normalize NHS number
    normalized_nhs = Patient.normalize_nhs_number(nhs_number)

    # Find or create patient
    result = await db.execute(
        select(Patient).where(Patient.nhs_number == normalized_nhs)
    )
    patient = result.scalar_one_or_none()

    if patient:
        # Update existing patient
        logger.debug(f"Found existing patient {patient.id} for NHS {normalized_nhs}")
        patient.update_last_seen()
    else:
        # Create new patient
        logger.info(f"Creating new patient for NHS {normalized_nhs}")
        patient = Patient(
            nhs_number=normalized_nhs,
            first_seen_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            document_count=1
        )
        db.add(patient)
        await db.flush()  # Get patient.id

    # Link all entities from this document to the patient
    result = await db.execute(
        select(ExtractedEntity).where(ExtractedEntity.document_id == document_id)
    )
    entities = result.scalars().all()

    for entity in entities:
        entity.patient_id = patient.id

    await db.commit()

    logger.info(f"Linked {len(entities)} entities to patient {patient.id}")
    
    return patient
