"""NHS FHIR UK Core Models and Validators.

This module provides wrapper classes for FHIR R4 resources that are compliant
with NHS FHIR UK Core profiles. It includes NHS-specific validation such as
NHS number checksum validation using the Modulus 11 algorithm.

References:
- FHIR R4: https://hl7.org/fhir/R4/
- NHS FHIR UK Core: https://simplifier.net/hl7fhirukcorer4
- NHS Number Format: https://www.datadictionary.nhs.uk/attributes/nhs_number.html
"""

from typing import Optional, List, Dict, Any
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.observation import Observation
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from pydantic import BaseModel, Field, field_validator


class NHSNumberValidationError(ValueError):
    """Raised when NHS number validation fails."""
    pass


def validate_nhs_number(nhs_number: str) -> bool:
    """Validate NHS number using Modulus 11 algorithm.

    NHS numbers are 10 digits long. The 10th digit is a check digit calculated
    using the Modulus 11 algorithm on the first 9 digits.

    Algorithm:
    1. Multiply each of the first 9 digits by (11 - position), where position is 1-9
    2. Sum all the results
    3. Calculate 11 - (sum mod 11)
    4. If result is 11, check digit is 0
    5. If result is 10, NHS number is invalid
    6. Otherwise, check digit should equal the result

    Args:
        nhs_number: NHS number as string (10 digits, spaces/hyphens ignored)

    Returns:
        True if valid, False otherwise

    Raises:
        NHSNumberValidationError: If NHS number format is invalid

    Examples:
        >>> validate_nhs_number("9434765870")  # Valid
        True
        >>> validate_nhs_number("943 476 5870")  # Valid (spaces ignored)
        True
        >>> validate_nhs_number("9434765871")  # Invalid checksum
        False
    """
    # Remove spaces, hyphens, and other non-digit characters
    cleaned = ''.join(c for c in nhs_number if c.isdigit())

    # Must be exactly 10 digits
    if len(cleaned) != 10:
        raise NHSNumberValidationError(
            f"NHS number must be 10 digits, got {len(cleaned)}"
        )

    # Extract first 9 digits and check digit
    digits = cleaned[:9]
    check_digit = int(cleaned[9])

    # Calculate checksum using Modulus 11 algorithm
    total = sum(int(digit) * (11 - position) for position, digit in enumerate(digits, start=1))

    remainder = total % 11
    calculated_check = 11 - remainder

    # Special cases
    if calculated_check == 11:
        calculated_check = 0
    elif calculated_check == 10:
        # NHS numbers with check digit 10 are invalid
        return False

    return calculated_check == check_digit


class UKCorePatient(BaseModel):
    """NHS FHIR UK Core Patient Profile.

    Wrapper around FHIR Patient resource with NHS-specific extensions:
    - NHS number validation (Modulus 11 checksum)
    - NHS number identifier system (https://fhir.nhs.uk/Id/nhs-number)

    Attributes:
        resource: Underlying FHIR Patient resource
        nhs_number: Patient's NHS number (validated)
    """

    resource: Patient = Field(..., description="FHIR Patient resource")
    nhs_number: Optional[str] = Field(None, description="NHS number (validated)")

    @field_validator('nhs_number')
    @classmethod
    def validate_nhs_number_field(cls, v: Optional[str]) -> Optional[str]:
        """Validate NHS number if provided."""
        if v is not None and not validate_nhs_number(v):
            raise NHSNumberValidationError(f"Invalid NHS number: {v}")
        return v

    @classmethod
    def from_fhir(cls, patient: Patient) -> "UKCorePatient":
        """Create UKCorePatient from FHIR Patient resource.

        Extracts NHS number from patient identifiers if present.

        Args:
            patient: FHIR Patient resource

        Returns:
            UKCorePatient instance
        """
        nhs_number = None

        if patient.identifier:
            for identifier in patient.identifier:
                if identifier.system == "https://fhir.nhs.uk/Id/nhs-number":
                    nhs_number = identifier.value
                    break

        return cls(resource=patient, nhs_number=nhs_number)

    def to_fhir(self) -> Patient:
        """Convert to FHIR Patient resource.

        Ensures NHS number is included in identifiers.

        Returns:
            FHIR Patient resource
        """
        patient = self.resource

        # Add NHS number identifier if provided
        if self.nhs_number:
            nhs_identifier = Identifier(
                system="https://fhir.nhs.uk/Id/nhs-number",
                value=self.nhs_number
            )

            if patient.identifier:
                # Replace existing NHS number or append
                nhs_found = False
                for i, identifier in enumerate(patient.identifier):
                    if identifier.system == "https://fhir.nhs.uk/Id/nhs-number":
                        patient.identifier[i] = nhs_identifier
                        nhs_found = True
                        break
                if not nhs_found:
                    patient.identifier.append(nhs_identifier)
            else:
                patient.identifier = [nhs_identifier]

        return patient


