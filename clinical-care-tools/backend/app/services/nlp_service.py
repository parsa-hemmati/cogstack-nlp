"""
NLP Processing Service

Orchestrates NLP processing of documents using CogStack-ModelServe.
Handles entity extraction, meta-annotations, and PHI detection.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import structlog

from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity
from app.clients.cogstack_client import (
    CogStackClient, NLPModel, CogStackClientError
)
from app.services.audit_service import AuditService
from app.services.document_service import DocumentService
from app.utils.encryption import decrypt_document

logger = structlog.get_logger()


class NLPService:
    """
    Service for NLP processing of clinical documents.

    Features:
    - Medical entity extraction (SNOMED-CT, UMLS, ICD-10)
    - Meta-annotation processing (negation, temporality, experiencer, certainty)
    - PHI detection and classification
    - Confidence thresholding
    - Batch processing support
    """

    def __init__(
        self,
        db: AsyncSession,
        cogstack_client: CogStackClient,
        audit_service: AuditService,
        document_service: DocumentService
    ):
        """
        Initialize NLP service.

        Args:
            db: Database session
            cogstack_client: CogStack-ModelServe client
            audit_service: Audit logging service
            document_service: Document service
        """
        self.db = db
        self.cogstack = cogstack_client
        self.audit = audit_service
        self.doc_service = document_service

    async def process_document(
        self,
        document_id: UUID,
        user_id: UUID,
        force_reprocess: bool = False
    ) -> Dict[str, Any]:
        """
        Process document with NLP to extract entities.

        Args:
            document_id: Document to process
            user_id: User requesting processing
            force_reprocess: Force reprocessing even if already done

        Returns:
            Processing results dictionary

        Raises:
            ValueError: If document not found
            CogStackClientError: If NLP processing fails
        """
        try:
            # Get document
            document = await self.db.get(Document, document_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            # Check if already processed
            if document.medcat_status == "complete" and not force_reprocess:
                logger.info(
                    "Document already processed",
                    document_id=str(document_id)
                )
                return {
                    "document_id": document_id,
                    "status": "already_processed",
                    "entities_count": await self._count_entities(document_id)
                }

            # Update status to processing
            await self.doc_service.update_processing_status(
                document_id, "processing"
            )

            # Decrypt document content
            content_bytes = decrypt_document(
                document.content,
                document.encryption_key_id
            )
            content_text = content_bytes.decode('utf-8', errors='replace')

            # Process with multiple models
            start_time = datetime.utcnow()

            # Extract medical entities (SNOMED-CT)
            medical_response = await self.cogstack.annotate_text(
                content_text,
                model=NLPModel.SNOMED_CT,
                threshold=0.7,
                include_meta_anns=True
            )

            # Detect PHI (DeID model)
            phi_entities = await self.cogstack.detect_phi(content_text)

            # Store extracted entities
            entities_created = await self._store_extracted_entities(
                document_id,
                document.project_id,
                medical_response.entities,
                phi_entities
            )

            # Update PHI types in document
            phi_types = list(set([e["phi_type"] for e in phi_entities]))
            if phi_types:
                document.phi_types = phi_types

            # Update document status
            processing_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            await self.doc_service.update_processing_status(
                document_id, "complete"
            )

            # Audit log
            await self.audit.log_nlp_processing(
                user_id=user_id,
                document_id=document_id,
                model_name="SNOMED_CT+DeID",
                entities_count=len(medical_response.entities),
                phi_count=len(phi_entities),
                processing_time_ms=processing_time_ms
            )

            logger.info(
                "Document processed successfully",
                document_id=str(document_id),
                entities_count=entities_created,
                processing_time_ms=processing_time_ms
            )

            return {
                "document_id": document_id,
                "status": "success",
                "entities_count": entities_created,
                "medical_entities": len(medical_response.entities),
                "phi_entities": len(phi_entities),
                "processing_time_ms": processing_time_ms
            }

        except CogStackClientError as e:
            # Update status to failed
            await self.doc_service.update_processing_status(
                document_id, "failed", str(e)
            )
            logger.error(
                "NLP processing failed",
                document_id=str(document_id),
                error=str(e)
            )
            raise

        except Exception as e:
            # Update status to failed
            await self.doc_service.update_processing_status(
                document_id, "failed", str(e)
            )
            logger.error(
                "Unexpected error during NLP processing",
                document_id=str(document_id),
                error=str(e)
            )
            raise

    async def _store_extracted_entities(
        self,
        document_id: UUID,
        project_id: UUID,
        medical_entities: List[Any],
        phi_entities: List[Dict[str, Any]]
    ) -> int:
        """
        Store extracted entities in database.

        Args:
            document_id: Source document ID
            project_id: Project ID
            medical_entities: Medical entities from CogStack
            phi_entities: PHI entities from DeID

        Returns:
            Number of entities created
        """
        entities_created = 0

        # Clear existing entities if reprocessing
        await self._clear_existing_entities(document_id)

        # Store medical entities
        for entity in medical_entities:
            # Apply meta-annotation filters
            if not self._should_include_entity(entity):
                continue

            extracted = ExtractedEntity(
                document_id=document_id,
                project_id=project_id,
                cui=entity.cui,
                concept_name=entity.pretty_name,
                source_value=entity.source_value,
                start_char=entity.start,
                end_char=entity.end,
                confidence=entity.confidence,
                meta_annotations={
                    "Negation": entity.meta_anns.Negation,
                    "Temporality": entity.meta_anns.Temporality,
                    "Experiencer": entity.meta_anns.Experiencer,
                    "Certainty": entity.meta_anns.Certainty
                },
                entity_type="CONDITION",  # Default, could be refined
                is_phi=False,
                medcat_version="1.0.0"  # NOTE: Get from config
            )
            self.db.add(extracted)
            entities_created += 1

        # Store PHI entities
        for phi in phi_entities:
            extracted = ExtractedEntity(
                document_id=document_id,
                project_id=project_id,
                cui=f"PHI_{phi['phi_type']}",
                concept_name=phi["phi_type"],
                source_value=phi["text"],
                start_char=phi["start"],
                end_char=phi["end"],
                confidence=phi["confidence"],
                meta_annotations={},
                entity_type=phi["phi_type"],
                is_phi=True,
                phi_category=self._classify_phi_category(phi["phi_type"]),
                structured_data=self._extract_structured_phi(phi),
                medcat_version="1.0.0"
            )
            self.db.add(extracted)
            entities_created += 1

        await self.db.commit()
        return entities_created

    def _should_include_entity(self, entity: Any) -> bool:
        """
        Apply meta-annotation filters to determine if entity should be included.

        Args:
            entity: Entity from CogStack

        Returns:
            True if entity should be included
        """
        # Filter out negated conditions
        if entity.meta_anns.Negation != "Affirmed":
            return False

        # Filter out family history
        if entity.meta_anns.Experiencer != "Patient":
            return False

        # Filter out past/hypothetical conditions (optional)
        if entity.meta_anns.Temporality == "Hypothetical":
            return False

        # Filter out low certainty (optional)
        if entity.meta_anns.Certainty == "Uncertain":
            return False

        return True

    def _classify_phi_category(self, phi_type: str) -> str:
        """
        Classify PHI into HIPAA categories.

        Args:
            phi_type: Type of PHI

        Returns:
            PHI category
        """
        direct_identifiers = [
            "NAME", "NHS_NUMBER", "MRN", "SSN", "EMAIL",
            "PHONE", "FAX", "DEVICE_ID", "URL", "IP"
        ]

        quasi_identifiers = [
            "DATE", "ADDRESS", "LOCATION", "AGE", "POSTCODE"
        ]

        if phi_type in direct_identifiers:
            return "DIRECT_IDENTIFIER"
        elif phi_type in quasi_identifiers:
            return "QUASI_IDENTIFIER"
        else:
            return "CLINICAL_DATA"

    def _extract_structured_phi(self, phi: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract structured data from PHI entity.

        Args:
            phi: PHI entity

        Returns:
            Structured data dictionary
        """
        structured = {}

        if phi["phi_type"] == "NAME":
            # Try to split into first/last name
            parts = phi["text"].split()
            if len(parts) >= 2:
                structured["first_name"] = parts[0]
                structured["last_name"] = " ".join(parts[1:])
            else:
                structured["full_name"] = phi["text"]

        elif phi["phi_type"] == "NHS_NUMBER":
            # Clean and validate NHS number
            nhs_num = "".join(filter(str.isdigit, phi["text"]))
            if len(nhs_num) == 10:
                structured["nhs_number"] = nhs_num

        elif phi["phi_type"] == "DATE":
            # Parse date if possible
            structured["date_string"] = phi["text"]
            # NOTE: Parse to actual date

        elif phi["phi_type"] == "ADDRESS":
            structured["address_text"] = phi["text"]
            # NOTE: Parse into components

        return structured

    async def _clear_existing_entities(self, document_id: UUID) -> None:
        """
        Clear existing entities for a document (for reprocessing).

        Args:
            document_id: Document ID
        """
        query = select(ExtractedEntity).where(
            ExtractedEntity.document_id == document_id
        )
        result = await self.db.execute(query)
        entities = result.scalars().all()

        for entity in entities:
            await self.db.delete(entity)

        await self.db.commit()

    async def _count_entities(self, document_id: UUID) -> int:
        """
        Count entities for a document.

        Args:
            document_id: Document ID

        Returns:
            Number of entities
        """
        query = select(ExtractedEntity).where(
            ExtractedEntity.document_id == document_id
        )
        result = await self.db.execute(query)
        return len(result.scalars().all())

    async def get_document_entities(
        self,
        document_id: UUID,
        include_phi: bool = True,
        entity_type: Optional[str] = None
    ) -> List[ExtractedEntity]:
        """
        Get entities extracted from a document.

        Args:
            document_id: Document ID
            include_phi: Whether to include PHI entities
            entity_type: Filter by entity type

        Returns:
            List of extracted entities
        """
        query = select(ExtractedEntity).where(
            ExtractedEntity.document_id == document_id
        )

        if not include_phi:
            query = query.where(ExtractedEntity.is_phi == False)

        if entity_type:
            query = query.where(ExtractedEntity.entity_type == entity_type)

        query = query.order_by(ExtractedEntity.start_char)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def batch_process_documents(
        self,
        document_ids: List[UUID],
        user_id: UUID,
        batch_size: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Process multiple documents in batches.

        Args:
            document_ids: List of document IDs
            user_id: User requesting processing
            batch_size: Number of documents per batch

        Returns:
            List of processing results
        """
        results = []

        for i in range(0, len(document_ids), batch_size):
            batch = document_ids[i:i + batch_size]

            # Process batch sequentially (could be parallel)
            for doc_id in batch:
                try:
                    result = await self.process_document(doc_id, user_id)
                    results.append(result)
                except Exception as e:
                    logger.error(
                        "Batch processing failed for document",
                        document_id=str(doc_id),
                        error=str(e)
                    )
                    results.append({
                        "document_id": doc_id,
                        "status": "failed",
                        "error": str(e)
                    })

        return results