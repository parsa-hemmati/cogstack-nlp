---
name: fhir-r4-mapper
description: Maps MedCAT NLP output to FHIR R4 resources (Observations, Conditions, DocumentReferences). Use when implementing FHIR integration, clinical decision support, EHR interoperability, or exporting NLP results to FHIR servers. Converts medical concepts to FHIR-compliant resources with proper SNOMED-CT/LOINC coding and meta-annotation qualifiers.
---

# FHIR R4 Mapper

Converts MedCAT NLP results to FHIR R4 resources for EHR integration and clinical decision support.

## What is FHIR R4?

**FHIR** (Fast Healthcare Interoperability Resources) R4 is the industry-standard format for healthcare data exchange. It enables integration with EHR systems like Epic, Cerner, and AllScripts.

## When to use this skill

Invoke when:
- Implementing FHIR integration (Sprint 3+)
- Exporting NLP results to EHR systems
- Building clinical decision support with CDS Hooks
- Creating interoperable healthcare applications
- Working with SNOMED-CT or LOINC codes

## Core mapping pattern

**MedCAT entity** → **FHIR Observation or Condition** resource

### MedCAT output structure

```python
{
  "pretty_name": "Diabetes Mellitus",
  "cui": "C0011849",  # UMLS CUI
  "type_ids": ["T047"],  # UMLS semantic type
  "snomed": ["73211009"],  # SNOMED-CT code
  "meta_anns": {
    "Negation": "Affirmed",
    "Experiencer": "Patient",
    "Temporality": "Current",
    "Certainty": "Confirmed"
  },
  "start": 45,
  "end": 61,
  "acc": 0.95  # Confidence score
}
```

### FHIR Observation resource

```json
{
  "resourceType": "Observation",
  "id": "nlp-obs-123",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "laboratory",
      "display": "Laboratory"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "73211009",
      "display": "Diabetes Mellitus"
    }],
    "text": "Diabetes Mellitus"
  },
  "subject": {
    "reference": "Patient/12345"
  },
  "effectiveDateTime": "2025-11-07T10:30:00Z",
  "valueBoolean": true,
  "interpretation": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
      "code": "POS",
      "display": "Positive"
    }]
  }],
  "note": [{
    "text": "Extracted via NLP from clinical note"
  }],
  "method": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "129438003",
      "display": "Natural language processing"
    }]
  },
  "extension": [{
    "url": "http://example.org/fhir/StructureDefinition/nlp-confidence",
    "valueDecimal": 0.95
  }]
}
```

## Mapping meta-annotations to FHIR

### Negation → interpretation or dataAbsentReason

**Affirmed** → Use `Observation.valueBoolean = true` or `Condition` resource

**Negated** → Use `dataAbsentReason` or create a negation extension

```json
// Negated condition
{
  "resourceType": "Observation",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "73211009",
      "display": "Diabetes Mellitus"
    }]
  },
  "subject": {"reference": "Patient/12345"},
  "valueBoolean": false,
  "interpretation": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
      "code": "NEG",
      "display": "Negative"
    }]
  }],
  "note": [{
    "text": "Condition explicitly ruled out in clinical note"
  }]
}
```

### Experiencer → performer or subject

**Patient** → Standard `subject` reference

**Family** → Use extension for family history or FamilyMemberHistory resource

```json
// Family history (use FamilyMemberHistory resource)
{
  "resourceType": "FamilyMemberHistory",
  "id": "family-diabetes-123",
  "status": "completed",
  "patient": {"reference": "Patient/12345"},
  "relationship": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "MTH",
      "display": "mother"
    }]
  },
  "condition": [{
    "code": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "73211009",
        "display": "Diabetes Mellitus"
      }]
    }
  }]
}
```

### Temporality → effectiveDateTime or status

**Current** → `status = "final"`, recent `effectiveDateTime`

**Historical** → Use `onsetDateTime` or historical `effectiveDateTime`

```json
// Historical condition
{
  "resourceType": "Condition",
  "id": "cond-historical-123",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "resolved",
      "display": "Resolved"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "233604007",
      "display": "Pneumonia"
    }]
  },
  "subject": {"reference": "Patient/12345"},
  "onsetDateTime": "2020-03-15",
  "abatementDateTime": "2020-03-30"
}
```

### Certainty → verificationStatus

**Confirmed** → `verificationStatus = "confirmed"`

**Suspected** → `verificationStatus = "provisional"` or `"differential"`

```json
// Suspected diagnosis
{
  "resourceType": "Condition",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    }]
  },
  "verificationStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "provisional",
      "display": "Provisional"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "74400008",
      "display": "Appendicitis"
    }]
  },
  "subject": {"reference": "Patient/12345"}
}
```

