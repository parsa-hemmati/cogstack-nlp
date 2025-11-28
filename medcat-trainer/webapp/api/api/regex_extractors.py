"""
Regex extraction utilities for clinical document fields.

Extracts structured fields from clinical letters:
- NHS Number (10 digits)
- Consultant/Doctor name
- Specialty/Department
"""

import re
from typing import Optional, Dict, Any


class ClinicalLetterExtractor:
    """Extract structured fields from clinical letters using regex patterns."""

    # NHS Number patterns (10 digits, may have spaces or dashes)
    NHS_PATTERNS = [
        r'NHS\s*(?:No|Number|#)?[:\s]*(\d{3}[\s-]?\d{3}[\s-]?\d{4})',
        r'(?:Patient\s+)?(?:NHS\s+)?(?:ID|Number)[:\s]*(\d{3}[\s-]?\d{3}[\s-]?\d{4})',
        r'(?:Hospital\s+)?Number[:\s]*(\d{3}[\s-]?\d{3}[\s-]?\d{4})',
        r'\b(\d{3}\s\d{3}\s\d{4})\b',  # Plain format with spaces
        r'(?:MRN|CHI|HCN)[:\s]*(\d{10})',  # Medical Record Number variants
    ]

    # Consultant/Doctor name patterns (names don't cross newlines)
    CONSULTANT_PATTERNS = [
        r'Consultant[:\s]+(?:Dr\.?\s*)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:\n|$)',
        r'(?:Seen|Reviewed|Examined)\s+by[:\s]+(?:Dr\.?\s*)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:\n|$)',
        r'Dictated\s+by[:\s]+(?:Dr\.?\s*)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:\n|$)',
        r'(?:Attending|Treating)\s+(?:Physician|Doctor|Consultant)[:\s]+(?:Dr\.?\s*)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:\n|$)',
        r'Yours\s+(?:sincerely|faithfully)[,\s]+(?:Dr\.?\s*)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:\n|$)',
        r'(?:Signed|Authored)[:\s]+(?:Dr\.?\s*)?([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})(?:\n|$)',
        r'^(?:Dr\.?\s+)([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,2})\s*$',  # Dr. Name on own line
    ]

    # Medical specialties (UK NHS)
    SPECIALTIES = [
        'Accident and Emergency', 'A&E', 'Emergency Medicine',
        'Acute Internal Medicine', 'Acute Medicine',
        'Allergy', 'Immunology', 'Clinical Immunology',
        'Anaesthetics', 'Anaesthesia',
        'Audiology',
        'Breast Surgery',
        'Cardiology', 'Cardiac Surgery', 'Cardiothoracic Surgery',
        'Chemical Pathology',
        'Clinical Genetics', 'Genetics',
        'Clinical Neurophysiology',
        'Clinical Oncology', 'Oncology', 'Cancer Services',
        'Clinical Pharmacology', 'Pharmacology',
        'Clinical Radiology', 'Radiology', 'Diagnostic Imaging',
        'Colorectal Surgery',
        'Community Medicine', 'Public Health',
        'Community Paediatrics',
        'Dermatology',
        'Diabetic Medicine', 'Diabetes', 'Endocrinology',
        'ENT', 'Ear Nose and Throat', 'Otolaryngology', 'Otorhinolaryngology',
        'Gastroenterology', 'GI Medicine',
        'General Medicine', 'General Internal Medicine', 'Internal Medicine',
        'General Practice', 'GP', 'Primary Care',
        'General Surgery',
        'Genito-urinary Medicine', 'GUM', 'Sexual Health',
        'Geriatric Medicine', 'Geriatrics', 'Care of the Elderly',
        'Gynaecological Oncology',
        'Gynaecology',
        'Haematology', 'Hematology',
        'Hand Surgery',
        'Hepatology', 'Liver Medicine',
        'Histopathology', 'Pathology',
        'Infectious Diseases', 'Infection',
        'Intensive Care', 'ICU', 'ITU', 'Critical Care',
        'Interventional Radiology',
        'Maxillofacial Surgery', 'Oral and Maxillofacial',
        'Medical Microbiology', 'Microbiology',
        'Medical Oncology',
        'Neonatology', 'Neonatal Medicine',
        'Nephrology', 'Renal Medicine',
        'Neurology',
        'Neurosurgery',
        'Nuclear Medicine',
        'Obstetrics', 'Obstetrics and Gynaecology', 'O&G',
        'Occupational Medicine', 'Occupational Health',
        'Ophthalmology', 'Eye',
        'Oral Surgery',
        'Orthopaedics', 'Orthopedics', 'Orthopaedic Surgery', 'Trauma and Orthopaedics',
        'Paediatric Surgery', 'Pediatric Surgery',
        'Paediatrics', 'Pediatrics', 'Child Health',
        'Pain Management', 'Pain Medicine', 'Chronic Pain',
        'Palliative Medicine', 'Palliative Care',
        'Plastic Surgery', 'Plastics',
        'Podiatry',
        'Psychiatry', 'Mental Health',
        'Rehabilitation Medicine',
        'Renal', 'Kidney',
        'Respiratory Medicine', 'Respiratory', 'Chest Medicine', 'Pulmonology',
        'Rheumatology',
        'Sport and Exercise Medicine', 'Sports Medicine',
        'Stroke Medicine',
        'Thoracic Surgery',
        'Transplant Surgery',
        'Trauma Surgery',
        'Upper GI Surgery',
        'Urology',
        'Vascular Surgery',
    ]

    def __init__(self):
        # Build specialty pattern from list
        escaped_specialties = [re.escape(s) for s in self.SPECIALTIES]
        self._specialty_pattern = '|'.join(escaped_specialties)

    def extract_nhs_number(self, text: str) -> Optional[str]:
        """
        Extract NHS number from text.

        Args:
            text: Clinical document text

        Returns:
            NHS number as 10 digits (no spaces/dashes) or None
        """
        if not text:
            return None

        for pattern in self.NHS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Normalize: remove spaces and dashes
                nhs = re.sub(r'[\s-]', '', match.group(1))
                # Validate: must be exactly 10 digits
                if len(nhs) == 10 and nhs.isdigit():
                    return nhs
        return None

    def extract_consultant(self, text: str) -> Optional[str]:
        """
        Extract consultant/doctor name from text.

        Args:
            text: Clinical document text

        Returns:
            Consultant name or None
        """
        if not text:
            return None

        for pattern in self.CONSULTANT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Basic validation: at least 2 characters
                if len(name) >= 2:
                    return name
        return None

    def extract_specialty(self, text: str) -> Optional[str]:
        """
        Extract medical specialty from text.

        Args:
            text: Clinical document text

        Returns:
            Specialty name or None
        """
        if not text:
            return None

        # Context-aware patterns for specialty (must be in a labeled context)
        context_patterns = [
            r'Specialty[:\s]+([A-Za-z\s&/]+?)(?:\n|,|$|\.|;)',
            r'Department\s+of\s+([A-Za-z\s&]+?)(?:\n|,|$|\.|:)',
            r'(?:Outpatient|Inpatient|Day\s+Case)\s+([A-Za-z\s&]+?)\s+(?:Clinic|Unit|Ward)',
            r'Service[:\s]+([A-Za-z\s&]+?)(?:\n|,|$|\.|;)',
            r'Consultant\s+(?:in\s+)?([A-Za-z\s&]+?)(?:\n|,|$)',
        ]

        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specialty = match.group(1).strip()
                # Validate against known specialties (fuzzy match)
                for known in self.SPECIALTIES:
                    if known.lower() in specialty.lower() or specialty.lower() in known.lower():
                        return known
                # Return as-is if reasonable length
                if 3 <= len(specialty) <= 50:
                    return specialty.title()

        return None

    def extract_all(self, text: str) -> Dict[str, Any]:
        """
        Extract all structured fields from text.

        Args:
            text: Clinical document text

        Returns:
            Dictionary with extracted fields
        """
        return {
            'nhs_number': self.extract_nhs_number(text),
            'consultant': self.extract_consultant(text),
            'specialty': self.extract_specialty(text),
        }

    def extract_all_with_positions(self, text: str) -> Dict[str, Any]:
        """
        Extract all structured fields from text WITH positions for highlighting.

        Args:
            text: Clinical document text

        Returns:
            Dictionary with extracted fields and their positions
        """
        result = {
            'nhs_number': None,
            'consultant': None,
            'specialty': None,
            'highlights': []  # List of {type, value, start, end} for highlighting
        }

        if not text:
            return result

        # Extract NHS Number with position
        for pattern in self.NHS_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                nhs = re.sub(r'[\s-]', '', match.group(1))
                if len(nhs) == 10 and nhs.isdigit():
                    result['nhs_number'] = nhs
                    # Get the full match position (including "NHS Number:" label)
                    result['highlights'].append({
                        'type': 'nhs_number',
                        'value': match.group(0),
                        'start': match.start(),
                        'end': match.end(),
                        'label': 'NHS Number'
                    })
                    break

        # Extract Consultant with position
        for pattern in self.CONSULTANT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if len(name) >= 2:
                    result['consultant'] = name
                    result['highlights'].append({
                        'type': 'consultant',
                        'value': match.group(0),
                        'start': match.start(),
                        'end': match.end(),
                        'label': 'Consultant'
                    })
                    break

        # Extract Specialty with position
        context_patterns = [
            r'Specialty[:\s]+([A-Za-z\s&/]+?)(?:\n|,|$|\.|;)',
            r'Department\s+of\s+([A-Za-z\s&]+?)(?:\n|,|$|\.|:)',
            r'(?:Outpatient|Inpatient|Day\s+Case)\s+([A-Za-z\s&]+?)\s+(?:Clinic|Unit|Ward)',
            r'Service[:\s]+([A-Za-z\s&]+?)(?:\n|,|$|\.|;)',
        ]
        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                specialty = match.group(1).strip()
                validated_specialty = None
                for known in self.SPECIALTIES:
                    if known.lower() in specialty.lower() or specialty.lower() in known.lower():
                        validated_specialty = known
                        break
                if validated_specialty or (3 <= len(specialty) <= 50):
                    result['specialty'] = validated_specialty or specialty.title()
                    result['highlights'].append({
                        'type': 'specialty',
                        'value': match.group(0),
                        'start': match.start(),
                        'end': match.end(),
                        'label': 'Specialty'
                    })
                    break

        return result


# Singleton instance for convenience
_extractor = ClinicalLetterExtractor()

def extract_nhs_number(text: str) -> Optional[str]:
    """Extract NHS number from text."""
    return _extractor.extract_nhs_number(text)

def extract_consultant(text: str) -> Optional[str]:
    """Extract consultant name from text."""
    return _extractor.extract_consultant(text)

def extract_specialty(text: str) -> Optional[str]:
    """Extract specialty from text."""
    return _extractor.extract_specialty(text)

def extract_all_fields(text: str) -> Dict[str, Any]:
    """Extract all clinical letter fields."""
    return _extractor.extract_all(text)

def extract_all_fields_with_positions(text: str) -> Dict[str, Any]:
    """Extract all clinical letter fields with positions for highlighting."""
    return _extractor.extract_all_with_positions(text)
