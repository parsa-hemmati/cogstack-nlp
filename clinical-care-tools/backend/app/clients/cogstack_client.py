"""
CogStack-ModelServe Client

HTTP client for interacting with CogStack-ModelServe NLP service.
Implements retry logic, timeout handling, and circuit breaker pattern.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from enum import Enum

import httpx
from pydantic import BaseModel, Field
import structlog

from app.config import Settings

logger = structlog.get_logger()


class CircuitState(str, Enum):
    """Circuit breaker states."""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class NLPModel(str, Enum):
    """Available NLP models."""
    SNOMED_CT = "snomed_ct"
    DEID = "deid"
    UMLS = "umls"
    ICD10 = "icd10"


class MetaAnnotation(BaseModel):
    """Meta-annotation result from MedCAT."""
    Negation: str = Field(default="Affirmed")
    Temporality: str = Field(default="Current")
    Experiencer: str = Field(default="Patient")
    Certainty: str = Field(default="Confirmed")


class ExtractedEntity(BaseModel):
    """Entity extracted by CogStack-ModelServe."""
    cui: str
    pretty_name: str
    source_value: str
    start: int
    end: int
    confidence: float
    meta_anns: MetaAnnotation
    types: List[str] = Field(default_factory=list)
    context_similarity: float = Field(default=0.0)


class CogStackResponse(BaseModel):
    """Response from CogStack-ModelServe."""
    entities: List[ExtractedEntity]
    processing_time_ms: float
    model_version: str
    success: bool = True
    error: Optional[str] = None


class CogStackClientError(Exception):
    """Base exception for CogStack client errors."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation for fault tolerance.

    The circuit breaker prevents cascading failures by failing fast when
    a service is unavailable, giving it time to recover.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CogStackClientError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CogStackClientError("Circuit breaker is open, service unavailable")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    async def async_call(self, func, *args, **kwargs):
        """
        Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CogStackClientError: If circuit is open
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CogStackClientError("Circuit breaker is open, service unavailable")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if we should try to reset the circuit."""
        return (
            self.last_failure_time and
            datetime.now() > self.last_failure_time + timedelta(seconds=self.recovery_timeout)
        )

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN


class CogStackClient:
    """
    HTTP client for CogStack-ModelServe.

    Provides methods to interact with the NLP service, including:
    - Text annotation with various models
    - PHI detection and classification
    - Batch processing support
    - Retry logic and circuit breaker pattern
    """

    def __init__(self, settings: Settings):
        """
        Initialize CogStack client.

        Args:
            settings: Application settings
        """
        self.base_url = settings.MEDCAT_SERVICE_URL
        self.timeout = settings.MEDCAT_SERVICE_TIMEOUT
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60,
            expected_exception=CogStackClientError
        )
        self.max_retries = 3
        self.retry_delay = 1.0

    async def annotate_text(
        self,
        text: str,
        model: NLPModel = NLPModel.SNOMED_CT,
        threshold: float = 0.7,
        include_meta_anns: bool = True
    ) -> CogStackResponse:
        """
        Annotate text with specified NLP model.

        Args:
            text: Text to annotate
            model: NLP model to use
            threshold: Confidence threshold (0.0-1.0)
            include_meta_anns: Include meta-annotations

        Returns:
            CogStackResponse with extracted entities

        Raises:
            CogStackClientError: If annotation fails
        """
        return await self.circuit_breaker.async_call(
            self._annotate_with_retry,
            text,
            model,
            threshold,
            include_meta_anns
        )

    async def _annotate_with_retry(
        self,
        text: str,
        model: NLPModel,
        threshold: float,
        include_meta_anns: bool
    ) -> CogStackResponse:
        """
        Annotate text with retry logic.

        Args:
            text: Text to annotate
            model: NLP model to use
            threshold: Confidence threshold
            include_meta_anns: Include meta-annotations

        Returns:
            CogStackResponse with extracted entities

        Raises:
            CogStackClientError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._make_annotation_request(
                    text, model, threshold, include_meta_anns
                )
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    logger.warning(
                        "CogStack request failed, retrying",
                        attempt=attempt + 1,
                        error=str(e)
                    )
                else:
                    logger.error(
                        "CogStack request failed after all retries",
                        attempts=self.max_retries,
                        error=str(e)
                    )

        raise CogStackClientError(f"Failed after {self.max_retries} attempts: {last_error}")

    async def _make_annotation_request(
        self,
        text: str,
        model: NLPModel,
        threshold: float,
        include_meta_anns: bool
    ) -> CogStackResponse:
        """
        Make annotation request to CogStack-ModelServe.

        Args:
            text: Text to annotate
            model: NLP model to use
            threshold: Confidence threshold
            include_meta_anns: Include meta-annotations

        Returns:
            CogStackResponse with extracted entities

        Raises:
            CogStackClientError: If request fails
        """
        url = f"{self.base_url}/api/v1/process"

        payload = {
            "text": text,
            "model": model.value,
            "threshold": threshold,
            "include_meta_anns": include_meta_anns
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                data = response.json()

                # Parse response into structured format
                entities = []
                for ent in data.get("entities", []):
                    entity = ExtractedEntity(
                        cui=ent["cui"],
                        pretty_name=ent["pretty_name"],
                        source_value=ent["source_value"],
                        start=ent["start"],
                        end=ent["end"],
                        confidence=ent["confidence"],
                        meta_anns=MetaAnnotation(**ent.get("meta_anns", {})),
                        types=ent.get("types", []),
                        context_similarity=ent.get("context_similarity", 0.0)
                    )
                    entities.append(entity)

                return CogStackResponse(
                    entities=entities,
                    processing_time_ms=data.get("processing_time_ms", 0),
                    model_version=data.get("model_version", "unknown"),
                    success=True
                )

            except httpx.TimeoutException:
                raise CogStackClientError(f"Request timed out after {self.timeout} seconds")
            except httpx.HTTPStatusError as e:
                raise CogStackClientError(f"HTTP error {e.response.status_code}: {e.response.text}")
            except Exception as e:
                raise CogStackClientError(f"Unexpected error: {str(e)}")

    async def detect_phi(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect and classify PHI in text using DeID model.

        Args:
            text: Text to analyze for PHI

        Returns:
            List of detected PHI entities with classifications

        Raises:
            CogStackClientError: If PHI detection fails
        """
        response = await self.annotate_text(
            text,
            model=NLPModel.DEID,
            threshold=0.9,  # Higher threshold for PHI detection
            include_meta_anns=False
        )

        phi_entities = []
        for entity in response.entities:
            # Classify PHI type based on entity types
            phi_type = self._classify_phi_type(entity)
            if phi_type:
                phi_entities.append({
                    "text": entity.source_value,
                    "start": entity.start,
                    "end": entity.end,
                    "phi_type": phi_type,
                    "confidence": entity.confidence
                })

        return phi_entities

    def _classify_phi_type(self, entity: ExtractedEntity) -> Optional[str]:
        """
        Classify PHI type based on entity types.

        Args:
            entity: Extracted entity

        Returns:
            PHI type classification or None
        """
        # Map entity types to PHI categories
        phi_mapping = {
            "PERSON": "NAME",
            "NHS_NUMBER": "NHS_NUMBER",
            "DATE": "DATE",
            "ADDRESS": "ADDRESS",
            "LOCATION": "LOCATION",
            "PHONE": "PHONE",
            "EMAIL": "EMAIL",
            "MRN": "MEDICAL_RECORD_NUMBER"
        }

        for entity_type in entity.types:
            if entity_type.upper() in phi_mapping:
                return phi_mapping[entity_type.upper()]

        return None

    async def batch_annotate(
        self,
        texts: List[str],
        model: NLPModel = NLPModel.SNOMED_CT,
        batch_size: int = 10
    ) -> List[CogStackResponse]:
        """
        Annotate multiple texts in batches.

        Args:
            texts: List of texts to annotate
            model: NLP model to use
            batch_size: Number of texts to process in parallel

        Returns:
            List of CogStackResponse objects

        Raises:
            CogStackClientError: If batch processing fails
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            # Process batch in parallel
            tasks = [
                self.annotate_text(text, model)
                for text in batch
            ]

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Handle results and errors
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error("Batch annotation failed for item", error=str(result))
                    # Add empty response for failed items
                    results.append(CogStackResponse(
                        entities=[],
                        processing_time_ms=0,
                        model_version="unknown",
                        success=False,
                        error=str(result)
                    ))
                else:
                    results.append(result)

        return results

    async def health_check(self) -> bool:
        """
        Check if CogStack-ModelServe is healthy.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception as e:
            logger.error("CogStack health check failed", error=str(e))
            return False