## Resource type decision guide

### Use Observation when:
- Representing findings or measurements
- NLP extracted a lab result or vital sign
- Want to represent presence/absence as boolean
- Need to include confidence scores

### Use Condition when:
- Representing diagnoses or clinical problems
- Building a problem list
- Need clinical/verification status
- Tracking onset and resolution dates

### Use DocumentReference when:
- Storing the original clinical document
- Linking NLP results back to source text
- Preserving document metadata (author, date, type)

## Complete mapping example

**Input**: MedCAT result from clinical text

```python
medcat_entity = {
  "pretty_name": "Hypertension",
  "cui": "C0020538",
  "snomed": ["38341003"],
  "meta_anns": {
    "Negation": "Affirmed",
    "Experiencer": "Patient",
    "Temporality": "Current",
    "Certainty": "Confirmed"
  },
  "acc": 0.92,
  "start": 12,
  "end": 24
}

clinical_text = "Patient has hypertension, well-controlled on lisinopril."
```

**Output**: FHIR Condition resource

```python
def medcat_to_fhir_condition(entity, patient_id, document_id=None):
    """Convert MedCAT entity to FHIR R4 Condition resource."""

    # Map meta-annotations
    clinical_status = "active" if entity['meta_anns']['Temporality'] in ['Current', 'Recent'] else "resolved"

    verification_status_map = {
        'Confirmed': 'confirmed',
        'Suspected': 'provisional',
        'Hypothetical': 'differential'
    }
    verification_status = verification_status_map.get(
        entity['meta_anns']['Certainty'],
        'unconfirmed'
    )

    condition = {
        "resourceType": "Condition",
        "id": f"nlp-cond-{entity['cui']}",
        "clinicalStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": clinical_status
            }]
        },
        "verificationStatus": {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": verification_status
            }]
        },
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": entity['snomed'][0],
                "display": entity['pretty_name']
            }],
            "text": entity['pretty_name']
        },
        "subject": {
            "reference": f"Patient/{patient_id}"
        },
        "recordedDate": datetime.utcnow().isoformat(),
        "note": [{
            "text": f"Extracted via NLP (confidence: {entity['acc']:.2f})"
        }]
    }

    # Add source document reference if available
    if document_id:
        condition["evidence"] = [{
            "detail": [{
                "reference": f"DocumentReference/{document_id}"
            }]
        }]

    # Add confidence as extension
    condition["extension"] = [{
        "url": "http://example.org/fhir/StructureDefinition/nlp-confidence",
        "valueDecimal": entity['acc']
    }]

    return condition
```

## CDS Hooks integration

**CDS Hooks** enable real-time clinical decision support by calling external services when clinicians interact with EHR.

### Hook: patient-view

Triggered when clinician opens patient chart.

```json
// Request from EHR to CDS service
{
  "hookInstance": "d1577c69-dfbe-44ad-ba6d-3e05e953b2ea",
  "hook": "patient-view",
  "context": {
    "userId": "Practitioner/123",
    "patientId": "Patient/456",
    "encounterId": "Encounter/789"
  }
}
```

**CDS service response** (with NLP-derived alert):

```json
{
  "cards": [{
    "uuid": "nlp-alert-diabetes-001",
    "summary": "Diabetes mentioned in recent note",
    "detail": "NLP detected 'diabetes mellitus' in progress note from 2025-11-05 (confidence: 94%). Consider adding to problem list if not already documented.",
    "indicator": "warning",
    "source": {
      "label": "MedCAT NLP Service"
    },
    "suggestions": [{
      "label": "Add Diabetes to Problem List",
      "actions": [{
        "type": "create",
        "description": "Add Condition resource",
        "resource": {
          "resourceType": "Condition",
          "code": {
            "coding": [{
              "system": "http://snomed.info/sct",
              "code": "73211009",
              "display": "Diabetes Mellitus"
            }]
          },
          "subject": {"reference": "Patient/456"}
        }
      }]
    }],
    "links": [{
      "label": "View Source Note",
      "url": "https://ehr.example.com/notes/12345",
      "type": "absolute"
    }]
  }]
}
```

## LOINC codes for observations

When mapping lab results or vitals (vs conditions):

**Common LOINC codes**:
- `8480-6`: Systolic blood pressure
- `8462-4`: Diastolic blood pressure
- `2339-0`: Glucose
- `2345-7`: Glucose (fasting)
- `4548-4`: Hemoglobin A1C
- `39156-5`: BMI

