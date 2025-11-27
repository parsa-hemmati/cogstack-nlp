"""
Unit tests for PHI Classifier Service.

Tests mapping of CogStack-ModelServe entity types to our PHI categories.
"""

import pytest

from app.services.phi_classifier import classify_entity


def test_classify_person_as_phi_name():
    """Test that Person type is classified as phi_name."""
    entity = {
        "types": ["Person"],
        "pretty_name": "John Doe",
        "cui": "PHI-PERSON"
    }

    result = classify_entity(entity)

    assert result == "phi_name"


def test_classify_name_as_phi_name():
    """Test that Name type is classified as phi_name."""
    entity = {
        "types": ["Name"],
        "pretty_name": "Jane Smith",
        "cui": "PHI-NAME"
    }

    result = classify_entity(entity)

    assert result == "phi_name"


def test_classify_nhs_number_as_phi_nhs_number():
    """Test that NHS Number type is classified as phi_nhs_number."""
    entity = {
        "types": ["NHS Number"],
        "pretty_name": "123 456 7890",
        "cui": "PHI-NHS-NUMBER"
    }

    result = classify_entity(entity)

    assert result == "phi_nhs_number"


def test_classify_medical_record_number_as_phi_nhs_number():
    """Test that Medical Record Number is classified as phi_nhs_number."""
    entity = {
        "types": ["Medical Record Number"],
        "pretty_name": "MRN-12345",
        "cui": "PHI-MRN"
    }

    result = classify_entity(entity)

    assert result == "phi_nhs_number"


def test_classify_address_as_phi_address():
    """Test that Address type is classified as phi_address."""
    entity = {
        "types": ["Address"],
        "pretty_name": "123 Main Street, London",
        "cui": "PHI-ADDRESS"
    }

    result = classify_entity(entity)

    assert result == "phi_address"


def test_classify_location_as_phi_address():
    """Test that Location type is classified as phi_address."""
    entity = {
        "types": ["Location"],
        "pretty_name": "Manchester Royal Infirmary",
        "cui": "PHI-LOCATION"
    }

    result = classify_entity(entity)

    assert result == "phi_address"


def test_classify_date_of_birth_as_phi_dob():
    """Test that Date with 'birth' context is classified as phi_dob."""
    entity = {
        "types": ["Date"],
        "pretty_name": "date of birth 01/01/1980",
        "cui": "PHI-DATE"
    }

    result = classify_entity(entity)

    assert result == "phi_dob"


def test_classify_dob_as_phi_dob():
    """Test that Date with 'dob' context is classified as phi_dob."""
    entity = {
        "types": ["Date"],
        "pretty_name": "DOB: 15-Mar-1975",
        "cui": "PHI-DATE"
    }

    result = classify_entity(entity)

    assert result == "phi_dob"


def test_classify_regular_date_as_phi_date():
    """Test that Date without birth context is classified as phi_date."""
    entity = {
        "types": ["Date"],
        "pretty_name": "15-11-2023",
        "cui": "PHI-DATE"
    }

    result = classify_entity(entity)

    assert result == "phi_date"


def test_classify_phone_as_phi_phone():
    """Test that Phone type is classified as phi_phone."""
    entity = {
        "types": ["Phone", "Contact"],
        "pretty_name": "020 7946 0958",
        "cui": "PHI-PHONE"
    }

    result = classify_entity(entity)

    assert result == "phi_phone"


def test_classify_email_as_phi_email():
    """Test that Email type is classified as phi_email."""
    entity = {
        "types": ["Email"],
        "pretty_name": "patient@example.com",
        "cui": "PHI-EMAIL"
    }

    result = classify_entity(entity)

    assert result == "phi_email"


def test_classify_clinical_entity():
    """Test that SNOMED clinical entities are classified as clinical."""
    entity = {
        "types": ["Disorder"],
        "pretty_name": "Diabetes Mellitus",
        "cui": "C0011849"
    }

    result = classify_entity(entity)

    assert result == "clinical"


def test_classify_entity_with_multiple_types():
    """Test that entity with multiple types uses first matching rule."""
    entity = {
        "types": ["Person", "Location"],  # Person should take precedence
        "pretty_name": "Dr. Smith",
        "cui": "PHI-PERSON"
    }

    result = classify_entity(entity)

    assert result == "phi_name"


def test_classify_entity_with_unknown_type():
    """Test that unknown PHI types default to clinical."""
    entity = {
        "types": ["Unknown"],
        "pretty_name": "Some unknown entity",
        "cui": "UNKNOWN"
    }

    result = classify_entity(entity)

    assert result == "clinical"


def test_classify_entity_without_types():
    """Test that entity without types field defaults to clinical."""
    entity = {
        "pretty_name": "Some entity",
        "cui": "C1234567"
    }

    result = classify_entity(entity)

    assert result == "clinical"


def test_classify_entity_with_empty_types():
    """Test that entity with empty types list defaults to clinical."""
    entity = {
        "types": [],
        "pretty_name": "Empty types entity",
        "cui": "C1234567"
    }

    result = classify_entity(entity)

    assert result == "clinical"


def test_classify_entity_case_insensitive():
    """Test that classification is case insensitive."""
    entity = {
        "types": ["person"],  # lowercase
        "pretty_name": "Test Person",
        "cui": "PHI-PERSON"
    }

    result = classify_entity(entity)

    assert result == "phi_name"
