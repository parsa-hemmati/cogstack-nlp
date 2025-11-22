"""
Security Headers Middleware

Adds security headers to all responses for protection against
common web vulnerabilities (XSS, clickjacking, etc.).
"""

from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements security best practices including:
    - Content Security Policy (CSP)
    - X-Frame-Options
    - X-Content-Type-Options
    - Strict-Transport-Security (HSTS)
    - X-XSS-Protection
    - Referrer-Policy
    - Permissions-Policy
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        """
        Add security headers to the response.

        Args:
            request: The incoming request.
            call_next: The next middleware or endpoint handler.

        Returns:
            Response with security headers added.
        """
        # Process the request
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response)

        return response

    def _add_security_headers(self, response: Response) -> None:
        """
        Add security headers to the response.

        Args:
            response: The response object to modify.
        """
        # Content Security Policy - Restrict resource loading
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Required for some frontend frameworks
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

        # In development, relax CSP for hot reload
        if settings.DEBUG:
            csp_directives = [
                "default-src *",
                "script-src * 'unsafe-inline' 'unsafe-eval'",
                "style-src * 'unsafe-inline'",
            ]

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enable HSTS in production
        if settings.APP_ENV == "production":
            # Strict Transport Security - Force HTTPS for 1 year
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Enable XSS protection (for older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (Feature Policy replacement)
        permissions = [
            "accelerometer=()",
            "camera=()",
            "geolocation=()",
            "gyroscope=()",
            "magnetometer=()",
            "microphone=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions)

        # Add custom security headers for healthcare compliance
        if settings.HIPAA_COMPLIANCE_MODE:
            # Indicate HIPAA compliance mode is active
            response.headers["X-Healthcare-Compliance"] = "HIPAA"

        if settings.GDPR_COMPLIANCE_MODE:
            # Indicate GDPR compliance mode is active
            if "X-Healthcare-Compliance" in response.headers:
                response.headers["X-Healthcare-Compliance"] += ", GDPR"
            else:
                response.headers["X-Healthcare-Compliance"] = "GDPR"

        # Add application version header (useful for debugging)
        response.headers["X-App-Version"] = settings.APP_VERSION

        # Remove sensitive headers that might leak information
        headers_to_remove = ["Server", "X-Powered-By"]
        for header in headers_to_remove:
            if header in response.headers:
                del response.headers[header]


def get_security_headers() -> dict:
    """
    Get security headers as a dictionary.

    Returns:
        dict: Security headers.
    """
    headers = {
        "X-Frame-Options": "DENY",
        "X-Content-Type-Options": "nosniff",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
    }

    # Add HSTS in production
    if settings.APP_ENV == "production":
        headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

    # Add compliance headers
    compliance = []
    if settings.HIPAA_COMPLIANCE_MODE:
        compliance.append("HIPAA")
    if settings.GDPR_COMPLIANCE_MODE:
        compliance.append("GDPR")
    if compliance:
        headers["X-Healthcare-Compliance"] = ", ".join(compliance)

    return headers