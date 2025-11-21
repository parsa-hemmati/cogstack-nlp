"""
PHI Entity Schema.

Pydantic models for PHI (Protected Health Information) entities
detected by MedCAT de-identification model.
"""
from typing import Optional
from pydantic import BaseModel, Field


class PHIEntity(BaseModel):
    """
    PHI entity detected in clinical text.

    Represents one of the 18 HIPAA Safe Harbor identifiers found in clinical notes.

    Attributes:
        entity_type: PHI category (NAME, DATE, PHONE, etc.)
        text: Actual PHI text found in document
        start: Character offset start position
        end: Character offset end position
        confidence: Detection confidence score (0.0 - 1.0)
        cui: UMLS CUI if applicable (optional for PHI)

    Example:
        >>> entity = PHIEntity(
        >>>     entity_type="NAME",
        >>>     text="John Smith",
        >>>     start=8,
        >>>     end=18,
        >>>     confidence=0.95
        >>> )
    """

    entity_type: str = Field(
        ...,
        description="PHI category (NAME, DATE, PHONE, EMAIL, SSN, MRN, etc.)"
    )
    text: str = Field(
        ...,
        description="Actual PHI text extracted from document"
    )
    start: int = Field(
        ...,
        ge=0,
        description="Character offset start position"
    )
    end: int = Field(
        ...,
        gt=0,
        description="Character offset end position"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score (0.0 - 1.0)"
    )
    cui: Optional[str] = Field(
        default=None,
        description="UMLS Concept Unique Identifier (if applicable)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "NAME",
                "text": "John Smith",
                "start": 8,
                "end": 18,
                "confidence": 0.95,
                "cui": None
            }
        }


class ModelInfo(BaseModel):
    """
    Information about the PHI detection model.

    Attributes:
        model_name: Name of the MedCAT model
        model_version: Model version string
        supported_phi_types: List of PHI entity types this model can detect

    Example:
        >>> info = ModelInfo(
        >>>     model_name="medcat_deid",
        >>>     model_version="1.0.0",
        >>>     supported_phi_types=["NAME", "DATE", "PHONE", ...]
        >>> )
    """

    model_name: str = Field(
        ...,
        description="Name of the MedCAT de-identification model"
    )
    model_version: str = Field(
        default="unknown",
        description="Model version string"
    )
    supported_phi_types: list[str] = Field(
        default_factory=list,
        description="List of PHI entity types this model can detect"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "model_name": "medcat_deid",
                "model_version": "1.0.0",
                "supported_phi_types": [
                    "NAME", "LOCATION", "DATE", "PHONE", "FAX",
                    "EMAIL", "SSN", "MRN", "HEALTHPLAN", "ACCOUNT",
                    "LICENSE", "VEHICLE", "DEVICE", "URL", "IPADDR",
                    "BIOMETRIC", "PHOTO", "IDENTIFIER"
                ]
            }
        }
