"""
PHI Classifier Service

Specialized service for PHI detection, classification, and de-identification.
Implements HIPAA Safe Harbor method and custom UK healthcare identifiers.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from enum import Enum

import structlog

logger = structlog.get_logger()


class PHIType(str, Enum):
    """HIPAA PHI types plus UK-specific identifiers."""
    # Direct Identifiers
    NAME = "NAME"
    NHS_NUMBER = "NHS_NUMBER"
    MRN = "MEDICAL_RECORD_NUMBER"
    SSN = "SOCIAL_SECURITY_NUMBER"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    FAX = "FAX"
    DEVICE_ID = "DEVICE_ID"
    URL = "URL"
    IP_ADDRESS = "IP_ADDRESS"
    BIOMETRIC = "BIOMETRIC"
    PHOTO = "PHOTO"
    UNIQUE_ID = "UNIQUE_ID"

    # Quasi-Identifiers
    DATE = "DATE"
    ADDRESS = "ADDRESS"
    POSTCODE = "POSTCODE"
    AGE = "AGE"
    LOCATION = "LOCATION"
    VEHICLE_ID = "VEHICLE_ID"

    # Clinical Data
    DIAGNOSIS = "DIAGNOSIS"
    PROCEDURE = "PROCEDURE"
    MEDICATION = "MEDICATION"
    LAB_RESULT = "LAB_RESULT"


class PHICategory(str, Enum):
    """PHI categorization for risk assessment."""
    DIRECT_IDENTIFIER = "DIRECT_IDENTIFIER"
    QUASI_IDENTIFIER = "QUASI_IDENTIFIER"
    CLINICAL_DATA = "CLINICAL_DATA"


class PHIClassifier:
    """
    Service for PHI detection and classification.

    Features:
    - UK NHS number detection and validation
    - Name detection with title recognition
    - Date detection and classification
    - Address and postcode detection
    - Email, phone, and URL detection
    - Risk scoring for re-identification
    """

    def __init__(self):
        """Initialize PHI classifier with regex patterns."""
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for PHI detection."""
        self.patterns = {
            # UK NHS Number (10 digits, with checksum validation)
            PHIType.NHS_NUMBER: re.compile(
                r'\b(?:\d[ -]?){9}\d\b'
            ),

            # Medical Record Number (various formats)
            PHIType.MRN: re.compile(
                r'\b(?:MRN|Medical Record Number|Hospital Number)[:\s]*([A-Z0-9]{6,12})\b',
                re.IGNORECASE
            ),

            # Names with titles
            PHIType.NAME: re.compile(
                r'\b(?:Mr|Mrs|Miss|Ms|Dr|Prof|Sir|Lady|Lord)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            ),

            # Email addresses
            PHIType.EMAIL: re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            ),

            # Phone numbers (UK format)
            PHIType.PHONE: re.compile(
                r'\b(?:\+44|0)(?:\d{10}|\d{4}\s?\d{6}|\d{3}\s?\d{3}\s?\d{4})\b'
            ),

            # UK Postcodes
            PHIType.POSTCODE: re.compile(
                r'\b[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2}\b',
                re.IGNORECASE
            ),

            # Dates (various formats)
            PHIType.DATE: re.compile(
                r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}|'
                r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b',
                re.IGNORECASE
            ),

            # URLs
            PHIType.URL: re.compile(
                r'https?://[^\s<>"{}|\\^`\[\]]+'
            ),

            # IP Addresses
            PHIType.IP_ADDRESS: re.compile(
                r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
                r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            ),

            # Age (when > 89)
            PHIType.AGE: re.compile(
                r'\b(?:age[d]?\s*[:=]?\s*)?([9][0-9]|1[0-9]{2})\s*(?:year|yr)s?\s*(?:old)?\b',
                re.IGNORECASE
            ),
        }

    def detect_phi(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect all PHI in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected PHI entities with positions
        """
        phi_entities = []

        for phi_type, pattern in self.patterns.items():
            for match in pattern.finditer(text):
                entity = {
                    "phi_type": phi_type.value,
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "category": self._categorize_phi(phi_type),
                    "confidence": self._calculate_confidence(phi_type, match.group())
                }

                # Special validation for NHS numbers
                if phi_type == PHIType.NHS_NUMBER:
                    if self._validate_nhs_number(match.group()):
                        entity["confidence"] = 0.95
                    else:
                        entity["confidence"] = 0.5

                # Extract structured data
                entity["structured_data"] = self._extract_structured_data(
                    phi_type, match.group()
                )

                phi_entities.append(entity)

        # Detect addresses (more complex pattern)
        phi_entities.extend(self._detect_addresses(text))

        # Sort by position
        phi_entities.sort(key=lambda x: x["start"])

        return phi_entities

    def _categorize_phi(self, phi_type: PHIType) -> PHICategory:
        """
        Categorize PHI type into risk categories.

        Args:
            phi_type: Type of PHI

        Returns:
            PHI category
        """
        direct_identifiers = {
            PHIType.NAME, PHIType.NHS_NUMBER, PHIType.MRN,
            PHIType.SSN, PHIType.EMAIL, PHIType.PHONE,
            PHIType.FAX, PHIType.DEVICE_ID, PHIType.URL,
            PHIType.IP_ADDRESS, PHIType.BIOMETRIC, PHIType.PHOTO,
            PHIType.UNIQUE_ID
        }

        quasi_identifiers = {
            PHIType.DATE, PHIType.ADDRESS, PHIType.POSTCODE,
            PHIType.AGE, PHIType.LOCATION, PHIType.VEHICLE_ID
        }

        if phi_type in direct_identifiers:
            return PHICategory.DIRECT_IDENTIFIER
        elif phi_type in quasi_identifiers:
            return PHICategory.QUASI_IDENTIFIER
        else:
            return PHICategory.CLINICAL_DATA

    def _calculate_confidence(self, phi_type: PHIType, text: str) -> float:
        """
        Calculate confidence score for PHI detection.

        Args:
            phi_type: Type of PHI
            text: Detected text

        Returns:
            Confidence score (0.0-1.0)
        """
        # High confidence for structured identifiers
        if phi_type in [PHIType.EMAIL, PHIType.URL, PHIType.IP_ADDRESS]:
            return 0.95

        # Medium-high for formatted numbers
        if phi_type in [PHIType.NHS_NUMBER, PHIType.PHONE, PHIType.POSTCODE]:
            return 0.85

        # Medium for dates and names
        if phi_type in [PHIType.DATE, PHIType.NAME]:
            return 0.75

        # Default
        return 0.7

    def _validate_nhs_number(self, nhs_number: str) -> bool:
        """
        Validate UK NHS number using modulus 11 algorithm.

        Args:
            nhs_number: NHS number string

        Returns:
            True if valid NHS number
        """
        # Remove spaces and hyphens
        nhs_clean = re.sub(r'[^0-9]', '', nhs_number)

        if len(nhs_clean) != 10:
            return False

        # Modulus 11 algorithm
        try:
            digits = [int(d) for d in nhs_clean]
            weights = [10, 9, 8, 7, 6, 5, 4, 3, 2]

            total = sum(d * w for d, w in zip(digits[:-1], weights))
            remainder = total % 11
            check_digit = 11 - remainder

            if check_digit == 11:
                check_digit = 0
            elif check_digit == 10:
                return False  # Invalid

            return digits[-1] == check_digit

        except (ValueError, IndexError):
            return False

    def _detect_addresses(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect UK addresses in text.

        Args:
            text: Text to analyze

        Returns:
            List of detected address entities
        """
        addresses = []

        # Look for common UK address patterns
        # e.g., "123 High Street, London, SW1A 1AA"
        address_pattern = re.compile(
            r'\b\d+\s+[A-Z][a-z]+\s+(?:Street|Road|Lane|Avenue|Close|Drive|Way|Place)'
            r'(?:,\s*[A-Z][a-z]+)?(?:,\s*[A-Z]{1,2}[0-9][0-9A-Z]?\s?[0-9][A-Z]{2})?\b',
            re.IGNORECASE
        )

        for match in address_pattern.finditer(text):
            addresses.append({
                "phi_type": PHIType.ADDRESS.value,
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "category": PHICategory.QUASI_IDENTIFIER,
                "confidence": 0.8,
                "structured_data": {"address_text": match.group()}
            })

        return addresses

    def _extract_structured_data(
        self,
        phi_type: PHIType,
        text: str
    ) -> Dict[str, Any]:
        """
        Extract structured data from PHI text.

        Args:
            phi_type: Type of PHI
            text: PHI text

        Returns:
            Structured data dictionary
        """
        structured = {}

        if phi_type == PHIType.NAME:
            # Parse name components
            parts = text.split()
            if len(parts) > 0:
                # Remove title if present
                if parts[0] in ['Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Prof']:
                    structured["title"] = parts[0]
                    parts = parts[1:]

                if len(parts) > 0:
                    structured["first_name"] = parts[0]
                if len(parts) > 1:
                    structured["last_name"] = " ".join(parts[1:])

        elif phi_type == PHIType.NHS_NUMBER:
            structured["nhs_number"] = re.sub(r'[^0-9]', '', text)

        elif phi_type == PHIType.EMAIL:
            structured["email"] = text.lower()

        elif phi_type == PHIType.PHONE:
            structured["phone"] = re.sub(r'[^0-9+]', '', text)

        elif phi_type == PHIType.POSTCODE:
            structured["postcode"] = text.upper()

        elif phi_type == PHIType.DATE:
            structured["date_string"] = text
            # Try to parse date
            try:
                # Simple date parsing (extend as needed)
                for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"]:
                    try:
                        dt = datetime.strptime(text, fmt)
                        structured["date"] = dt.isoformat()
                        break
                    except ValueError:
                        continue
            except:
                pass

        elif phi_type == PHIType.AGE:
            # Extract numeric age
            age_match = re.search(r'\d+', text)
            if age_match:
                structured["age"] = int(age_match.group())

        return structured

    def calculate_reidentification_risk(
        self,
        phi_entities: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate re-identification risk based on detected PHI.

        Args:
            phi_entities: List of detected PHI entities

        Returns:
            Risk assessment dictionary
        """
        # Count PHI by category
        direct_count = sum(
            1 for e in phi_entities
            if e["category"] == PHICategory.DIRECT_IDENTIFIER
        )
        quasi_count = sum(
            1 for e in phi_entities
            if e["category"] == PHICategory.QUASI_IDENTIFIER
        )

        # Calculate risk score
        risk_score = 0.0

        # Direct identifiers = very high risk
        if direct_count > 0:
            risk_score = 0.9 + (0.1 * min(direct_count - 1, 1))

        # Multiple quasi-identifiers = increasing risk
        elif quasi_count >= 3:
            risk_score = 0.7
        elif quasi_count == 2:
            risk_score = 0.5
        elif quasi_count == 1:
            risk_score = 0.3

        # Determine risk level
        if risk_score >= 0.9:
            risk_level = "VERY_HIGH"
        elif risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.5:
            risk_level = "MEDIUM"
        elif risk_score >= 0.3:
            risk_level = "LOW"
        else:
            risk_level = "VERY_LOW"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "direct_identifiers": direct_count,
            "quasi_identifiers": quasi_count,
            "total_phi": len(phi_entities),
            "requires_deidentification": risk_score >= 0.5
        }

    def redact_phi(
        self,
        text: str,
        phi_entities: List[Dict[str, Any]],
        redaction_char: str = "█"
    ) -> str:
        """
        Redact PHI from text.

        Args:
            text: Original text
            phi_entities: List of PHI entities to redact
            redaction_char: Character to use for redaction

        Returns:
            Redacted text
        """
        # Sort entities by position (reverse order for replacement)
        sorted_entities = sorted(
            phi_entities,
            key=lambda x: x["start"],
            reverse=True
        )

        redacted_text = text
        for entity in sorted_entities:
            # Replace with redaction characters
            redaction = redaction_char * len(entity["text"])

            # Or use category-based replacement
            # redaction = f"[{entity['phi_type']}]"

            redacted_text = (
                redacted_text[:entity["start"]] +
                redaction +
                redacted_text[entity["end"]:]
            )

        return redacted_text

    def pseudonymize_phi(
        self,
        text: str,
        phi_entities: List[Dict[str, Any]]
    ) -> Tuple[str, Dict[str, str]]:
        """
        Replace PHI with pseudonyms.

        Args:
            text: Original text
            phi_entities: List of PHI entities

        Returns:
            Tuple of (pseudonymized text, mapping dictionary)
        """
        # Sort entities by position (reverse order)
        sorted_entities = sorted(
            phi_entities,
            key=lambda x: x["start"],
            reverse=True
        )

        pseudonymized_text = text
        mapping = {}
        counters = {}

        for entity in sorted_entities:
            phi_type = entity["phi_type"]

            # Generate consistent pseudonym
            if phi_type not in counters:
                counters[phi_type] = 1
            else:
                counters[phi_type] += 1

            # Create pseudonym based on type
            if phi_type == "NAME":
                pseudonym = f"PATIENT_{counters[phi_type]:03d}"
            elif phi_type == "NHS_NUMBER":
                pseudonym = f"NHS_{counters[phi_type]:010d}"
            elif phi_type == "DATE":
                pseudonym = f"[DATE_{counters[phi_type]:02d}]"
            elif phi_type == "ADDRESS":
                pseudonym = f"[ADDRESS_{counters[phi_type]:02d}]"
            else:
                pseudonym = f"[{phi_type}_{counters[phi_type]:02d}]"

            # Store mapping
            mapping[entity["text"]] = pseudonym

            # Replace in text
            pseudonymized_text = (
                pseudonymized_text[:entity["start"]] +
                pseudonym +
                pseudonymized_text[entity["end"]:]
            )

        return pseudonymized_text, mapping