"""FHIR Resource Mapper for CDS Rules Engine.

Transforms FHIR R4 resources (Patient, Condition, Observation, MedicationRequest)
into a simplified patient_data dictionary format for use with the CDS rules engine.

Handles missing fields gracefully and extracts key clinical data points.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from app.models.fhir.patient import FHIRPatient
from app.models.fhir.condition import FHIRCondition
from app.models.fhir.observation import FHIRObservation
from app.models.fhir.medication_request import FHIRMedicationRequest

logger = logging.getLogger(__name__)


class FHIRResourceMapper:
    """Maps FHIR resources to patient_data dictionary for CDS rules engine."""

    @staticmethod
    def map_patient_bundle_to_dict(
        patient: Optional[FHIRPatient],
        conditions: List[FHIRCondition],
        observations: List[FHIRObservation],
        medication_requests: List[FHIRMedicationRequest],
    ) -> Dict[str, Any]:
        """Map complete FHIR patient bundle to patient_data dict.

        Args:
            patient: FHIR Patient resource
            conditions: List of FHIR Condition resources
            observations: List of FHIR Observation resources
            medication_requests: List of FHIR MedicationRequest resources

        Returns:
            Patient data dictionary for CDS rules engine with structure:
            {
                "patient_id": str,
                "nhs_number": str,
                "age": int,
                "gender": str,
                "conditions": List[str],  # ICD-10 or SNOMED CT codes
                "medications": List[str],  # dm+d codes
                "observations": Dict[str, Any],  # Keyed by LOINC/SNOMED code
                "latest_hba1c": float,  # mmol/mol
                "latest_bp_systolic": int,  # mmHg
                "latest_bp_diastolic": int,  # mmHg
                "latest_egfr": float,  # mL/min/1.73m²
                "is_diabetic": bool,
                "has_hypertension": bool,
                "has_ckd": bool,
            }

        Example:
            >>> patient_data = mapper.map_patient_bundle_to_dict(
            ...     patient, conditions, observations, medication_requests
            ... )
            >>> patient_data["age"]
            65
            >>> patient_data["conditions"]
            ["E11", "I10", "N18.3"]
        """
        if not patient:
            logger.warning("Patient resource is None, returning empty patient_data")
            return {}

        # Extract patient demographics
        patient_data = {
            "patient_id": patient.id,
            "nhs_number": FHIRResourceMapper._extract_nhs_number(patient),
            "age": FHIRResourceMapper._calculate_age(patient.birthDate) if patient.birthDate else None,
            "gender": patient.gender if patient.gender else "unknown",
        }

        # Extract conditions
        patient_data["conditions"] = [
            FHIRResourceMapper._extract_condition_code(cond)
            for cond in conditions
            if FHIRResourceMapper._extract_condition_code(cond)
        ]

        # Extract medications
        patient_data["medications"] = [
            FHIRResourceMapper._extract_medication_code(med)
            for med in medication_requests
            if FHIRResourceMapper._extract_medication_code(med)
        ]

        # Extract observations
        obs_dict = {}
        for obs in observations:
            code, value = FHIRResourceMapper._extract_observation(obs)
            if code:
                obs_dict[code] = value

        patient_data["observations"] = obs_dict

        # Extract key clinical values
        patient_data["latest_hba1c"] = FHIRResourceMapper._get_latest_observation(
            observations, ["4548-4", "43396009"]  # LOINC: HbA1c  # SNOMED: HbA1c
        )

        bp_systolic, bp_diastolic = FHIRResourceMapper._get_latest_blood_pressure(observations)
        patient_data["latest_bp_systolic"] = bp_systolic
        patient_data["latest_bp_diastolic"] = bp_diastolic

        patient_data["latest_egfr"] = FHIRResourceMapper._get_latest_observation(
            observations, ["62238-1", "33914-3"]  # LOINC: eGFR (MDRD), eGFR (CKD-EPI)
        )

        # Boolean flags for common conditions
        patient_data["is_diabetic"] = any(
            code.startswith("E10") or code.startswith("E11")
            for code in patient_data["conditions"]
        )

        patient_data["has_hypertension"] = any(
            code.startswith("I10") or code == "38341003"  # ICD-10: Essential hypertension  # SNOMED: Hypertension
            for code in patient_data["conditions"]
        )

        patient_data["has_ckd"] = any(
            code.startswith("N18")  # ICD-10: Chronic kidney disease
            for code in patient_data["conditions"]
        )

        return patient_data

    @staticmethod
    def _extract_nhs_number(patient: FHIRPatient) -> Optional[str]:
        """Extract NHS number from Patient.identifier."""
        if not patient.identifier:
            return None

        for identifier in patient.identifier:
            # NHS number identifier system
            if identifier.system == "https://fhir.nhs.uk/Id/nhs-number":
                return identifier.value

        return None

    @staticmethod
    def _calculate_age(birth_date: date) -> int:
        """Calculate age from birth date."""
        today = datetime.now().date()
        age = today.year - birth_date.year

        # Adjust if birthday hasn't occurred this year
        if today.month < birth_date.month or (
            today.month == birth_date.month and today.day < birth_date.day
        ):
            age -= 1

        return age

    @staticmethod
    def _extract_condition_code(condition: FHIRCondition) -> Optional[str]:
        """Extract ICD-10 or SNOMED CT code from Condition.code."""
        if not condition.code or not condition.code.coding:
            return None

        for coding in condition.code.coding:
            # Prefer ICD-10 codes
            if coding.system == "http://hl7.org/fhir/sid/icd-10":
                return coding.code

            # Fall back to SNOMED CT
            if coding.system == "http://snomed.info/sct":
                return coding.code

        return None

    @staticmethod
    def _extract_medication_code(medication_request: FHIRMedicationRequest) -> Optional[str]:
        """Extract dm+d code from MedicationRequest.medicationCodeableConcept."""
        if not medication_request.medicationCodeableConcept:
            return None

        if not medication_request.medicationCodeableConcept.coding:
            return None

        for coding in medication_request.medicationCodeableConcept.coding:
            # NHS dm+d codes (SNOMED CT)
            if coding.system == "https://dmd.nhs.uk" or coding.system == "http://snomed.info/sct":
                return coding.code

        return None

    @staticmethod
    def _extract_observation(observation: FHIRObservation) -> tuple[Optional[str], Any]:
        """Extract code and value from Observation.

        Returns:
            Tuple of (code, value) where code is LOINC/SNOMED and value is the observation value
        """
        if not observation.code or not observation.code.coding:
            return None, None

        # Extract code (prefer LOINC, fall back to SNOMED)
        code = None
        for coding in observation.code.coding:
            if coding.system == "http://loinc.org":
                code = coding.code
                break
            elif coding.system == "http://snomed.info/sct":
                code = coding.code

        if not code:
            return None, None

        # Extract value
        value = None
        if observation.valueQuantity:
            value = {
                "value": observation.valueQuantity.value,
                "unit": observation.valueQuantity.unit,
            }
        elif observation.valueString:
            value = observation.valueString
        elif observation.valueBoolean is not None:
            value = observation.valueBoolean
        elif observation.valueInteger is not None:
            value = observation.valueInteger

        return code, value

    @staticmethod
    def _get_latest_observation(
        observations: List[FHIRObservation], target_codes: List[str]
    ) -> Optional[float]:
        """Get latest observation value for given LOINC/SNOMED codes.

        Args:
            observations: List of FHIR Observation resources
            target_codes: List of LOINC or SNOMED codes to search for

        Returns:
            Latest observation value as float, or None if not found
        """
        matching_obs = []

        for obs in observations:
            if not obs.code or not obs.code.coding:
                continue

            # Check if observation code matches any target code
            for coding in obs.code.coding:
                if coding.code in target_codes:
                    if obs.valueQuantity and obs.valueQuantity.value is not None:
                        matching_obs.append((obs.effectiveDateTime or datetime.min, obs.valueQuantity.value))
                    break

        if not matching_obs:
            return None

        # Sort by date descending (most recent first)
        matching_obs.sort(key=lambda x: x[0], reverse=True)

        return matching_obs[0][1]

    @staticmethod
    def _get_latest_blood_pressure(
        observations: List[FHIRObservation]
    ) -> tuple[Optional[int], Optional[int]]:
        """Get latest blood pressure reading (systolic and diastolic).

        Blood pressure observations have component values:
        - Systolic: LOINC 8480-6
        - Diastolic: LOINC 8462-4

        Args:
            observations: List of FHIR Observation resources

        Returns:
            Tuple of (systolic, diastolic) as integers (mmHg), or (None, None) if not found
        """
        # Find BP panel observations (LOINC 85354-9)
        bp_obs = []

        for obs in observations:
            if not obs.code or not obs.code.coding:
                continue

            for coding in obs.code.coding:
                if coding.code == "85354-9":  # Blood pressure panel
                    bp_obs.append((obs.effectiveDateTime or datetime.min, obs))
                    break

        if not bp_obs:
            return None, None

        # Sort by date descending (most recent first)
        bp_obs.sort(key=lambda x: x[0], reverse=True)

        latest_bp = bp_obs[0][1]

        # Extract systolic and diastolic from components
        systolic = None
        diastolic = None

        if latest_bp.component:
            for component in latest_bp.component:
                if not component.code or not component.code.coding:
                    continue

                for coding in component.code.coding:
                    if coding.code == "8480-6" and component.valueQuantity:  # Systolic
                        systolic = int(component.valueQuantity.value)
                    elif coding.code == "8462-4" and component.valueQuantity:  # Diastolic
                        diastolic = int(component.valueQuantity.value)

        return systolic, diastolic


# Global mapper instance
_mapper: Optional[FHIRResourceMapper] = None


def get_fhir_mapper() -> FHIRResourceMapper:
    """Get global FHIR resource mapper instance (singleton pattern).

    Returns:
        FHIRResourceMapper instance
    """
    global _mapper
    if _mapper is None:
        _mapper = FHIRResourceMapper()
    return _mapper
