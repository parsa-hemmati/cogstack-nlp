# Technical Plan: EHR De-Identification (Sprint 4)

**Version**: 1.0.0
**Date**: 2025-11-18
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Sprint Duration**: 4 weeks (~120 hours)
**Dependencies**: Sprint 1-3, CogStack-ModelServe anonymization model

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Overview](#architecture-overview)
3. [Technology Stack](#technology-stack)
4. [API Design](#api-design)
5. [Database Schema](#database-schema)
6. [Component Design](#component-design)
7. [Testing Strategy](#testing-strategy)
8. [Performance Requirements](#performance-requirements)
9. [Risks & Mitigations](#risks--mitigations)
10. [Implementation Phases](#implementation-phases)

---

## Overview

### Goals

Sprint 4 delivers **automated de-identification** using CogStack-ModelServe:
- **Automated PII detection**: Detect names, addresses, dates, IDs using NER models
- **Redaction modes**: Mask, replace with surrogates, remove entirely
- **Re-identification mapping**: Store original→surrogate mapping for research
- **Audit logging**: Track all de-identification operations
- **Batch processing**: De-identify multiple documents in batch
- **Preview mode**: Show what will be redacted before applying

### Success Criteria

- [ ] Automated de-identification using CogStack-ModelServe operational
- [ ] Support 3 redaction modes (mask, surrogate, remove)
- [ ] Re-identification mapping stored securely (encrypted)
- [ ] Batch de-identification processing 100+ documents
- [ ] Audit logging for all de-identification operations
- [ ] 80% test coverage (unit + integration)
- [ ] Performance: <5 seconds per document

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  DeidentificationView.vue                             │  │
│  │  - Document selection (single or batch)               │  │
│  │  - Redaction mode selector                            │  │
│  │  - Preview pane (highlighted PII)                     │  │
│  │  - Apply de-identification button                     │  │
│  │  - Download de-identified documents                   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  De-identification Service                            │  │
│  │  - POST /api/v1/deidentify/preview                    │  │
│  │  - POST /api/v1/deidentify/apply                      │  │
│  │  - POST /api/v1/deidentify/batch                      │  │
│  │  - GET /api/v1/deidentify/audit                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  CogStack-ModelServe Client                           │  │
│  │  - POST /api/process (anonymization model)            │  │
│  │  - Detects: PERSON, DATE, ID, LOCATION, PHONE        │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
┌─────────────────────────────────────────────────────────────┐
│         CogStack-ModelServe (port 8001)                     │
│  - medcat_ner_phi model (PHI detection)                     │
│  - Entity types: PERSON, DATE, ID, LOCATION, PHONE, EMAIL  │
└─────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL (Encrypted Re-ID Mapping)           │
│  - reidentification_mappings table (pgcrypto)               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

**De-Identification Flow**:
1. User selects document(s) → Click "Preview De-identification"
2. Frontend sends POST `/api/v1/deidentify/preview` with document IDs
3. Backend fetches document text from PostgreSQL
4. Backend calls CogStack-ModelServe `/api/process` with anonymization model
5. ModelServe returns detected entities: `[{text: "John Doe", label: "PERSON", start: 10, end: 18}]`
6. Backend generates surrogates (e.g., "John Doe" → "Patient-A")
7. Backend stores original→surrogate mapping in `reidentification_mappings` (encrypted)
8. Backend returns preview with highlighted PII
9. User reviews preview → Click "Apply De-identification"
10. Backend applies redaction (mask/surrogate/remove) and creates de-identified document
11. De-identified document stored in `deidentified_documents` table
12. Audit log entry created

---

## Technology Stack

### Backend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| NLP Service | CogStack-ModelServe | latest | PHI detection (NER) |
| NER Model | medcat_ner_phi | latest | Trained on i2b2 dataset |
| Encryption | pgcrypto | PostgreSQL ext | Encrypt re-ID mappings |
| Web Framework | FastAPI | 0.104 | REST API endpoints |
| Task Queue | Celery | 5.3 | Batch processing |
| Message Broker | Redis | 7.2 | Celery backend |

### Frontend

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Framework | Vue 3 | 3.3 | Reactive UI |
| UI Library | Vuetify | 3.4 | Material Design components |
| Text Highlighting | mark.js | 9.0 | Highlight PII in preview |

---

## API Design

### Endpoints

#### POST `/api/v1/deidentify/preview`

Preview de-identification (show what will be redacted).

**Request Schema**:
```json
{
  "document_ids": ["doc-123", "doc-456"],
  "redaction_mode": "surrogate"  // "mask", "surrogate", "remove"
}
```

**Response Schema**:
```json
{
  "previews": [
    {
      "document_id": "doc-123",
      "original_text": "Patient John Doe (DOB: 01/15/1980) presents with chest pain...",
      "entities": [
        {
          "text": "John Doe",
          "label": "PERSON",
          "start": 8,
          "end": 16,
          "surrogate": "Patient-A",
          "confidence": 0.98
        },
        {
          "text": "01/15/1980",
          "label": "DATE",
          "start": 23,
          "end": 33,
          "surrogate": "01/15/19XX",
          "confidence": 0.95
        }
      ],
      "redacted_text": "Patient [Patient-A] (DOB: [01/15/19XX]) presents with chest pain..."
    }
  ]
}
```

---

#### POST `/api/v1/deidentify/apply`

Apply de-identification (create de-identified document).

**Request Schema**:
```json
{
  "document_ids": ["doc-123"],
  "redaction_mode": "surrogate",
  "store_mapping": true  // Store re-ID mapping for research
}
```

**Response Schema**:
```json
{
  "deidentified_documents": [
    {
      "original_document_id": "doc-123",
      "deidentified_document_id": "deid-789",
      "redaction_mode": "surrogate",
      "entities_redacted": 5,
      "mapping_id": "map-321",  // Re-identification mapping ID
      "audit_log_id": "audit-654"
    }
  ]
}
```

---

#### POST `/api/v1/deidentify/batch`

Batch de-identify documents (async processing).

**Request Schema**:
```json
{
  "document_ids": ["doc-1", "doc-2", ...],  // Up to 1000 documents
  "redaction_mode": "surrogate",
  "store_mapping": true
}
```

**Response Schema**:
```json
{
  "job_id": "job-999",
  "status": "pending",  // "pending", "processing", "completed", "failed"
  "total_documents": 1000,
  "estimated_completion": "2023-11-17T11:30:00Z"
}
```

**Check status**: `GET /api/v1/deidentify/batch/{job_id}`

---

#### GET `/api/v1/deidentify/audit`

Get de-identification audit log.

**Query Parameters**:
```
date_from: str      # Start date (ISO format)
date_to: str        # End date (ISO format)
user_id: str        # Filter by user (optional)
limit: int          # Max results (default: 100)
```

**Response Schema**:
```json
{
  "audit_entries": [
    {
      "id": "audit-123",
      "user_id": "user-456",
      "operation": "deidentify_apply",
      "document_ids": ["doc-123"],
      "redaction_mode": "surrogate",
      "entities_redacted": 5,
      "timestamp": "2023-11-17T10:30:00Z"
    }
  ]
}
```

---

## Database Schema

### New Tables

#### `deidentified_documents` (De-Identified Document Storage)

```sql
CREATE TABLE deidentified_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    original_document_id UUID NOT NULL REFERENCES documents(id),
    redaction_mode VARCHAR(20) NOT NULL,  -- "mask", "surrogate", "remove"
    redacted_text TEXT NOT NULL,
    entities_redacted INTEGER NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deid_original_doc ON deidentified_documents(original_document_id);
CREATE INDEX idx_deid_created_at ON deidentified_documents(created_at);
```

#### `reidentification_mappings` (Original→Surrogate Mapping, Encrypted)

```sql
-- Enable pgcrypto extension
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE reidentification_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    entity_type VARCHAR(50) NOT NULL,  -- "PERSON", "DATE", "ID", etc.
    original_value_encrypted BYTEA NOT NULL,  -- Encrypted original value
    surrogate_value VARCHAR(200) NOT NULL,    -- Surrogate (e.g., "Patient-A")
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_reid_document ON reidentification_mappings(document_id);
CREATE INDEX idx_reid_surrogate ON reidentification_mappings(surrogate_value);

-- Encryption/Decryption functions
CREATE OR REPLACE FUNCTION encrypt_value(plaintext TEXT, key TEXT)
RETURNS BYTEA AS $$
BEGIN
    RETURN pgp_sym_encrypt(plaintext, key);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION decrypt_value(ciphertext BYTEA, key TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN pgp_sym_decrypt(ciphertext, key);
END;
$$ LANGUAGE plpgsql;
```

**Security Note**: Encryption key stored in environment variable `REID_ENCRYPTION_KEY` (rotate regularly)

#### `deidentification_jobs` (Batch Processing Jobs)

```sql
CREATE TABLE deidentification_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    document_ids UUID[] NOT NULL,
    redaction_mode VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',  -- "pending", "processing", "completed", "failed"
    total_documents INTEGER NOT NULL,
    processed_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deid_jobs_user ON deidentification_jobs(user_id);
CREATE INDEX idx_deid_jobs_status ON deidentification_jobs(status);
```

---

## Component Design

### Backend Services

#### `DeidentificationService` (`app/services/deidentification_service.py`)

```python
from typing import List, Dict
from app.clients.cogstack_modelserve import CogStackModelServeClient
from app.models import Document, ReidentificationMapping
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib

class RedactionMode(str, Enum):
    MASK = "mask"          # Replace with *** or [REDACTED]
    SURROGATE = "surrogate"  # Replace with "Patient-A", "Date-1", etc.
    REMOVE = "remove"      # Remove entirely

class DetectedEntity(BaseModel):
    text: str
    label: str  # PERSON, DATE, ID, LOCATION, PHONE, EMAIL
    start: int
    end: int
    confidence: float

class DeidentificationPreview(BaseModel):
    document_id: str
    original_text: str
    entities: List[DetectedEntity]
    redacted_text: str

class DeidentificationService:
    """De-identification service using CogStack-ModelServe"""

    def __init__(
        self,
        modelserve_client: CogStackModelServeClient,
        db: AsyncSession,
        encryption_key: str
    ):
        self.modelserve = modelserve_client
        self.db = db
        self.encryption_key = encryption_key

    async def preview_deidentification(
        self,
        document_ids: List[str],
        redaction_mode: RedactionMode
    ) -> List[DeidentificationPreview]:
        """
        Preview de-identification (show what will be redacted).

        Args:
            document_ids: Documents to preview
            redaction_mode: How to redact (mask, surrogate, remove)

        Returns:
            List of previews with detected entities and redacted text
        """
        previews = []

        for doc_id in document_ids:
            # Fetch document text
            doc = await self._get_document(doc_id)

            # Detect PHI using CogStack-ModelServe
            entities = await self._detect_phi(doc.content)

            # Generate redacted text
            redacted_text = self._apply_redaction(
                doc.content,
                entities,
                redaction_mode,
                generate_surrogates=True
            )

            previews.append(DeidentificationPreview(
                document_id=doc_id,
                original_text=doc.content,
                entities=entities,
                redacted_text=redacted_text
            ))

        return previews

    async def apply_deidentification(
        self,
        document_ids: List[str],
        redaction_mode: RedactionMode,
        store_mapping: bool,
        user_id: str
    ) -> List[Dict]:
        """
        Apply de-identification (create de-identified documents).

        Args:
            document_ids: Documents to de-identify
            redaction_mode: How to redact
            store_mapping: Store re-identification mapping?
            user_id: User applying de-identification

        Returns:
            List of de-identified document IDs
        """
        results = []

        for doc_id in document_ids:
            # Fetch document
            doc = await self._get_document(doc_id)

            # Detect PHI
            entities = await self._detect_phi(doc.content)

            # Generate surrogates
            entity_mappings = self._generate_surrogates(entities)

            # Apply redaction
            redacted_text = self._apply_redaction(
                doc.content,
                entities,
                redaction_mode,
                entity_mappings=entity_mappings
            )

            # Store de-identified document
            deid_doc = await self._store_deidentified_document(
                original_document_id=doc_id,
                redacted_text=redacted_text,
                redaction_mode=redaction_mode,
                entities_redacted=len(entities),
                user_id=user_id
            )

            # Store re-identification mapping (encrypted)
            mapping_id = None
            if store_mapping:
                mapping_id = await self._store_reid_mapping(
                    document_id=doc_id,
                    entity_mappings=entity_mappings
                )

            # Audit log
            audit_log_id = await self._create_audit_log(
                user_id=user_id,
                operation="deidentify_apply",
                document_ids=[doc_id],
                redaction_mode=redaction_mode,
                entities_redacted=len(entities)
            )

            results.append({
                "original_document_id": doc_id,
                "deidentified_document_id": str(deid_doc.id),
                "redaction_mode": redaction_mode,
                "entities_redacted": len(entities),
                "mapping_id": mapping_id,
                "audit_log_id": audit_log_id
            })

        return results

    async def _detect_phi(self, text: str) -> List[DetectedEntity]:
        """Detect PHI using CogStack-ModelServe NER model"""
        response = await self.modelserve.process(
            text=text,
            model="medcat_ner_phi"
        )

        entities = []
        for ent in response.get("entities", []):
            entities.append(DetectedEntity(
                text=ent["text"],
                label=ent["label"],  # PERSON, DATE, ID, LOCATION, PHONE, EMAIL
                start=ent["start"],
                end=ent["end"],
                confidence=ent.get("confidence", 1.0)
            ))

        return entities

    def _generate_surrogates(self, entities: List[DetectedEntity]) -> Dict[str, str]:
        """
        Generate surrogates for entities.

        Examples:
        - PERSON: "John Doe" → "Patient-A", "Jane Smith" → "Patient-B"
        - DATE: "01/15/1980" → "01/15/19XX" (year masked)
        - ID: "123-45-6789" → "ID-0001"
        - LOCATION: "123 Main St" → "Address-1"
        - PHONE: "555-1234" → "Phone-1"
        """
        entity_mappings = {}
        counters = {
            "PERSON": 0,
            "DATE": 0,
            "ID": 0,
            "LOCATION": 0,
            "PHONE": 0,
            "EMAIL": 0
        }

        for entity in entities:
            original = entity.text

            if original in entity_mappings:
                continue  # Already mapped

            if entity.label == "PERSON":
                counters["PERSON"] += 1
                surrogate = f"Patient-{chr(64 + counters['PERSON'])}"  # Patient-A, Patient-B, ...
            elif entity.label == "DATE":
                # Mask year (keep month/day for temporal analysis)
                import re
                date_masked = re.sub(r'\d{4}', '19XX', original)
                surrogate = date_masked
            elif entity.label == "ID":
                counters["ID"] += 1
                surrogate = f"ID-{counters['ID']:04d}"
            elif entity.label == "LOCATION":
                counters["LOCATION"] += 1
                surrogate = f"Address-{counters['LOCATION']}"
            elif entity.label == "PHONE":
                counters["PHONE"] += 1
                surrogate = f"Phone-{counters['PHONE']}"
            elif entity.label == "EMAIL":
                counters["EMAIL"] += 1
                surrogate = f"email-{counters['EMAIL']}@example.com"
            else:
                surrogate = "[REDACTED]"

            entity_mappings[original] = surrogate

        return entity_mappings

    def _apply_redaction(
        self,
        text: str,
        entities: List[DetectedEntity],
        redaction_mode: RedactionMode,
        entity_mappings: Dict[str, str] = None
    ) -> str:
        """Apply redaction to text"""
        # Sort entities by start position (reverse order to preserve offsets)
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

        redacted_text = text
        for entity in sorted_entities:
            original = entity.text

            if redaction_mode == RedactionMode.MASK:
                replacement = "[REDACTED]"
            elif redaction_mode == RedactionMode.SURROGATE:
                replacement = entity_mappings.get(original, "[REDACTED]")
            elif redaction_mode == RedactionMode.REMOVE:
                replacement = ""

            # Replace entity in text
            redacted_text = (
                redacted_text[:entity.start] +
                replacement +
                redacted_text[entity.end:]
            )

        return redacted_text

    async def _store_reid_mapping(
        self,
        document_id: str,
        entity_mappings: Dict[str, str]
    ) -> str:
        """Store re-identification mapping (encrypted)"""
        mapping_id = str(uuid.uuid4())

        for original, surrogate in entity_mappings.items():
            # Encrypt original value
            encrypted_original = await self.db.execute(
                "SELECT encrypt_value(:plaintext, :key)",
                {"plaintext": original, "key": self.encryption_key}
            )

            # Store mapping
            await self.db.execute(
                """
                INSERT INTO reidentification_mappings
                (id, document_id, entity_type, original_value_encrypted, surrogate_value)
                VALUES (:id, :document_id, :entity_type, :encrypted, :surrogate)
                """,
                {
                    "id": str(uuid.uuid4()),
                    "document_id": document_id,
                    "entity_type": "UNKNOWN",  # Could detect type from surrogate format
                    "encrypted": encrypted_original,
                    "surrogate": surrogate
                }
            )

        await self.db.commit()
        return mapping_id

    async def batch_deidentify(
        self,
        document_ids: List[str],
        redaction_mode: RedactionMode,
        store_mapping: bool,
        user_id: str
    ) -> str:
        """
        Batch de-identify documents (async processing using Celery).

        Returns:
            Job ID for status tracking
        """
        # Create job record
        job_id = str(uuid.uuid4())
        await self.db.execute(
            """
            INSERT INTO deidentification_jobs
            (id, user_id, document_ids, redaction_mode, total_documents)
            VALUES (:id, :user_id, :doc_ids, :mode, :total)
            """,
            {
                "id": job_id,
                "user_id": user_id,
                "doc_ids": document_ids,
                "mode": redaction_mode,
                "total": len(document_ids)
            }
        )
        await self.db.commit()

        # Queue Celery task
        from app.tasks import deidentify_batch_task
        deidentify_batch_task.delay(
            job_id=job_id,
            document_ids=document_ids,
            redaction_mode=redaction_mode,
            store_mapping=store_mapping,
            user_id=user_id
        )

        return job_id
```

---

### Frontend Components

#### `DeidentificationView.vue` (Simplified Structure)

```vue
<template>
  <v-container>
    <h1>De-Identification</h1>

    <!-- Document Selection -->
    <v-card>
      <v-card-title>Select Documents</v-card-title>
      <v-card-text>
        <v-data-table
          v-model="selectedDocuments"
          :items="documents"
          :headers="headers"
          show-select
        />
      </v-card-text>
    </v-card>

    <!-- Redaction Mode -->
    <v-card class="mt-4">
      <v-card-title>Redaction Mode</v-card-title>
      <v-card-text>
        <v-radio-group v-model="redactionMode">
          <v-radio label="Mask (***)" value="mask" />
          <v-radio label="Surrogate (Patient-A)" value="surrogate" />
          <v-radio label="Remove Entirely" value="remove" />
        </v-radio-group>

        <v-checkbox
          v-model="storeMapping"
          label="Store re-identification mapping (for research)"
        />
      </v-card-text>
    </v-card>

    <!-- Actions -->
    <v-card-actions>
      <v-btn @click="previewDeidentification" color="secondary">
        Preview
      </v-btn>
      <v-btn @click="applyDeidentification" color="primary">
        Apply De-identification
      </v-btn>
    </v-card-actions>

    <!-- Preview Dialog -->
    <v-dialog v-model="previewDialog" max-width="800">
      <v-card>
        <v-card-title>De-identification Preview</v-card-title>
        <v-card-text>
          <div v-for="preview in previews" :key="preview.document_id">
            <h3>{{ preview.document_id }}</h3>
            <div class="preview-text" v-html="highlightEntities(preview)"></div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-btn @click="previewDialog = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useDeidentificationStore } from '@/stores/deidentification'

const deidStore = useDeidentificationStore()

const selectedDocuments = ref([])
const redactionMode = ref('surrogate')
const storeMapping = ref(true)
const previews = ref([])
const previewDialog = ref(false)

async function previewDeidentification() {
  previews.value = await deidStore.preview({
    document_ids: selectedDocuments.value.map(d => d.id),
    redaction_mode: redactionMode.value
  })
  previewDialog.value = true
}

async function applyDeidentification() {
  await deidStore.apply({
    document_ids: selectedDocuments.value.map(d => d.id),
    redaction_mode: redactionMode.value,
    store_mapping: storeMapping.value
  })
  // Show success notification
}

function highlightEntities(preview) {
  let html = preview.original_text
  // Highlight detected entities
  for (const entity of preview.entities.sort((a, b) => b.start - a.start)) {
    html = html.slice(0, entity.start) +
           `<mark class="entity-${entity.label}">${entity.text}</mark>` +
           html.slice(entity.end)
  }
  return html
}
</script>
```

---

## Testing Strategy

### Unit Tests (60%)

```python
@pytest.mark.asyncio
async def test_detect_phi(deid_service):
    """Test PHI detection"""
    text = "Patient John Doe (DOB: 01/15/1980, SSN: 123-45-6789) presents with chest pain."
    entities = await deid_service._detect_phi(text)

    assert len(entities) >= 3  # PERSON, DATE, ID
    assert any(e.label == "PERSON" and "John Doe" in e.text for e in entities)
    assert any(e.label == "DATE" and "01/15/1980" in e.text for e in entities)
    assert any(e.label == "ID" and "123-45-6789" in e.text for e in entities)

@pytest.mark.asyncio
async def test_generate_surrogates(deid_service):
    """Test surrogate generation"""
    entities = [
        DetectedEntity(text="John Doe", label="PERSON", start=0, end=8, confidence=0.98),
        DetectedEntity(text="Jane Smith", label="PERSON", start=20, end=30, confidence=0.97)
    ]
    mappings = deid_service._generate_surrogates(entities)

    assert mappings["John Doe"] == "Patient-A"
    assert mappings["Jane Smith"] == "Patient-B"
```

### Integration Tests (30%)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_preview_endpoint(async_client, auth_headers):
    """Test POST /api/v1/deidentify/preview"""
    response = await async_client.post(
        "/api/v1/deidentify/preview",
        json={"document_ids": ["doc-123"], "redaction_mode": "surrogate"},
        headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["previews"]) == 1
    assert "entities" in data["previews"][0]
```

### E2E Tests (10%)

```typescript
test('de-identification workflow', async ({ page }) => {
  await page.goto('http://localhost:8080/deidentification')

  // Select document
  await page.check('input[type="checkbox"]')

  // Select redaction mode
  await page.click('text=Surrogate (Patient-A)')

  // Preview
  await page.click('button:has-text("Preview")')
  await page.waitForSelector('.preview-text')

  // Verify highlighted PII
  await expect(page.locator('mark.entity-PERSON')).toContainText('John Doe')

  // Apply
  await page.click('button:has-text("Apply")')
  await page.waitForSelector('text=De-identification completed')
})
```

---

## Performance Requirements

- **PHI Detection**: <5 seconds per document (up to 10KB text)
- **Batch Processing**: 100 documents in <10 minutes
- **Preview Generation**: <3 seconds per document
- **Re-ID Mapping Storage**: <1 second (encrypted)

---

## Risks & Mitigations

### Risk 1: False Negatives (Missed PII)

**Mitigation**:
- Use high-recall NER model (i2b2-trained)
- Manual review before release
- Audit random samples

---

## Implementation Phases

### Phase 4.1: CogStack-ModelServe Integration (1 week, 30h)
- Integrate medcat_ner_phi model
- Build PHI detection service
- Unit tests

### Phase 4.2: Redaction Modes (1 week, 30h)
- Implement mask/surrogate/remove modes
- Generate surrogates
- Unit tests

### Phase 4.3: Re-ID Mapping Storage (1 week, 30h)
- Create reidentification_mappings table
- Implement pgcrypto encryption
- Store mappings securely

### Phase 4.4: Batch Processing (1 week, 30h)
- Celery task for batch de-identification
- Job status tracking
- Integration tests

---

## Deployment Checklist

- [ ] CogStack-ModelServe running with medcat_ner_phi model
- [ ] PostgreSQL pgcrypto extension enabled
- [ ] Environment variable `REID_ENCRYPTION_KEY` set (32-byte key)
- [ ] Celery worker running for batch processing
- [ ] Audit logging enabled

---

**Document Version**: 1.0.0
**Status**: Ready for implementation
**Estimated Effort**: 120 hours over 4 weeks
