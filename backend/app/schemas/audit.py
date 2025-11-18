"""Audit log schemas for API.

Pydantic models for audit log viewing operations.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AuditLogEntry(BaseModel):
    """Audit log entry."""

    id: UUID
    user_id: UUID
    username: str
    action: str
    resource_type: str
    resource_id: Optional[str]
    details: Optional[Dict[str, Any]]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: str  # "success", "failure"
    error_message: Optional[str]

    model_config = {"from_attributes": True}


class AuditLogListResponse(BaseModel):
    """Paginated list of audit logs."""

    items: List[AuditLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int
