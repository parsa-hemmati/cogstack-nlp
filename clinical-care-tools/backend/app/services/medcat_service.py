"""MedCAT NLP service client."""

import logging
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class MedCATService:
    """
    Client for CogStack-ModelServe (MedCAT) service.

    Provides methods for NLP processing of clinical text.
    """

    def __init__(self):
        """Initialize MedCAT service client."""
        self.base_url = settings.MODELSERVE_URL
        self.timeout = settings.MODELSERVE_TIMEOUT

    async def process_text(
        self,
        text: str,
        model_name: str = "medcat_snomed",
    ) -> Dict[str, Any]:
        """
        Process text with MedCAT NLP.

        Args:
            text: Clinical text to process
            model_name: Model to use (medcat_snomed or medcat_deid)

        Returns:
            NLP results with entities and meta-annotations

        Raises:
            httpx.HTTPError: If request fails
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/process",
                    json={"text": text, "model_name": model_name},
                    timeout=self.timeout,
                )
                response.raise_for_status()

                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"MedCAT processing failed: {e}")
                raise

    async def process_bulk(
        self,
        texts: List[str],
        model_name: str = "medcat_snomed",
    ) -> List[Dict[str, Any]]:
        """
        Process multiple texts in bulk.

        Args:
            texts: List of clinical texts
            model_name: Model to use

        Returns:
            List of NLP results
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/process_bulk",
                    json={"texts": texts, "model_name": model_name},
                    timeout=self.timeout * len(texts),
                )
                response.raise_for_status()

                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"MedCAT bulk processing failed: {e}")
                raise

    async def get_models(self) -> List[Dict[str, str]]:
        """
        Get available models.

        Returns:
            List of available models
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/models",
                    timeout=self.timeout,
                )
                response.raise_for_status()

                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to get models: {e}")
                return []

    async def health_check(self) -> bool:
        """
        Check if MedCAT service is healthy.

        Returns:
            True if service is healthy
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/api/health",
                    timeout=5,
                )
                return response.status_code == 200
            except httpx.HTTPError:
                return False

    def extract_entities(self, nlp_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract entities from NLP result.

        Args:
            nlp_result: Result from process_text()

        Returns:
            List of entities with meta-annotations
        """
        entities = []

        # Extract entities from result
        # Format depends on CogStack-ModelServe response structure
        if "entities" in nlp_result:
            for entity in nlp_result["entities"]:
                entities.append(
                    {
                        "cui": entity.get("cui"),
                        "name": entity.get("pretty_name", entity.get("name")),
                        "type": entity.get("type"),
                        "start": entity.get("start"),
                        "end": entity.get("end"),
                        "confidence": entity.get("confidence", 1.0),
                        # Meta-annotations
                        "negation": entity.get("meta_anns", {}).get("Negation", "Affirmed"),
                        "temporality": entity.get("meta_anns", {}).get(
                            "Temporality", "Current"
                        ),
                        "experiencer": entity.get("meta_anns", {}).get(
                            "Experiencer", "Patient"
                        ),
                        "certainty": entity.get("meta_anns", {}).get("Certainty", "Certain"),
                    }
                )

        return entities

    def filter_active_patient_conditions(
        self,
        entities: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Filter entities to only active patient conditions.

        Removes:
        - Negated conditions (Negation != "Affirmed")
        - Family history (Experiencer != "Patient")
        - Historical conditions (Temporality not in ["Current", "Recent"])
        - Uncertain conditions (Certainty != "Certain")

        Args:
            entities: List of entities from extract_entities()

        Returns:
            Filtered list of active patient conditions
        """
        filtered = []

        for entity in entities:
            # Check meta-annotations
            if (
                entity.get("negation") == "Affirmed"
                and entity.get("experiencer") == "Patient"
                and entity.get("temporality") in ["Current", "Recent"]
                and entity.get("certainty") == "Certain"
            ):
                filtered.append(entity)

        return filtered


# Global service instance
medcat_service = MedCATService()
