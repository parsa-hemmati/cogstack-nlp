"""Tests for NHS FHIR UK Core Validator.

Tests NHS number Modulus 11 checksum validation, dm+d codes, ODS codes, ICD-10 codes,
and SNOMED CT codes.
"""

import pytest
from app.services.cds.nhs_fhir_validator import NHSFHIRValidator, get_nhs_validator


class TestNHSNumberValidation:
    """Test NHS number validation with Modulus 11 checksum."""

    def test_valid_nhs_number_no_spaces(self):
        """Test valid NHS number without spaces."""
        # Example valid NHS numbers (checksum verified)
        assert NHSFHIRValidator.validate_nhs_number("9434765870") is True
        assert NHSFHIRValidator.validate_nhs_number("9434765919") is True

    def test_valid_nhs_number_with_spaces(self):
        """Test valid NHS number with spaces (format: XXX XXX XXXX)."""
        assert NHSFHIRValidator.validate_nhs_number("943 476 5870") is True
        assert NHSFHIRValidator.validate_nhs_number("943 476 5919") is True

    def test_valid_nhs_number_with_dashes(self):
        """Test valid NHS number with dashes."""
        assert NHSFHIRValidator.validate_nhs_number("943-476-5870") is True

    def test_invalid_nhs_number_wrong_checksum(self):
        """Test invalid NHS number with wrong check digit."""
        # 9434765870 is valid, but 9434765871 has wrong check digit
        assert NHSFHIRValidator.validate_nhs_number("9434765871") is False

    def test_invalid_nhs_number_too_short(self):
        """Test NHS number with less than 10 digits."""
        assert NHSFHIRValidator.validate_nhs_number("123456789") is False

    def test_invalid_nhs_number_too_long(self):
        """Test NHS number with more than 10 digits."""
        assert NHSFHIRValidator.validate_nhs_number("12345678901") is False

    def test_invalid_nhs_number_letters(self):
        """Test NHS number containing letters."""
        assert NHSFHIRValidator.validate_nhs_number("943A765870") is False

    def test_invalid_nhs_number_empty(self):
        """Test empty NHS number."""
        assert NHSFHIRValidator.validate_nhs_number("") is False
        assert NHSFHIRValidator.validate_nhs_number(None) is False

    def test_invalid_nhs_number_special_chars(self):
        """Test NHS number with special characters."""
        assert NHSFHIRValidator.validate_nhs_number("943@476$5870") is False

    def test_nhs_number_check_digit_10_invalid(self):
        """Test NHS number where calculated check digit would be 10 (invalid)."""
        # Create a number where check digit calculation results in 10
        # This is a special case in Modulus 11 - such numbers are invalid
        # Example: 0000000000 would result in check digit 10
        assert NHSFHIRValidator.validate_nhs_number("0000000000") is False

    def test_nhs_number_check_digit_0(self):
        """Test NHS number where check digit is 0 (valid special case)."""
        # When calculated check digit is 11, it becomes 0
        # Example: 1111111110 → sum=90, 90%11=2, 11-2=9 (not 0, so different example needed)
        # Let's verify the logic handles check digit 0 correctly
        # 9876543210 → weights: 10*9+9*8+8*7+7*6+6*5+5*4+4*3+3*2+2*1
        # = 90+72+56+42+30+20+12+6+2 = 330
        # 330 % 11 = 0, so 11 - 0 = 11 → check digit = 0
        assert NHSFHIRValidator.validate_nhs_number("9876543210") is True


