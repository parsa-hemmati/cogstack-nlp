"""
Unit tests for PHI Classifier Service

Tests PHI detection, classification, and de-identification functionality.
"""

import pytest
from app.services.phi_classifier import PHIClassifier, PHIType, PHICategory


@pytest.fixture
def phi_classifier():
    """Create PHI classifier instance."""
    return PHIClassifier()


class TestPHIClassifier:
    """Test PHI classifier functionality."""

    def test_detect_nhs_number(self, phi_classifier):
        """Test NHS number detection."""
        text = "Patient NHS number: 123 456 7890"
        results = phi_classifier.detect_phi(text)

        assert len(results) > 0
        nhs_entities = [r for r in results if r["phi_type"] == PHIType.NHS_NUMBER.value]
        assert len(nhs_entities) == 1
        assert "123 456 7890" in nhs_entities[0]["text"]

    def test_validate_nhs_number_valid(self, phi_classifier):
        """Test valid NHS number validation."""
        # This is a valid test NHS number with correct checksum
        valid_nhs = "9434765919"
        result = phi_classifier._validate_nhs_number(valid_nhs)
        assert result is True

    def test_validate_nhs_number_invalid_checksum(self, phi_classifier):
        """Test invalid NHS number checksum."""
        invalid_nhs = "1234567890"
        result = phi_classifier._validate_nhs_number(invalid_nhs)
        assert result is False

    def test_validate_nhs_number_invalid_length(self, phi_classifier):
        """Test NHS number with invalid length."""
        invalid_nhs = "12345"
        result = phi_classifier._validate_nhs_number(invalid_nhs)
        assert result is False

    def test_detect_names_with_titles(self, phi_classifier):
        """Test name detection with titles."""
        text = "Seen by Dr Smith and Mrs Johnson today."
        results = phi_classifier.detect_phi(text)

        name_entities = [r for r in results if r["phi_type"] == PHIType.NAME.value]
        assert len(name_entities) >= 2
        assert any("Dr Smith" in r["text"] for r in name_entities)
        assert any("Mrs Johnson" in r["text"] for r in name_entities)

    def test_detect_email_addresses(self, phi_classifier):
        """Test email address detection."""
        text = "Contact patient at john.smith@example.com"
        results = phi_classifier.detect_phi(text)

        email_entities = [r for r in results if r["phi_type"] == PHIType.EMAIL.value]
        assert len(email_entities) == 1
        assert email_entities[0]["text"] == "john.smith@example.com"
        assert email_entities[0]["confidence"] == 0.95

    def test_detect_phone_numbers_uk_format(self, phi_classifier):
        """Test UK phone number detection."""
        text = "Call patient on 07123 456789 or +44 20 7123 4567"
        results = phi_classifier.detect_phi(text)

        phone_entities = [r for r in results if r["phi_type"] == PHIType.PHONE.value]
        assert len(phone_entities) >= 1

    def test_detect_uk_postcodes(self, phi_classifier):
        """Test UK postcode detection."""
        text = "Patient lives at SW1A 1AA, London"
        results = phi_classifier.detect_phi(text)

        postcode_entities = [r for r in results if r["phi_type"] == PHIType.POSTCODE.value]
        assert len(postcode_entities) == 1
        assert postcode_entities[0]["text"].upper() == "SW1A 1AA"

    def test_detect_dates(self, phi_classifier):
        """Test date detection in various formats."""
        text = "Born on 15/03/1980. Admitted 2023-01-15. Seen 5 Jan 2024."
        results = phi_classifier.detect_phi(text)

        date_entities = [r for r in results if r["phi_type"] == PHIType.DATE.value]
        assert len(date_entities) >= 3

    def test_detect_age_over_89(self, phi_classifier):
        """Test detection of age over 89 (HIPAA requirement)."""
        text = "Patient is 92 years old"
        results = phi_classifier.detect_phi(text)

        age_entities = [r for r in results if r["phi_type"] == PHIType.AGE.value]
        assert len(age_entities) == 1
        assert "92" in age_entities[0]["text"]

    def test_detect_addresses(self, phi_classifier):
        """Test UK address detection."""
        text = "Lives at 123 High Street, London"
        results = phi_classifier.detect_phi(text)

        address_entities = [r for r in results if r["phi_type"] == PHIType.ADDRESS.value]
        assert len(address_entities) >= 1

    def test_categorize_phi_direct_identifier(self, phi_classifier):
        """Test PHI categorization for direct identifiers."""
        assert phi_classifier._categorize_phi(PHIType.NAME) == PHICategory.DIRECT_IDENTIFIER
        assert phi_classifier._categorize_phi(PHIType.NHS_NUMBER) == PHICategory.DIRECT_IDENTIFIER
        assert phi_classifier._categorize_phi(PHIType.EMAIL) == PHICategory.DIRECT_IDENTIFIER

    def test_categorize_phi_quasi_identifier(self, phi_classifier):
        """Test PHI categorization for quasi-identifiers."""
        assert phi_classifier._categorize_phi(PHIType.DATE) == PHICategory.QUASI_IDENTIFIER
        assert phi_classifier._categorize_phi(PHIType.POSTCODE) == PHICategory.QUASI_IDENTIFIER
        assert phi_classifier._categorize_phi(PHIType.AGE) == PHICategory.QUASI_IDENTIFIER

    def test_calculate_reidentification_risk_very_high(self, phi_classifier):
        """Test re-identification risk calculation with direct identifiers."""
        phi_entities = [
            {"category": PHICategory.DIRECT_IDENTIFIER, "phi_type": "NAME"},
            {"category": PHICategory.DIRECT_IDENTIFIER, "phi_type": "NHS_NUMBER"}
        ]

        risk = phi_classifier.calculate_reidentification_risk(phi_entities)

        assert risk["risk_level"] == "VERY_HIGH"
        assert risk["risk_score"] >= 0.9
        assert risk["direct_identifiers"] == 2
        assert risk["requires_deidentification"] is True

    def test_calculate_reidentification_risk_medium(self, phi_classifier):
        """Test re-identification risk calculation with quasi-identifiers."""
        phi_entities = [
            {"category": PHICategory.QUASI_IDENTIFIER, "phi_type": "DATE"},
            {"category": PHICategory.QUASI_IDENTIFIER, "phi_type": "POSTCODE"}
        ]

        risk = phi_classifier.calculate_reidentification_risk(phi_entities)

        assert risk["risk_level"] == "MEDIUM"
        assert risk["risk_score"] == 0.5
        assert risk["quasi_identifiers"] == 2

    def test_redact_phi(self, phi_classifier):
        """Test PHI redaction."""
        text = "Patient John Smith, NHS: 1234567890"
        phi_entities = [
            {"text": "John Smith", "start": 8, "end": 18, "phi_type": "NAME"},
            {"text": "1234567890", "start": 25, "end": 35, "phi_type": "NHS_NUMBER"}
        ]

        redacted = phi_classifier.redact_phi(text, phi_entities)

        assert "John Smith" not in redacted
        assert "1234567890" not in redacted
        assert "██████████" in redacted  # Redaction characters

    def test_pseudonymize_phi(self, phi_classifier):
        """Test PHI pseudonymization."""
        text = "Patient John Smith, DOB: 01/01/1980"
        phi_entities = [
            {"text": "John Smith", "start": 8, "end": 18, "phi_type": "NAME"},
            {"text": "01/01/1980", "start": 25, "end": 35, "phi_type": "DATE"}
        ]

        pseudonymized, mapping = phi_classifier.pseudonymize_phi(text, phi_entities)

        assert "John Smith" not in pseudonymized
        assert "PATIENT_001" in pseudonymized
        assert "01/01/1980" not in pseudonymized
        assert "[DATE_01]" in pseudonymized
        assert mapping["John Smith"] == "PATIENT_001"
        assert mapping["01/01/1980"] == "[DATE_01]"

    def test_extract_structured_data_name(self, phi_classifier):
        """Test structured data extraction for names."""
        result = phi_classifier._extract_structured_data(
            PHIType.NAME,
            "Dr John Smith"
        )

        assert result["title"] == "Dr"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Smith"

    def test_extract_structured_data_nhs_number(self, phi_classifier):
        """Test structured data extraction for NHS numbers."""
        result = phi_classifier._extract_structured_data(
            PHIType.NHS_NUMBER,
            "123-456-7890"
        )

        assert result["nhs_number"] == "1234567890"

    def test_extract_structured_data_postcode(self, phi_classifier):
        """Test structured data extraction for postcodes."""
        result = phi_classifier._extract_structured_data(
            PHIType.POSTCODE,
            "sw1a 1aa"
        )

        assert result["postcode"] == "SW1A 1AA"