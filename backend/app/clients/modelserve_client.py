"""
CogStack-ModelServe Client.

Async HTTP client for CogStack-ModelServe API (MedCAT NLP service).
Supports SNOMED-CT entity extraction and PHI detection.
"""
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, field

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


class ProcessingError(Exception):
    """Exception raised when ModelServe processing fails."""

    pass


@dataclass
class Entity:
    """
    Entity extracted by MedCAT.

    Attributes:
        cui: SNOMED-CT or UMLS Concept Unique Identifier (optional for PHI)
        pretty_name: Human-readable entity name
        types: Entity types (e.g., ["Disease or Syndrome"], ["Person", "Name"])
        start: Character offset start position
        end: Character offset end position
        accuracy: Confidence score (0.0-1.0)
        meta_anns: Meta-annotations (Negation, Temporality, Experiencer, Certainty)
    """

    pretty_name: str
    types: List[str]
    start: int
    end: int
    accuracy: float
    cui: Optional[str] = None
    meta_anns: Dict[str, str] = field(default_factory=dict)


class CogStackModelServeClient:
    """
    Async HTTP client for CogStack-ModelServe API.

    CogStack-ModelServe is a production-ready service for serving MedCAT models.
    It provides endpoints for clinical NLP processing and PHI detection.

    Features:
    - SNOMED-CT entity extraction (clinical concepts)
    - PHI detection with de-identification model
    - Meta-annotations: Negation, Temporality, Experiencer, Certainty
    - Bulk processing support
    - Health checks

    Example:
        >>> client = CogStackModelServeClient(base_url="http://localhost:8000")
        >>> entities = await client.process_text("Patient has diabetes", model_name="medcat_snomed")
        >>> for entity in entities:
        >>>     print(f"{entity.pretty_name} (CUI: {entity.cui})")
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize ModelServe client.

        Args:
            base_url: ModelServe URL (default: from MODELSERVE_URL env var)
        """
        self.base_url = base_url or os.getenv(
            "MODELSERVE_URL", "http://cogstack-modelserve:8000"
        )
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
    )
    async def process_text(
        self, text: str, model_name: str = "medcat_snomed"
    ) -> List[Entity]:
        """
        Process text with MedCAT model.

        Retries up to 3 times with exponential backoff for transient errors.

        Args:
            text: Clinical text to process
            model_name: Model name (e.g., "medcat_snomed", "medcat_deid")

        Returns:
            List of extracted entities

        Raises:
            ProcessingError: If processing fails
            httpx.TimeoutException: After 3 retry attempts
            httpx.NetworkError: After 3 retry attempts

        Example:
            >>> entities = await client.process_text(
            >>>     "Patient has diabetes mellitus and hypertension",
            >>>     model_name="medcat_snomed"
            >>> )
        """
        try:
            response = await self.client.post(
                f"{self.base_url}/api/process",
                json={"text": text, "model_name": model_name},
            )

            if response.status_code != 200:
                raise ProcessingError(
                    f"ModelServe returned {response.status_code}: {response.text}"
                )

            data = response.json()
            entities = data.get("entities", [])

            return [self._parse_entity(e) for e in entities]

        except httpx.HTTPError as e:
            raise ProcessingError(f"HTTP error: {e}")

    async def detect_phi(self, text: str) -> List[Entity]:
        """
        Detect PHI in text using de-identification model.

        Args:
            text: Text to scan for PHI

        Returns:
            List of PHI entities (names, NHS numbers, dates, addresses)

        Example:
            >>> phi_entities = await client.detect_phi("John Smith, NHS 1234567890")
        """
        return await self.process_text(text, model_name="medcat_deid")

    async def process_text_bulk(
        self, texts: List[str], model_name: str = "medcat_snomed"
    ) -> List[List[Entity]]:
        """
        Process multiple texts in bulk.

        Args:
            texts: List of clinical texts
            model_name: Model name

        Returns:
            List of entity lists (one per text)

        Example:
            >>> results = await client.process_text_bulk([
            >>>     "Patient has diabetes",
            >>>     "No signs of infection"
            >>> ])
        """
        results = []
        for text in texts:
            entities = await self.process_text(text, model_name)
            results.append(entities)
        return results

    def classify_entity_type(self, entity: Entity) -> str:
        """
        Classify entity as clinical or PHI category.

        Maps ModelServe entity types to our database schema:
        - clinical: SNOMED-CT medical concepts
        - phi_name: Patient names
        - phi_nhs_number: NHS numbers
        - phi_dob: Dates of birth
        - phi_address: Addresses

        Args:
            entity: Entity from ModelServe

        Returns:
            Entity type string

        Example:
            >>> entity = Entity(pretty_name="Diabetes", types=["Disease"], ...)
            >>> entity_type = client.classify_entity_type(entity)
            >>> assert entity_type == "clinical"
        """
        types = entity.types
        pretty_name_lower = entity.pretty_name.lower()

        # PHI: Names
        if "Person" in types or "Name" in types:
            return "phi_name"

        # PHI: NHS Number / Medical Record Number
        if "NHS Number" in types or "Medical Record Number" in types:
            return "phi_nhs_number"

        # PHI: Address / Location
        if "Address" in types or "Location" in types:
            return "phi_address"

        # PHI: Date of Birth
        if "Date" in types and any(
            word in pretty_name_lower for word in ["birth", "dob", "born"]
        ):
            return "phi_dob"

        # Default: Clinical entity (SNOMED-CT concept)
        return "clinical"

    async def health_check(self) -> bool:
        """
        Check if ModelServe is healthy.

        Returns:
            True if healthy, False otherwise

        Example:
            >>> is_healthy = await client.health_check()
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models from ModelServe.

        Returns:
            List of model names

        Example:
            >>> models = await client.get_available_models()
            >>> assert "medcat_snomed" in models
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/models")
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
            return []
        except httpx.HTTPError:
            return []

    def _parse_entity(self, entity_data: Dict) -> Entity:
        """
        Parse entity from ModelServe JSON response.

        Args:
            entity_data: Entity dictionary from API

        Returns:
            Entity dataclass instance
        """
        return Entity(
            cui=entity_data.get("cui"),
            pretty_name=entity_data["pretty_name"],
            types=entity_data.get("types", []),
            start=entity_data["start"],
            end=entity_data["end"],
            accuracy=entity_data.get("accuracy", 0.0),
            meta_anns=entity_data.get("meta_anns", {}),
        )

    @classmethod
    def from_env(cls) -> "CogStackModelServeClient":
        """
        Create client from environment variables.

        Returns:
            CogStackModelServeClient instance

        Example:
            >>> # MODELSERVE_URL=http://localhost:8000
            >>> client = CogStackModelServeClient.from_env()
        """
        return cls()