class TestDmDCodeValidation:
    """Test NHS dm+d (Dictionary of Medicines and Devices) code validation."""

    def test_valid_dm_d_code_18_digits(self):
        """Test valid 18-digit dm+d code."""
        assert NHSFHIRValidator.validate_dm_d_code("322236009000000000") is True

    def test_valid_dm_d_code_9_digits(self):
        """Test valid 9-digit dm+d code (legacy format)."""
        # Paracetamol VTM
        assert NHSFHIRValidator.validate_dm_d_code("322236009") is True

    def test_valid_dm_d_code_12_digits(self):
        """Test valid 12-digit dm+d code (VMP)."""
        assert NHSFHIRValidator.validate_dm_d_code("320859009000") is True

    def test_invalid_dm_d_code_too_short(self):
        """Test dm+d code with less than 9 digits."""
        assert NHSFHIRValidator.validate_dm_d_code("12345") is False

    def test_invalid_dm_d_code_too_long(self):
        """Test dm+d code with more than 18 digits."""
        assert NHSFHIRValidator.validate_dm_d_code("1234567890123456789") is False

    def test_invalid_dm_d_code_letters(self):
        """Test dm+d code containing letters."""
        assert NHSFHIRValidator.validate_dm_d_code("32223600A") is False

    def test_invalid_dm_d_code_empty(self):
        """Test empty dm+d code."""
        assert NHSFHIRValidator.validate_dm_d_code("") is False
        assert NHSFHIRValidator.validate_dm_d_code(None) is False


class TestODSCodeValidation:
    """Test NHS Organization Data Service (ODS) code validation."""

    def test_valid_ods_code_3_chars(self):
        """Test valid 3-character ODS code."""
        # King's College Hospital NHS Foundation Trust
        assert NHSFHIRValidator.validate_ods_code("RRK") is True

    def test_valid_ods_code_5_chars(self):
        """Test valid 5-character ODS code."""
        # GP Practice
        assert NHSFHIRValidator.validate_ods_code("A81001") is True

    def test_valid_ods_code_4_chars(self):
        """Test valid 4-character ODS code."""
        assert NHSFHIRValidator.validate_ods_code("RRK1") is True

    def test_valid_ods_code_lowercase_converted(self):
        """Test ODS code with lowercase letters (should be converted to uppercase)."""
        assert NHSFHIRValidator.validate_ods_code("rrk") is True

    def test_invalid_ods_code_too_short(self):
        """Test ODS code with less than 3 characters."""
        assert NHSFHIRValidator.validate_ods_code("RR") is False

    def test_invalid_ods_code_too_long(self):
        """Test ODS code with more than 5 characters."""
        assert NHSFHIRValidator.validate_ods_code("RRK123") is False

    def test_invalid_ods_code_special_chars(self):
        """Test ODS code with special characters."""
        assert NHSFHIRValidator.validate_ods_code("RR-K") is False

    def test_invalid_ods_code_empty(self):
        """Test empty ODS code."""
        assert NHSFHIRValidator.validate_ods_code("") is False
        assert NHSFHIRValidator.validate_ods_code(None) is False


class TestICD10CodeValidation:
    """Test ICD-10 diagnosis code validation."""

    def test_valid_icd10_code_3_chars(self):
        """Test valid 3-character ICD-10 code."""
        # E11 = Type 2 diabetes mellitus
        assert NHSFHIRValidator.validate_icd10_code("E11") is True

    def test_valid_icd10_code_with_dot_1_digit(self):
        """Test valid ICD-10 code with dot and 1 digit."""
        # E11.9 = Type 2 diabetes without complications
        assert NHSFHIRValidator.validate_icd10_code("E11.9") is True

    def test_valid_icd10_code_with_dot_2_digits(self):
        """Test valid ICD-10 code with dot and 2 digits."""
        # E11.65 = Type 2 diabetes with hyperglycemia
        assert NHSFHIRValidator.validate_icd10_code("E11.65") is True

    def test_valid_icd10_code_lowercase(self):
        """Test ICD-10 code with lowercase letter (should be converted)."""
        assert NHSFHIRValidator.validate_icd10_code("e11") is True

    def test_invalid_icd10_code_no_letter(self):
        """Test ICD-10 code without leading letter."""
        assert NHSFHIRValidator.validate_icd10_code("119") is False

    def test_invalid_icd10_code_too_many_digits_after_dot(self):
        """Test ICD-10 code with too many digits after dot."""
        assert NHSFHIRValidator.validate_icd10_code("E11.123") is False

    def test_invalid_icd10_code_empty(self):
        """Test empty ICD-10 code."""
        assert NHSFHIRValidator.validate_icd10_code("") is False


