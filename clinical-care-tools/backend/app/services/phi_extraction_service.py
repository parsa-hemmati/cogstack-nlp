"""
PHI Extraction Service

Extracts, categorizes, and stores PHI from clinical documents.
Implements deduplication and patient matching logic.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
import structlog

from app.models.extracted_entity import ExtractedEntity
from app.models.patient import Patient
from app.services.phi_classifier import PHIClassifier, PHIType
from app.services.audit_service import AuditService

logger = structlog.get_logger()


class PHIExtractionService:
    """
    Service for extracting and managing PHI from clinical documents.

    Features:
    - Extract PHI from document entities
    - Categorize and structure PHI data
    - Patient matching and deduplication
    - PHI aggregation across documents
    """

    def __init__(
        self,
        db: AsyncSession,
        phi_classifier: PHIClassifier,
        audit_service: AuditService
    ):
        """
        Initialize PHI extraction service.

        Args:
            db: Database session
            phi_classifier: PHI classification service
            audit_service: Audit logging service
        """
        self.db = db
        self.classifier = phi_classifier
        self.audit = audit_service

    async def extract_patient_identifiers(
        self,
        document_id: UUID
    ) -> Dict[str, Any]:
        """
        Extract patient identifiers from document entities.

        Args:
            document_id: Document to extract from

        Returns:
            Dictionary of patient identifiers
        """
        # Get PHI entities from document
        phi_entities = await self._get_phi_entities(document_id)

        # Extract identifiers
        identifiers = {
            "nhs_number": None,
            "mrn": None,
            "name": {"first_name": None, "last_name": None},
            "date_of_birth": None,
            "address": None,
            "postcode": None,
            "phone": None,
            "email": None
        }

        for entity in phi_entities:
            structured = entity.structured_data or {}

            if entity.entity_type == PHIType.NHS_NUMBER.value:
                if "nhs_number" in structured:
                    identifiers["nhs_number"] = structured["nhs_number"]

            elif entity.entity_type == PHIType.MRN.value:
                identifiers["mrn"] = entity.source_value

            elif entity.entity_type == PHIType.NAME.value:
                if "first_name" in structured:
                    identifiers["name"]["first_name"] = structured["first_name"]
                if "last_name" in structured:
                    identifiers["name"]["last_name"] = structured["last_name"]

            elif entity.entity_type == PHIType.DATE.value:
                # Check if this might be DOB based on context
                if self._is_likely_dob(entity):
                    identifiers["date_of_birth"] = structured.get("date")

            elif entity.entity_type == PHIType.ADDRESS.value:
                identifiers["address"] = entity.source_value

            elif entity.entity_type == PHIType.POSTCODE.value:
                identifiers["postcode"] = structured.get("postcode")

            elif entity.entity_type == PHIType.PHONE.value:
                identifiers["phone"] = structured.get("phone")

            elif entity.entity_type == PHIType.EMAIL.value:
                identifiers["email"] = structured.get("email")

        return identifiers

    async def match_or_create_patient(
        self,
        identifiers: Dict[str, Any],
        document_id: UUID
    ) -> Optional[Patient]:
        """
        Match identifiers to existing patient or create new one.

        Args:
            identifiers: Extracted patient identifiers
            document_id: Source document ID

        Returns:
            Patient record (existing or new)
        """
        # Try to match by NHS number first (most reliable)
        if identifiers.get("nhs_number"):
            patient = await self._find_patient_by_nhs(identifiers["nhs_number"])
            if patient:
                logger.info(
                    "Patient matched by NHS number",
                    nhs_number=identifiers["nhs_number"],
                    patient_id=str(patient.id)
                )
                return await self._update_patient(patient, identifiers, document_id)

        # Try to match by MRN
        if identifiers.get("mrn"):
            patient = await self._find_patient_by_mrn(identifiers["mrn"])
            if patient:
                logger.info(
                    "Patient matched by MRN",
                    mrn=identifiers["mrn"],
                    patient_id=str(patient.id)
                )
                return await self._update_patient(patient, identifiers, document_id)

        # Try fuzzy match by name + DOB
        if identifiers["name"]["last_name"] and identifiers.get("date_of_birth"):
            patient = await self._find_patient_by_demographics(
                identifiers["name"],
                identifiers["date_of_birth"]
            )
            if patient:
                logger.info(
                    "Patient matched by demographics",
                    name=identifiers["name"],
                    patient_id=str(patient.id)
                )
                return await self._update_patient(patient, identifiers, document_id)

        # No match found - create new patient if we have minimum data
        if identifiers["nhs_number"] or identifiers["mrn"] or identifiers["name"]["last_name"]:
            return await self._create_patient(identifiers, document_id)

        logger.warning(
            "Insufficient identifiers to create patient",
            document_id=str(document_id)
        )
        return None

    async def aggregate_patient_data(
        self,
        patient_id: UUID
    ) -> Dict[str, Any]:
        """
        Aggregate all PHI data for a patient across documents.

        Args:
            patient_id: Patient ID

        Returns:
            Aggregated patient data
        """
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            return {}

        # Get all documents for this patient
        document_ids = patient.source_document_ids

        # Collect all PHI entities from these documents
        all_phi = []
        for doc_id in document_ids:
            phi_entities = await self._get_phi_entities(doc_id)
            all_phi.extend(phi_entities)

        # Aggregate by type
        aggregated = {
            "patient_id": patient_id,
            "identifiers": {
                "nhs_number": patient.nhs_number,
                "mrn": patient.mrn
            },
            "demographics": {
                "name": f"{patient.first_name} {patient.last_name}".strip(),
                "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
                "gender": patient.gender
            },
            "contact": {
                "address": self._format_address(patient),
                "postcode": patient.postcode,
                "phones": [],
                "emails": []
            },
            "clinical_concepts": [],
            "dates": [],
            "document_count": len(document_ids)
        }

        # Extract unique contact information
        phones = set()
        emails = set()
        dates = []

        for entity in all_phi:
            if entity.entity_type == PHIType.PHONE.value:
                phones.add(entity.source_value)
            elif entity.entity_type == PHIType.EMAIL.value:
                emails.add(entity.source_value)
            elif entity.entity_type == PHIType.DATE.value:
                dates.append({
                    "date": entity.source_value,
                    "context": self._extract_date_context(entity)
                })

        aggregated["contact"]["phones"] = list(phones)
        aggregated["contact"]["emails"] = list(emails)
        aggregated["dates"] = dates

        # Get clinical concepts (non-PHI entities)
        clinical_entities = await self._get_clinical_entities(document_ids)
        aggregated["clinical_concepts"] = self._aggregate_clinical_concepts(clinical_entities)

        return aggregated

    async def _get_phi_entities(self, document_id: UUID) -> List[ExtractedEntity]:
        """
        Get PHI entities for a document.

        Args:
            document_id: Document ID

        Returns:
            List of PHI entities
        """
        query = select(ExtractedEntity).where(
            and_(
                ExtractedEntity.document_id == document_id,
                ExtractedEntity.is_phi == True
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _get_clinical_entities(
        self,
        document_ids: List[UUID]
    ) -> List[ExtractedEntity]:
        """
        Get clinical (non-PHI) entities for documents.

        Args:
            document_ids: List of document IDs

        Returns:
            List of clinical entities
        """
        query = select(ExtractedEntity).where(
            and_(
                ExtractedEntity.document_id.in_(document_ids),
                ExtractedEntity.is_phi == False
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    def _aggregate_clinical_concepts(
        self,
        entities: List[ExtractedEntity]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate clinical concepts from entities.

        Args:
            entities: List of clinical entities

        Returns:
            Aggregated concepts with frequency
        """
        concept_map = {}

        for entity in entities:
            # Filter by meta-annotations
            meta = entity.meta_annotations
            if (meta.get("Negation") != "Affirmed" or
                meta.get("Experiencer") != "Patient" or
                meta.get("Temporality") == "Hypothetical"):
                continue

            cui = entity.cui
            if cui not in concept_map:
                concept_map[cui] = {
                    "cui": cui,
                    "name": entity.concept_name,
                    "frequency": 0,
                    "first_mentioned": entity.extracted_at,
                    "confidence_avg": 0
                }

            concept_map[cui]["frequency"] += 1
            concept_map[cui]["confidence_avg"] += entity.confidence

        # Calculate average confidence
        for concept in concept_map.values():
            concept["confidence_avg"] /= concept["frequency"]

        # Sort by frequency
        concepts = list(concept_map.values())
        concepts.sort(key=lambda x: x["frequency"], reverse=True)

        return concepts[:20]  # Top 20 concepts

    async def _find_patient_by_nhs(self, nhs_number: str) -> Optional[Patient]:
        """Find patient by NHS number."""
        query = select(Patient).where(Patient.nhs_number == nhs_number)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _find_patient_by_mrn(self, mrn: str) -> Optional[Patient]:
        """Find patient by MRN."""
        query = select(Patient).where(Patient.mrn == mrn)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _find_patient_by_demographics(
        self,
        name: Dict[str, str],
        date_of_birth: str
    ) -> Optional[Patient]:
        """
        Find patient by name and DOB (fuzzy matching).

        Args:
            name: Name dictionary
            date_of_birth: DOB string

        Returns:
            Matching patient or None
        """
        # Simple exact match for now
        # NOTE: Implement fuzzy matching with Levenshtein distance
        query = select(Patient).where(
            and_(
                Patient.last_name == name.get("last_name"),
                Patient.first_name == name.get("first_name"),
                # Patient.date_of_birth == date_of_birth
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _create_patient(
        self,
        identifiers: Dict[str, Any],
        document_id: UUID
    ) -> Patient:
        """
        Create new patient record.

        Args:
            identifiers: Patient identifiers
            document_id: Source document

        Returns:
            Created patient
        """
        patient = Patient(
            nhs_number=identifiers.get("nhs_number"),
            mrn=identifiers.get("mrn"),
            first_name=identifiers["name"].get("first_name"),
            last_name=identifiers["name"].get("last_name"),
            # date_of_birth=identifiers.get("date_of_birth"),
            # Parse address if available
            address_line1=identifiers.get("address"),
            postcode=identifiers.get("postcode"),
            source_document_ids=[document_id],
            last_updated_from=document_id,
            confidence_score=0.8  # Default confidence
        )

        self.db.add(patient)
        await self.db.commit()
        await self.db.refresh(patient)

        logger.info(
            "Created new patient",
            patient_id=str(patient.id),
            nhs_number=patient.nhs_number
        )

        return patient

    async def _update_patient(
        self,
        patient: Patient,
        identifiers: Dict[str, Any],
        document_id: UUID
    ) -> Patient:
        """
        Update existing patient with new information.

        Args:
            patient: Existing patient
            identifiers: New identifiers
            document_id: Source document

        Returns:
            Updated patient
        """
        # Update missing fields only
        if not patient.nhs_number and identifiers.get("nhs_number"):
            patient.nhs_number = identifiers["nhs_number"]

        if not patient.mrn and identifiers.get("mrn"):
            patient.mrn = identifiers["mrn"]

        if not patient.first_name and identifiers["name"].get("first_name"):
            patient.first_name = identifiers["name"]["first_name"]

        if not patient.last_name and identifiers["name"].get("last_name"):
            patient.last_name = identifiers["name"]["last_name"]

        if not patient.address_line1 and identifiers.get("address"):
            patient.address_line1 = identifiers["address"]

        if not patient.postcode and identifiers.get("postcode"):
            patient.postcode = identifiers["postcode"]

        # Add document to source list
        if document_id not in patient.source_document_ids:
            patient.source_document_ids.append(document_id)

        patient.last_updated_from = document_id
        patient.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(patient)

        return patient

    def _is_likely_dob(self, entity: ExtractedEntity) -> bool:
        """
        Check if date entity is likely a date of birth.

        Args:
            entity: Date entity

        Returns:
            True if likely DOB
        """
        # Check surrounding text for DOB indicators
        # This is simplified - could be improved with context analysis
        dob_keywords = ["born", "dob", "birth", "age", "patient born"]
        text_lower = entity.source_value.lower()

        return any(keyword in text_lower for keyword in dob_keywords)

    def _extract_date_context(self, entity: ExtractedEntity) -> str:
        """
        Extract context for a date entity.

        Args:
            entity: Date entity

        Returns:
            Context string
        """
        # NOTE: Extract surrounding text for context
        # For now, return generic context
        if self._is_likely_dob(entity):
            return "Date of Birth"
        return "Clinical Date"

    def _format_address(self, patient: Patient) -> Optional[str]:
        """
        Format patient address.

        Args:
            patient: Patient record

        Returns:
            Formatted address or None
        """
        parts = []
        if patient.address_line1:
            parts.append(patient.address_line1)
        if patient.address_line2:
            parts.append(patient.address_line2)
        if patient.city:
            parts.append(patient.city)
        if patient.postcode:
            parts.append(patient.postcode)

        return ", ".join(parts) if parts else None