class UKCoreCondition(BaseModel):
    """NHS FHIR UK Core Condition Profile.

    Wrapper around FHIR Condition resource with NHS-specific coding systems:
    - ICD-10 (http://hl7.org/fhir/sid/icd-10)
    - SNOMED CT (http://snomed.info/sct)

    Attributes:
        resource: Underlying FHIR Condition resource
        icd10_code: ICD-10 code if available
        snomed_code: SNOMED CT code if available
    """

    resource: Condition = Field(..., description="FHIR Condition resource")
    icd10_code: Optional[str] = Field(None, description="ICD-10 code")
    snomed_code: Optional[str] = Field(None, description="SNOMED CT code")

    @classmethod
    def from_fhir(cls, condition: Condition) -> "UKCoreCondition":
        """Create UKCoreCondition from FHIR Condition resource.

        Extracts ICD-10 and SNOMED CT codes from condition coding.

        Args:
            condition: FHIR Condition resource

        Returns:
            UKCoreCondition instance
        """
        icd10_code = None
        snomed_code = None

        if condition.code and condition.code.coding:
            for coding in condition.code.coding:
                if coding.system == "http://hl7.org/fhir/sid/icd-10":
                    icd10_code = coding.code
                elif coding.system == "http://snomed.info/sct":
                    snomed_code = coding.code

        return cls(resource=condition, icd10_code=icd10_code, snomed_code=snomed_code)

    def to_fhir(self) -> Condition:
        """Convert to FHIR Condition resource.

        Returns:
            FHIR Condition resource
        """
        return self.resource


class UKCoreObservation(BaseModel):
    """NHS FHIR UK Core Observation Profile.

    Wrapper around FHIR Observation resource for clinical observations:
    - Vital signs (blood pressure, heart rate, temperature, etc.)
    - Lab results (HbA1c, cholesterol, eGFR, etc.)
    - SNOMED CT coding

    Attributes:
        resource: Underlying FHIR Observation resource
        loinc_code: LOINC code if available (international lab codes)
        snomed_code: SNOMED CT code if available (UK preferred)
    """

    resource: Observation = Field(..., description="FHIR Observation resource")
    loinc_code: Optional[str] = Field(None, description="LOINC code")
    snomed_code: Optional[str] = Field(None, description="SNOMED CT code")

    @classmethod
    def from_fhir(cls, observation: Observation) -> "UKCoreObservation":
        """Create UKCoreObservation from FHIR Observation resource.

        Extracts LOINC and SNOMED CT codes from observation coding.

        Args:
            observation: FHIR Observation resource

        Returns:
            UKCoreObservation instance
        """
        loinc_code = None
        snomed_code = None

        if observation.code and observation.code.coding:
            for coding in observation.code.coding:
                if coding.system == "http://loinc.org":
                    loinc_code = coding.code
                elif coding.system == "http://snomed.info/sct":
                    snomed_code = coding.code

        return cls(resource=observation, loinc_code=loinc_code, snomed_code=snomed_code)

    def to_fhir(self) -> Observation:
        """Convert to FHIR Observation resource.

        Returns:
            FHIR Observation resource
        """
        return self.resource


class UKCoreMedicationRequest(BaseModel):
    """NHS FHIR UK Core MedicationRequest Profile.

    Wrapper around FHIR MedicationRequest resource with NHS-specific coding:
    - NHS dm+d (Dictionary of Medicines and Devices)
    - System: https://dmd.nhs.uk

    Attributes:
        resource: Underlying FHIR MedicationRequest resource
        dmd_code: NHS dm+d code if available
    """

    resource: MedicationRequest = Field(..., description="FHIR MedicationRequest resource")
    dmd_code: Optional[str] = Field(None, description="NHS dm+d code")

    @classmethod
    def from_fhir(cls, medication_request: MedicationRequest) -> "UKCoreMedicationRequest":
        """Create UKCoreMedicationRequest from FHIR MedicationRequest resource.

        Extracts NHS dm+d code from medication coding.

        Args:
            medication_request: FHIR MedicationRequest resource

        Returns:
            UKCoreMedicationRequest instance
        """
        dmd_code = None

        # Check medicationCodeableConcept
        if hasattr(medication_request, 'medicationCodeableConcept') and medication_request.medicationCodeableConcept:
            if medication_request.medicationCodeableConcept.coding:
                for coding in medication_request.medicationCodeableConcept.coding:
                    if coding.system == "https://dmd.nhs.uk":
                        dmd_code = coding.code
                        break

        return cls(resource=medication_request, dmd_code=dmd_code)

    def to_fhir(self) -> MedicationRequest:
        """Convert to FHIR MedicationRequest resource.

        Returns:
            FHIR MedicationRequest resource
        """
        return self.resource
