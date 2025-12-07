"""Event Bus Schemas (Sprint 5.5)"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Event types published to event bus"""
    # Document events
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"

    # Patient events
    PATIENT_CREATED = "patient.created"
    PATIENT_UPDATED = "patient.updated"

    # Coding events
    CODES_ASSIGNED = "coding.assigned"
    CODING_REVIEWED = "coding.reviewed"

    # De-identification events
    DOCUMENT_DEIDENTIFIED = "deidentification.completed"

    # Search events
    SEARCH_PERFORMED = "search.performed"

    # Alert events
    ALERT_TRIGGERED = "alert.triggered"
    ALERT_ACKNOWLEDGED = "alert.acknowledged"

    # CDS events
    CDS_RECOMMENDATION = "cds.recommendation"


class Event(BaseModel):
    """Base event model"""
    event_id: UUID = Field(..., description="Unique event ID")
    event_type: EventType = Field(..., description="Event type")
    timestamp: datetime = Field(..., description="Event timestamp (ISO format)")
    source: str = Field(..., description="Event source (service/module name)")
    user_id: Optional[UUID] = Field(None, description="User who triggered event (if applicable)")
    correlation_id: Optional[UUID] = Field(None, description="Correlation ID for tracing")
    payload: Dict[str, Any] = Field(..., description="Event-specific data")

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "document.created",
                "timestamp": "2023-11-18T10:30:00Z",
                "source": "document-service",
                "user_id": "789abcde-f012-3456-7890-abcdef012345",
                "correlation_id": "111e2222-a33b-44c5-d666-777788889999",
                "payload": {
                    "document_id": "doc-123",
                    "patient_id": "patient-456",
                    "document_type": "discharge_summary"
                }
            }
        }


class DocumentCreatedEvent(Event):
    """Document created event"""
    event_type: EventType = EventType.DOCUMENT_CREATED

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "document.created",
                "timestamp": "2023-11-18T10:30:00Z",
                "source": "document-service",
                "user_id": "789abcde-f012-3456-7890-abcdef012345",
                "payload": {
                    "document_id": "doc-123",
                    "patient_id": "patient-456",
                    "document_type": "discharge_summary",
                    "title": "Discharge Summary - 2023-11-17"
                }
            }
        }


class CodesAssignedEvent(Event):
    """Codes assigned event"""
    event_type: EventType = EventType.CODES_ASSIGNED

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "coding.assigned",
                "timestamp": "2023-11-18T10:30:00Z",
                "source": "coding-service",
                "user_id": "789abcde-f012-3456-7890-abcdef012345",
                "payload": {
                    "document_id": "doc-123",
                    "codes": ["E11.9", "I10"],
                    "coder_id": "user-123"
                }
            }
        }


class AlertTriggeredEvent(Event):
    """Alert triggered event"""
    event_type: EventType = EventType.ALERT_TRIGGERED

    class Config:
        json_schema_extra = {
            "example": {
                "event_id": "123e4567-e89b-12d3-a456-426614174000",
                "event_type": "alert.triggered",
                "timestamp": "2023-11-18T10:30:00Z",
                "source": "alerting-service",
                "payload": {
                    "alert_id": "alert-123",
                    "alert_type": "critical_finding",
                    "patient_id": "patient-456",
                    "severity": "high",
                    "message": "Critical lab result detected"
                }
            }
        }
