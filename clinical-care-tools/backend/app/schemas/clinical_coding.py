"""Clinical Coding Schemas (Sprint 5)"""

from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class CodeSource(str, Enum):
    """Source of ICD-10 code assignment"""
    AI = "ai"  # AI-suggested (from NER model)
    MANUAL = "manual"  # Manually added by coder
    APPROVED = "approved"  # AI suggestion approved by coder


class ICD10Code(BaseModel):
    """ICD-10-CM code reference"""
    code: str = Field(..., description="ICD-10-CM code (e.g., E11.9)")
    description: str = Field(..., description="Code description")
    category: Optional[str] = Field(None, description="Category (e.g., 'E08-E13: Diabetes mellitus')")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "E11.9",
                "description": "Type 2 diabetes mellitus without complications",
                "category": "E08-E13: Diabetes mellitus"
            }
        }


class ICD10SuggestedCode(ICD10Code):
    """AI-suggested ICD-10 code with evidence"""
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence: str = Field(..., description="Text evidence from document")
    position: int = Field(..., ge=0, description="Character position in document")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "E11.9",
                "description": "Type 2 diabetes mellitus without complications",
                "category": "E08-E13: Diabetes mellitus",
                "confidence": 0.95,
                "evidence": "Patient has Type 2 Diabetes Mellitus.",
                "position": 120
            }
        }


class CodingSuggestionsResponse(BaseModel):
    """AI coding suggestions for document"""
    document_id: UUID = Field(..., description="Document ID")
    suggestions: List[ICD10SuggestedCode] = Field(default_factory=list, description="AI-suggested codes")
    total_suggestions: int = Field(..., ge=0, description="Total suggestions")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "suggestions": [
                    {
                        "code": "E11.9",
                        "description": "Type 2 diabetes mellitus without complications",
                        "confidence": 0.95,
                        "evidence": "Patient has Type 2 Diabetes Mellitus.",
                        "position": 120
                    }
                ],
                "total_suggestions": 1
            }
        }


class CodeAssignment(BaseModel):
    """Code assignment for document"""
    code: str = Field(..., max_length=10, description="ICD-10-CM code")
    is_primary: bool = Field(False, description="Is this the primary diagnosis code?")
    source: CodeSource = Field(..., description="Source of code assignment")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "E11.9",
                "is_primary": True,
                "source": "ai"
            }
        }


class AssignCodesRequest(BaseModel):
    """Request to assign codes to document"""
    codes: List[CodeAssignment] = Field(..., min_length=1, description="Codes to assign")

    class Config:
        json_schema_extra = {
            "example": {
                "codes": [
                    {"code": "E11.9", "is_primary": True, "source": "ai"},
                    {"code": "I10", "is_primary": False, "source": "ai"}
                ]
            }
        }


class AssignCodesResponse(BaseModel):
    """Response from code assignment"""
    document_id: UUID = Field(..., description="Document ID")
    codes_assigned: int = Field(..., ge=0, description="Number of codes assigned")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    audit_log_id: UUID = Field(..., description="Audit log entry ID")

    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "codes_assigned": 2,
                "validation_errors": [],
                "audit_log_id": "789abcde-f012-3456-7890-abcdef012345"
            }
        }


class ICD10SearchRequest(BaseModel):
    """Search ICD-10 library"""
    q: str = Field(..., min_length=1, description="Search query")
    limit: int = Field(10, ge=1, le=100, description="Max results")


class ICD10SearchResponse(BaseModel):
    """Search results"""
    results: List[ICD10Code] = Field(default_factory=list, description="Matching codes")
    total: int = Field(..., ge=0, description="Total results")


class CodingQueueDocument(BaseModel):
    """Document in coding queue"""
    document_id: UUID = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    patient_id: UUID = Field(..., description="Patient ID")
    date: str = Field(..., description="Document date (ISO format)")
    status: str = Field(..., description="Coding status: uncoded, in_progress, coded")


class CodingQueueResponse(BaseModel):
    """Coding queue"""
    uncoded: List[CodingQueueDocument] = Field(default_factory=list, description="Uncoded documents")
    in_progress: List[CodingQueueDocument] = Field(default_factory=list, description="In-progress documents")
    coded: List[CodingQueueDocument] = Field(default_factory=list, description="Coded documents")
    total: int = Field(..., ge=0, description="Total documents")
