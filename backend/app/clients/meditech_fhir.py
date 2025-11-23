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

    async def _request_full_url(
        self,
        method: str,
        url: str,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make HTTP request to full URL (for pagination links).

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Full URL (including base URL)
            retry_count: Current retry attempt

        Returns:
            JSON response as dict
        """
        headers = await self._get_headers()

        try:
            response = await self.http_client.request(
                method=method,
                url=url,
                headers=headers
            )

            # Handle 401 Unauthorized (token expired)
            if response.status_code == 401:
                logger.warning("OAuth token expired, refreshing...")
                oauth = await self._get_oauth_client()
                await oauth.invalidate_token()
                if retry_count < 1:
                    return await self._request_full_url(method, url, retry_count + 1)

            # Handle 429 Rate Limit (exponential backoff)
            if response.status_code == 429:
                if retry_count < 3:
                    wait_time = 2 ** retry_count  # 1s, 2s, 4s
                    logger.warning(f"Rate limited, waiting {wait_time}s before retry...")
                    import asyncio
                    await asyncio.sleep(wait_time)
                    return await self._request_full_url(method, url, retry_count + 1)

            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"FHIR API request error: {str(e)} - {url}")
            raise

    def _get_next_link(self, bundle: Dict[str, Any]) -> Optional[str]:
        """Extract next link from FHIR Bundle for pagination.

        Args:
            bundle: FHIR Bundle response

        Returns:
            Next link URL if found, None otherwise
        """
        if not bundle or "link" not in bundle:
            return None

        for link in bundle["link"]:
            if link.get("relation") == "next":
                return link.get("url")

        return None

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

    async def get_conditions(
        self,
        patient_id: str,
        code: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        follow_pagination: bool = True
    ) -> List[FHIRCondition]:
        """Get all conditions for a patient with optional filtering.

        Args:
            patient_id: FHIR Patient resource ID
            code: Optional ICD-10 or SNOMED CT code to filter by
            date_from: Optional start date (ISO format: YYYY-MM-DD)
            date_to: Optional end date (ISO format: YYYY-MM-DD)
            follow_pagination: If True, automatically follow pagination links to get all results

        Returns:
            List of FHIRCondition resources

        Example:
            # Get all diabetes conditions
            conditions = await client.get_conditions(
                patient_id="123",
                code="E11",
                date_from="2023-01-01"
            )
        """
        logger.info(f"Fetching conditions for patient: {patient_id}")

        params = {
            "patient": patient_id,
            "_count": 100  # Max 100 per page
        }

        # Add optional filters
        if code:
            params["code"] = code
        if date_from and date_to:
            params["date"] = f"ge{date_from}&date=le{date_to}"
        elif date_from:
            params["date"] = f"ge{date_from}"
        elif date_to:
            params["date"] = f"le{date_to}"

        response = await self._request("GET", "/Condition", params=params)

        if not response:
            return []

        # Extract conditions from Bundle
        conditions = []
        entries = response.get("entry", [])

        for entry in entries:
            condition_resource = entry.get("resource", {})
            try:
                conditions.append(FHIRCondition(**condition_resource))
            except Exception as e:
                logger.warning(f"Failed to parse condition: {str(e)}")

        # Follow pagination links if enabled
        if follow_pagination:
            next_url = self._get_next_link(response)
            while next_url:
                logger.debug(f"Following pagination link: {next_url}")
                response = await self._request_full_url("GET", next_url)

                if not response:
                    break

                entries = response.get("entry", [])
                for entry in entries:
                    condition_resource = entry.get("resource", {})
                    try:
                        conditions.append(FHIRCondition(**condition_resource))
                    except Exception as e:
                        logger.warning(f"Failed to parse condition: {str(e)}")

                next_url = self._get_next_link(response)

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

    async def get_patient_bundle_via_everything(self, patient_id: str) -> Dict[str, Any]:
        """Get all patient data using FHIR $everything operation (single API call).

        This is more efficient than 4 separate API calls (Patient + Conditions + Observations + Medications).

        Args:
            patient_id: FHIR Patient resource ID

        Returns:
            Dict with keys: patient, conditions, observations, medication_requests

        Example:
            bundle = await client.get_patient_bundle_via_everything("patient-123")
            patient = bundle["patient"]
            conditions = bundle["conditions"]
        """
        logger.info(f"Fetching patient bundle via $everything for patient: {patient_id}")

        # Use FHIR $everything operation to get all patient data in single call
        response = await self._request("GET", f"/Patient/{patient_id}/$everything", params={})

        if not response:
            logger.warning(f"No data returned from $everything for patient: {patient_id}")
            return {
                "patient": None,
                "conditions": [],
                "observations": [],
                "medication_requests": []
            }

        # Parse Bundle and separate by resource type
        patient = None
        conditions = []
        observations = []
        medication_requests = []

        entries = response.get("entry", [])

        for entry in entries:
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            try:
                if resource_type == "Patient":
                    patient = FHIRPatient(**resource)
                elif resource_type == "Condition":
                    conditions.append(FHIRCondition(**resource))
                elif resource_type == "Observation":
                    observations.append(FHIRObservation(**resource))
                elif resource_type == "MedicationRequest":
                    medication_requests.append(FHIRMedicationRequest(**resource))
            except Exception as e:
                logger.warning(f"Failed to parse {resource_type}: {str(e)}")

        logger.info(
            f"$everything returned: Patient={patient is not None}, "
            f"Conditions={len(conditions)}, Observations={len(observations)}, "
            f"MedicationRequests={len(medication_requests)}"
        )

        return {
            "patient": patient,
            "conditions": conditions,
            "observations": observations,
            "medication_requests": medication_requests
        }

    async def get_patient_bundle(
        self,
        nhs_number: str,
        use_everything: bool = False
    ) -> Dict[str, Any]:
        """Get all patient data (Patient + Conditions + Observations + Medications).

        Args:
            nhs_number: 10-digit NHS number
            use_everything: If True, use FHIR $everything operation (single API call).
                           If False, use separate API calls (concurrent).

        Returns:
            Dict with keys: patient, conditions, observations, medication_requests

        Example:
            # Using $everything (1 API call)
            bundle = await client.get_patient_bundle("1234567881", use_everything=True)

            # Using separate calls (4 concurrent API calls)
            bundle = await client.get_patient_bundle("1234567881", use_everything=False)
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

        # Use $everything operation if requested
        if use_everything:
            return await self.get_patient_bundle_via_everything(patient_id)

        # Otherwise, fetch all resources concurrently (4 API calls)
        import asyncio
        conditions, observations, medication_requests = await asyncio.gather(
            self.get_conditions(patient_id, follow_pagination=True),
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
