"""Break-Glass schemas for emergency PHI access.

Pydantic models for break-glass workflow operations.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BreakGlassRequest(BaseModel):
    """Request for break-glass emergency access."""

    patient_id: Optional[str] = Field(None, description="Patient ID for access (optional)")
    resource_type: str = Field(description="Type of resource being accessed")
    resource_id: Optional[str] = Field(None, description="Specific resource ID (optional)")
    justification: str = Field(min_length=20, description="Reason for emergency access (min 20 chars)")


class BreakGlassResponse(BaseModel):
    """Response after granting break-glass access."""

    access_granted: bool
    break_glass_id: UUID
    user_id: UUID
    username: str
    timestamp: datetime
    justification: str
    expires_at: datetime = Field(description="When this emergency access expires (24h)")
    resource_type: str
    resource_id: Optional[str]
    message: str = Field(description="Instructions or warnings for the user")


class BreakGlassLogEntry(BaseModel):
    """Break-glass audit log entry."""

    id: UUID
    user_id: UUID
    username: str
    patient_id: Optional[str]
    resource_type: str
    resource_id: Optional[str]
    justification: str
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]

    model_config = {"from_attributes": True}


class BreakGlassLogListResponse(BaseModel):
    """Paginated list of break-glass audit logs."""

    items: List[BreakGlassLogEntry]
    total: int
    page: int
    page_size: int
    total_pages: int
