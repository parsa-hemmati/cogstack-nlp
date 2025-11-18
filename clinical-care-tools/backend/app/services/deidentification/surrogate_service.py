"""Surrogate Generation Service (Sprint 4, Phase 4.2, Task 4.2.1)

Generates human-readable surrogates for PHI entities:
- PERSON: Patient-A, Patient-B, Patient-C, ...
- DATE: Mask year (01/15/19XX)
- ID: ID-0001, ID-0002, ...
- LOCATION: Address-1, Address-2, ...
- PHONE: Phone-1, Phone-2, ...
- EMAIL: email-1@example.com, email-2@example.com, ...
"""

import re
from typing import Dict, List
from app.schemas.phi import DetectedEntity, PHIEntityType


class SurrogateGenerationService:
    """Service for generating surrogates for PHI entities"""

    def __init__(self):
        """Initialize surrogate generation service"""
        self.counters: Dict[PHIEntityType, int] = {
            PHIEntityType.PERSON: 0,
            PHIEntityType.DATE: 0,
            PHIEntityType.ID: 0,
            PHIEntityType.LOCATION: 0,
            PHIEntityType.PHONE: 0,
            PHIEntityType.EMAIL: 0,
            PHIEntityType.ORGANIZATION: 0,
            PHIEntityType.AGE: 0
        }

    def generate_surrogates(self, entities: List[DetectedEntity]) -> Dict[str, str]:
        """Generate surrogates for detected entities

        Maintains consistency: same original text gets same surrogate.

        Args:
            entities: List of detected PHI entities

        Returns:
            Dictionary mapping original text to surrogate value

        Example:
            {
                "John Doe": "Patient-A",
                "Jane Smith": "Patient-B",
                "01/15/1980": "01/15/19XX",
                "123-45-6789": "ID-0001"
            }
        """
        entity_mappings: Dict[str, str] = {}

        for entity in entities:
            original = entity.text

            # Skip if already mapped (consistency)
            if original in entity_mappings:
                continue

            # Generate surrogate based on entity type
            surrogate = self._generate_surrogate(entity)
            entity_mappings[original] = surrogate

        return entity_mappings

    def _generate_surrogate(self, entity: DetectedEntity) -> str:
        """Generate surrogate for a single entity

        Args:
            entity: Detected PHI entity

        Returns:
            Surrogate value
        """
        original = entity.text
        entity_type = entity.label

        if entity_type == PHIEntityType.PERSON:
            # Person: Patient-A, Patient-B, ..., Patient-Z, Patient-AA, ...
            self.counters[PHIEntityType.PERSON] += 1
            suffix = self._number_to_alpha(self.counters[PHIEntityType.PERSON])
            return f"Patient-{suffix}"

        elif entity_type == PHIEntityType.DATE:
            # Date: Mask year but keep month/day for temporal analysis
            # 01/15/1980 → 01/15/19XX
            # 2023-11-17 → 2023-11-XX
            return self._mask_date(original)

        elif entity_type == PHIEntityType.ID:
            # ID: ID-0001, ID-0002, ...
            self.counters[PHIEntityType.ID] += 1
            return f"ID-{self.counters[PHIEntityType.ID]:04d}"

        elif entity_type == PHIEntityType.LOCATION:
            # Location: Address-1, Address-2, ...
            self.counters[PHIEntityType.LOCATION] += 1
            return f"Address-{self.counters[PHIEntityType.LOCATION]}"

        elif entity_type == PHIEntityType.PHONE:
            # Phone: Phone-1, Phone-2, ...
            self.counters[PHIEntityType.PHONE] += 1
            return f"Phone-{self.counters[PHIEntityType.PHONE]}"

        elif entity_type == PHIEntityType.EMAIL:
            # Email: email-1@example.com, email-2@example.com, ...
            self.counters[PHIEntityType.EMAIL] += 1
            return f"email-{self.counters[PHIEntityType.EMAIL]}@example.com"

        elif entity_type == PHIEntityType.ORGANIZATION:
            # Organization: Org-1, Org-2, ...
            self.counters[PHIEntityType.ORGANIZATION] += 1
            return f"Organization-{self.counters[PHIEntityType.ORGANIZATION]}"

        elif entity_type == PHIEntityType.AGE:
            # Age: Mask specific age (92 → 90+)
            return "90+"

        else:
            # Fallback for unknown types
            return "[REDACTED]"

    def _number_to_alpha(self, num: int) -> str:
        """Convert number to alphabetic sequence

        Examples:
            1 → A
            2 → B
            26 → Z
            27 → AA
            28 → AB

        Args:
            num: Number to convert (1-indexed)

        Returns:
            Alphabetic sequence
        """
        result = ""
        num -= 1  # Convert to 0-indexed

        while True:
            result = chr(ord('A') + (num % 26)) + result
            num = num // 26
            if num == 0:
                break
            num -= 1  # Adjust for 0-indexing

        return result

    def _mask_date(self, date_str: str) -> str:
        """Mask date while preserving format

        Strategies:
        - MM/DD/YYYY → MM/DD/19XX (mask year)
        - YYYY-MM-DD → YYYY-MM-XX (mask day)
        - Month DD, YYYY → Month DD, 19XX (mask year)

        Args:
            date_str: Original date string

        Returns:
            Masked date string
        """
        # MM/DD/YYYY or MM-DD-YYYY format
        if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', date_str):
            # Mask year: 01/15/1980 → 01/15/19XX
            masked = re.sub(r'\d{2,4}$', lambda m: '19XX' if len(m.group()) == 4 else 'XX', date_str)
            return masked

        # YYYY-MM-DD format (ISO)
        if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
            # Mask day: 2023-11-17 → 2023-11-XX
            masked = re.sub(r'-\d{2}$', '-XX', date_str)
            return masked

        # Month DD, YYYY format
        if re.search(r'\d{4}', date_str):
            # Mask year
            masked = re.sub(r'\d{4}', '19XX', date_str)
            return masked

        # Fallback: mask all digits
        return re.sub(r'\d', 'X', date_str)

    def reset_counters(self):
        """Reset all counters (for testing or new document batch)"""
        for key in self.counters:
            self.counters[key] = 0
