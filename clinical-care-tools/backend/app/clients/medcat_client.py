"""
MedCAT Client - Web Environment Adaptation

Mock client for development/testing in web environment.
Production: Replace with actual CogStack-ModelServe client.

NOTE: This is a MOCK implementation for development only.
      In production, use the real CogStack-ModelServe API.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import httpx
from pydantic import BaseModel

from app.core.config import settings


# Response Models

class MetaAnnotation(BaseModel):
    """Meta-annotation for a medical concept."""
    name: str
    value: str
    confidence: float


class MedicalConcept(BaseModel):
    """Medical concept extracted from text."""
    cui: str  # SNOMED-CT or UMLS concept unique identifier
    name: str  # Preferred name
    types: List[str]  # Semantic types (e.g., ['disorder', 'finding'])
    start: int  # Character position in text
    end: int  # Character position in text
    text: str  # Matched text
    confidence: float  # Confidence score (0-1)
    meta_anns: Dict[str, MetaAnnotation]  # Meta-annotations


class ProcessingResult(BaseModel):
    """Result from processing clinical text."""
    text: str
    concepts: List[MedicalConcept]
    processing_time: float
    model_name: str


class DeIDResult(BaseModel):
    """Result from de-identification."""
    original_text: str
    deidentified_text: str
    phi_entities: List[Dict[str, Any]]
    processing_time: float


# Mock Data

MOCK_CONCEPTS = {
    "diabetes": {
        "cui": "C0011849",
        "name": "Diabetes Mellitus",
        "types": ["disorder"],
    },
    "hypertension": {
        "cui": "C0020538",
        "name": "Hypertensive disorder",
        "types": ["disorder"],
    },
    "atrial fibrillation": {
        "cui": "C0004238",
        "name": "Atrial Fibrillation",
        "types": ["disorder"],
    },
    "chest pain": {
        "cui": "C0008031",
        "name": "Chest Pain",
        "types": ["finding", "symptom"],
    },
}


class MedCATClient:
    """
    MedCAT Client for NLP processing.

    Web Environment: Mock implementation for development.
    Production: Connects to actual CogStack-ModelServe API.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        mock_mode: bool = True,  # Always True in web environment
    ):
        """
        Initialize MedCAT client.

        Args:
            base_url: CogStack-ModelServe base URL
            api_key: Optional API key for authentication
            mock_mode: If True, use mock implementation (web environment)
        """
        self.base_url = base_url or settings.medcat_service_url
        self.api_key = api_key or settings.medcat_api_key
        self.mock_mode = mock_mode  # Always True in web environment

        if not self.mock_mode:
            # Production: Create HTTP client
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
                timeout=30.0,
            )
        else:
            self.client = None

    async def close(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()

    async def extract_concepts(
        self,
        text: str,
        filter_meta_annotations: bool = True,
    ) -> ProcessingResult:
        """
        Extract medical concepts from clinical text.

        Args:
            text: Clinical text to process
            filter_meta_annotations: If True, filter by meta-annotations
                                      (Negation=Affirmed, Experiencer=Patient)

        Returns:
            ProcessingResult with extracted concepts
        """
        if self.mock_mode:
            return await self._mock_extract_concepts(text, filter_meta_annotations)

        # Production: Call actual CogStack-ModelServe API
        response = await self.client.post(
            "/api/process",
            json={"text": text},
        )
        response.raise_for_status()
        data = response.json()
        return ProcessingResult(**data)

    async def deidentify(self, text: str) -> DeIDResult:
        """
        De-identify clinical text (remove PHI/PII).

        Args:
            text: Clinical text to de-identify

        Returns:
            DeIDResult with de-identified text and PHI entities
        """
        if self.mock_mode:
            return await self._mock_deidentify(text)

        # Production: Call actual CogStack-ModelServe API
        response = await self.client.post(
            "/api/deid",
            json={"text": text},
        )
        response.raise_for_status()
        data = response.json()
        return DeIDResult(**data)

    async def health_check(self) -> bool:
        """
        Check if MedCAT service is healthy.

        Returns:
            True if service is healthy
        """
        if self.mock_mode:
            return True  # Mock is always healthy

        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False

    # Mock Implementations (Web Environment)

    async def _mock_extract_concepts(
        self, text: str, filter_meta_annotations: bool
    ) -> ProcessingResult:
        """
        Mock implementation of concept extraction.

        Searches for known medical terms in text and creates mock concepts.
        """
        import time
        start_time = time.time()

        concepts = []

        # Search for mock concepts in text
        text_lower = text.lower()
        for term, concept_data in MOCK_CONCEPTS.items():
            if term in text_lower:
                start_pos = text_lower.index(term)
                end_pos = start_pos + len(term)

                # Create meta-annotations
                # For mock: assume all are affirmed, patient-related, current
                meta_anns = {
                    "Negation": MetaAnnotation(
                        name="Negation",
                        value="Affirmed",
                        confidence=0.95,
                    ),
                    "Experiencer": MetaAnnotation(
                        name="Experiencer",
                        value="Patient",
                        confidence=0.90,
                    ),
                    "Temporality": MetaAnnotation(
                        name="Temporality",
                        value="Recent",
                        confidence=0.85,
                    ),
                }

                concept = MedicalConcept(
                    cui=concept_data["cui"],
                    name=concept_data["name"],
                    types=concept_data["types"],
                    start=start_pos,
                    end=end_pos,
                    text=text[start_pos:end_pos],
                    confidence=0.92,
                    meta_anns=meta_anns,
                )

                # Apply meta-annotation filter if requested
                if filter_meta_annotations:
                    # Only include affirmed, patient-related concepts
                    if (
                        concept.meta_anns["Negation"].value == "Affirmed"
                        and concept.meta_anns["Experiencer"].value == "Patient"
                    ):
                        concepts.append(concept)
                else:
                    concepts.append(concept)

        processing_time = time.time() - start_time

        return ProcessingResult(
            text=text,
            concepts=concepts,
            processing_time=processing_time,
            model_name="medcat_snomed_mock",
        )

    async def _mock_deidentify(self, text: str) -> DeIDResult:
        """
        Mock implementation of de-identification.

        Simple pattern-based PHI detection for demonstration.
        Production: Use trained DeID model.
        """
        import re
        import time

        start_time = time.time()

        # Mock PHI patterns
        phi_entities = []
        deidentified_text = text

        # NHS number pattern (mock: 10 digits)
        nhs_pattern = r'\b\d{10}\b'
        for match in re.finditer(nhs_pattern, text):
            phi_entities.append({
                "type": "NHS_NUMBER",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
            })
            deidentified_text = deidentified_text.replace(
                match.group(), "[NHS_NUMBER]"
            )

        # Date pattern (mock: simple date detection)
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b'
        for match in re.finditer(date_pattern, text):
            phi_entities.append({
                "type": "DATE",
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
            })
            deidentified_text = deidentified_text.replace(match.group(), "[DATE]")

        processing_time = time.time() - start_time

        return DeIDResult(
            original_text=text,
            deidentified_text=deidentified_text,
            phi_entities=phi_entities,
            processing_time=processing_time,
        )


# Global client instance
medcat_client = MedCATClient(mock_mode=True)


async def get_medcat() -> MedCATClient:
    """
    Dependency for getting MedCAT client.

    Usage:
        @app.get("/endpoint")
        async def endpoint(medcat: MedCATClient = Depends(get_medcat)):
            ...
    """
    return medcat_client
