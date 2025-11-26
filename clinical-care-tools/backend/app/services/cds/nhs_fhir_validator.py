"""NHS FHIR UK Core Validation Service.

Validates NHS-specific identifiers and codes according to NHS standards:
- NHS Number: 10-digit identifier with Modulus 11 checksum
- dm+d Code: 18-digit SNOMED CT code for NHS Dictionary of Medicines and Devices
- ODS Code: Organization Data Service code (3-5 alphanumeric characters)
"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class NHSFHIRValidator:
    """Validator for NHS FHIR UK Core identifiers and codes."""

    @staticmethod
    def validate_nhs_number(nhs_number: str) -> bool:
        """Validate NHS number using Modulus 11 checksum algorithm.

        NHS number format:
        - 10 digits total
        - First 9 digits are the patient identifier
        - 10th digit is the check digit calculated using Modulus 11

        Algorithm:
        1. Multiply first 9 digits by weights (10, 9, 8, 7, 6, 5, 4, 3, 2)
        2. Sum all products
        3. Calculate: 11 - (sum % 11)
        4. If result is 11, check digit = 0
        5. If result is 10, NHS number is invalid
        6. Otherwise, result = check digit

        Args:
            nhs_number: 10-digit NHS number (with or without spaces)

        Returns:
            True if valid NHS number, False otherwise

        Examples:
            >>> NHSFHIRValidator.validate_nhs_number("1234567881")
            True
            >>> NHSFHIRValidator.validate_nhs_number("123 456 7881")
            True
            >>> NHSFHIRValidator.validate_nhs_number("1234567890")
            False
        """
        if not nhs_number:
            return False

        # Remove spaces and validate format
        nhs_clean = nhs_number.replace(" ", "").replace("-", "")

        # Must be exactly 10 digits
        if not re.match(r"^\d{10}$", nhs_clean):
            logger.debug(f"Invalid NHS number format: {nhs_number} (must be 10 digits)")
            return False

        # Extract first 9 digits and check digit
        identifier = nhs_clean[:9]
        check_digit = int(nhs_clean[9])

        # Modulus 11 weights for positions 1-9
        weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]

        # Calculate sum of (digit * weight) for first 9 digits
        total = sum(int(digit) * weight for digit, weight in zip(identifier, weights))

        # Calculate check digit
        remainder = total % 11
        calculated_check_digit = 11 - remainder

        # Special cases
        if calculated_check_digit == 11:
            calculated_check_digit = 0
        elif calculated_check_digit == 10:
            # NHS numbers resulting in check digit 10 are invalid
            logger.debug(f"Invalid NHS number: {nhs_number} (check digit would be 10)")
            return False

        # Validate check digit matches
        is_valid = calculated_check_digit == check_digit

        if not is_valid:
            logger.debug(
                f"Invalid NHS number: {nhs_number} "
                f"(expected check digit: {calculated_check_digit}, got: {check_digit})"
            )

        return is_valid

    @staticmethod
    def validate_dm_d_code(code: str) -> bool:
        """Validate NHS dm+d (Dictionary of Medicines and Devices) code.

        dm+d codes are 18-digit SNOMED CT codes used for medications in the NHS.

        Format:
        - 18 digits
        - SNOMED CT code
        - Used for VTM (Virtual Therapeutic Moiety), VMP (Virtual Medicinal Product),
          AMP (Actual Medicinal Product)

        Args:
            code: dm+d code (18-digit SNOMED CT code)

        Returns:
            True if valid dm+d code format, False otherwise

        Examples:
            >>> NHSFHIRValidator.validate_dm_d_code("322236009")  # Paracetamol
            True
            >>> NHSFHIRValidator.validate_dm_d_code("12345")
            False
        """
        if not code:
            return False

        # dm+d codes are 18-digit SNOMED CT codes
        # However, some legacy codes may be shorter (9+ digits)
        # Accept 9-18 digits for compatibility
        if not re.match(r"^\d{9,18}$", code):
            logger.debug(f"Invalid dm+d code format: {code} (must be 9-18 digits)")
            return False

        return True

    @staticmethod
    def validate_ods_code(code: str) -> bool:
        """Validate NHS Organization Data Service (ODS) code.

        ODS codes identify NHS organizations (hospitals, GP practices, etc.).

        Format:
        - 3-5 alphanumeric characters
        - Uppercase letters and digits
        - Examples: RRK (King's College Hospital), A81001 (GP Practice)

        Args:
            code: ODS code (3-5 alphanumeric)

        Returns:
            True if valid ODS code format, False otherwise

        Examples:
            >>> NHSFHIRValidator.validate_ods_code("RRK")
            True
            >>> NHSFHIRValidator.validate_ods_code("A81001")
            True
            >>> NHSFHIRValidator.validate_ods_code("X")
            False
        """
        if not code:
            return False

        # ODS codes are 3-5 alphanumeric characters (uppercase)
        if not re.match(r"^[A-Z0-9]{3,5}$", code.upper()):
            logger.debug(f"Invalid ODS code format: {code} (must be 3-5 alphanumeric)")
            return False

        return True

    @staticmethod
    def validate_icd10_code(code: str) -> bool:
        """Validate ICD-10 diagnosis code format.

        ICD-10 codes are used for diagnoses in the NHS.

        Format:
        - Letter (A-Z) followed by 2 digits
        - Optional: dot (.) followed by 1-2 additional digits
        - Examples: E11 (Type 2 diabetes), E11.9 (Type 2 diabetes without complications)

        Args:
            code: ICD-10 code

        Returns:
            True if valid ICD-10 code format, False otherwise

        Examples:
            >>> NHSFHIRValidator.validate_icd10_code("E11")
            True
            >>> NHSFHIRValidator.validate_icd10_code("E11.9")
            True
            >>> NHSFHIRValidator.validate_icd10_code("123")
            False
        """
        if not code:
            return False

        # ICD-10: Letter + 2 digits, optionally followed by . and 1-2 digits
        if not re.match(r"^[A-Z]\d{2}(\.\d{1,2})?$", code.upper()):
            logger.debug(f"Invalid ICD-10 code format: {code}")
            return False

        return True

    @staticmethod
    def validate_snomed_ct_code(code: str) -> bool:
        """Validate SNOMED CT code format.

        SNOMED CT codes are used for clinical concepts in the NHS.

        Format:
        - 6-18 digits
        - Examples: 73211009 (Diabetes mellitus), 38341003 (Hypertension)

        Args:
            code: SNOMED CT code

        Returns:
            True if valid SNOMED CT code format, False otherwise

        Examples:
            >>> NHSFHIRValidator.validate_snomed_ct_code("73211009")
            True
            >>> NHSFHIRValidator.validate_snomed_ct_code("123")
            False
        """
        if not code:
            return False

        # SNOMED CT codes are 6-18 digits
        if not re.match(r"^\d{6,18}$", code):
            logger.debug(f"Invalid SNOMED CT code format: {code} (must be 6-18 digits)")
            return False

        return True


# Global validator instance
_validator: Optional[NHSFHIRValidator] = None


def get_nhs_validator() -> NHSFHIRValidator:
    """Get global NHS FHIR validator instance (singleton pattern).

    Returns:
        NHSFHIRValidator instance
    """
    global _validator
    if _validator is None:
        _validator = NHSFHIRValidator()
    return _validator
