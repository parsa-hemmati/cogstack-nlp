"""
CogStack-ModelServe Client.

Async HTTP client for CogStack-ModelServe API (https://github.com/CogStack/CogStack-ModelServe).
Provides SNOMED entity extraction, PHI detection, and meta-annotation parsing.

CogStack-ModelServe is a production-ready API service that wraps MedCAT models
with built-in retry logic, authentication, and monitoring.

Usage:
    >>> client = CogStackModelServeClient()
    >>>
    >>> # Extract SNOMED entities
    >>> entities = await client.process_text("Patient has diabetes and hypertension")
    >>> for entity in entities:
    ...     print(f"{entity['pretty_name']} (CUI: {entity['cui']})")
    ...     print(f"  Negation: {entity['meta_anns']['Negation']['value']}")
    >>>
    >>> # Detect PHI
    >>> phi_entities = await client.detect_phi("Patient John Doe, NHS: 123 456 7890")
    >>> for phi in phi_entities:
    ...     print(f"{phi['entity_type']}: {phi['pretty_name']}")
"""

import os
import logging
from typing import List, Dict, Any, Optional
import httpx


logger = logging.getLogger(__name__)


class ModelServeError(Exception):
    """Raised when CogStack-ModelServe API call fails."""
    pass


class CogStackModelServeClient:
    """
    Async client for CogStack-ModelServe API.

    CogStack-ModelServe provides production-ready NLP processing with:
    - SNOMED-CT entity extraction (medcat_snomed model)
    - PHI detection and classification (medcat_deid model)
    - Meta-annotations (Negation, Temporality, Experiencer, Certainty)
    - Built-in retry logic and authentication
    - Prometheus metrics (optional)

    Attributes:
        base_url: CogStack-ModelServe API base URL
        client: httpx AsyncClient for API calls
        timeout: Request timeout in seconds (default: 30)

    Example:
        >>> client = CogStackModelServeClient(base_url="http://localhost:8000")
        >>> entities = await client.process_text("Diabetes diagnosis")
        >>> print(entities[0]["cui"])  # C0011849
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize CogStack-ModelServe client.

        Args:
            base_url: CogStack-ModelServe API URL (default: from MODELSERVE_URL env var)
            timeout: Request timeout in seconds (default: 30)

        Environment Variables:
            MODELSERVE_URL: CogStack-ModelServe base URL (default: http://cogstack-modelserve:8000)
        """
        self.base_url = base_url or os.getenv("MODELSERVE_URL", "http://cogstack-modelserve:8000")
        self.timeout = timeout

        # Create async HTTP client
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers={"Content-Type": "application/json"}
        )

        logger.info(f"CogStack-ModelServe client initialized: {self.base_url}")

    async def process_text(
        self,
        text: str,
        model_name: str = "medcat_snomed"
    ) -> List[Dict[str, Any]]:
        """
        Process text and extract medical entities.

        Args:
            text: Clinical text to process
            model_name: Model name to use (default: "medcat_snomed")

        Returns:
            List of entities with CUI codes, names, positions, and meta-annotations

        Raises:
            ModelServeError: If API call fails

        Example:
            >>> entities = await client.process_text("Patient has diabetes")
            >>> entities[0]
            {
                "cui": "C0011849",
                "pretty_name": "Diabetes Mellitus",
                "start": 12,
                "end": 20,
                "meta_anns": {
                    "Negation": {"value": "Affirmed", "confidence": 0.95},
                    "Temporality": {"value": "Current", "confidence": 0.89},
                    ...
                }
            }
        """
        try:
            logger.debug(f"Processing text with {model_name}: {text[:50]}...")

            response = await self.client.post(
                "/api/process",
                json={
                    "text": text,
                    "model_name": model_name
                }
            )

            if response.status_code != 200:
                raise ModelServeError(
                    f"CogStack-ModelServe returned {response.status_code}: {response.text}"
                )

            result = response.json()
            entities = result.get("entities", [])

            logger.debug(f"Extracted {len(entities)} entities from text")

            return entities

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling CogStack-ModelServe: {e}")
            raise ModelServeError(f"Failed to process text: {str(e)}")

    async def detect_phi(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PHI (Protected Health Information) in text.

        Uses CogStack-ModelServe's medcat_deid model to identify PHI entities
        like names, NHS numbers, dates, addresses, etc.

        Args:
            text: Clinical text potentially containing PHI

        Returns:
            List of PHI entities with types and positions

        Raises:
            ModelServeError: If API call fails

        Example:
            >>> phi_entities = await client.detect_phi("Patient John Doe, NHS: 123 456 7890")
            >>> phi_entities[0]
            {
                "cui": "PHI-NAME",
                "pretty_name": "John Doe",
                "entity_type": "PHI-NAME",
                "start": 8,
                "end": 16
            }
        """
        return await self.process_text(text, model_name="medcat_deid")

    async def process_text_bulk(
        self,
        texts: List[str],
        model_name: str = "medcat_snomed"
    ) -> List[List[Dict[str, Any]]]:
        """
        Process multiple texts in batch.

        Args:
            texts: List of clinical texts to process
            model_name: Model name to use (default: "medcat_snomed")

        Returns:
            List of entity lists (one per input text)

        Raises:
            ModelServeError: If any API call fails

        Example:
            >>> texts = ["Diabetes diagnosis", "Hypertension noted"]
            >>> results = await client.process_text_bulk(texts)
            >>> len(results)  # 2
            >>> len(results[0])  # Entities from first text
        """
        results = []

        for text in texts:
            entities = await self.process_text(text, model_name=model_name)
            results.append(entities)

        logger.info(f"Bulk processed {len(texts)} texts with {model_name}")

        return results

    def classify_entity_type(self, entity: Dict[str, Any]) -> str:
        """
        Classify entity as PHI or clinical based on CUI/entity_type.

        Args:
            entity: Entity dict from CogStack-ModelServe

        Returns:
            Entity type classification:
            - "phi_name": Patient/person name
            - "phi_nhs_number": NHS number
            - "phi_date": Date of birth or other date
            - "phi_address": Address
            - "phi_phone": Phone number
            - "phi_email": Email address
            - "clinical": Clinical concept (SNOMED-CT)

        Example:
            >>> entity = {"cui": "PHI-NAME", "entity_type": "PHI-NAME"}
            >>> client.classify_entity_type(entity)
            'phi_name'
            >>> entity = {"cui": "C0011849", "entity_type": "CLINICAL"}
            >>> client.classify_entity_type(entity)
            'clinical'
        """
        # Check CUI prefix
        cui = entity.get("cui", "")
        entity_type = entity.get("entity_type", "")

        # PHI entity types (from CogStack-ModelServe medcat_deid model)
        if cui.startswith("PHI-") or entity_type.startswith("PHI-"):
            phi_type = cui.replace("PHI-", "").lower() if cui.startswith("PHI-") else entity_type.replace("PHI-", "").lower()

            # Map PHI types
            phi_mapping = {
                "name": "phi_name",
                "nhs-number": "phi_nhs_number",
                "nhs_number": "phi_nhs_number",
                "date": "phi_date",
                "address": "phi_address",
                "phone": "phi_phone",
                "email": "phi_email",
            }

            return phi_mapping.get(phi_type, f"phi_{phi_type}")

        # Clinical entity (SNOMED-CT or other)
        return "clinical"

    async def health_check(self) -> bool:
        """
        Check if CogStack-ModelServe is healthy.

        Returns:
            True if service is healthy, False otherwise

        Example:
            >>> is_healthy = await client.health_check()
            >>> print(is_healthy)
            True
        """
        try:
            response = await self.client.get("/health")

            if response.status_code == 200:
                logger.debug("CogStack-ModelServe health check: OK")
                return True
            else:
                logger.warning(f"CogStack-ModelServe health check failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"CogStack-ModelServe health check error: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models from CogStack-ModelServe.

        Returns:
            List of model names (e.g., ["medcat_snomed", "medcat_deid"])

        Raises:
            ModelServeError: If API call fails

        Example:
            >>> models = await client.get_available_models()
            >>> print(models)
            ['medcat_snomed', 'medcat_deid', 'medcat_umls']
        """
        try:
            response = await self.client.get("/models")

            if response.status_code != 200:
                raise ModelServeError(
                    f"Failed to get models: {response.status_code} {response.text}"
                )

            result = response.json()
            models = result.get("models", [])

            logger.info(f"Available models: {models}")

            return models

        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting models: {e}")
            raise ModelServeError(f"Failed to get available models: {str(e)}")

    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
        logger.debug("CogStack-ModelServe client closed")

    async def __aenter__(self):
        """Context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
