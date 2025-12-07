"""PHI Detection Service using NER model (Sprint 4, Phase 4.1)

This service detects Protected Health Information (PHI) in clinical text.

Implementation Strategy:
- Production: Uses CogStack-ModelServe with medcat_ner_phi model
- Development/Mock: Uses rule-based pattern matching for testing

The mock implementation can be replaced with real ModelServe client when available.
"""

import re
import logging
from typing import List, Optional
from app.schemas.phi import DetectedEntity, PHIEntityType

logger = logging.getLogger(__name__)


class PHIDetectionService:
    """Service for detecting PHI in clinical text

    This is a mock implementation using regex patterns for development/testing.
    Replace with CogStack-ModelServe client in production.
    """

    def __init__(self, use_mock: bool = True):
        """Initialize PHI detection service

        Args:
            use_mock: If True, use mock regex-based detection.
                     If False, use CogStack-ModelServe (requires running service)
        """
        self.use_mock = use_mock
        self.modelserve_url = None  # Set when using real ModelServe

        # Regex patterns for mock implementation
        self.patterns = {
            PHIEntityType.PERSON: [
                # Names: Capital Letter + lowercase letters (2+ words)
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b'
            ],
            PHIEntityType.DATE: [
                # MM/DD/YYYY or MM-DD-YYYY
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                # Month DD, YYYY
                r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
                # YYYY-MM-DD (ISO format)
                r'\b\d{4}-\d{2}-\d{2}\b'
            ],
            PHIEntityType.ID: [
                # SSN: 123-45-6789
                r'\b\d{3}-\d{2}-\d{4}\b',
                # MRN: MRN followed by digits
                r'\bMRN[:\s]?\d{6,10}\b',
                # Generic ID: ID followed by digits
                r'\b(?:ID|id)[:\s]?\d{4,}\b'
            ],
            PHIEntityType.LOCATION: [
                # Street addresses: number + street name
                r'\b\d+\s+[A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b',
                # US States (abbreviations)
                r'\b(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b',
                # ZIP codes
                r'\b\d{5}(?:-\d{4})?\b'
            ],
            PHIEntityType.PHONE: [
                # (123) 456-7890 or 123-456-7890
                r'\b(?:\(\d{3}\)\s?|\d{3}-)?\d{3}-\d{4}\b'
            ],
            PHIEntityType.EMAIL: [
                # email@example.com
                r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'
            ],
            PHIEntityType.AGE: [
                # Age > 89 (HIPAA requirement)
                r'\b(?:9[0-9]|[1-9]\d{2,})\s*(?:years?|y\.?o\.?)\b'
            ]
        }

    async def detect_phi(self, text: str) -> List[DetectedEntity]:
        """Detect PHI entities in text

        Args:
            text: Clinical text to analyze

        Returns:
            List of detected PHI entities with positions and confidence
        """
        if self.use_mock:
            return self._detect_phi_mock(text)
        else:
            return await self._detect_phi_modelserve(text)

    def _detect_phi_mock(self, text: str) -> List[DetectedEntity]:
        """Mock PHI detection using regex patterns

        This is a development/testing implementation. Replace with CogStack-ModelServe in production.

        Args:
            text: Clinical text to analyze

        Returns:
            List of detected PHI entities
        """
        entities: List[DetectedEntity] = []
        detected_spans = set()  # Track (start, end) to avoid duplicates

        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    start, end = match.span()

                    # Skip if overlaps with existing entity
                    if any(start < e_end and end > e_start for e_start, e_end in detected_spans):
                        continue

                    # Filter out false positives
                    matched_text = match.group()
                    if self._is_likely_phi(matched_text, entity_type):
                        entities.append(DetectedEntity(
                            text=matched_text,
                            label=entity_type,
                            start=start,
                            end=end,
                            confidence=0.85  # Mock confidence score
                        ))
                        detected_spans.add((start, end))

        # Sort by position
        entities.sort(key=lambda e: e.start)

        logger.info(f"Mock PHI detection found {len(entities)} entities in {len(text)} chars")
        return entities

    def _is_likely_phi(self, text: str, entity_type: PHIEntityType) -> bool:
        """Filter out common false positives

        Args:
            text: Matched text
            entity_type: Detected entity type

        Returns:
            True if likely to be PHI, False if likely false positive
        """
        # Filter out common non-PHI terms that match person names
        if entity_type == PHIEntityType.PERSON:
            false_positives = {
                'Patient', 'Doctor', 'Nurse', 'Physician', 'Clinic', 'Hospital',
                'Medical', 'Health', 'Care', 'Department', 'Unit', 'Service',
                'General', 'Medicine', 'Surgery', 'Emergency', 'Radiology'
            }
            if text in false_positives:
                return False

            # Require at least 2 capital words for person names
            capital_words = [w for w in text.split() if w and w[0].isupper()]
            if len(capital_words) < 2:
                return False

        return True

    async def _detect_phi_modelserve(self, text: str) -> List[DetectedEntity]:
        """Detect PHI using CogStack-ModelServe (production implementation)

        This method calls the real CogStack-ModelServe API with medcat_ner_phi model.

        Args:
            text: Clinical text to analyze

        Returns:
            List of detected PHI entities

        Raises:
            RuntimeError: If ModelServe is not available
        """
        # TODO: Implement CogStack-ModelServe client
        # Example implementation:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{self.modelserve_url}/api/process",
        #         json={"text": text, "model": "medcat_ner_phi"}
        #     )
        #     response.raise_for_status()
        #     data = response.json()
        #
        #     entities = []
        #     for ent in data.get("entities", []):
        #         entities.append(DetectedEntity(
        #             text=ent["text"],
        #             label=PHIEntityType(ent["label"]),
        #             start=ent["start"],
        #             end=ent["end"],
        #             confidence=ent.get("confidence", 1.0)
        #         ))
        #
        #     return entities

        raise RuntimeError(
            "CogStack-ModelServe integration not implemented. "
            "Use use_mock=True for development or implement ModelServe client."
        )