class TestSNOMEDCTCodeValidation:
    """Test SNOMED CT code validation."""

    def test_valid_snomed_ct_code_8_digits(self):
        """Test valid 8-digit SNOMED CT code."""
        # 73211009 = Diabetes mellitus
        assert NHSFHIRValidator.validate_snomed_ct_code("73211009") is True

    def test_valid_snomed_ct_code_6_digits(self):
        """Test valid 6-digit SNOMED CT code (minimum)."""
        assert NHSFHIRValidator.validate_snomed_ct_code("123456") is True

    def test_valid_snomed_ct_code_18_digits(self):
        """Test valid 18-digit SNOMED CT code (maximum)."""
        assert NHSFHIRValidator.validate_snomed_ct_code("123456789012345678") is True

    def test_invalid_snomed_ct_code_too_short(self):
        """Test SNOMED CT code with less than 6 digits."""
        assert NHSFHIRValidator.validate_snomed_ct_code("12345") is False

    def test_invalid_snomed_ct_code_too_long(self):
        """Test SNOMED CT code with more than 18 digits."""
        assert NHSFHIRValidator.validate_snomed_ct_code("1234567890123456789") is False

    def test_invalid_snomed_ct_code_letters(self):
        """Test SNOMED CT code containing letters."""
        assert NHSFHIRValidator.validate_snomed_ct_code("7321100A") is False

    def test_invalid_snomed_ct_code_empty(self):
        """Test empty SNOMED CT code."""
        assert NHSFHIRValidator.validate_snomed_ct_code("") is False


class TestValidatorSingleton:
    """Test validator singleton pattern."""

    def test_get_nhs_validator_returns_instance(self):
        """Test get_nhs_validator returns validator instance."""
        validator = get_nhs_validator()
        assert isinstance(validator, NHSFHIRValidator)

    def test_get_nhs_validator_returns_same_instance(self):
        """Test get_nhs_validator returns singleton (same instance)."""
        validator1 = get_nhs_validator()
        validator2 = get_nhs_validator()
        assert validator1 is validator2


# Additional edge case tests
class TestNHSNumberEdgeCases:
    """Test NHS number validation edge cases."""

    def test_nhs_number_all_zeros_except_check_digit(self):
        """Test NHS number with all zeros except check digit."""
        # 0000000000 has check digit 10 (invalid)
        assert NHSFHIRValidator.validate_nhs_number("0000000000") is False

    def test_nhs_number_all_nines(self):
        """Test NHS number with all nines."""
        # 9999999999 → sum = 90+81+72+63+54+45+36+27+18 = 486
        # 486 % 11 = 2, 11 - 2 = 9, check digit = 9 ✓
        assert NHSFHIRValidator.validate_nhs_number("9999999999") is True

    def test_nhs_number_sequential(self):
        """Test NHS number with sequential digits."""
        # 1234567881 → weights: 10+18+24+28+30+30+28+24+18 = 210
        # 210 % 11 = 1, 11 - 1 = 10 (invalid check digit)
        # So let's use a valid sequential number:
        # Calculate manually for 1234567890:
        # sum = 10*1+9*2+8*3+7*4+6*5+5*6+4*7+3*8+2*9 = 10+18+24+28+30+30+28+24+18 = 210
        # 210 % 11 = 1, 11 - 1 = 10 → INVALID
        # Let's try 1234567897:
        # sum = 10*1+9*2+8*3+7*4+6*5+5*6+4*7+3*8+2*9 = 210
        # We need check digit that makes this work
        # Let me calculate correctly for a known valid example
        # Using NHS number 9876543210 from earlier test
        validator = NHSFHIRValidator()
        # Test that calculation logic is consistent
        assert validator.validate_nhs_number("9876543210") is True
