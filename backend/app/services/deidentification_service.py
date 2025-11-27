"""
De-identification Service.

Implements HIPAA Safe Harbor de-identification methods to remove, replace, or
generalize PHI entities detected by MedCAT PHI detection model.

Methods:
- Removal: Replace PHI with [TYPE] placeholders
- Replacement: Replace with consistent synthetic data
- Generalization: Keep partial info (year only, state only, 90+)
"""
import re
from typing import List, Dict, Optional
from collections import defaultdict

from app.clients.modelserve_client import CogStackModelServeClient, Entity
from app.schemas.deidentification import (
    PHIEntity,
    DeidentificationResult,
    ValidationReport,
    ValidationWarning,
)


class DeidentificationService:
    """
    Service for de-identifying clinical notes using HIPAA Safe Harbor methods.

    Supports three de-identification methods:
    1. Removal: Replace PHI with placeholders ([NAME], [DATE], etc.)
    2. Replacement: Replace with consistent synthetic data (Patient A, DATE_1, etc.)
    3. Generalization: Partial de-identification (year only, state only, ages 90+)

    Example:
        >>> service = DeidentificationService(medcat_client)
        >>> result = await service.deidentify(
        >>>     "Patient John Doe, NHS 123456789, DOB 01/15/1980",
        >>>     method="removal"
        >>> )
        >>> print(result.deidentified_text)
        "Patient [NAME], NHS [NHS_NUMBER], DOB [DATE]"
    """

    def __init__(self, medcat_client: CogStackModelServeClient):
        """
        Initialize de-identification service.

        Args:
            medcat_client: MedCAT client for PHI detection
        """
        self.medcat_client = medcat_client

    async def deidentify(
        self, text: str, method: str = "removal", confidence_threshold: float = 0.7
    ) -> DeidentificationResult:
        """
        De-identify text using specified method.

        Args:
            text: Original text with PHI
            method: De-identification method (removal, replacement, generalization)
            confidence_threshold: Minimum confidence for PHI detection (default 0.7)

        Returns:
            DeidentificationResult with de-identified text and metadata

        Raises:
            ValueError: If method is invalid
            Exception: If PHI detection fails

        Example:
            >>> result = await service.deidentify(
            >>>     "Patient John Doe visited on 01/15/2024",
            >>>     method="removal"
            >>> )
        """
        # Handle empty text
        if not text or not text.strip():
            return DeidentificationResult(
                original_text=text,
                deidentified_text=text,
                entities_removed=[],
                method_used=method,
                confidence_score=0.0,
                review_required=True,  # Flag empty text for review
                entity_mappings={},
            )

        # Validate method
        valid_methods = ["removal", "replacement", "generalization"]
        if method not in valid_methods:
            raise ValueError(
                f"Invalid method '{method}'. Must be one of: {valid_methods}"
            )

        # Detect PHI entities
        try:
            entities = await self.medcat_client.detect_phi(text)
        except Exception as e:
            raise Exception(f"PHI detection failed: {str(e)}")

        # Convert to PHIEntity objects
        phi_entities = self._convert_entities(entities, confidence_threshold)

        # Remove overlapping entities (keep longer ones)
        phi_entities = self._remove_overlapping_entities(phi_entities)

        # Sort entities by start offset (reverse order for replacement)
        phi_entities.sort(key=lambda e: e.start, reverse=True)

        # Apply de-identification method
        if method == "removal":
            deidentified_text, entity_mappings = self._apply_removal(text, phi_entities)
        elif method == "replacement":
            deidentified_text, entity_mappings = self._apply_replacement(
                text, phi_entities
            )
        elif method == "generalization":
            deidentified_text, entity_mappings = self._apply_generalization(
                text, phi_entities
            )

        # Calculate confidence score (average)
        confidence_score = (
            sum(e.confidence for e in phi_entities) / len(phi_entities)
            if phi_entities
            else 0.0
        )

        # Determine if manual review required
        review_required = self._should_review(phi_entities, confidence_score)

        return DeidentificationResult(
            original_text=text,
            deidentified_text=deidentified_text,
            entities_removed=phi_entities,
            method_used=method,
            confidence_score=confidence_score,
            review_required=review_required,
            entity_mappings=entity_mappings,
        )

    async def deidentify_batch(
        self, texts: List[str], method: str = "removal", confidence_threshold: float = 0.7
    ) -> List[DeidentificationResult]:
        """
        De-identify multiple texts in batch.

        Args:
            texts: List of texts to de-identify
            method: De-identification method
            confidence_threshold: Minimum confidence threshold

        Returns:
            List of DeidentificationResult (maintains order)

        Example:
            >>> results = await service.deidentify_batch(
            >>>     ["Text 1...", "Text 2..."],
            >>>     method="removal"
            >>> )
        """
        results = []
        for text in texts:
            result = await self.deidentify(text, method, confidence_threshold)
            results.append(result)
        return results

    async def validate_deidentification(
        self, original_text: str, deidentified_text: str
    ) -> ValidationReport:
        """
        Validate de-identified text has no remaining PHI.

        Performs:
        1. PHI detection on de-identified text (should find none)
        2. Readability check (text still makes sense)
        3. Regex pattern matching for common PHI

        Args:
            original_text: Original text with PHI
            deidentified_text: De-identified text to validate

        Returns:
            ValidationReport with validation results

        Example:
            >>> report = await service.validate_deidentification(
            >>>     "Patient John Doe...",
            >>>     "Patient [NAME]..."
            >>> )
            >>> assert report.is_valid is True
        """
        warnings = []
        phi_detected = []

        # 1. Run PHI detection on de-identified text
        try:
            entities = await self.medcat_client.detect_phi(deidentified_text)
            if entities:
                # Convert to PHIEntity
                phi_detected = self._convert_entities(entities, confidence_threshold=0.7)
                warnings.append(
                    ValidationWarning(
                        warning_type="phi_detected",
                        message=f"Found {len(phi_detected)} PHI entities in de-identified text",
                        location=None,
                    )
                )
        except Exception as e:
            warnings.append(
                ValidationWarning(
                    warning_type="validation_error",
                    message=f"PHI detection failed during validation: {str(e)}",
                    location=None,
                )
            )

        # 2. Readability check
        readability_score = self._calculate_readability(
            original_text, deidentified_text
        )

        if readability_score < 0.5:
            warnings.append(
                ValidationWarning(
                    warning_type="low_readability",
                    message=f"Low readability score: {readability_score:.2f} (may be over-redacted)",
                    location=None,
                )
            )

        # 3. Regex pattern check for common PHI
        regex_warnings = self._check_phi_patterns(deidentified_text)
        warnings.extend(regex_warnings)

        # Validation passed if no PHI detected
        is_valid = len(phi_detected) == 0

        return ValidationReport(
            is_valid=is_valid,
            warnings=warnings,
            phi_detected=phi_detected,
            readability_score=readability_score,
        )

    # -------------------------------------------------------------------------
    # Internal Helper Methods
    # -------------------------------------------------------------------------

    def _convert_entities(
        self, entities: List[Entity], confidence_threshold: float
    ) -> List[PHIEntity]:
        """
        Convert MedCAT Entity objects to PHIEntity.

        Args:
            entities: List of MedCAT Entity objects
            confidence_threshold: Minimum confidence to include

        Returns:
            List of PHIEntity objects
        """
        phi_entities = []
        for entity in entities:
            # Filter by confidence
            if entity.accuracy < confidence_threshold:
                continue

            # Classify entity type
            entity_type = self.medcat_client.classify_entity_type(entity)

            phi_entities.append(
                PHIEntity(
                    entity_type=entity_type,
                    text=entity.pretty_name,
                    start=entity.start,
                    end=entity.end,
                    confidence=entity.accuracy,
                    cui=entity.cui,
                )
            )

        return phi_entities

    def _remove_overlapping_entities(
        self, entities: List[PHIEntity]
    ) -> List[PHIEntity]:
        """
        Remove overlapping entities (keep longer ones).

        Args:
            entities: List of PHIEntity objects

        Returns:
            List with overlapping entities removed
        """
        # Sort by start, then by length (descending)
        sorted_entities = sorted(
            entities, key=lambda e: (e.start, -(e.end - e.start))
        )

        filtered = []
        for entity in sorted_entities:
            # Check if overlaps with any already-kept entity
            overlaps = False
            for kept in filtered:
                if self._entities_overlap(entity, kept):
                    overlaps = True
                    break

            if not overlaps:
                filtered.append(entity)

        return filtered

    def _entities_overlap(self, e1: PHIEntity, e2: PHIEntity) -> bool:
        """
        Check if two entities overlap.

        Args:
            e1: First entity
            e2: Second entity

        Returns:
            True if entities overlap
        """
        return not (e1.end <= e2.start or e2.end <= e1.start)

    def _apply_removal(
        self, text: str, entities: List[PHIEntity]
    ) -> tuple[str, Dict[str, str]]:
        """
        Apply removal method: Replace PHI with [TYPE] placeholders.

        Args:
            text: Original text
            entities: PHI entities to remove (sorted by start, reverse)

        Returns:
            Tuple of (deidentified_text, entity_mappings)
        """
        deidentified_text = text
        entity_mappings = {}

        for entity in entities:
            # Determine placeholder based on entity type
            placeholder = self._get_placeholder(entity.entity_type)

            # Replace entity text with placeholder
            deidentified_text = (
                deidentified_text[: entity.start]
                + placeholder
                + deidentified_text[entity.end :]
            )

            # Track mapping
            entity_mappings[entity.text] = placeholder

        return deidentified_text, entity_mappings

    def _apply_replacement(
        self, text: str, entities: List[PHIEntity]
    ) -> tuple[str, Dict[str, str]]:
        """
        Apply replacement method: Replace with consistent synthetic data.

        Same PHI → same replacement within document.

        Args:
            text: Original text
            entities: PHI entities (sorted by start, reverse)

        Returns:
            Tuple of (deidentified_text, entity_mappings)
        """
        deidentified_text = text
        entity_mappings = {}
        type_counters = defaultdict(int)  # Counter for each type

        # First pass: Build consistent mappings
        for entity in reversed(entities):  # Process in forward order for consistent numbering
            if entity.text not in entity_mappings:
                # Generate consistent replacement
                type_counters[entity.entity_type] += 1
                replacement = self._generate_replacement(
                    entity.entity_type, type_counters[entity.entity_type]
                )
                entity_mappings[entity.text] = replacement

        # Second pass: Apply replacements (in reverse order to maintain offsets)
        for entity in entities:
            replacement = entity_mappings[entity.text]
            deidentified_text = (
                deidentified_text[: entity.start]
                + replacement
                + deidentified_text[entity.end :]
            )

        return deidentified_text, entity_mappings

    def _apply_generalization(
        self, text: str, entities: List[PHIEntity]
    ) -> tuple[str, Dict[str, str]]:
        """
        Apply generalization method: Partial de-identification.

        - Dates: Keep year only
        - Ages >89: Replace with "90+"
        - Locations: Keep state/region only

        Args:
            text: Original text
            entities: PHI entities (sorted by start, reverse)

        Returns:
            Tuple of (deidentified_text, entity_mappings)
        """
        deidentified_text = text
        entity_mappings = {}

        for entity in entities:
            # Generalize based on entity type
            generalized = self._generalize_entity(entity)

            # Replace entity text with generalized version
            deidentified_text = (
                deidentified_text[: entity.start]
                + generalized
                + deidentified_text[entity.end :]
            )

            # Track mapping
            entity_mappings[entity.text] = generalized

        return deidentified_text, entity_mappings

    def _get_placeholder(self, entity_type: str) -> str:
        """
        Get placeholder for entity type (removal method).

        Args:
            entity_type: Entity type (phi_name, phi_date, etc.)

        Returns:
            Placeholder string
        """
        placeholders = {
            "phi_name": "[NAME]",
            "phi_nhs_number": "[NHS_NUMBER]",
            "phi_mrn": "[MRN]",
            "phi_address": "[ADDRESS]",
            "phi_dob": "[DATE]",
            "phi_date": "[DATE]",
            "phi_phone": "[PHONE]",
            "phi_email": "[EMAIL]",
            "phi_url": "[URL]",
            "phi_ip": "[IP_ADDRESS]",
            "phi_age": "[AGE]",
            "clinical": "[DATE]",  # Default for unclassified
        }
        return placeholders.get(entity_type, "[REDACTED]")

    def _generate_replacement(self, entity_type: str, counter: int) -> str:
        """
        Generate consistent replacement for entity (replacement method).

        Args:
            entity_type: Entity type
            counter: Counter for this entity type

        Returns:
            Replacement string (e.g., "Patient A", "DATE_1")
        """
        replacements = {
            "phi_name": f"Patient {chr(64 + counter)}",  # Patient A, Patient B, etc.
            "phi_nhs_number": f"NHS_{counter:03d}",
            "phi_mrn": f"MRN_{counter:03d}",
            "phi_address": f"ADDRESS_{counter}",
            "phi_dob": f"DATE_{counter}",
            "phi_date": f"DATE_{counter}",
            "phi_phone": f"PHONE_{counter}",
            "phi_email": f"EMAIL_{counter}@example.com",
            "phi_url": f"URL_{counter}",
            "phi_ip": f"10.0.0.{counter}",
        }
        return replacements.get(entity_type, f"REDACTED_{counter}")

    def _generalize_entity(self, entity: PHIEntity) -> str:
        """
        Generalize entity based on type (generalization method).

        Args:
            entity: PHI entity to generalize

        Returns:
            Generalized string
        """
        # Dates: Extract year only
        if "date" in entity.entity_type.lower() or "dob" in entity.entity_type.lower():
            year_match = re.search(r"\b(19|20)\d{2}\b", entity.text)
            if year_match:
                return year_match.group(0)  # Return year only
            return "[YEAR]"

        # Ages: Check if >89
        if "age" in entity.entity_type.lower():
            age_match = re.search(r"\b(\d+)\b", entity.text)
            if age_match:
                age = int(age_match.group(1))
                if age > 89:
                    return "90+"
                else:
                    return entity.text  # Keep age if ≤89
            return entity.text

        # Addresses: Extract state/region
        if "address" in entity.entity_type.lower() or "location" in entity.entity_type.lower():
            # Look for US state abbreviations or names
            state_match = re.search(r"\b([A-Z]{2})\b", entity.text)  # State code (MA, CA, etc.)
            if state_match:
                state_code = state_match.group(1)
                state_names = {
                    "MA": "Massachusetts",
                    "CA": "California",
                    "NY": "New York",
                    # Add more as needed
                }
                return state_names.get(state_code, state_code)

            # Look for UK regions (London, etc.) - just remove street details
            if "London" in entity.text:
                return "London"

            return "[REGION]"

        # Names: Replace entirely (no partial generalization)
        if "name" in entity.entity_type.lower():
            return "[NAME]"

        # Default: Remove entirely
        return "[REDACTED]"

    def _should_review(
        self, entities: List[PHIEntity], confidence_score: float
    ) -> bool:
        """
        Determine if manual review is required.

        Review required if:
        - Any entity confidence <0.8
        - >20 entities detected (high PHI density)
        - Conflicting entity types (handled earlier)

        Args:
            entities: List of PHI entities
            confidence_score: Average confidence

        Returns:
            True if manual review recommended
        """
        # Check low confidence
        if any(e.confidence < 0.8 for e in entities):
            return True

        # Check high PHI density
        if len(entities) > 20:
            return True

        # Check average confidence
        if confidence_score < 0.8:
            return True

        return False

    def _calculate_readability(self, original: str, deidentified: str) -> float:
        """
        Calculate readability score for de-identified text.

        Simple metric: ratio of preserved characters to original.

        Args:
            original: Original text
            deidentified: De-identified text

        Returns:
            Readability score (0.0-1.0)
        """
        if not original:
            return 1.0

        # Count non-placeholder characters
        # Remove placeholders ([NAME], [DATE], etc.)
        clean_deidentified = re.sub(r"\[\w+\]", "", deidentified)

        # Calculate ratio
        ratio = len(clean_deidentified) / len(original) if len(original) > 0 else 0.0

        # Clamp to [0.0, 1.0]
        return min(max(ratio, 0.0), 1.0)

    def _check_phi_patterns(self, text: str) -> List[ValidationWarning]:
        """
        Check for common PHI patterns using regex.

        Patterns checked:
        - Email addresses
        - Phone numbers
        - NHS numbers
        - Dates (MM/DD/YYYY, DD/MM/YYYY)

        Args:
            text: Text to check

        Returns:
            List of ValidationWarning if patterns found
        """
        warnings = []

        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if re.search(email_pattern, text):
            warnings.append(
                ValidationWarning(
                    warning_type="email_detected",
                    message="Email address pattern detected",
                    location=None,
                )
            )

        # Phone pattern (UK/US formats)
        phone_pattern = r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b"
        if re.search(phone_pattern, text):
            warnings.append(
                ValidationWarning(
                    warning_type="phone_detected",
                    message="Phone number pattern detected",
                    location=None,
                )
            )

        # NHS number pattern (XXX XXX XXXX)
        nhs_pattern = r"\b\d{3}\s?\d{3}\s?\d{4}\b"
        if re.search(nhs_pattern, text):
            warnings.append(
                ValidationWarning(
                    warning_type="nhs_number_detected",
                    message="NHS number pattern detected",
                    location=None,
                )
            )

        # Date patterns (MM/DD/YYYY, DD/MM/YYYY)
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        if re.search(date_pattern, text):
            warnings.append(
                ValidationWarning(
                    warning_type="date_detected",
                    message="Date pattern detected",
                    location=None,
                )
            )

        return warnings
