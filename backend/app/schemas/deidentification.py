"""
De-identification schemas.

Pydantic models for de-identification requests, results, and validation reports.
"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

from app.schemas.phi_entity import PHIEntity


class DeidentificationResult(BaseModel):
    """
    De-identification result.

    Attributes:
        original_text: Original text with PHI
        deidentified_text: De-identified text
        entities_removed: List of PHI entities removed
        method_used: De-identification method applied
        confidence_score: Average confidence of detected PHI
        review_required: True if manual review needed
        entity_mappings: Consistent entity mappings used (for replacement method)
    """

    original_text: str = Field(..., description="Original text")
    deidentified_text: str = Field(..., description="De-identified text")
    entities_removed: List[PHIEntity] = Field(
        default_factory=list, description="PHI entities removed"
    )
    method_used: str = Field(
        ..., description="De-identification method (removal, replacement, generalization)"
    )
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Average PHI detection confidence"
    )
    review_required: bool = Field(
        ..., description="True if manual review recommended"
    )
    entity_mappings: Dict[str, str] = Field(
        default_factory=dict,
        description="Entity mappings for consistent replacement",
    )


class ValidationWarning(BaseModel):
    """
    Validation warning.

    Attributes:
        warning_type: Type of warning
        message: Warning message
        location: Optional character offset
    """

    warning_type: str = Field(..., description="Warning type")
    message: str = Field(..., description="Warning message")
    location: Optional[int] = Field(None, description="Character offset if applicable")


class ValidationReport(BaseModel):
    """
    De-identification validation report.

    Attributes:
        is_valid: True if no PHI detected in de-identified text
        warnings: List of validation warnings
        phi_detected: PHI entities still detected (should be empty)
        readability_score: Text readability score (0.0-1.0)
    """

    is_valid: bool = Field(..., description="True if validation passed")
    warnings: List[ValidationWarning] = Field(
        default_factory=list, description="Validation warnings"
    )
    phi_detected: List[PHIEntity] = Field(
        default_factory=list, description="PHI still detected (should be empty)"
    )
    readability_score: float = Field(
        ..., ge=0.0, le=1.0, description="Readability score (1.0 = fully readable)"
    )


class DeidentificationRequest(BaseModel):
    """
    De-identification request.

    Attributes:
        text: Text to de-identify
        method: De-identification method (removal, replacement, generalization)
        confidence_threshold: Minimum confidence for PHI detection (default 0.7)
    """

    text: str = Field(..., min_length=1, description="Text to de-identify")
    method: str = Field(
        default="removal",
        description="De-identification method (removal, replacement, generalization)",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold for PHI detection",
    )


class DeidentificationBatchRequest(BaseModel):
    """
    Batch de-identification request.

    Attributes:
        texts: List of texts to de-identify
        method: De-identification method
        confidence_threshold: Minimum confidence for PHI detection
    """

    texts: List[str] = Field(..., min_items=1, description="Texts to de-identify")
    method: str = Field(
        default="removal", description="De-identification method"
    )
    confidence_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"
    )
