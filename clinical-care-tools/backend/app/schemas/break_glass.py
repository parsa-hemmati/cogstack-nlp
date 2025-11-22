"""
Pydantic schemas for break-glass emergency access.

Defines request/response models for emergency patient data access.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class BreakGlassRequest(BaseModel):
    """Request for emergency access to patient data."""

    patient_id: str = Field(
        ...,
        description="Patient ID needing emergency access"
    )
    justification: str = Field(
        ...,
        min_length=10,
        description="Clinical reason for emergency access (required by HIPAA, min 10 chars)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "patient_id": "patient-123",
                "justification": "Emergency: Patient in critical condition, need immediate access to medication history"
            }
        }


class BreakGlassResponse(BaseModel):
    """Response with break-glass access details."""

    id: str = Field(
        ...,
        description="Break-glass request ID"
    )
    user_id: str = Field(
        ...,
        description="Clinician who requested access"
    )
    patient_id: str = Field(
        ...,
        description="Patient ID"
    )
    status: str = Field(
        ...,
        description="Request status: pending/approved/denied/revoked/expired"
    )
    justification: str = Field(
        ...,
        description="Clinical justification"
    )
    created_at: datetime = Field(
        ...,
        description="When request was created"
    )
    access_granted_at: Optional[datetime] = Field(
        None,
        description="When access was approved"
    )
    access_expires_at: Optional[datetime] = Field(
        None,
        description="When access window expires"
    )
    accessed_at: Optional[datetime] = Field(
        None,
        description="When data was accessed"
    )
    reviewed_by: Optional[str] = Field(
        None,
        description="Security team member who reviewed"
    )
    reviewed_at: Optional[datetime] = Field(
        None,
        description="When reviewed (must be within 24 hours)"
    )
    review_notes: Optional[str] = Field(
        None,
        description="Security team notes"
    )

    class Config:
        from_attributes = True


class BreakGlassReview(BaseModel):
    """Security team review of break-glass request."""

    decision: str = Field(
        ...,
        pattern="^(approve|deny)$",
        description="Approval decision: approve or deny"
    )
    notes: Optional[str] = Field(
        None,
        description="Optional notes on review decision"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "decision": "approve",
                "notes": "Approved: Clinician verified as treating physician"
            }
        }


class BreakGlassRevoke(BaseModel):
    """Request to revoke break-glass access."""

    reason: Optional[str] = Field(
        None,
        description="Reason for revocation"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "reason": "Emergency situation resolved, access no longer needed"
            }
        }


class BreakGlassList(BaseModel):
    """List of break-glass access requests."""

    total: int = Field(
        ...,
        description="Total number of requests"
    )
    limit: int = Field(
        ...,
        description="Limit of results returned"
    )
    offset: int = Field(
        ...,
        description="Pagination offset"
    )
    requests: list[BreakGlassResponse] = Field(
        ...,
        description="List of break-glass requests"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "limit": 20,
                "offset": 0,
                "requests": []
            }
        }
