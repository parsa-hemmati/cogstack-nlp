"""Unit tests for NHS FHIR UK Core models and validators.

Tests cover:
- NHS number validation (Modulus 11 algorithm)
- UKCorePatient NHS number extraction
- UKCoreCondition ICD-10/SNOMED extraction
- UKCoreObservation LOINC/SNOMED extraction
- UKCoreMedicationRequest dm+d code extraction
"""

import pytest
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.observation import Observation
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.identifier import Identifier
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding

from app.schemas.cds.fhir_models import (
    validate_nhs_number,
    NHSNumberValidationError,
    UKCorePatient,
    UKCoreCondition,
    UKCoreObservation,
    UKCoreMedicationRequest,
)


class TestNHSNumberValidation:
    """Test NHS number validation using Modulus 11 algorithm."""

    def test_valid_nhs_number(self):
        """Test validation of a valid NHS number."""
        # Known valid NHS number: 943 476 5870
        assert validate_nhs_number("9434765870") is True

    def test_valid_nhs_number_with_spaces(self):
        """Test validation handles spaces correctly."""
        assert validate_nhs_number("943 476 5870") is True

    def test_valid_nhs_number_with_hyphens(self):
        """Test validation handles hyphens correctly."""
        assert validate_nhs_number("943-476-5870") is True

    def test_invalid_nhs_number_wrong_checksum(self):
        """Test validation rejects NHS number with wrong checksum."""
        # Same number but wrong check digit (0 instead of correct)
        assert validate_nhs_number("9434765871") is False

    def test_invalid_nhs_number_check_digit_10(self):
        """Test validation rejects NHS number with check digit 10."""
        # NHS numbers with calculated check digit 10 are invalid
        # This is a constructed example that would result in check digit 10
        assert validate_nhs_number("1234567890") is False

    def test_nhs_number_too_short(self):
        """Test validation raises error for too-short NHS number."""
        with pytest.raises(NHSNumberValidationError, match="must be 10 digits"):
            validate_nhs_number("12345")

    def test_nhs_number_too_long(self):
        """Test validation raises error for too-long NHS number."""
        with pytest.raises(NHSNumberValidationError, match="must be 10 digits"):
            validate_nhs_number("12345678901")

    def test_nhs_number_with_letters(self):
        """Test validation raises error for NHS number with letters."""
        with pytest.raises(NHSNumberValidationError, match="must be 10 digits"):
            validate_nhs_number("943ABC5870")


class TestUKCorePatient:
    """Test UKCorePatient NHS FHIR UK Core profile."""

    def test_from_fhir_extracts_nhs_number(self):
        """Test NHS number extraction from FHIR Patient resource."""
        # Create FHIR Patient with NHS number identifier
        patient = Patient(
            identifier=[
                Identifier(
                    system="https://fhir.nhs.uk/Id/nhs-number",
                    value="9434765870"
                )
            ]
        )

        uk_patient = UKCorePatient.from_fhir(patient)

        assert uk_patient.nhs_number == "9434765870"
        assert uk_patient.resource == patient

    def test_from_fhir_without_nhs_number(self):
        """Test Patient without NHS number identifier."""
        patient = Patient(identifier=[])

        uk_patient = UKCorePatient.from_fhir(patient)

        assert uk_patient.nhs_number is None
        assert uk_patient.resource == patient

    def test_to_fhir_adds_nhs_number_identifier(self):
        """Test NHS number is added to identifiers when converting to FHIR."""
        patient = Patient(identifier=[])
        uk_patient = UKCorePatient(resource=patient, nhs_number="9434765870")

        fhir_patient = uk_patient.to_fhir()

        assert len(fhir_patient.identifier) == 1
        assert fhir_patient.identifier[0].system == "https://fhir.nhs.uk/Id/nhs-number"
        assert fhir_patient.identifier[0].value == "9434765870"

    def test_validation_rejects_invalid_nhs_number(self):
        """Test Pydantic validation rejects invalid NHS number."""
        patient = Patient(identifier=[])

        with pytest.raises(NHSNumberValidationError):
            UKCorePatient(resource=patient, nhs_number="9434765871")  # Invalid checksum


