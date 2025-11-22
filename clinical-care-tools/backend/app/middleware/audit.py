"""
Audit Logging Middleware

HIPAA/GDPR compliant audit logging for all API requests.
Tracks who accessed what data, when, and from where.
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from app.config import settings

# Configure structured logger for audit logs
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs if enabled
if settings.AUDIT_LOG_ENABLED and settings.AUDIT_LOG_FILE:
    from logging.handlers import RotatingFileHandler

    handler = RotatingFileHandler(
        settings.AUDIT_LOG_FILE,
        maxBytes=settings.AUDIT_LOG_MAX_BYTES,
        backupCount=settings.AUDIT_LOG_BACKUP_COUNT
    )
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(message)s')
    )
    audit_logger.addHandler(handler)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive audit logging of all requests.

    Captures request details, response status, timing, and user information
    for compliance with HIPAA and GDPR requirements.
    """

    # Paths to exclude from audit logging (e.g., health checks)
    EXCLUDED_PATHS = {
        "/",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/health",
        "/api/metrics",
    }

    # Sensitive headers to redact in logs
    SENSITIVE_HEADERS = {
        "authorization",
        "x-api-key",
        "cookie",
        "set-cookie",
    }

    # PHI/PII related endpoints that require enhanced logging
    PHI_ENDPOINTS = {
        "/api/v1/patients",
        "/api/v1/documents",
        "/api/v1/extracted-entities",
    }

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Process the request and log audit information.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint handler.

        Returns:
            Response: The response from the endpoint.
        """
        # Skip logging for excluded paths
        if request.url.path in self.EXCLUDED_PATHS:
            return await call_next(request)

        # Generate audit entry ID
        audit_id = str(uuid4())
        request.state.audit_id = audit_id

        # Capture start time
        start_time = time.time()

        # Extract request information
        audit_entry = await self._create_audit_entry(request, audit_id, start_time)

        # Store original response for potential modification
        response = None

        try:
            # Process the request
            response = await call_next(request)

            # Capture response information
            await self._add_response_info(audit_entry, response, start_time)

            # Log the audit entry
            self._log_audit_entry(audit_entry)

            # Add audit ID to response headers for tracing
            response.headers["X-Audit-ID"] = audit_id

            return response

        except Exception as e:
            # Log error in audit trail
            audit_entry["error"] = {
                "type": type(e).__name__,
                "message": str(e),
            }
            audit_entry["response_status"] = 500
            audit_entry["duration_ms"] = int((time.time() - start_time) * 1000)

            self._log_audit_entry(audit_entry)
            raise

    async def _create_audit_entry(
        self,
        request: Request,
        audit_id: str,
        start_time: float
    ) -> Dict[str, Any]:
        """
        Create the initial audit log entry.

        Args:
            request: The incoming request.
            audit_id: Unique identifier for this audit entry.
            start_time: Request start timestamp.

        Returns:
            Dict containing audit information.
        """
        # Get user information if authenticated
        user_info = await self._get_user_info(request)

        # Check if this is a PHI-related endpoint
        is_phi_access = any(
            request.url.path.startswith(endpoint)
            for endpoint in self.PHI_ENDPOINTS
        )

        entry = {
            "audit_id": audit_id,
            "timestamp": datetime.utcnow().isoformat(),
            "request": {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params) if request.query_params else {},
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_id": request.headers.get("x-request-id"),
            },
            "user": user_info,
            "is_phi_access": is_phi_access,
            "environment": settings.APP_ENV,
        }

        # Add sanitized headers (exclude sensitive ones)
        entry["request"]["headers"] = self._sanitize_headers(dict(request.headers))

        # For PHI endpoints, add additional tracking
        if is_phi_access and settings.AUDIT_ALL_PHI_ACCESS:
            entry["phi_access"] = {
                "endpoint_type": self._classify_phi_endpoint(request.url.path),
                "compliance_mode": {
                    "hipaa": settings.HIPAA_COMPLIANCE_MODE,
                    "gdpr": settings.GDPR_COMPLIANCE_MODE,
                }
            }

        return entry

    async def _add_response_info(
        self,
        audit_entry: Dict[str, Any],
        response: Response,
        start_time: float
    ) -> None:
        """
        Add response information to the audit entry.

        Args:
            audit_entry: The audit log entry to update.
            response: The response object.
            start_time: Request start timestamp.
        """
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        audit_entry["response"] = {
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }

        # Add performance warning if request took too long
        if duration_ms > 5000:  # 5 seconds
            audit_entry["performance_warning"] = f"Slow request: {duration_ms}ms"

        # Track successful vs failed PHI access
        if audit_entry.get("is_phi_access"):
            audit_entry["phi_access"]["success"] = response.status_code < 400

    async def _get_user_info(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract user information from the request.

        Args:
            request: The incoming request.

        Returns:
            Dict containing user information, or None if not authenticated.
        """
        # Check if user is set in request state (by auth dependency)
        if hasattr(request.state, "user"):
            user = request.state.user
            return {
                "id": str(user.get("id")),
                "email": user.get("email"),
                "role": user.get("role"),
                "authenticated": True,
            }

        # Try to decode JWT from Authorization header
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from jose import jwt
                token = auth_header[7:]
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_signature": False}  # Just for user info
                )
                return {
                    "id": payload.get("sub"),
                    "email": payload.get("email"),
                    "role": payload.get("role"),
                    "authenticated": True,
                }
            except Exception:
                pass

        return {"authenticated": False}

    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """
        Remove or redact sensitive headers.

        Args:
            headers: Original headers dictionary.

        Returns:
            Sanitized headers dictionary.
        """
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.SENSITIVE_HEADERS:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def _classify_phi_endpoint(self, path: str) -> str:
        """
        Classify the type of PHI access based on endpoint.

        Args:
            path: The request path.

        Returns:
            Classification string.
        """
        if "/patients" in path:
            if "/search" in path:
                return "patient_search"
            elif "/timeline" in path:
                return "patient_timeline"
            else:
                return "patient_data"
        elif "/documents" in path:
            return "clinical_documents"
        elif "/extracted-entities" in path:
            return "nlp_results"
        else:
            return "unknown_phi"

    def _log_audit_entry(self, entry: Dict[str, Any]) -> None:
        """
        Log the audit entry to the configured audit logger.

        Args:
            entry: The audit log entry.
        """
        # Convert to JSON string for structured logging
        audit_logger.info(json.dumps(entry))

        # If in development mode, also log to console
        if settings.DEBUG:
            import pprint
            print("\n=== AUDIT LOG ===")
            pprint.pprint(entry)
            print("================\n")

        # NOTE: Also save to database audit_logs table for persistence
        # This would be done asynchronously to avoid blocking the request
        # Example:
        # asyncio.create_task(self._save_to_database(entry))