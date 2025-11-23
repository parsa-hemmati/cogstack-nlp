"""Meditech FHIR Client for Read Operations.

Provides async methods to fetch FHIR resources from Meditech Expanse API.
Implements error handling, retries, and exponential backoff for rate limiting.
"""

import logging
from typing import List, Optional, Dict, Any
import httpx
from app.core.config import settings
from app.clients.meditech_oauth import get_oauth_client
from app.models.fhir.patient import FHIRPatient
from app.models.fhir.condition import FHIRCondition
from app.models.fhir.observation import FHIRObservation
from app.models.fhir.medication_request import FHIRMedicationRequest

logger = logging.getLogger(__name__)


class MeditechFHIRClient:
    """FHIR client for Meditech Expanse API.

    Implements read operations for Patient, Condition, Observation, MedicationRequest resources.
    Handles OAuth authentication, error handling, and rate limiting.
    """

    def __init__(self):
        """Initialize FHIR client with Meditech base URL."""
        self.base_url = settings.MEDITECH_FHIR_BASE_URL  # e.g., https://meditech-uk.cloud/fhir/r4
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.oauth_client = None  # Lazy initialization

    async def _get_oauth_client(self):
        """Get OAuth client instance (lazy initialization)."""
        if self.oauth_client is None:
            self.oauth_client = await get_oauth_client()
        return self.oauth_client

    async def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers with OAuth token.

        Returns:
            Dict of headers including Authorization
        """
        oauth = await self._get_oauth_client()
        token = await oauth.get_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json"
        }

    async def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make HTTP request to Meditech FHIR API with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path (e.g., /Patient/123)
            params: Query parameters
            retry_count: Current retry attempt (for exponential backoff)

        Returns:
            JSON response as dict

        Raises:
            HTTPException: If request fails after retries
        """
        url = f"{self.base_url}{path}"
        headers = await self._get_headers()

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                params=params,
                headers=headers
            )

            # Handle 401 Unauthorized (token expired)
            if response.status_code == 401:
                logger.warning("OAuth token expired, refreshing...")
                oauth = await self._get_oauth_client()
                await oauth.invalidate_token()
                # Retry once with new token
                if retry_count < 1:
                    return await self._request(method, path, params, retry_count + 1)

            # Handle 429 Rate Limit (exponential backoff)
            if response.status_code == 429:
                if retry_count < 3:
                    wait_time = 2 ** retry_count  # 1s, 2s, 4s
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry...")
                    import asyncio
                    await asyncio.sleep(wait_time)
                    return await self._request(method, path, params, retry_count + 1)
                else:
                    logger.error("Rate limit exceeded after 3 retries")

            # Handle 404 Not Found (return None)
            if response.status_code == 404:
                logger.info(f"Resource not found: {path}")
                return None

            # Handle 500 Server Error (log and return None)
            if response.status_code >= 500:
                logger.error(f"Meditech server error: HTTP {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error(f"FHIR API error: HTTP {e.response.status_code} - {path}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"FHIR API request error: {str(e)} - {path}")
            raise

    async def get_patient(self, nhs_number: str) -> Optional[FHIRPatient]:
        """Get patient by NHS number.

        Args:
            nhs_number: 10-digit NHS number

        Returns:
            FHIRPatient if found, None otherwise
        """
        logger.info(f"Fetching patient with NHS number: {nhs_number}")

        # Search for patient by NHS number identifier
        params = {
            "identifier": f"https://fhir.nhs.uk/Id/nhs-number|{nhs_number}"
        }

        response = await self._request("GET", "/Patient", params=params)

        if not response or response.get("total", 0) == 0:
            logger.info(f"No patient found with NHS number: {nhs_number}")
            return None

        # Get first patient from Bundle
        entries = response.get("entry", [])
        if not entries:
            return None

        patient_resource = entries[0].get("resource", {})

        # Convert to FHIRPatient Pydantic model
        return FHIRPatient(**patient_resource)

    async def get_conditions(self, patient_id: str) -> List[FHIRCondition]:
        """Get all conditions for a patient.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            List of FHIRCondition resources
        """
        logger.info(f"Fetching conditions for patient: {patient_id}")

        params = {
            "patient": patient_id,
            "_count": 100  # Max 100 per page
        }

        response = await self._request("GET", "/Condition", params=params)

        if not response:
            return []

        # Extract conditions from Bundle
        entries = response.get("entry", [])
        conditions = []

        for entry in entries:
            condition_resource = entry.get("resource", {})
            try:
                conditions.append(FHIRCondition(**condition_resource))
            except Exception as e:
                logger.warning(f"Failed to parse condition: {str(e)}")

        logger.info(f"Found {len(conditions)} conditions for patient {patient_id}")
        return conditions

    async def get_observations(self, patient_id: str) -> List[FHIRObservation]:
        """Get all observations for a patient.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            List of FHIRObservation resources
        """
        logger.info(f"Fetching observations for patient: {patient_id}")

        params = {
            "patient": patient_id,
            "_count": 100  # Max 100 per page
        }

        response = await self._request("GET", "/Observation", params=params)

        if not response:
            return []

        # Extract observations from Bundle
        entries = response.get("entry", [])
        observations = []

        for entry in entries:
            observation_resource = entry.get("resource", {})
            try:
                observations.append(FHIRObservation(**observation_resource))
            except Exception as e:
                logger.warning(f"Failed to parse observation: {str(e)}")

        logger.info(f"Found {len(observations)} observations for patient {patient_id}")
        return observations

    async def get_medication_requests(self, patient_id: str) -> List[FHIRMedicationRequest]:
        """Get all medication requests for a patient.

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            List of FHIRMedicationRequest resources
        """
        logger.info(f"Fetching medication requests for patient: {patient_id}")

        params = {
            "patient": patient_id,
            "_count": 100  # Max 100 per page
        }

        response = await self._request("GET", "/MedicationRequest", params=params)

        if not response:
            return []

        # Extract medication requests from Bundle
        entries = response.get("entry", [])
        medication_requests = []

        for entry in entries:
            med_request_resource = entry.get("resource", {})
            try:
                medication_requests.append(FHIRMedicationRequest(**med_request_resource))
            except Exception as e:
                logger.warning(f"Failed to parse medication request: {str(e)}")

        logger.info(f"Found {len(medication_requests)} medication requests for patient {patient_id}")
        return medication_requests

    async def get_patient_bundle(self, nhs_number: str) -> Dict[str, Any]:
        """Get all patient data in a single call (Patient + Conditions + Observations + Medications).

        Args:
            nhs_number: 10-digit NHS number

        Returns:
            Dict with keys: patient, conditions, observations, medication_requests
        """
        logger.info(f"Fetching complete patient bundle for NHS number: {nhs_number}")

        # Get patient first
        patient = await self.get_patient(nhs_number)

        if not patient:
            logger.warning(f"Patient not found: {nhs_number}")
            return {
                "patient": None,
                "conditions": [],
                "observations": [],
                "medication_requests": []
            }

        patient_id = patient.id

        # Fetch all resources concurrently
        import asyncio
        conditions, observations, medication_requests = await asyncio.gather(
            self.get_conditions(patient_id),
            self.get_observations(patient_id),
            self.get_medication_requests(patient_id),
            return_exceptions=True  # Don't fail if one resource fails
        )

        # Handle exceptions
        if isinstance(conditions, Exception):
            logger.error(f"Failed to fetch conditions: {str(conditions)}")
            conditions = []
        if isinstance(observations, Exception):
            logger.error(f"Failed to fetch observations: {str(observations)}")
            observations = []
        if isinstance(medication_requests, Exception):
            logger.error(f"Failed to fetch medication requests: {str(medication_requests)}")
            medication_requests = []

        return {
            "patient": patient,
            "conditions": conditions,
            "observations": observations,
            "medication_requests": medication_requests
        }

    async def close(self) -> None:
        """Close HTTP client connection."""
        await self.http_client.aclose()


# Global FHIR client instance
_fhir_client: Optional[MeditechFHIRClient] = None


async def get_fhir_client() -> MeditechFHIRClient:
    """Get global FHIR client instance (singleton pattern).

    Returns:
        MeditechFHIRClient instance
    """
    global _fhir_client
    if _fhir_client is None:
        _fhir_client = MeditechFHIRClient()
    return _fhir_client
