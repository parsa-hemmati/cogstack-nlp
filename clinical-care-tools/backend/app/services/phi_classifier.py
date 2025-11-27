"""
PHI Classifier Service.

Maps CogStack-ModelServe entity types to our PHI categories for database storage.

CogStack-ModelServe's DeID model already classifies PHI by type (Person, NHS Number, etc.).
This service provides a simple mapping layer from their types to our database schema.

Categories:
- phi_name: Patient/person names
- phi_nhs_number: NHS numbers or medical record numbers
- phi_dob: Date of birth
- phi_date: Other dates
- phi_address: Addresses and locations
- phi_phone: Phone numbers
- phi_email: Email addresses
- clinical: Clinical entities (SNOMED-CT, UMLS, etc.)

Usage:
    >>> from app.services.phi_classifier import classify_entity
    >>>
    >>> entity = {
    ...     "types": ["Person"],
    ...     "pretty_name": "John Doe",
    ...     "cui": "PHI-PERSON"
    ... }
    >>> category = classify_entity(entity)
    >>> print(category)
    'phi_name'
    >>>
    >>> clinical_entity = {
    ...     "types": ["Disorder"],
    ...     "pretty_name": "Diabetes Mellitus",
    ...     "cui": "C0011849"
    ... }
    >>> category = classify_entity(clinical_entity)
    >>> print(category)
    'clinical'
"""

from typing import Dict, List, Any


def classify_entity(entity: Dict[str, Any]) -> str:
    """
    Classify entity from CogStack-ModelServe as PHI or clinical.

    Maps CogStack-ModelServe entity types to our PHI categories for database storage.

    Args:
        entity: Entity dict from CogStack-ModelServe with:
            - types: List of entity types (e.g., ["Person"], ["NHS Number"])
            - pretty_name: Entity text (used for DOB detection)
            - cui: Concept unique identifier

    Returns:
        str: PHI category:
            - "phi_name": Patient/person names
            - "phi_nhs_number": NHS numbers or medical record numbers
            - "phi_dob": Date of birth
            - "phi_date": Other dates
            - "phi_address": Addresses and locations
            - "phi_phone": Phone numbers
            - "phi_email": Email addresses
            - "clinical": Clinical entities (SNOMED-CT, UMLS)

    Classification Rules (in priority order):
        1. Person, Name → phi_name
        2. NHS Number, Medical Record Number → phi_nhs_number
        3. Phone, Contact → phi_phone
        4. Email → phi_email
        5. Address, Location → phi_address
        6. Date + ("birth" or "dob" in text) → phi_dob
        7. Date → phi_date
        8. Everything else → clinical

    Example:
        >>> # PHI entity (name)
        >>> entity = {"types": ["Person"], "pretty_name": "Jane Doe", "cui": "PHI-PERSON"}
        >>> classify_entity(entity)
        'phi_name'

        >>> # PHI entity (NHS number)
        >>> entity = {"types": ["NHS Number"], "pretty_name": "123 456 7890", "cui": "PHI-NHS"}
        >>> classify_entity(entity)
        'phi_nhs_number'

        >>> # PHI entity (DOB)
        >>> entity = {"types": ["Date"], "pretty_name": "dob 01/01/1980", "cui": "PHI-DATE"}
        >>> classify_entity(entity)
        'phi_dob'

        >>> # Clinical entity (SNOMED)
        >>> entity = {"types": ["Disorder"], "pretty_name": "Diabetes", "cui": "C0011849"}
        >>> classify_entity(entity)
        'clinical'
    """
    # Get entity types (case-insensitive)
    types = entity.get("types", [])
    types_lower = [t.lower() for t in types]

    # Get pretty_name for DOB detection
    pretty_name = entity.get("pretty_name", "").lower()

    # Classification rules (priority order)

    # 1. Person/Name → phi_name
    if any(t in types_lower for t in ["person", "name"]):
        return "phi_name"

    # 2. NHS Number / Medical Record Number → phi_nhs_number
    if any(t in types_lower for t in ["nhs number", "medical record number", "mrn"]):
        return "phi_nhs_number"

    # 3. Phone/Contact → phi_phone
    if any(t in types_lower for t in ["phone", "contact", "telephone"]):
        return "phi_phone"

    # 4. Email → phi_email
    if "email" in types_lower:
        return "phi_email"

    # 5. Address/Location → phi_address
    if any(t in types_lower for t in ["address", "location"]):
        return "phi_address"

    # 6. Date + birth context → phi_dob
    if "date" in types_lower:
        # Check if date is related to birth
        if any(keyword in pretty_name for keyword in ["birth", "dob", "born"]):
            return "phi_dob"
        else:
            # Regular date
            return "phi_date"

    # 7. Everything else (including clinical entities) → clinical
    return "clinical"


def is_phi_entity(category: str) -> bool:
    """
    Check if entity category is PHI.

    Args:
        category: Entity category from classify_entity()

    Returns:
        bool: True if category is PHI, False if clinical

    Example:
        >>> is_phi_entity("phi_name")
        True
        >>> is_phi_entity("clinical")
        False
    """
    return category.startswith("phi_")


def get_phi_categories() -> List[str]:
    """
    Get list of all PHI categories.

    Returns:
        List[str]: All PHI category names

    Example:
        >>> categories = get_phi_categories()
        >>> print(categories)
        ['phi_name', 'phi_nhs_number', 'phi_dob', 'phi_date', 'phi_address', 'phi_phone', 'phi_email']
    """
    return [
        "phi_name",
        "phi_nhs_number",
        "phi_dob",
        "phi_date",
        "phi_address",
        "phi_phone",
        "phi_email",
    ]
