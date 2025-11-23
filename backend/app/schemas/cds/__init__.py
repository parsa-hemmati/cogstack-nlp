"""CDS (Clinical Decision Support) Schemas Package.

This package contains FHIR R4 models, validators, and schemas for the
Clinical Decision Support module, including:
- NHS FHIR UK Core models
- NHS number validation
- Clinical guidelines schemas
- CDS rules schemas
- Drug interaction schemas
"""

from .fhir_models import (
    UKCorePatient,
    UKCoreCondition,
    UKCoreObservation,
    UKCoreMedicationRequest,
    validate_nhs_number,
)
from .guideline_schemas import (
    CDSGuidelineBase,
    CDSGuidelineCreate,
    CDSGuidelineUpdate,
    CDSGuidelineResponse,
    CDSGuidelineSearchRequest,
    CDSGuidelineListResponse,
)
from .rule_schemas import (
    CDSRuleBase,
    CDSRuleCreate,
    CDSRuleUpdate,
    CDSRuleResponse,
    CDSRuleListResponse,
    CDSRuleEvaluationRequest,
    CDSRecommendation,
    CDSRuleEvaluationResponse,
)

__all__ = [
    # FHIR models
    "UKCorePatient",
    "UKCoreCondition",
    "UKCoreObservation",
    "UKCoreMedicationRequest",
    "validate_nhs_number",
    # Guideline schemas
    "CDSGuidelineBase",
    "CDSGuidelineCreate",
    "CDSGuidelineUpdate",
    "CDSGuidelineResponse",
    "CDSGuidelineSearchRequest",
    "CDSGuidelineListResponse",
    # Rule schemas
    "CDSRuleBase",
    "CDSRuleCreate",
    "CDSRuleUpdate",
    "CDSRuleResponse",
    "CDSRuleListResponse",
    "CDSRuleEvaluationRequest",
    "CDSRecommendation",
    "CDSRuleEvaluationResponse",
]
