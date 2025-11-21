"""
PHI Detection Service.

Service for detecting Protected Health Information (PHI) in clinical text
using MedCAT de-identification model. Supports all 18 HIPAA Safe Harbor identifiers.
"""
import asyncio
from typing import List, Optional

from app.clients.modelserve_client import CogStackModelServeClient, Entity, ProcessingError
from app.schemas.phi_entity import PHIEntity, ModelInfo


class PHIDetectionService:
    """
    Service for PHI entity detection using MedCAT.

    Detects all 18 HIPAA Safe Harbor identifiers:
    1. NAME - Patient, relative, employer names
    2. LOCATION - Cities, streets, zip codes
    3. DATE - All dates except year
    4. PHONE - Telephone numbers
    5. FAX - Fax numbers
    6. EMAIL - Email addresses
    7. SSN - Social Security Numbers
    8. MRN - Medical record numbers
    9. HEALTHPLAN - Health plan beneficiary numbers
    10. ACCOUNT - Account numbers
    11. LICENSE - Certificate/license numbers
    12. VEHICLE - Vehicle identifiers
    13. DEVICE - Device identifiers/serial numbers
    14. URL - Web URLs
    15. IPADDR - IP addresses
    16. BIOMETRIC - Biometric identifiers
    17. PHOTO - Full-face photo references
    18. IDENTIFIER - Other unique identifying numbers

    Features:
    - Confidence threshold filtering (default: 0.7)
    - Batch processing support
    - Character offset preservation
    - Error handling with graceful degradation

    Example:
        >>> client = CogStackModelServeClient.from_env()
        >>> service = PHIDetectionService(medcat_client=client)
        >>> entities = await service.detect_phi("Patient John Smith, NHS: 1234567890")
        >>> for entity in entities:
        >>>     print(f"{entity.entity_type}: {entity.text} (confidence: {entity.confidence})")
    """

    # Mapping from MedCAT entity types to HIPAA PHI categories
    PHI_TYPE_MAPPING = {
        # Names
        "Person": "NAME",
        "Name": "NAME",
        "Patient Name": "NAME",
        "Relative Name": "NAME",
        "Employer Name": "NAME",

        # Locations
        "Location": "LOCATION",
        "Address": "LOCATION",
        "City": "LOCATION",
        "Street": "LOCATION",
        "Zip Code": "LOCATION",
        "Postal Code": "LOCATION",

        # Dates
        "Date": "DATE",
        "Date of Birth": "DATE",
        "DOB": "DATE",

        # Contact Information
        "Phone": "PHONE",
        "Telephone": "PHONE",
        "Phone Number": "PHONE",
        "Fax": "FAX",
        "Fax Number": "FAX",
        "Email": "EMAIL",
        "Email Address": "EMAIL",

        # Identifiers
        "SSN": "SSN",
        "Social Security Number": "SSN",
        "Medical Record Number": "MRN",
        "MRN": "MRN",
        "NHS Number": "MRN",  # NHS number treated as MRN
        "Health Plan": "HEALTHPLAN",
        "Health Plan Number": "HEALTHPLAN",
        "Account": "ACCOUNT",
        "Account Number": "ACCOUNT",
        "License": "LICENSE",
        "License Number": "LICENSE",
        "Certificate": "LICENSE",
        "Vehicle": "VEHICLE",
        "Vehicle Identifier": "VEHICLE",
        "Device": "DEVICE",
        "Device Identifier": "DEVICE",
        "Serial Number": "DEVICE",
        "URL": "URL",
        "Web URL": "URL",
        "IP Address": "IPADDR",
        "Biometric": "BIOMETRIC",
        "Biometric Identifier": "BIOMETRIC",
        "Photo": "PHOTO",
        "Image": "PHOTO",
        "Identifier": "IDENTIFIER",
        "Unique Identifier": "IDENTIFIER",
    }

    # All supported PHI types (18 total)
    SUPPORTED_PHI_TYPES = [
        "NAME", "LOCATION", "DATE", "PHONE", "FAX", "EMAIL", "SSN", "MRN",
        "HEALTHPLAN", "ACCOUNT", "LICENSE", "VEHICLE", "DEVICE", "URL",
        "IPADDR", "BIOMETRIC", "PHOTO", "IDENTIFIER"
    ]

    def __init__(self, medcat_client: CogStackModelServeClient):
        """
        Initialize PHI detection service.

        Args:
            medcat_client: CogStack ModelServe client instance
        """
        self.medcat_client = medcat_client

    async def detect_phi(
        self,
        text: str,
        confidence_threshold: float = 0.7
    ) -> List[PHIEntity]:
        """
        Detect PHI entities in text.

        Args:
            text: Clinical text to analyze
            confidence_threshold: Minimum confidence score (0.0-1.0, default: 0.7)

        Returns:
            List of PHI entities found in text

        Raises:
            ProcessingError: If MedCAT service fails

        Example:
            >>> entities = await service.detect_phi("Patient: John Smith")
            >>> print(f"Found {len(entities)} PHI entities")
        """
        # Handle empty or whitespace-only input
        if not text or not text.strip():
            return []

        # Call MedCAT de-identification model
        medcat_entities = await self.medcat_client.detect_phi(text)

        # Convert to PHI entities and filter
        phi_entities = []
        for entity in medcat_entities:
            # Map entity type to PHI category
            phi_type = self._map_entity_to_phi_type(entity)

            # Skip non-PHI entities (clinical concepts)
            if phi_type is None:
                continue

            # Apply confidence threshold
            if entity.accuracy < confidence_threshold:
                continue

            # Extract text from original input
            entity_text = text[entity.start:entity.end]

            # Create PHI entity
            phi_entity = PHIEntity(
                entity_type=phi_type,
                text=entity_text,
                start=entity.start,
                end=entity.end,
                confidence=entity.accuracy,
                cui=entity.cui
            )
            phi_entities.append(phi_entity)

        return phi_entities

    async def detect_phi_batch(
        self,
        texts: List[str],
        confidence_threshold: float = 0.7,
        skip_errors: bool = False
    ) -> List[Optional[List[PHIEntity]]]:
        """
        Process multiple texts in batch.

        Args:
            texts: List of clinical texts
            confidence_threshold: Minimum confidence score (0.0-1.0, default: 0.7)
            skip_errors: If True, return None for failed texts; if False, raise error

        Returns:
            List of PHI entity lists (one per text, None if error and skip_errors=True)

        Raises:
            ProcessingError: If processing fails and skip_errors=False

        Example:
            >>> results = await service.detect_phi_batch([
            >>>     "Patient: John Smith",
            >>>     "Contact: 555-1234"
            >>> ])
            >>> print(f"Processed {len(results)} documents")
        """
        results = []

        # Process each text (could be optimized with concurrent processing)
        for text in texts:
            try:
                entities = await self.detect_phi(text, confidence_threshold)
                results.append(entities)
            except ProcessingError as e:
                if skip_errors:
                    results.append(None)
                else:
                    raise

        return results

    def get_model_info(self) -> ModelInfo:
        """
        Get information about the PHI detection model.

        Returns:
            ModelInfo with model name, version, and supported PHI types

        Example:
            >>> info = service.get_model_info()
            >>> print(f"Model: {info.model_name}")
            >>> print(f"Supported PHI types: {len(info.supported_phi_types)}")
        """
        return ModelInfo(
            model_name="medcat_deid",
            model_version="1.0.0",
            supported_phi_types=self.SUPPORTED_PHI_TYPES
        )

    def _map_entity_to_phi_type(self, entity: Entity) -> Optional[str]:
        """
        Map MedCAT entity to HIPAA PHI category.

        Args:
            entity: Entity from MedCAT

        Returns:
            PHI type string (e.g., "NAME", "DATE") or None if not PHI

        Example:
            >>> entity = Entity(pretty_name="John", types=["Person", "Name"], ...)
            >>> phi_type = service._map_entity_to_phi_type(entity)
            >>> assert phi_type == "NAME"
        """
        # Check each entity type against mapping
        for entity_type in entity.types:
            if entity_type in self.PHI_TYPE_MAPPING:
                return self.PHI_TYPE_MAPPING[entity_type]

        # Not a PHI entity (probably a clinical concept)
        return None

    @classmethod
    def from_env(cls) -> "PHIDetectionService":
        """
        Create service from environment variables.

        Reads MODELSERVE_URL from environment to configure MedCAT client.

        Returns:
            PHIDetectionService instance

        Example:
            >>> # MODELSERVE_URL=http://localhost:8000
            >>> service = PHIDetectionService.from_env()
        """
        medcat_client = CogStackModelServeClient.from_env()
        return cls(medcat_client=medcat_client)
