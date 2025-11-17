# FHIR Integration Guide for CogStack NLP

**Last Updated**: 2025-01-07
**FHIR Version**: R4 (with notes on R5 differences)
**Difficulty**: Advanced
**Prerequisites**: Understanding of FHIR resources, REST APIs, and MedCAT basics

---

## Table of Contents

1. [Overview](#overview)
2. [Why FHIR Integration?](#why-fhir-integration)
3. [Architecture Patterns](#architecture-patterns)
4. [FHIR Resource Mappings](#fhir-resource-mappings)
5. [Implementation Guide](#implementation-guide)
6. [CDS Hooks Integration](#cds-hooks-integration)
7. [Bulk FHIR Operations](#bulk-fhir-operations)
8. [Security & Compliance](#security--compliance)
9. [Examples & Code](#examples--code)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This guide explains how to integrate CogStack NLP with FHIR (Fast Healthcare Interoperability Resources), the modern standard for healthcare data exchange.

**What This Enables**:
- Expose NLP results as FHIR Observations
- Process clinical notes from FHIR DocumentReference resources
- Integrate with FHIR-based EHR systems
- Provide real-time clinical decision support via CDS Hooks
- Enable SMART-on-FHIR applications using NLP insights

---

## Why FHIR Integration?

### Healthcare Interoperability

**Traditional Challenge**: Each EHR has proprietary APIs
**FHIR Solution**: Standardized RESTful API across all vendors

**Benefits**:
- **Vendor-neutral**: Works with Epic, Cerner, AllScripts, and any FHIR-compliant EHR
- **Future-proof**: Industry standard backed by HL7
- **Ecosystem**: Leverage existing FHIR tools, libraries, and frameworks
- **Compliance**: Aligns with ONC (Office of the National Coordinator) interoperability rules

### Real-World Use Cases

1. **Condition Extraction**: Extract diagnoses from clinical notes → FHIR Condition resources
2. **Medication Extraction**: Identify medications → FHIR MedicationStatement resources
3. **Clinical Decision Support**: Real-time alerts via CDS Hooks
4. **Population Health**: Bulk export for analytics (FHIR Bulk Data Access)
5. **Patient-Facing Apps**: SMART-on-FHIR apps showing NLP-derived insights

---

## Architecture Patterns

### Pattern 1: NLP Results as FHIR Observations

```
┌─────────────┐
│   EHR       │
│   System    │
└──────┬──────┘
       │ 1. GET DocumentReference
       ▼
┌─────────────────┐
│ FHIR Server     │
│ (HAPI/Firely)   │
└──────┬──────────┘
       │ 2. Return clinical note
       ▼
┌─────────────────┐
│ NLP Processor   │
│ (MedCAT +       │
│  FHIR Adapter)  │
└──────┬──────────┘
       │ 3. Extract concepts
       ▼
┌─────────────────┐
│ FHIR Observation│
│ Resources       │
│                 │
│ code: SNOMED-CT │
│ value: present  │
│ derivedFrom:    │
│   DocumentRef   │
└─────────────────┘
```

---

### Pattern 2: CDS Hooks for Real-Time NLP

```
┌─────────────┐
│ Clinician   │
│ Documents   │
│ in EHR      │
└──────┬──────┘
       │ 1. Draft note
       ▼
┌─────────────────┐
│ EHR System      │
│ Fires CDS Hook: │
│ "note-create"   │
└──────┬──────────┘
       │ 2. HTTP POST with note content
       ▼
┌─────────────────┐
│ CDS Service     │
│ (NLP-powered)   │
└──────┬──────────┘
       │ 3. MedCAT processes
       │    Returns "Cards"
       ▼
┌─────────────────┐
│ EHR displays    │
│ Alert cards:    │
│ - Critical      │
│   findings      │
│ - Suggestions   │
└─────────────────┘
```

---

### Pattern 3: Bulk FHIR Export for Analytics

```
┌──────────────┐
│ FHIR Server  │
│ $export      │
│ operation    │
└──────┬───────┘
       │ 1. Export all DocumentReferences
       ▼
┌──────────────────┐
│ Bulk NLP         │
│ Processor        │
│ (Batch MedCAT)   │
└──────┬───────────┘
       │ 2. Process all notes
       ▼
┌──────────────────┐
│ Analytics DB     │
│ (Elasticsearch)  │
│                  │
│ Aggregated       │
│ concepts for     │
│ cohort analysis  │
└──────────────────┘
```

---

## FHIR Resource Mappings

### Input: DocumentReference → Clinical Note

**FHIR Resource**: `DocumentReference`

**Example**:
```json
{
  "resourceType": "DocumentReference",
  "id": "doc-123",
  "status": "current",
  "type": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "11488-4",
      "display": "Consult note"
    }]
  },
  "subject": {
    "reference": "Patient/patient-456"
  },
  "date": "2024-01-15T10:30:00Z",
  "content": [{
    "attachment": {
      "contentType": "text/plain",
      "data": "UGF0aWVudCBwcmVzZW50cyB3aXRoIGNoZXN0IHBhaW4uLi4="
    }
  }]
}
```

**Mapping**:
- `content.attachment.data` → Text to process with MedCAT
- `subject.reference` → Link NLP results back to patient
- `id` → Reference in derived Observations

---

### Output: Extracted Condition → FHIR Condition

**MedCAT Output**:
```python
{
  "cui": "C0011860",
  "pretty_name": "Type 2 Diabetes Mellitus",
  "source_value": "type 2 diabetes",
  "start": 45,
  "end": 60,
  "meta_anns": {
    "Negation": "Affirmed",
    "Temporality": "Current"
  }
}
```

**FHIR Condition Resource**:
```json
{
  "resourceType": "Condition",
  "id": "condition-from-nlp-789",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active"
    }]
  },
  "verificationStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "unconfirmed",
      "display": "Unconfirmed (extracted via NLP)"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "44054006",
      "display": "Type 2 Diabetes Mellitus"
    }],
    "text": "type 2 diabetes"
  },
  "subject": {
    "reference": "Patient/patient-456"
  },
  "onsetDateTime": "2024-01-15",
  "evidence": [{
    "detail": [{
      "reference": "DocumentReference/doc-123"
    }]
  }],
  "note": [{
    "text": "Extracted via MedCAT NLP from clinical note (confidence: 0.98)"
  }]
}
```

**Key Mappings**:
- MedCAT CUI → SNOMED-CT code (via CDB mapping)
- `meta_anns.Negation="Affirmed"` → `clinicalStatus="active"`
- `meta_anns.Temporality="Current"` → `clinicalStatus="active"`
- Source document → `evidence.detail`

---

### Output: Extracted Concept → FHIR Observation

**Alternative to Condition**: Use Observation for general concepts.

```json
{
  "resourceType": "Observation",
  "id": "obs-nlp-101",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "exam",
      "display": "Exam"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "44054006",
      "display": "Type 2 Diabetes Mellitus"
    }],
    "text": "type 2 diabetes"
  },
  "subject": {
    "reference": "Patient/patient-456"
  },
  "effectiveDateTime": "2024-01-15T10:30:00Z",
  "valueBoolean": true,
  "note": [{
    "text": "NLP extracted from DocumentReference/doc-123 (char 45-60)"
  }],
  "derivedFrom": [{
    "reference": "DocumentReference/doc-123"
  }],
  "component": [
    {
      "code": {
        "text": "Negation Status"
      },
      "valueString": "Affirmed"
    },
    {
      "code": {
        "text": "Temporality"
      },
      "valueString": "Current"
    },
    {
      "code": {
        "text": "Confidence Score"
      },
      "valueDecimal": 0.98
    }
  ]
}
```

**When to Use**:
- Observation: General findings, symptoms, exam findings
- Condition: Confirmed diagnoses, chronic conditions
- MedicationStatement: Medications mentioned in notes

---

## Implementation Guide

### Step 1: Set Up FHIR Server

**Option A: HAPI FHIR (Java)**

```bash
docker run -p 8080:8080 \
  -e hapi.fhir.fhir_version=R4 \
  hapiproject/hapi:latest
```

**Option B: Firely Server (.NET)**

```bash
docker run -p 4080:4080 \
  -e ASPNETCORE_ENVIRONMENT=Development \
  firely/server:latest
```

---

### Step 2: Create FHIR Adapter Service

**Python Example** (FastAPI + FHIR Python Client):

```python
from fastapi import FastAPI, HTTPException
from fhir.resources.documentreference import DocumentReference
from fhir.resources.observation import Observation, ObservationComponent
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from medcat.cat import CAT
import base64

app = FastAPI()
cat = CAT.load_model_pack("./models/medcat_model.zip")

@app.post("/process-document")
async def process_fhir_document(doc_ref_dict: dict):
    """Process FHIR DocumentReference and return NLP Observations"""

    # Parse FHIR DocumentReference
    doc_ref = DocumentReference(**doc_ref_dict)

    # Extract text
    content = doc_ref.content[0].attachment.data
    text = base64.b64decode(content).decode('utf-8')

    # Process with MedCAT
    entities = cat.get_entities(text)

    # Convert to FHIR Observations
    observations = []
    for ent_id, ent in entities['entities'].items():
        obs = create_fhir_observation(
            ent,
            patient_ref=doc_ref.subject.reference,
            source_doc_ref=f"DocumentReference/{doc_ref.id}"
        )
        observations.append(obs.dict())

    return {"observations": observations}


def create_fhir_observation(entity, patient_ref, source_doc_ref):
    """Convert MedCAT entity to FHIR Observation"""

    obs = Observation(
        status="final",
        code=CodeableConcept(
            coding=[
                Coding(
                    system="http://snomed.info/sct",
                    code=entity.get('snomed', ''),
                    display=entity['pretty_name']
                )
            ],
            text=entity['source_value']
        ),
        subject={"reference": patient_ref},
        valueBoolean=True,  # Concept is present
        derivedFrom=[{"reference": source_doc_ref}],
        component=[
            ObservationComponent(
                code={"text": "Negation"},
                valueString=entity['meta_anns'].get('Negation', 'Unknown')
            ),
            ObservationComponent(
                code={"text": "Confidence"},
                valueDecimal=entity['acc']
            )
        ]
    )

    return obs
```

---

### Step 3: Post Observations to FHIR Server

```python
from fhirclient import client
from fhir.resources.observation import Observation

# Configure FHIR client
settings = {
    'app_id': 'cogstack_nlp',
    'api_base': 'http://localhost:8080/fhir'
}
smart = client.FHIRClient(settings=settings)

# Post observation
for obs_dict in observations:
    obs = Observation(**obs_dict)
    obs.create(smart.server)
    print(f"Created Observation/{obs.id}")
```

---

## CDS Hooks Integration

### What are CDS Hooks?

**CDS Hooks** is a standard for integrating clinical decision support into EHR workflows.

**Workflow**:
1. Clinician documents in EHR
2. EHR fires hook (e.g., "patient-view", "order-select")
3. CDS Service receives hook, runs NLP
4. Returns "Cards" with suggestions/alerts
5. EHR displays cards to clinician

---

### Example: Sepsis Alert via NLP

**Hook**: `note-update`

**CDS Service Endpoint**:

```python
@app.post("/cds-services/sepsis-detection")
async def sepsis_detection_hook(request: dict):
    """CDS Hook for real-time sepsis detection"""

    # Extract note content from hook
    context = request['context']
    note_text = context.get('note', '')
    patient_id = context.get('patientId')

    # Process with MedCAT
    entities = cat.get_entities(note_text)

    # Check for sepsis indicators
    sepsis_indicators = ['sepsis', 'septic shock', 'bacteremia']
    found_indicators = [
        ent for ent in entities['entities'].values()
        if any(ind in ent['pretty_name'].lower() for ind in sepsis_indicators)
        and ent['meta_anns'].get('Negation') == 'Affirmed'
    ]

    if found_indicators:
        # Return alert card
        return {
            "cards": [{
                "summary": "⚠️ Possible Sepsis Detected",
                "detail": f"NLP detected mention of: {', '.join([e['source_value'] for e in found_indicators])}",
                "indicator": "critical",
                "source": {
                    "label": "CogStack NLP"
                },
                "suggestions": [{
                    "label": "Order Sepsis Bundle",
                    "actions": [{
                        "type": "create",
                        "description": "Order lactate, blood cultures, antibiotics",
                        "resource": {
                            "resourceType": "ServiceRequest",
                            "code": {
                                "text": "Sepsis Management Bundle"
                            }
                        }
                    }]
                }]
            }]
        }

    # No alerts
    return {"cards": []}
```

**EHR Integration**: Register service at `https://your-server.com/cds-services`

---

## Bulk FHIR Operations

### FHIR Bulk Data Access (FHIR $export)

**Use Case**: Export all clinical notes for batch NLP processing.

**Step 1: Initiate Bulk Export**

```bash
curl -X POST "http://fhir-server/DocumentReference/$export" \
  -H "Accept: application/fhir+json" \
  -H "Prefer: respond-async"
```

**Response**:
```
202 Accepted
Content-Location: http://fhir-server/bulkstatus/job-123
```

**Step 2: Poll for Completion**

```bash
curl "http://fhir-server/bulkstatus/job-123"
```

**Response** (when complete):
```json
{
  "transactionTime": "2024-01-15T12:00:00Z",
  "request": "http://fhir-server/DocumentReference/$export",
  "output": [
    {
      "type": "DocumentReference",
      "url": "http://fhir-server/files/documentrefs-001.ndjson"
    }
  ]
}
```

**Step 3: Download and Process**

```python
import requests
import ndjson
from medcat.cat import CAT

cat = CAT.load_model_pack("./models/medcat.zip")

# Download NDJSON file
resp = requests.get("http://fhir-server/files/documentrefs-001.ndjson")
doc_refs = ndjson.loads(resp.text)

# Process each document
for doc_ref in doc_refs:
    text = extract_text_from_docref(doc_ref)
    entities = cat.get_entities(text)

    # Store results
    store_nlp_results(doc_ref['id'], entities)
```

---

## Security & Compliance

### Authentication

**OAuth 2.0 / SMART-on-FHIR**:

```python
from fhirclient import client

settings = {
    'app_id': 'cogstack_nlp',
    'api_base': 'https://fhir.example.com',
    'redirect_uri': 'https://your-app.com/callback'
}

smart = client.FHIRClient(settings=settings)
smart.authorize_url  # Redirect user here
# After auth callback:
smart.handle_callback(request.url)

# Now authenticated
patient = Patient.read('patient-123', smart.server)
```

---

### Audit Logging

**Track all FHIR access**:

```python
import logging

logger = logging.getLogger('fhir_audit')

@app.middleware("http")
async def audit_fhir_access(request, call_next):
    logger.info(f"FHIR Access: {request.method} {request.url} by {request.user}")
    response = await call_next(request)
    return response
```

---

### PHI Handling

**De-identification before FHIR export**:

```python
from medcat.cat import CAT
from anoncat import AnonCAT

cat = CAT.load_model_pack("./models/medcat.zip")
anon = AnonCAT()

# De-identify before creating FHIR resource
text = "Patient John Smith, MRN 12345, has diabetes."
anon_text = anon.redact(text)
# "Patient [REDACTED], MRN [REDACTED], has diabetes."

# Create FHIR DocumentReference with anonymized text
```

---

## Troubleshooting

### Issue: FHIR Server Rejects Observation

**Error**: "Observation.code is required"

**Fix**: Ensure every Observation has a valid SNOMED-CT or LOINC code.

```python
obs.code = CodeableConcept(
    coding=[
        Coding(
            system="http://snomed.info/sct",
            code="44054006"  # Must be valid SNOMED code
        )
    ]
)
```

---

### Issue: CDS Hook Not Firing

**Checklist**:
- [ ] Service registered at `/cds-services` discovery endpoint
- [ ] Hook name matches EHR config (e.g., "note-update")
- [ ] Endpoint reachable from EHR network
- [ ] Returns valid CDS Hooks response format

---

## Related Resources

- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [CDS Hooks Specification](https://cds-hooks.org/)
- [HAPI FHIR Documentation](https://hapifhir.io/)
- [SMART-on-FHIR](https://docs.smarthealthit.org/)
- [MedCAT Documentation](https://github.com/CogStack/MedCAT)

---

**Questions?** Visit [CogStack Discourse](https://discourse.cogstack.org/) or open an issue on GitHub.
