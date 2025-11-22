"""
Patient Service

Manages patient records, aggregation, and timeline generation.
Provides patient search and discovery capabilities.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import structlog

from app.models.patient import Patient
from app.models.document import Document
from app.models.extracted_entity import ExtractedEntity
from app.services.audit_service import AuditService
from app.services.phi_extraction_service import PHIExtractionService

logger = structlog.get_logger()


class PatientService:
    """
    Service for patient management and data aggregation.

    Features:
    - Patient search and discovery
    - Demographics aggregation
    - Clinical timeline generation
    - Document association
    - De-duplication by MRN/NHS number
    """

    def __init__(
        self,
        db: AsyncSession,
        audit_service: AuditService,
        phi_extraction_service: PHIExtractionService
    ):
        """
        Initialize patient service.

        Args:
            db: Database session
            audit_service: Audit logging service
            phi_extraction_service: PHI extraction service
        """
        self.db = db
        self.audit = audit_service
        self.phi_extraction = phi_extraction_service

    async def search_patients(
        self,
        query: Optional[str] = None,
        nhs_number: Optional[str] = None,
        mrn: Optional[str] = None,
        last_name: Optional[str] = None,
        postcode: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Patient], int]:
        """
        Search for patients with various criteria.

        Args:
            query: General search query
            nhs_number: NHS number search
            mrn: Medical record number search
            last_name: Last name search
            postcode: Postcode search
            page: Page number
            page_size: Items per page

        Returns:
            Tuple of (patients, total_count)
        """
        # Build query
        stmt = select(Patient)
        conditions = []

        if nhs_number:
            conditions.append(Patient.nhs_number == nhs_number)

        if mrn:
            conditions.append(Patient.mrn == mrn)

        if last_name:
            conditions.append(
                func.lower(Patient.last_name).contains(last_name.lower())
            )

        if postcode:
            conditions.append(Patient.postcode == postcode.upper())

        if query:
            # General search across multiple fields
            query_lower = query.lower()
            conditions.append(
                or_(
                    func.lower(Patient.first_name).contains(query_lower),
                    func.lower(Patient.last_name).contains(query_lower),
                    Patient.nhs_number.contains(query),
                    Patient.mrn.contains(query)
                )
            )

        if conditions:
            stmt = stmt.where(or_(*conditions))

        # Get total count
        count_stmt = select(func.count()).select_from(Patient)
        if conditions:
            count_stmt = count_stmt.where(or_(*conditions))
        total_count = await self.db.scalar(count_stmt)

        # Apply pagination
        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)
        stmt = stmt.order_by(Patient.last_name, Patient.first_name)

        # Execute query
        result = await self.db.execute(stmt)
        patients = result.scalars().all()

        return patients, total_count

    async def get_patient(
        self,
        patient_id: UUID,
        user_id: UUID
    ) -> Optional[Patient]:
        """
        Get patient details by ID.

        Args:
            patient_id: Patient ID
            user_id: User requesting access

        Returns:
            Patient record or None
        """
        patient = await self.db.get(Patient, patient_id)

        if patient:
            # Audit PHI access
            await self.audit.log_phi_access(
                user_id=user_id,
                resource_type="patient",
                resource_id=patient_id,
                action="view"
            )

        return patient

    async def get_patient_timeline(
        self,
        patient_id: UUID,
        user_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Generate patient clinical timeline from documents and entities.

        Args:
            patient_id: Patient ID
            user_id: User requesting timeline

        Returns:
            List of timeline events
        """
        patient = await self.get_patient(patient_id, user_id)
        if not patient:
            return []

        timeline_events = []

        # Get all documents for patient
        documents = await self.get_patient_documents(patient_id)

        for doc in documents:
            # Add document event
            timeline_events.append({
                "date": doc.uploaded_at.isoformat(),
                "type": "document",
                "title": f"Document: {doc.filename}",
                "description": f"Type: {doc.document_type or 'Unknown'}",
                "document_id": str(doc.id),
                "contains_phi": doc.contains_phi
            })

            # Get clinical entities from document
            entities = await self._get_document_clinical_events(doc.id)

            for entity in entities:
                # Filter by meta-annotations
                meta = entity.meta_annotations
                if (meta.get("Negation") != "Affirmed" or
                    meta.get("Experiencer") != "Patient"):
                    continue

                # Determine event type
                event_type = self._classify_clinical_event(entity)

                timeline_events.append({
                    "date": entity.extracted_at.isoformat(),
                    "type": event_type,
                    "title": entity.concept_name,
                    "description": f"From: {entity.source_value}",
                    "cui": entity.cui,
                    "confidence": entity.confidence,
                    "temporality": meta.get("Temporality", "Unknown"),
                    "document_id": str(doc.id)
                })

        # Sort timeline by date
        timeline_events.sort(key=lambda x: x["date"], reverse=True)

        # Audit timeline access
        await self.audit.log_phi_access(
            user_id=user_id,
            resource_type="patient_timeline",
            resource_id=patient_id,
            action="view"
        )

        return timeline_events

    async def get_patient_documents(
        self,
        patient_id: UUID
    ) -> List[Document]:
        """
        Get all documents associated with a patient.

        Args:
            patient_id: Patient ID

        Returns:
            List of documents
        """
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            return []

        # Get documents by ID
        if not patient.source_document_ids:
            return []

        stmt = select(Document).where(
            Document.id.in_(patient.source_document_ids)
        )
        stmt = stmt.order_by(Document.uploaded_at.desc())

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def aggregate_patient_from_document(
        self,
        document_id: UUID,
        user_id: UUID
    ) -> Optional[Patient]:
        """
        Create or update patient record from document.

        Args:
            document_id: Document to process
            user_id: User performing aggregation

        Returns:
            Patient record or None
        """
        try:
            # Extract patient identifiers from document
            identifiers = await self.phi_extraction.extract_patient_identifiers(
                document_id
            )

            if not identifiers:
                logger.warning(
                    "No patient identifiers found",
                    document_id=str(document_id)
                )
                return None

            # Match or create patient
            patient = await self.phi_extraction.match_or_create_patient(
                identifiers,
                document_id
            )

            if patient:
                logger.info(
                    "Patient aggregated from document",
                    patient_id=str(patient.id),
                    document_id=str(document_id)
                )

                # Audit the aggregation
                await self.audit.log_phi_access(
                    user_id=user_id,
                    resource_type="patient_aggregation",
                    resource_id=patient.id,
                    action="aggregate",
                    details={
                        "document_id": str(document_id),
                        "identifiers_found": bool(identifiers.get("nhs_number") or identifiers.get("mrn"))
                    }
                )

            return patient

        except Exception as e:
            logger.error(
                "Patient aggregation failed",
                document_id=str(document_id),
                error=str(e)
            )
            return None

    async def merge_patients(
        self,
        primary_patient_id: UUID,
        duplicate_patient_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Merge duplicate patient records.

        Args:
            primary_patient_id: Primary patient to keep
            duplicate_patient_id: Duplicate to merge
            user_id: User performing merge

        Returns:
            True if successful
        """
        try:
            primary = await self.db.get(Patient, primary_patient_id)
            duplicate = await self.db.get(Patient, duplicate_patient_id)

            if not primary or not duplicate:
                return False

            # Merge data (prefer primary's data)
            if not primary.nhs_number and duplicate.nhs_number:
                primary.nhs_number = duplicate.nhs_number

            if not primary.mrn and duplicate.mrn:
                primary.mrn = duplicate.mrn

            # Merge document lists
            for doc_id in duplicate.source_document_ids:
                if doc_id not in primary.source_document_ids:
                    primary.source_document_ids.append(doc_id)

            # Update confidence score
            primary.confidence_score = max(
                primary.confidence_score or 0,
                duplicate.confidence_score or 0
            )

            # Delete duplicate
            await self.db.delete(duplicate)
            await self.db.commit()

            # Audit the merge
            await self.audit.log_phi_access(
                user_id=user_id,
                resource_type="patient_merge",
                resource_id=primary_patient_id,
                action="merge",
                details={
                    "merged_patient_id": str(duplicate_patient_id),
                    "document_count": len(primary.source_document_ids)
                }
            )

            logger.info(
                "Patients merged successfully",
                primary_id=str(primary_patient_id),
                duplicate_id=str(duplicate_patient_id)
            )

            return True

        except Exception as e:
            logger.error(
                "Patient merge failed",
                error=str(e)
            )
            await self.db.rollback()
            return False

    async def calculate_patient_statistics(
        self,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """
        Calculate statistics for a patient.

        Args:
            patient_id: Patient ID

        Returns:
            Statistics dictionary
        """
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            return {}

        # Get document count
        doc_count = len(patient.source_document_ids)

        # Get entity counts
        entity_stmt = select(
            func.count(ExtractedEntity.id),
            func.count(ExtractedEntity.id).filter(ExtractedEntity.is_phi == True)
        ).where(
            ExtractedEntity.document_id.in_(patient.source_document_ids)
        )

        result = await self.db.execute(entity_stmt)
        total_entities, phi_entities = result.one()

        # Get unique conditions
        condition_stmt = select(
            func.count(func.distinct(ExtractedEntity.cui))
        ).where(
            and_(
                ExtractedEntity.document_id.in_(patient.source_document_ids),
                ExtractedEntity.is_phi == False,
                ExtractedEntity.entity_type == "CONDITION"
            )
        )

        unique_conditions = await self.db.scalar(condition_stmt)

        return {
            "patient_id": str(patient_id),
            "document_count": doc_count,
            "total_entities": total_entities or 0,
            "phi_entities": phi_entities or 0,
            "clinical_entities": (total_entities or 0) - (phi_entities or 0),
            "unique_conditions": unique_conditions or 0,
            "confidence_score": patient.confidence_score,
            "last_updated": patient.updated_at.isoformat() if patient.updated_at else None
        }

    async def _get_document_clinical_events(
        self,
        document_id: UUID
    ) -> List[ExtractedEntity]:
        """
        Get clinical events from document entities.

        Args:
            document_id: Document ID

        Returns:
            List of clinical entities
        """
        stmt = select(ExtractedEntity).where(
            and_(
                ExtractedEntity.document_id == document_id,
                ExtractedEntity.is_phi == False
            )
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    def _classify_clinical_event(self, entity: ExtractedEntity) -> str:
        """
        Classify clinical entity into event type.

        Args:
            entity: Clinical entity

        Returns:
            Event type string
        """
        entity_type = entity.entity_type.upper()

        if entity_type in ["CONDITION", "DIAGNOSIS", "SYMPTOM"]:
            return "diagnosis"
        elif entity_type in ["MEDICATION", "DRUG"]:
            return "medication"
        elif entity_type in ["PROCEDURE", "SURGERY"]:
            return "procedure"
        elif entity_type in ["LAB", "LAB_RESULT", "TEST"]:
            return "lab_result"
        elif entity_type in ["ALLERGY"]:
            return "allergy"
        else:
            return "clinical_note"