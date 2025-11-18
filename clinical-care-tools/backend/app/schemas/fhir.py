"""FHIR R4 Schemas (Sprint 6)"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class FHIRResource(BaseModel):
    """Base FHIR resource"""
    resourceType: str = Field(..., description="Resource type")
    id: Optional[str] = Field(None, description="Logical ID")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata")


class FHIRPatient(FHIRResource):
    """FHIR Patient resource"""
    resourceType: str = "Patient"
    identifier: List[Dict[str, Any]] = Field(..., description="Patient identifiers")
    name: List[Dict[str, Any]] = Field(..., description="Patient names")
    gender: str = Field(..., description="Gender")
    birthDate: str = Field(..., description="Birth date")

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Patient",
                "id": "patient-123",
                "identifier": [
                    {"system": "urn:oid:2.16.840.1.113883.2.1.4.1", "value": "NHS1234567890"}
                ],
                "name": [{"family": "Doe", "given": ["John"]}],
                "gender": "male",
                "birthDate": "1980-01-15"
            }
        }


class FHIRObservation(FHIRResource):
    """FHIR Observation resource"""
    resourceType: str = "Observation"
    status: str = Field(..., description="Status")
    code: Dict[str, Any] = Field(..., description="Observation code (SNOMED/LOINC)")
    subject: Dict[str, str] = Field(..., description="Patient reference")
    effectiveDateTime: str = Field(..., description="Observation datetime")
    valueQuantity: Optional[Dict[str, Any]] = Field(None, description="Value")

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Observation",
                "status": "final",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "271649006", "display": "Diabetes mellitus"}
                    ]
                },
                "subject": {"reference": "Patient/patient-123"},
                "effectiveDateTime": "2023-11-17T10:30:00Z",
                "valueQuantity": {"value": 7.5, "unit": "mmol/L", "system": "http://unitsofmeasure.org"}
            }
        }


class FHIRCondition(FHIRResource):
    """FHIR Condition resource"""
    resourceType: str = "Condition"
    clinicalStatus: Dict[str, Any] = Field(..., description="Clinical status")
    code: Dict[str, Any] = Field(..., description="Condition code (SNOMED/ICD-10)")
    subject: Dict[str, str] = Field(..., description="Patient reference")
    onsetDateTime: Optional[str] = Field(None, description="Onset date")

    class Config:
        json_schema_extra = {
            "example": {
                "resourceType": "Condition",
                "clinicalStatus": {
                    "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
                },
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "44054006", "display": "Type 2 diabetes mellitus"}
                    ]
                },
                "subject": {"reference": "Patient/patient-123"},
                "onsetDateTime": "2020-05-10"
            }
        }
