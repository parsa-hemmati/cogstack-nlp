"""
Pydantic schemas for data retention policies.

Defines request/response models for retention management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class RetentionPolicyResponse(BaseModel):
    """Data retention policy details."""

    id: str = Field(
        ...,
        description="Policy ID"
    )
    data_type: str = Field(
        ...,
        description="Type of data: clinical_documents, audit_logs, session_data, temp_files, research_data"
    )
    retention_years: Optional[int] = Field(
        None,
        description="Retention period in years"
    )
    retention_days: Optional[int] = Field(
        None,
        description="Retention period in days"
    )
    retention_description: str = Field(
        ...,
        description="Human-readable description"
    )
    is_active: bool = Field(
        ...,
        description="Whether policy is active"
    )
    archive_enabled: bool = Field(
        ...,
        description="Whether to archive before delete"
    )
    records_archived_count: int = Field(
        ...,
        description="Total records archived"
    )
    records_deleted_count: int = Field(
        ...,
        description="Total records deleted"
    )
    last_executed_at: Optional[datetime] = Field(
        None,
        description="When retention job last ran"
    )
    next_execution_at: Optional[datetime] = Field(
        None,
        description="When retention job should run next"
    )

    class Config:
        from_attributes = True


class RetentionReport(BaseModel):
    """Data retention compliance report."""

    generated_at: datetime = Field(
        ...,
        description="When report was generated"
    )
    period: Dict[str, str] = Field(
        ...,
        description="Report period (start, end)"
    )
    policies: List[Dict[str, Any]] = Field(
        ...,
        description="Policy statistics"
    )
    totals: Dict[str, int] = Field(
        ...,
        description="Overall totals (archived, deleted, failed)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "generated_at": "2024-01-15T10:30:00Z",
                "period": {
                    "start": "2023-12-16T10:30:00Z",
                    "end": "2024-01-15T10:30:00Z"
                },
                "policies": [
                    {
                        "data_type": "audit_logs",
                        "retention": "7 years",
                        "archived": 1000,
                        "deleted": 500,
                        "failed": 0
                    }
                ],
                "totals": {
                    "archived": 2000,
                    "deleted": 1500,
                    "failed": 10
                }
            }
        }


class DueForDeletion(BaseModel):
    """Record due for deletion."""

    id: str = Field(
        ...,
        description="Record ID"
    )
    resource_type: str = Field(
        ...,
        description="Type of resource"
    )
    resource_id: str = Field(
        ...,
        description="ID of resource"
    )
    data_type: str = Field(
        ...,
        description="Data type according to retention policy"
    )
    created_at: datetime = Field(
        ...,
        description="When resource was created"
    )
    will_delete_at: datetime = Field(
        ...,
        description="When resource will be deleted"
    )
    days_remaining: int = Field(
        ...,
        description="Days until deletion"
    )

    class Config:
        from_attributes = True


class RetentionList(BaseModel):
    """List of items due for deletion."""

    total: int = Field(
        ...,
        description="Total items due for deletion"
    )
    limit: int = Field(
        ...,
        description="Limit of results returned"
    )
    offset: int = Field(
        ...,
        description="Pagination offset"
    )
    items: List[DueForDeletion] = Field(
        ...,
        description="Items due for deletion"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total": 150,
                "limit": 20,
                "offset": 0,
                "items": []
            }
        }


class RetentionPoliciesList(BaseModel):
    """List of retention policies."""

    total: int = Field(
        ...,
        description="Total policies"
    )
    policies: List[RetentionPolicyResponse] = Field(
        ...,
        description="List of policies"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "policies": []
            }
        }