**Example**:

```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "8480-6",
      "display": "Systolic blood pressure"
    }]
  },
  "subject": {"reference": "Patient/123"},
  "valueQuantity": {
    "value": 140,
    "unit": "mmHg",
    "system": "http://unitsofmeasure.org",
    "code": "mm[Hg]"
  }
}
```

## Reference documentation

**Comprehensive FHIR guide**: See [docs/integration/fhir-integration-guide.md](../../docs/integration/fhir-integration-guide.md)

**FHIR R4 Specification**: https://hl7.org/fhir/R4/

**SNOMED CT Browser**: https://browser.ihtsdotools.org/

**LOINC Search**: https://loinc.org/

**CDS Hooks**: https://cds-hooks.org/

## Common coding systems

**SNOMED CT**: Clinical terms, conditions, procedures
- System URL: `http://snomed.info/sct`
- Example: `73211009` = Diabetes Mellitus

**LOINC**: Lab tests, observations, vital signs
- System URL: `http://loinc.org`
- Example: `2339-0` = Glucose

**RxNorm**: Medications
- System URL: `http://www.nlm.nih.gov/research/umls/rxnorm`
- Example: `197361` = Lisinopril

**ICD-10-CM**: Diagnosis codes (for billing)
- System URL: `http://hl7.org/fhir/sid/icd-10-cm`
- Example: `E11` = Type 2 Diabetes

## Integration workflow

1. **Extract concepts** with MedCAT
2. **Filter by meta-annotations** (use `medcat-meta-annotations` skill)
3. **Map to FHIR resources** (use patterns above)
4. **Post to FHIR server** or respond to CDS Hook
5. **Link back to source** using DocumentReference

## Python implementation template

```python
from typing import List, Dict
from datetime import datetime

class FHIRMapper:
    """Maps MedCAT NLP results to FHIR R4 resources."""

    @staticmethod
    def create_condition(
        entity: Dict,
        patient_id: str,
        document_id: str = None
    ) -> Dict:
        """Create FHIR Condition from MedCAT entity."""

        # Determine status from meta-annotations
        temporality = entity['meta_anns'].get('Temporality', 'Current')
        clinical_status = "active" if temporality in ['Current', 'Recent'] else "resolved"

        certainty = entity['meta_anns'].get('Certainty', 'Confirmed')
        verification_map = {
            'Confirmed': 'confirmed',
            'Suspected': 'provisional',
            'Hypothetical': 'differential'
        }
        verification_status = verification_map.get(certainty, 'unconfirmed')

        condition = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": clinical_status
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": verification_status
                }]
            },
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": entity['snomed'][0],
                    "display": entity['pretty_name']
                }]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "recordedDate": datetime.utcnow().isoformat()
        }

        # Add confidence extension
        if 'acc' in entity:
            condition["extension"] = [{
                "url": "http://example.org/fhir/StructureDefinition/nlp-confidence",
                "valueDecimal": entity['acc']
            }]

        return condition

    @staticmethod
    def batch_convert(
        entities: List[Dict],
        patient_id: str
    ) -> List[Dict]:
        """Convert multiple MedCAT entities to FHIR resources."""

        resources = []

        for entity in entities:
            # Skip negated or non-patient entities
            if (entity['meta_anns'].get('Negation') == 'Negated' or
                entity['meta_anns'].get('Experiencer') != 'Patient'):
                continue

            condition = FHIRMapper.create_condition(entity, patient_id)
            resources.append(condition)

        return resources
```

## Testing your FHIR mappings

Use FHIR validator:
- https://validator.fhir.org/
- Upload your JSON to validate against FHIR R4 spec

## Integration with other skills

Works with:
- `medcat-meta-annotations`: Filter entities before FHIR mapping
- `healthcare-compliance-checker`: FHIR resources must protect PHI
- `spec-kit-enforcer`: FHIR integration should have specification

## Quick decision guide

**Creating FHIR resources**:
- Current diagnosis → Condition (clinicalStatus: active)
- Historical diagnosis → Condition (clinicalStatus: resolved)
- Lab result → Observation (LOINC code)
- Medication → MedicationStatement
- Procedure → Procedure
- Family history → FamilyMemberHistory

**For CDS Hooks**:
- Use `patient-view` hook for chart-open alerts
- Use `order-select` hook for order-specific guidance
- Return Card array with suggestions

**For EHR integration**:
- POST to `/Condition` endpoint
- Include source DocumentReference
- Use SNOMED-CT codes for interoperability

Remember: FHIR integration requires careful mapping and validation. Test thoroughly before production deployment.
