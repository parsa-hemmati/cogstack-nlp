"""FHIR API Endpoints (Sprint 6)"""

from fastapi import APIRouter, Depends
from typing import Annotated

from app.schemas.fhir import FHIRPatient, FHIRObservation, FHIRCondition
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/fhir", tags=["FHIR R4"])


@router.get("/Patient/{patient_id}", response_model=FHIRPatient)
async def get_fhir_patient(
    patient_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
) -> FHIRPatient:
    """Get FHIR Patient resource"""
    # TODO: Implement FHIR patient transformation
    raise NotImplementedError("FHIR Patient endpoint pending")


@router.get("/Observation", response_model=list[FHIRObservation])
async def search_observations(
    patient: str,
    current_user: Annotated[User, Depends(get_current_user)]
) -> list[FHIRObservation]:
    """Search FHIR Observations"""
    # TODO: Implement FHIR observation search
    return []


@router.get("/Condition", response_model=list[FHIRCondition])
async def search_conditions(
    patient: str,
    current_user: Annotated[User, Depends(get_current_user)]
) -> list[FHIRCondition]:
    """Search FHIR Conditions"""
    # TODO: Implement FHIR condition search
    return []
