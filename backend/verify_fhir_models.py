#!/usr/bin/env python3
"""Simple verification script for FHIR models and NHS number validation.

This script can be run independently to verify the NHS number validation
logic works correctly without requiring the full test infrastructure.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from schemas.cds.fhir_models import validate_nhs_number, NHSNumberValidationError


def test_nhs_number_validation():
    """Run basic NHS number validation tests."""

    print("Testing NHS Number Validation (Modulus 11 Algorithm)")
    print("=" * 60)

    # Test 1: Valid NHS number
    test_cases = [
        ("9434765870", True, "Valid NHS number"),
        ("943 476 5870", True, "Valid with spaces"),
        ("943-476-5870", True, "Valid with hyphens"),
        ("9434765871", False, "Invalid checksum"),
        ("1234567890", False, "Check digit 10 (invalid)"),
    ]

    passed = 0
    failed = 0

    for nhs_number, expected, description in test_cases:
        try:
            result = validate_nhs_number(nhs_number)
            status = "✓ PASS" if result == expected else "✗ FAIL"
            if result == expected:
                passed += 1
            else:
                failed += 1
            print(f"{status}: {description} ('{nhs_number}') -> {result}")
        except Exception as e:
            if not expected:
                passed += 1
                print(f"✓ PASS: {description} ('{nhs_number}') -> Exception: {type(e).__name__}")
            else:
                failed += 1
                print(f"✗ FAIL: {description} ('{nhs_number}') -> Unexpected exception: {e}")

    # Test 2: Invalid formats (should raise NHSNumberValidationError)
    print("\nTesting invalid formats (should raise exceptions):")
    invalid_formats = [
        ("12345", "Too short"),
        ("12345678901", "Too long"),
        ("943ABC5870", "Contains letters"),
    ]

    for nhs_number, description in invalid_formats:
        try:
            validate_nhs_number(nhs_number)
            failed += 1
            print(f"✗ FAIL: {description} ('{nhs_number}') -> Should have raised exception")
        except NHSNumberValidationError as e:
            passed += 1
            print(f"✓ PASS: {description} ('{nhs_number}') -> {type(e).__name__}")
        except Exception as e:
            failed += 1
            print(f"✗ FAIL: {description} ('{nhs_number}') -> Wrong exception: {type(e).__name__}")

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = test_nhs_number_validation()
    sys.exit(0 if success else 1)
