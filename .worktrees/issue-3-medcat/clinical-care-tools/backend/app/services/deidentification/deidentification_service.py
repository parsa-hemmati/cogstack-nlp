"""De-identification Service (Sprint 4, Phase 4.2)

Main service for de-identifying clinical documents.

Workflow:
1. Detect PHI using PHI detection service
2. Generate surrogates using surrogate service
3. Apply redaction based on mode (mask/surrogate/remove)
4. Store de-identified document
5. Optionally store re-identification mapping (Phase 4.3)
6. Create audit log
"""

import logging
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.phi import DetectedEntity
from app.schemas.deidentification import (
    RedactionMode,
    DeidentificationPreview,
    EntityWithSurrogate,
    DeidentifiedDocumentResult
)
from app.services.phi import PHIDetectionService
from app.services.deidentification.surrogate_service import SurrogateGenerationService
from app.core.audit import audit_log

logger = logging.getLogger(__name__)


class DeidentificationService:
    """Service for de-identifying clinical documents"""

    def __init__(
        self,
        db: AsyncSession,
        phi_service: Optional[PHIDetectionService] = None,
        surrogate_service: Optional[SurrogateGenerationService] = None
    ):
        """Initialize de-identification service

        Args:
            db: Database session
            phi_service: PHI detection service (created if None)
            surrogate_service: Surrogate generation service (created if None)
        """
        self.db = db
        self.phi_service = phi_service or PHIDetectionService(use_mock=True)
        self.surrogate_service = surrogate_service or SurrogateGenerationService()

    async def preview_deidentification(
        self,
        document_ids: List[UUID],
        redaction_mode: RedactionMode,
        user_id: UUID
    ) -> List[DeidentificationPreview]:
        """Preview de-identification (show what will be redacted)

        Args:
            document_ids: Documents to preview
            redaction_mode: How to redact (mask/surrogate/remove)
            user_id: User requesting preview (for audit logging)

        Returns:
            List of previews with detected entities and redacted text
        """
        previews: List[DeidentificationPreview] = []

        for doc_id in document_ids:
            # Fetch document text
            doc_text = await self._get_document_text(doc_id)
            if doc_text is None:
                logger.warning(f"Document {doc_id} not found, skipping")
                continue

            # Detect PHI
            entities = await self.phi_service.detect_phi(doc_text)

            # Generate surrogates (for preview)
            entity_mappings = self.surrogate_service.generate_surrogates(entities)

            # Create entities with surrogates
            entities_with_surrogates = [
                EntityWithSurrogate(
                    **entity.model_dump(),
                    surrogate=entity_mappings.get(entity.text)
                )
                for entity in entities
            ]

            # Apply redaction (preview)
            redacted_text = self._apply_redaction(
                doc_text,
                entities,
                redaction_mode,
                entity_mappings
            )

            previews.append(DeidentificationPreview(
                document_id=doc_id,
                original_text=doc_text,
                entities=entities_with_surrogates,
                redacted_text=redacted_text,
                entities_count=len(entities)
            ))

            # Audit log (preview action)
            audit_log(
                user_id=user_id,
                action="DEIDENTIFY_PREVIEW",
                resource_type="document",
                resource_id=doc_id,
                details={
                    "redaction_mode": redaction_mode.value,
                    "entities_detected": len(entities)
                }
            )

        return previews

    async def apply_deidentification(
        self,
        document_ids: List[UUID],
        redaction_mode: RedactionMode,
        store_mapping: bool,
        user_id: UUID
    ) -> List[DeidentifiedDocumentResult]:
        """Apply de-identification (create de-identified documents)

        Args:
            document_ids: Documents to de-identify
            redaction_mode: How to redact (mask/surrogate/remove)
            store_mapping: Store re-identification mapping?
            user_id: User applying de-identification

        Returns:
            List of de-identified document results
        """
        results: List[DeidentifiedDocumentResult] = []

        for doc_id in document_ids:
            try:
                # Fetch document text
                doc_text = await self._get_document_text(doc_id)
                if doc_text is None:
                    logger.error(f"Document {doc_id} not found")
                    continue

                # Detect PHI
                entities = await self.phi_service.detect_phi(doc_text)

                # Generate surrogates
                entity_mappings = self.surrogate_service.generate_surrogates(entities)

                # Apply redaction
                redacted_text = self._apply_redaction(
                    doc_text,
                    entities,
                    redaction_mode,
                    entity_mappings
                )

                # Store de-identified document
                deid_doc_id = await self._store_deidentified_document(
                    original_doc_id=doc_id,
                    redacted_text=redacted_text,
                    redaction_mode=redaction_mode,
                    entities_redacted=len(entities),
                    user_id=user_id
                )

                # Store re-identification mapping (Phase 4.3)
                mapping_id: Optional[UUID] = None
                if store_mapping:
                    # TODO: Implement in Phase 4.3
                    # mapping_id = await self._store_reid_mapping(doc_id, entity_mappings)
                    pass

                # Create audit log
                audit_log_id = UUID(audit_log(
                    user_id=user_id,
                    action="DEIDENTIFY_APPLY",
                    resource_type="document",
                    resource_id=doc_id,
                    details={
                        "deidentified_doc_id": str(deid_doc_id),
                        "redaction_mode": redaction_mode.value,
                        "entities_redacted": len(entities),
                        "store_mapping": store_mapping
                    }
                ))

                results.append(DeidentifiedDocumentResult(
                    original_document_id=doc_id,
                    deidentified_document_id=deid_doc_id,
                    redaction_mode=redaction_mode,
                    entities_redacted=len(entities),
                    mapping_id=mapping_id,
                    audit_log_id=audit_log_id
                ))

            except Exception as e:
                logger.error(f"Failed to de-identify document {doc_id}: {e}")
                # Continue with other documents

        return results

    def _apply_redaction(
        self,
        text: str,
        entities: List[DetectedEntity],
        redaction_mode: RedactionMode,
        entity_mappings: Optional[Dict[str, str]] = None
    ) -> str:
        """Apply redaction to text

        Args:
            text: Original text
            entities: Detected PHI entities
            redaction_mode: How to redact
            entity_mappings: Original → surrogate mappings (for surrogate mode)

        Returns:
            Redacted text
        """
        # Sort entities by position (reverse order to preserve offsets)
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

        redacted_text = text

        for entity in sorted_entities:
            original = entity.text

            # Determine replacement based on mode
            if redaction_mode == RedactionMode.MASK:
                replacement = "[REDACTED]"
            elif redaction_mode == RedactionMode.SURROGATE:
                replacement = entity_mappings.get(original, "[REDACTED]") if entity_mappings else "[REDACTED]"
            elif redaction_mode == RedactionMode.REMOVE:
                replacement = ""
            else:
                replacement = "[REDACTED]"

            # Replace entity in text (working backwards preserves offsets)
            redacted_text = (
                redacted_text[:entity.start] +
                replacement +
                redacted_text[entity.end:]
            )

        return redacted_text

    async def _get_document_text(self, doc_id: UUID) -> Optional[str]:
        """Fetch document text from database

        Args:
            doc_id: Document ID

        Returns:
            Document text or None if not found
        """
        # TODO: Replace with actual database query
        # Example:
        # result = await self.db.execute(
        #     select(Document.content).where(Document.id == doc_id)
        # )
        # doc = result.scalar_one_or_none()
        # return doc.content if doc else None

        # Mock implementation for testing
        logger.warning(f"Using mock document fetch for {doc_id}")
        return f"Patient John Doe (DOB: 01/15/1980, MRN: 12345678) presents with chest pain."

    async def _store_deidentified_document(
        self,
        original_doc_id: UUID,
        redacted_text: str,
        redaction_mode: RedactionMode,
        entities_redacted: int,
        user_id: UUID
    ) -> UUID:
        """Store de-identified document in database

        Args:
            original_doc_id: Original document ID
            redacted_text: Redacted text
            redaction_mode: Redaction mode used
            entities_redacted: Number of entities redacted
            user_id: User who created de-identified document

        Returns:
            De-identified document ID
        """
        # TODO: Replace with actual database insert
        # Example:
        # deid_doc = DeidentifiedDocument(
        #     id=uuid4(),
        #     original_document_id=original_doc_id,
        #     redaction_mode=redaction_mode.value,
        #     redacted_text=redacted_text,
        #     entities_redacted=entities_redacted,
        #     created_by=user_id,
        #     created_at=datetime.utcnow()
        # )
        # self.db.add(deid_doc)
        # await self.db.commit()
        # return deid_doc.id

        # Mock implementation
        deid_doc_id = uuid4()
        logger.info(
            f"Stored de-identified document {deid_doc_id} "
            f"(original: {original_doc_id}, mode: {redaction_mode.value}, "
            f"entities: {entities_redacted})"
        )
        return deid_doc_id
