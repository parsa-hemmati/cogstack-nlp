# Technical Plan: Clinical Coding Module (Sprint 5)

**Version**: 1.0.0  
**Date**: 2025-11-18  
**Sprint Duration**: 4 weeks (~120 hours)  
**Dependencies**: Sprint 1-4, CogStack-ModelServe medcat_icd10 model

---

## Overview

### Goals

- **Automated ICD-10 extraction** using CogStack-ModelServe `medcat_icd10` model
- **Clinical coder assistance UI** with review/approve/reject workflow
- **Code validation** (format, existence, combinations, guidelines)
- **Coding quality metrics** (AI precision/recall, coder productivity)
- **Comprehensive audit logging** for all coding assignments

### Success Criteria

- [ ] AI extracts ICD-10 codes with ≥90% precision, ≥85% recall
- [ ] Coder can review, approve, reject, modify AI suggestions
- [ ] Bulk coding workflow (queue, auto-advance to next document)
- [ ] Code validation (format, existence, excludes1/excludes2 rules)
- [ ] Coding quality metrics dashboard
- [ ] 80% test coverage

---

## Architecture Overview

```
Frontend (Vue 3)
  - ClinicalCodingView.vue
    - Document queue (uncoded, in-progress, coded)
    - AI-suggested codes list (with confidence scores)
    - Code search/add interface (ICD-10 library)
    - Coding summary

Backend (FastAPI)
  - ClinicalCodingService
    - GET /api/v1/coding/queue
    - GET /api/v1/coding/documents/{id}/suggestions
    - POST /api/v1/coding/documents/{id}/codes
    - GET /api/v1/coding/icd10/search
  - ICD10CodeValidator

CogStack-ModelServe
  - medcat_icd10 model (ICD-10 code extraction)
  - Input: Document text
  - Output: ICD-10 codes with confidence scores

PostgreSQL
  - icd10_library (ICD-10-CM code reference)
  - coding_assignments (document coding)
  - coding_metrics (quality metrics)
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| NLP Service | CogStack-ModelServe | latest | ICD-10 extraction |
| ICD-10 Model | medcat_icd10 | latest | Trained on MIMIC-III |
| Code Library | ICD-10-CM 2024 | 2024 | CMS official codes |
| Backend | FastAPI | 0.104 | REST API |
| Frontend | Vue 3 + Vuetify | 3.3 / 3.4 | UI |
| Database | PostgreSQL | 15 | Code storage |

---

## API Design

### GET `/api/v1/coding/queue`

Get coding queue (uncoded, in-progress, coded documents).

**Response**:
```json
{
  "uncoded": [
    {"document_id": "doc-123", "title": "Discharge Summary", "patient_id": "patient-456", "date": "2023-11-15"}
  ],
  "in_progress": [],
  "coded": []
}
```

### GET `/api/v1/coding/documents/{document_id}/suggestions`

Get AI-suggested ICD-10 codes for document.

**Response**:
```json
{
  "document_id": "doc-123",
  "suggestions": [
    {
      "code": "E11.9",
      "description": "Type 2 diabetes mellitus without complications",
      "confidence": 0.95,
      "evidence": "Patient has Type 2 Diabetes Mellitus.",
      "position": 120
    },
    {
      "code": "I10",
      "description": "Essential (primary) hypertension",
      "confidence": 0.89,
      "evidence": "Hypertension managed with medication.",
      "position": 245
    }
  ]
}
```

### POST `/api/v1/coding/documents/{document_id}/codes`

Assign codes to document.

**Request**:
```json
{
  "codes": [
    {"code": "E11.9", "is_primary": true, "source": "ai"},
    {"code": "I10", "is_primary": false, "source": "ai"},
    {"code": "Z79.4", "is_primary": false, "source": "manual"}
  ]
}
```

**Response**:
```json
{
  "document_id": "doc-123",
  "codes_assigned": 3,
  "validation_errors": [],
  "audit_log_id": "audit-789"
}
```

### GET `/api/v1/coding/icd10/search`

Search ICD-10 library (autocomplete for manual code entry).

**Query**: `?q=diabetes&limit=10`

**Response**:
```json
{
  "results": [
    {"code": "E11.9", "description": "Type 2 diabetes mellitus without complications"},
    {"code": "E10.9", "description": "Type 1 diabetes mellitus without complications"}
  ]
}
```

---

## Database Schema

### `icd10_library` (ICD-10-CM Code Reference)

```sql
CREATE TABLE icd10_library (
    code VARCHAR(10) PRIMARY KEY,
    description TEXT NOT NULL,
    category VARCHAR(100),
    parent_code VARCHAR(10),
    is_deprecated BOOLEAN DEFAULT FALSE,
    effective_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_icd10_description ON icd10_library USING gin(to_tsvector('english', description));
```

**Data Source**: CMS ICD-10-CM FY2024 codes (~72,000 codes)

### `coding_assignments` (Document Coding)

```sql
CREATE TABLE coding_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    codes JSONB NOT NULL,  -- Array of {code, is_primary, source, confidence}
    coded_by UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'draft',  -- "draft", "final"
    coded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_coding_assignments_document ON coding_assignments(document_id);
CREATE INDEX idx_coding_assignments_coded_by ON coding_assignments(coded_by);
```

### `coding_metrics` (Quality Metrics)

```sql
CREATE TABLE coding_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    date DATE NOT NULL,
    documents_coded INTEGER DEFAULT 0,
    ai_suggestions_accepted INTEGER DEFAULT 0,
    ai_suggestions_rejected INTEGER DEFAULT 0,
    manual_codes_added INTEGER DEFAULT 0,
    coding_errors INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_coding_metrics_user_date ON coding_metrics(user_id, date);
```

---

## Component Design

### Backend: `ClinicalCodingService`

```python
from typing import List, Dict
from app.clients.cogstack_modelserve import CogStackModelServeClient

class ICD10CodeSuggestion(BaseModel):
    code: str
    description: str
    confidence: float
    evidence: str  # Sentence where condition mentioned
    position: int  # Character offset

class AssignedCode(BaseModel):
    code: str
    is_primary: bool
    source: str  # "ai" or "manual"
    confidence: Optional[float]

class ClinicalCodingService:
    """Clinical coding service"""

    def __init__(self, modelserve: CogStackModelServeClient, db: AsyncSession):
        self.modelserve = modelserve
        self.db = db

    async def get_code_suggestions(self, document_id: str) -> List[ICD10CodeSuggestion]:
        """Get AI-suggested ICD-10 codes"""
        # 1. Get document text
        doc = await self._get_document(document_id)

        # 2. Call CogStack-ModelServe medcat_icd10 model
        response = await self.modelserve.process(
            text=doc.content,
            model="medcat_icd10"
        )

        # 3. Parse ICD-10 codes with confidence scores
        suggestions = []
        for entity in response.get("entities", []):
            if entity.get("cui"):  # ICD-10 code in CUI field
                suggestions.append(ICD10CodeSuggestion(
                    code=entity["cui"],
                    description=entity["pretty_name"],
                    confidence=entity.get("confidence", 1.0),
                    evidence=entity["context"],
                    position=entity["start"]
                ))

        return suggestions

    async def assign_codes(
        self,
        document_id: str,
        codes: List[AssignedCode],
        user_id: str
    ) -> Dict:
        """Assign ICD-10 codes to document"""
        # 1. Validate codes
        validation_errors = await self._validate_codes(codes)
        if validation_errors:
            return {"validation_errors": validation_errors}

        # 2. Save to database
        await self.db.execute(
            """
            INSERT INTO coding_assignments (document_id, codes, coded_by, status)
            VALUES (:doc_id, :codes, :user_id, 'draft')
            """,
            {"doc_id": document_id, "codes": [c.dict() for c in codes], "user_id": user_id}
        )

        # 3. Audit log
        audit_log_id = await self._create_audit_log(user_id, document_id, codes)

        # 4. Update coding metrics
        await self._update_coding_metrics(user_id, codes)

        return {
            "document_id": document_id,
            "codes_assigned": len(codes),
            "validation_errors": [],
            "audit_log_id": audit_log_id
        }

    async def _validate_codes(self, codes: List[AssignedCode]) -> List[str]:
        """Validate ICD-10 codes"""
        errors = []

        for code in codes:
            # Format validation
            if not re.match(r'^[A-TV-Z][0-9][A-Z0-9](\.[A-Z0-9]{1,4})?$', code.code):
                errors.append(f"Invalid code format: {code.code}")
                continue

            # Existence check
            exists = await self.db.fetchone(
                "SELECT 1 FROM icd10_library WHERE code = :code",
                {"code": code.code}
            )
            if not exists:
                errors.append(f"Code not found in library: {code.code}")

            # Deprecation check
            deprecated = await self.db.fetchone(
                "SELECT 1 FROM icd10_library WHERE code = :code AND is_deprecated = TRUE",
                {"code": code.code}
            )
            if deprecated:
                errors.append(f"Deprecated code: {code.code}")

        return errors

    async def search_icd10_codes(self, query: str, limit: int = 10) -> List[Dict]:
        """Search ICD-10 library (autocomplete)"""
        results = await self.db.fetchall(
            """
            SELECT code, description
            FROM icd10_library
            WHERE to_tsvector('english', description) @@ plainto_tsquery('english', :query)
            ORDER BY ts_rank(to_tsvector('english', description), plainto_tsquery('english', :query)) DESC
            LIMIT :limit
            """,
            {"query": query, "limit": limit}
        )
        return [{"code": r.code, "description": r.description} for r in results]
```

### Frontend: `ClinicalCodingView.vue`

```vue
<template>
  <v-container fluid>
    <h1>Clinical Coding</h1>

    <!-- Coding Queue -->
    <v-row>
      <v-col cols="3">
        <v-card>
          <v-card-title>Uncoded Documents ({{ uncodedCount }})</v-card-title>
          <v-list>
            <v-list-item
              v-for="doc in uncodedDocs"
              :key="doc.document_id"
              @click="loadDocument(doc.document_id)"
              :class="{ 'v-list-item--active': currentDocId === doc.document_id }"
            >
              <v-list-item-title>{{ doc.title }}</v-list-item-title>
              <v-list-item-subtitle>{{ doc.date }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-card>
      </v-col>

      <!-- Coding Interface -->
      <v-col cols="9">
        <v-card v-if="currentDoc">
          <v-card-title>{{ currentDoc.title }}</v-card-title>
          <v-card-text>
            <!-- Document Text -->
            <div class="document-text">{{ currentDoc.content }}</div>

            <!-- AI-Suggested Codes -->
            <h3 class="mt-4">AI-Suggested Codes</h3>
            <v-list>
              <v-list-item v-for="suggestion in suggestions" :key="suggestion.code">
                <v-list-item-content>
                  <v-list-item-title>
                    {{ suggestion.code }} - {{ suggestion.description }}
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    Confidence: {{ (suggestion.confidence * 100).toFixed(0) }}%
                  </v-list-item-subtitle>
                  <v-list-item-subtitle class="mt-1 text-caption grey--text">
                    Evidence: "{{ suggestion.evidence }}"
                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-list-item-action>
                  <v-btn icon @click="approveCode(suggestion)" color="success">
                    <v-icon>mdi-check</v-icon>
                  </v-btn>
                  <v-btn icon @click="rejectCode(suggestion)" color="error">
                    <v-icon>mdi-close</v-icon>
                  </v-btn>
                </v-list-item-action>
              </v-list-item>
            </v-list>

            <!-- Assigned Codes -->
            <h3 class="mt-4">Assigned Codes</h3>
            <v-chip
              v-for="code in assignedCodes"
              :key="code.code"
              close
              @click:close="removeCode(code)"
              class="ma-1"
            >
              {{ code.code }} {{ code.is_primary ? '(Primary)' : '' }}
            </v-chip>

            <!-- Add Code Manually -->
            <v-autocomplete
              v-model="selectedCode"
              :items="searchResults"
              :search-input.sync="searchQuery"
              label="Add code manually"
              item-text="description"
              item-value="code"
              return-object
              @change="addCode"
              class="mt-4"
            >
              <template v-slot:item="{ item }">
                <v-list-item-content>
                  <v-list-item-title>{{ item.code }}</v-list-item-title>
                  <v-list-item-subtitle>{{ item.description }}</v-list-item-subtitle>
                </v-list-item-content>
              </template>
            </v-autocomplete>
          </v-card-text>

          <v-card-actions>
            <v-btn @click="saveCodes" color="primary">Save Codes</v-btn>
            <v-btn @click="nextDocument" color="secondary">Next Document</v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useCodingStore } from '@/stores/coding'

const codingStore = useCodingStore()

const uncodedDocs = ref([])
const currentDoc = ref(null)
const currentDocId = ref(null)
const suggestions = ref([])
const assignedCodes = ref([])
const searchQuery = ref('')
const searchResults = ref([])
const selectedCode = ref(null)

async function loadDocument(docId: string) {
  currentDocId.value = docId
  currentDoc.value = await codingStore.getDocument(docId)
  suggestions.value = await codingStore.getSuggestions(docId)
  assignedCodes.value = []
}

function approveCode(suggestion) {
  assignedCodes.value.push({
    code: suggestion.code,
    is_primary: assignedCodes.value.length === 0,
    source: 'ai',
    confidence: suggestion.confidence
  })
  suggestions.value = suggestions.value.filter(s => s.code !== suggestion.code)
}

function rejectCode(suggestion) {
  suggestions.value = suggestions.value.filter(s => s.code !== suggestion.code)
  // Track rejection for metrics
  codingStore.trackRejection(suggestion.code)
}

function addCode() {
  if (selectedCode.value) {
    assignedCodes.value.push({
      code: selectedCode.value.code,
      is_primary: false,
      source: 'manual'
    })
    selectedCode.value = null
    searchQuery.value = ''
  }
}

async function saveCodes() {
  await codingStore.assignCodes(currentDocId.value, assignedCodes.value)
  nextDocument()
}

function nextDocument() {
  const currentIndex = uncodedDocs.value.findIndex(d => d.document_id === currentDocId.value)
  if (currentIndex < uncodedDocs.value.length - 1) {
    loadDocument(uncodedDocs.value[currentIndex + 1].document_id)
  }
}

// Watch search query for autocomplete
watch(searchQuery, async (newValue) => {
  if (newValue && newValue.length >= 2) {
    searchResults.value = await codingStore.searchCodes(newValue)
  }
})

// Load uncoded documents on mount
uncodedDocs.value = await codingStore.getQueue()
</script>
```

---

## Testing Strategy

### Unit Tests (60%)

```python
@pytest.mark.asyncio
async def test_extract_icd10_codes(coding_service):
    """Test ICD-10 code extraction"""
    suggestions = await coding_service.get_code_suggestions("doc-123")
    assert len(suggestions) >= 2
    assert any(s.code == "E11.9" for s in suggestions)  # T2DM
    assert any(s.code == "I10" for s in suggestions)  # HTN

@pytest.mark.asyncio
async def test_validate_code_format(coding_service):
    """Test code format validation"""
    valid_codes = [AssignedCode(code="E11.9", is_primary=True, source="ai")]
    errors = await coding_service._validate_codes(valid_codes)
    assert len(errors) == 0

    invalid_codes = [AssignedCode(code="INVALID", is_primary=True, source="manual")]
    errors = await coding_service._validate_codes(invalid_codes)
    assert len(errors) == 1
    assert "Invalid code format" in errors[0]
```

### Integration Tests (30%)

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_assign_codes_endpoint(async_client, auth_headers):
    """Test POST /api/v1/coding/documents/{id}/codes"""
    response = await async_client.post(
        "/api/v1/coding/documents/doc-123/codes",
        json={"codes": [{"code": "E11.9", "is_primary": True, "source": "ai"}]},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["codes_assigned"] == 1
```

### E2E Tests (10%)

```typescript
test('clinical coding workflow', async ({ page }) => {
  await page.goto('http://localhost:8080/coding')
  await page.click('.v-list-item:first-child')  // Select first uncoded document
  await page.waitForSelector('.v-list-item-title:has-text("E11.9")')
  await page.click('button[aria-label="Approve"]')  // Approve AI suggestion
  await page.click('button:has-text("Save Codes")')
  await page.waitForSelector('text=Codes saved successfully')
})
```

---

## Performance Requirements

- **ICD-10 extraction**: <2 seconds per document
- **Code validation**: <100ms
- **Coder UI actions**: <300ms
- **AI precision**: ≥90%
- **AI recall**: ≥85%

---

## Risks & Mitigations

### Risk 1: ICD-10 Model Accuracy

**Risk**: AI precision/recall below targets (90%/85%)

**Mitigation**:
- Fine-tune medcat_icd10 model on local data
- Collect coder feedback to improve model
- Hybrid approach: AI + manual review

---

## Implementation Phases

### Phase 5.1: CogStack-ModelServe Integration (1 week, 30h)
- Integrate medcat_icd10 model
- Build code suggestion service
- Unit tests

### Phase 5.2: Clinical Coder UI (1 week, 30h)
- Build coding queue
- Build code review interface
- Build code search/add interface

### Phase 5.3: Code Validation (1 week, 30h)
- Implement ICD-10 validator
- Format, existence, deprecation checks
- Excludes1/excludes2 validation

### Phase 5.4: Coding Quality Metrics (1 week, 30h)
- Track AI precision/recall
- Track coder productivity
- Build metrics dashboard

---

## Deployment Checklist

- [ ] CogStack-ModelServe running with medcat_icd10 model
- [ ] ICD-10-CM 2024 library loaded into PostgreSQL
- [ ] Coding tables created (migrations applied)
- [ ] Audit logging enabled
- [ ] Clinical coder role configured (RBAC)

---

**Document Version**: 1.0.0  
**Status**: Ready for implementation  
**Estimated Effort**: 120 hours over 4 weeks
