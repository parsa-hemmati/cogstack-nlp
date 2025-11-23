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

__all__ = [
    "UKCorePatient",
    "UKCoreCondition",
    "UKCoreObservation",
    "UKCoreMedicationRequest",
    "validate_nhs_number",
]
