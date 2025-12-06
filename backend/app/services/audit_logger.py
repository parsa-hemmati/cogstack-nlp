"""
Audit Logger Module
Provides a singleton instance of AuditService for easy import and use.
"""
from app.services.audit_service import AuditService

# Export singleton instance for convenience
audit_logger = AuditService()