class TestUKCoreCondition:
    """Test UKCoreCondition NHS FHIR UK Core profile."""

    def test_from_fhir_extracts_icd10_code(self):
        """Test ICD-10 code extraction from FHIR Condition resource."""
        condition = Condition(
            code=CodeableConcept(
                coding=[
                    Coding(
                        system="http://hl7.org/fhir/sid/icd-10",
                        code="E11.9",
                        display="Type 2 diabetes mellitus without complications"
                    )
                ]
            )
        )

        uk_condition = UKCoreCondition.from_fhir(condition)

        assert uk_condition.icd10_code == "E11.9"
        assert uk_condition.snomed_code is None

    def test_from_fhir_extracts_snomed_code(self):
        """Test SNOMED CT code extraction from FHIR Condition resource."""
        condition = Condition(
            code=CodeableConcept(
                coding=[
                    Coding(
                        system="http://snomed.info/sct",
                        code="44054006",
                        display="Type 2 diabetes mellitus"
                    )
                ]
            )
        )

        uk_condition = UKCoreCondition.from_fhir(condition)

        assert uk_condition.snomed_code == "44054006"
        assert uk_condition.icd10_code is None

    def test_from_fhir_extracts_both_codes(self):
        """Test extraction of both ICD-10 and SNOMED CT codes."""
        condition = Condition(
            code=CodeableConcept(
                coding=[
                    Coding(
                        system="http://hl7.org/fhir/sid/icd-10",
                        code="E11.9",
                        display="Type 2 diabetes mellitus"
                    ),
                    Coding(
                        system="http://snomed.info/sct",
                        code="44054006",
                        display="Type 2 diabetes mellitus"
                    )
                ]
            )
        )

        uk_condition = UKCoreCondition.from_fhir(condition)

        assert uk_condition.icd10_code == "E11.9"
        assert uk_condition.snomed_code == "44054006"


class TestUKCoreObservation:
    """Test UKCoreObservation NHS FHIR UK Core profile."""

    def test_from_fhir_extracts_loinc_code(self):
        """Test LOINC code extraction from FHIR Observation resource."""
        observation = Observation(
            code=CodeableConcept(
                coding=[
                    Coding(
                        system="http://loinc.org",
                        code="4548-4",
                        display="Hemoglobin A1c/Hemoglobin.total in Blood"
                    )
                ]
            ),
            status="final"
        )

        uk_observation = UKCoreObservation.from_fhir(observation)

        assert uk_observation.loinc_code == "4548-4"
        assert uk_observation.snomed_code is None

    def test_from_fhir_extracts_snomed_code(self):
        """Test SNOMED CT code extraction from FHIR Observation resource."""
        observation = Observation(
            code=CodeableConcept(
                coding=[
                    Coding(
                        system="http://snomed.info/sct",
                        code="365812005",
                        display="Finding of HbA1c level"
                    )
                ]
            ),
            status="final"
        )

        uk_observation = UKCoreObservation.from_fhir(observation)

        assert uk_observation.snomed_code == "365812005"
        assert uk_observation.loinc_code is None


class TestUKCoreMedicationRequest:
    """Test UKCoreMedicationRequest NHS FHIR UK Core profile."""

    def test_from_fhir_extracts_dmd_code(self):
        """Test NHS dm+d code extraction from FHIR MedicationRequest resource."""
        medication_request = MedicationRequest(
            medicationCodeableConcept=CodeableConcept(
                coding=[
                    Coding(
                        system="https://dmd.nhs.uk",
                        code="39113611000001102",
                        display="Metformin 500mg tablets"
                    )
                ]
            ),
            status="active",
            intent="order"
        )

        uk_med_request = UKCoreMedicationRequest.from_fhir(medication_request)

        assert uk_med_request.dmd_code == "39113611000001102"

    def test_from_fhir_without_dmd_code(self):
        """Test MedicationRequest without NHS dm+d code."""
        medication_request = MedicationRequest(
            medicationCodeableConcept=CodeableConcept(
                coding=[
                    Coding(
                        system="http://www.nlm.nih.gov/research/umls/rxnorm",
                        code="860975",
                        display="Metformin 500 MG Oral Tablet"
                    )
                ]
            ),
            status="active",
            intent="order"
        )

        uk_med_request = UKCoreMedicationRequest.from_fhir(medication_request)

        assert uk_med_request.dmd_code is None
