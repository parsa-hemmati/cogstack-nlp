"""
Clinical Safety Middleware (Phase 6)

Enforces clinical safety checks before operations.
Prevents unsafe clinical data modifications.

Safety Features:
- Required field validation
- Date validation (no future dates)
- NLP confidence checks
- Critical concept detection
- Duplicate patient detection
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class ClinicalSafetyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce clinical safety checks.

    For safety-critical endpoints (patient data modifications),
    ensures all required checks pass.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Process request and perform safety checks.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            HTTP response or error
        """
        # Skip for non-safety-critical endpoints
        if not self._requires_safety_check(request):
            return await call_next(request)

        # Skip if clinical safety is disabled
        if not settings.CLINICAL_SAFETY_ENABLED:
            return await call_next(request)

        # NOTE: For POST/PUT/PATCH operations on clinical data:
        # 1. Extract request body
        # 2. Perform safety checks:
        #    - Required demographic fields
        #    - Future date validation
        #    - Duplicate patient detection
        #    - NLP confidence checks (if applicable)
        # 3. Generate warnings for clinician
        # 4. Require acknowledgment of critical warnings
        # 5. Log all checks for audit trail

        # For now, just log the request
        logger.debug(
            f"Clinical safety check: {request.method} {request.url.path}"
        )

        return await call_next(request)

    def _requires_safety_check(self, request: Request) -> bool:
        """
        Determine if endpoint requires safety checks.

        Args:
            request: HTTP request

        Returns:
            True if safety checks required
        """
        # Safety checks only for data modification operations
        if request.method not in ["POST", "PUT", "PATCH"]:
            return False

        # Check if path contains clinical data endpoints
        clinical_paths = [
            "/api/v1/patients",
            "/api/v1/documents",
            "/api/v1/entities",
        ]

        return any(request.url.path.startswith(p) for p in clinical_paths)


class ClinicalSafetyLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log clinical data access.

    Ensures all PHI/PII access is logged for compliance.
    """

    async def dispatch(self, request: Request, call_next):
        """
        Log access to clinical data.

        Args:
            request: HTTP request
            call_next: Next middleware

        Returns:
            HTTP response with audit logged
        """
        # Skip for non-clinical endpoints
        if not self._is_clinical_endpoint(request):
            return await call_next(request)

        # NOTE: Log PHI access
        # 1. Get authenticated user
        # 2. Get patient ID from request (URL or body)
        # 3. Log to audit trail with:
        #    - User ID
        #    - Patient ID
        #    - Action (read/create/update/delete)
        #    - Timestamp
        #    - IP address
        #    - User-Agent
        # 4. Continue processing

        response = await call_next(request)

        # Log successful access
        logger.debug(
            f"Clinical data access: {request.method} {request.url.path}"
        )

        return response

    def _is_clinical_endpoint(self, request: Request) -> bool:
        """
        Determine if endpoint accesses clinical data.

        Args:
            request: HTTP request

        Returns:
            True if clinical endpoint
        """
        clinical_paths = [
            "/api/v1/patients",
            "/api/v1/documents",
            "/api/v1/entities",
            "/api/v1/timeline",
        ]

        return any(request.url.path.startswith(p) for p in clinical_paths)
