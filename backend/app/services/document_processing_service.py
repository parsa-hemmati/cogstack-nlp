"""
Document Processing Service.

Background job for extracting PHI and clinical entities from documents using MedCAT.
"""
import logging
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.modelserve_client import CogStackModelServeClient, Entity
from app.models.document import Document, ProcessingStatus
from app.models.extracted_entity import EntityType, ExtractedEntity
from app.models.patient import Patient
from app.services.encryption_service import EncryptionService
from app.services.patient_aggregation_service import PatientAggregationService

logger = logging.getLogger(__name__)


class DocumentProcessingService:
    """
    Document processing service for PHI/entity extraction.

    Workflow:
        1. Fetch pending document from database
        2. Decrypt document content
        3. Extract entities using MedCAT (CogStack-ModelServe)
        4. Classify entities (clinical vs PHI types)
        5. Store entities in database
        6. Extract PHI (name, NHS number, DOB, address)
        7. Aggregate patient record by NHS number
        8. Link entities to patient
        9. Update document status (completed/failed)

    Features:
        - Batch processing of pending documents
        - Error handling with failed status
        - Patient aggregation by NHS number
        - Meta-annotation preservation (Negation, Temporality, etc.)
        - PHI classification (name, NHS number, DOB, address)

    Example:
        >>> service = DocumentProcessingService()
        >>> await service.process_pending_documents(db, batch_size=10)
        5  # Processed 5 documents
    """

    def __init__(self):
        """Initialize document processing service."""
        self.encryption_service = EncryptionService.from_env()
        self.modelserve_client = CogStackModelServeClient()
        self.patient_aggregation_service = PatientAggregationService()

    async def process_document(
        self, document_id: UUID, db: AsyncSession
    ) -> Optional[Document]:
        """
        Process single document: decrypt, extract entities, aggregate patient.

        Args:
            document_id: Document ID to process
            db: Database session

        Returns:
            Processed document with updated status

        Example:
            >>> doc = await service.process_document(doc_id, db)
            >>> assert doc.processing_status == ProcessingStatus.COMPLETED
        """
        # Fetch document
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            logger.error(f"Document {document_id} not found")
            return None

        # Update status to processing
        document.processing_status = ProcessingStatus.PROCESSING
        await db.commit()

        try:
            # Decrypt content
            plaintext = self.encryption_service.decrypt(document.encrypted_content)
            text = plaintext.decode("utf-8")

            logger.info(
                f"Processing document {document_id}: {len(text)} chars, "
                f"filename={document.filename}"
            )

            # Extract entities using MedCAT
            entities = await self.modelserve_client.process_text(
                text, model_name="medcat_snomed"
            )

            logger.info(
                f"Extracted {len(entities)} entities from document {document_id}"
            )

            # Extract PHI for patient aggregation
            phi_data = self._extract_phi(entities)

            # Create patient record (if PHI found)
            patient = None
            if phi_data.get("nhs_number"):
                patient = await self.patient_aggregation_service.aggregate_patient(
                    db=db,
                    nhs_number=phi_data["nhs_number"],
                    full_name=phi_data.get("full_name"),
                    date_of_birth=phi_data.get("date_of_birth"),
                    address=phi_data.get("address"),
                    document_date=document.created_at,
                )
                logger.info(
                    f"Aggregated patient {patient.nhs_number} for document {document_id}"
                )

            # Store extracted entities
            for entity in entities:
                entity_type = self._classify_entity_type(entity)

                extracted_entity = ExtractedEntity(
                    document_id=document.id,
                    patient_id=patient.id if patient else None,
                    entity_type=entity_type,
                    cui=entity.cui,
                    pretty_name=entity.pretty_name,
                    start_char=entity.start,
                    end_char=entity.end,
                    accuracy=entity.accuracy,
                    meta_anns=entity.meta_anns,
                )
                db.add(extracted_entity)

            # Update document status to completed
            document.processing_status = ProcessingStatus.COMPLETED
            await db.commit()
            await db.refresh(document)

            logger.info(f"Document {document_id} processing completed successfully")

            return document

        except Exception as e:
            # Update status to failed
            document.processing_status = ProcessingStatus.FAILED
            await db.commit()

            logger.error(
                f"Document {document_id} processing failed: {e}", exc_info=True
            )

            return document

    async def process_pending_documents(
        self, db: AsyncSession, batch_size: int = 10
    ) -> int:
        """
        Process batch of pending documents.

        Args:
            db: Database session
            batch_size: Maximum documents to process in this batch

        Returns:
            Number of documents processed

        Example:
            >>> count = await service.process_pending_documents(db, batch_size=5)
            >>> print(f"Processed {count} documents")
        """
        # Fetch pending documents
        result = await db.execute(
            select(Document)
            .where(Document.processing_status == ProcessingStatus.PENDING)
            .limit(batch_size)
        )
        documents = result.scalars().all()

        logger.info(f"Found {len(documents)} pending documents (batch_size={batch_size})")

        # Process each document
        processed_count = 0
        for document in documents:
            await self.process_document(document.id, db)
            processed_count += 1

        logger.info(f"Batch processing complete: {processed_count} documents processed")

        return processed_count

    def _extract_phi(self, entities: list[Entity]) -> dict:
        """
        Extract PHI fields from entity list.

        Args:
            entities: List of extracted entities

        Returns:
            Dictionary with PHI fields: nhs_number, full_name, date_of_birth, address

        Example:
            >>> phi = service._extract_phi(entities)
            >>> print(phi['nhs_number'])  # "1234567890"
        """
        phi_data = {}

        for entity in entities:
            entity_type = self._classify_entity_type(entity)

            if entity_type == EntityType.PHI_NHS_NUMBER:
                # Extract NHS number (10 digits)
                nhs_number = "".join(c for c in entity.pretty_name if c.isdigit())
                if len(nhs_number) == 10:
                    phi_data["nhs_number"] = nhs_number

            elif entity_type == EntityType.PHI_NAME:
                # Extract patient name
                phi_data["full_name"] = entity.pretty_name

            elif entity_type == EntityType.PHI_DOB:
                # Extract date of birth
                dob = self._parse_date(entity.pretty_name)
                if dob:
                    phi_data["date_of_birth"] = dob

            elif entity_type == EntityType.PHI_ADDRESS:
                # Extract address
                phi_data["address"] = entity.pretty_name

        return phi_data

    def _classify_entity_type(self, entity: Entity) -> EntityType:
        """
        Classify entity as clinical concept or PHI type.

        Args:
            entity: MedCAT entity

        Returns:
            EntityType enum value

        Classification rules:
            - Person/Name → PHI_NAME
            - NHS Number → PHI_NHS_NUMBER
            - DOB/Date of Birth → PHI_DOB
            - Address/Location → PHI_ADDRESS
            - Has CUI → CLINICAL (SNOMED-CT concept)

        Example:
            >>> entity = Entity(types=["Person"], ...)
            >>> entity_type = service._classify_entity_type(entity)
            >>> assert entity_type == EntityType.PHI_NAME
        """
        # Check for PHI types
        types_lower = [t.lower() for t in entity.types]

        if "person" in types_lower or "name" in types_lower:
            return EntityType.PHI_NAME

        if "nhs number" in types_lower or "nhs_number" in types_lower:
            return EntityType.PHI_NHS_NUMBER

        if "dob" in types_lower or "date of birth" in types_lower:
            return EntityType.PHI_DOB

        if "address" in types_lower or "location" in types_lower:
            return EntityType.PHI_ADDRESS

        # Default to clinical concept (SNOMED-CT)
        return EntityType.CLINICAL

    def _parse_date(self, date_string: str) -> Optional[date]:
        """
        Parse date string to date object.

        Supports formats: DD/MM/YYYY, YYYY-MM-DD, DD-MM-YYYY

        Args:
            date_string: Date string to parse

        Returns:
            date object or None if parsing fails

        Example:
            >>> dob = service._parse_date("15/01/1980")
            >>> assert dob == date(1980, 1, 15)
        """
        formats = [
            "%d/%m/%Y",  # 15/01/1980
            "%Y-%m-%d",  # 1980-01-15
            "%d-%m-%Y",  # 15-01-1980
            "%d.%m.%Y",  # 15.01.1980
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(date_string.strip(), fmt)
                return dt.date()
            except ValueError:
                continue

        logger.warning(f"Failed to parse date: {date_string}")
        return None
