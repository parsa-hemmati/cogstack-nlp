"""ICD-10 Extraction Service (Sprint 5)

Mock implementation using pattern matching for common conditions.
Replace with CogStack-ModelServe medcat_icd10 model in production.
"""

import re
import logging
from typing import List

from app.schemas.clinical_coding import ICD10SuggestedCode

logger = logging.getLogger(__name__)


class ICD10ExtractionService:
    """Service for extracting ICD-10 codes from clinical text

    Mock implementation using pattern matching for development/testing.
    Replace with CogStack-ModelServe medcat_icd10 model in production.
    """

    def __init__(self, use_mock: bool = True):
        """Initialize ICD-10 extraction service

        Args:
            use_mock: If True, use mock pattern-based extraction
        """
        self.use_mock = use_mock

        # Common condition patterns → ICD-10 codes (mock data)
        self.condition_patterns = [
            # Diabetes
            (
                r'(?:type\s*2\s*)?diabetes\s*(?:mellitus)?(?:\s*without\s*complications)?',
                "E11.9",
                "Type 2 diabetes mellitus without complications",
                "E08-E13: Diabetes mellitus"
            ),
            (
                r'type\s*1\s*diabetes',
                "E10.9",
                "Type 1 diabetes mellitus without complications",
                "E08-E13: Diabetes mellitus"
            ),
            # Hypertension
            (
                r'(?:essential\s*)?(?:primary\s*)?hypertension',
                "I10",
                "Essential (primary) hypertension",
                "I10-I16: Hypertensive diseases"
            ),
            # Cardiovascular
            (
                r'atrial\s*fibrillation',
                "I48.91",
                "Unspecified atrial fibrillation",
                "I30-I5A: Other forms of heart disease"
            ),
            (
                r'coronary\s*artery\s*disease|CAD',
                "I25.10",
                "Atherosclerotic heart disease of native coronary artery without angina pectoris",
                "I20-I25: Ischemic heart diseases"
            ),
            (
                r'heart\s*failure|CHF',
                "I50.9",
                "Heart failure, unspecified",
                "I30-I5A: Other forms of heart disease"
            ),
            # Respiratory
            (
                r'chronic\s*obstructive\s*pulmonary\s*disease|COPD',
                "J44.9",
                "Chronic obstructive pulmonary disease, unspecified",
                "J40-J47: Chronic lower respiratory diseases"
            ),
            (
                r'asthma',
                "J45.909",
                "Unspecified asthma, uncomplicated",
                "J40-J47: Chronic lower respiratory diseases"
            ),
            (
                r'pneumonia',
                "J18.9",
                "Pneumonia, unspecified organism",
                "J09-J18: Influenza and pneumonia"
            ),
            # Chronic kidney disease
            (
                r'chronic\s*kidney\s*disease|CKD',
                "N18.9",
                "Chronic kidney disease, unspecified",
                "N17-N19: Renal failure"
            ),
            # Obesity
            (
                r'obesity',
                "E66.9",
                "Obesity, unspecified",
                "E65-E68: Overweight, obesity and other hyperalimentation"
            ),
            # Depression/anxiety
            (
                r'major\s*depressive\s*disorder|depression',
                "F32.9",
                "Major depressive disorder, single episode, unspecified",
                "F30-F39: Mood [affective] disorders"
            ),
            (
                r'anxiety',
                "F41.9",
                "Anxiety disorder, unspecified",
                "F40-F48: Anxiety, dissociative, stress-related, somatoform and other nonpsychotic mental disorders"
            ),
            # Cancer (general)
            (
                r'malignant\s*neoplasm|cancer',
                "C80.1",
                "Malignant (primary) neoplasm, unspecified",
                "C00-D49: Neoplasms"
            ),
            # Stroke
            (
                r'cerebrovascular\s*accident|stroke|CVA',
                "I63.9",
                "Cerebral infarction, unspecified",
                "I60-I69: Cerebrovascular diseases"
            ),
            # Anemia
            (
                r'anemia',
                "D64.9",
                "Anemia, unspecified",
                "D50-D53: Nutritional anemias"
            ),
            # Hyperlipidemia
            (
                r'hyperlipidemia|dyslipidemia|high\s*cholesterol',
                "E78.5",
                "Hyperlipidemia, unspecified",
                "E70-E88: Metabolic disorders"
            ),
        ]

    async def extract_codes(self, text: str) -> List[ICD10SuggestedCode]:
        """Extract ICD-10 codes from clinical text

        Args:
            text: Clinical document text

        Returns:
            List of suggested ICD-10 codes with evidence
        """
        if self.use_mock:
            return self._extract_codes_mock(text)
        else:
            return await self._extract_codes_modelserve(text)

    def _extract_codes_mock(self, text: str) -> List[ICD10SuggestedCode]:
        """Mock ICD-10 extraction using pattern matching

        Args:
            text: Clinical text

        Returns:
            List of suggested codes
        """
        suggestions: List[ICD10SuggestedCode] = []
        text_lower = text.lower()

        for pattern, code, description, category in self.condition_patterns:
            matches = list(re.finditer(pattern, text_lower, re.IGNORECASE))
            if matches:
                # Use first match for evidence
                match = matches[0]
                evidence = text[match.start():min(match.end() + 50, len(text))]

                suggestions.append(ICD10SuggestedCode(
                    code=code,
                    description=description,
                    category=category,
                    confidence=0.85 + (len(matches) * 0.05),  # Higher confidence if mentioned multiple times
                    evidence=evidence.strip(),
                    position=match.start()
                ))

        # Sort by confidence (highest first)
        suggestions.sort(key=lambda x: x.confidence, reverse=True)

        logger.info(f"Mock ICD-10 extraction found {len(suggestions)} codes in {len(text)} chars")
        return suggestions

    async def _extract_codes_modelserve(self, text: str) -> List[ICD10SuggestedCode]:
        """Extract ICD-10 codes using CogStack-ModelServe (production)

        Args:
            text: Clinical text

        Returns:
            List of suggested codes

        Raises:
            RuntimeError: If ModelServe not available
        """
        from app.clients.modelserve_client import CogStackModelServeClient, ModelServeError

        try:
            client = CogStackModelServeClient()
            # Call process_text with medcat_icd10 model
            raw_entities = await client.process_text(text, model_name="medcat_icd10")
            
            suggestions = []
            for ent in raw_entities:
                # Map MedCAT output to ICD10SuggestedCode
                suggestions.append(ICD10SuggestedCode(
                    code=ent.get("cui", "UNKNOWN"),
                    description=ent.get("pretty_name", ""),
                    category="ICD-10", # Generic category, could be refined
                    confidence=ent.get("confidence", 0.0),
                    evidence=ent.get("source_value", text[ent.get("start", 0):ent.get("end", 0)]), # Use source text as evidence
                    position=ent.get("start", 0)
                ))
            
            await client.close()
            
            # Sort by confidence
            suggestions.sort(key=lambda x: x.confidence, reverse=True)
            return suggestions

        except ModelServeError as e:
            logger.error(f"ModelServe ICD-10 extraction failed: {e}")
            raise RuntimeError(f"ICD-10 extraction unavailable: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in ICD-10 extraction: {e}")
            raise RuntimeError(f"ICD-10 extraction error: {e}")
