"""
Middleware Package

Custom middleware for the Clinical Care Tools application.
Includes audit logging, CORS, and security headers.
"""

from app.middleware.audit import AuditLogMiddleware
from app.middleware.security import SecurityHeadersMiddleware

__all__ = [
    "AuditLogMiddleware",
    "SecurityHeadersMiddleware",
]