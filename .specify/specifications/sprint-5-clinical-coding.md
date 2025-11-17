# Specification: Clinical Coding Module (Sprint 5)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 4 weeks (~120 hours)

**Version History**:
- **1.0.0** (2025-11-17): Initial specification for Clinical Coding Module

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Database Schema](#database-schema)
8. [ICD-10 Coding Workflow](#icd-10-coding-workflow)
9. [Code Validation](#code-validation)
10. [Integration Points](#integration-points)
11. [Performance Requirements](#performance-requirements)
12. [Constraints](#constraints)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Alignment with Constitution](#alignment-with-constitution)
15. [Testing Strategy](#testing-strategy)
16. [Deployment Considerations](#deployment-considerations)
17. [Open Questions](#open-questions)

---

## Context

### Background

The **Clinical Coding Module** enables automated ICD-10 coding with AI augmentation to assist clinical coders.

**CogStack Product Alignment**: Clinical Coding (Automated ICD-10 coding with AI augmentation)

**Sprints 1-4 delivered**:
- Patient Search, Timeline View, Full-Text Search, De-Identification

### The Problem

Clinical coding is **time-consuming and error-prone**:
1. **Manual burden**: Coders manually review documents, assign codes
2. **Inconsistency**: Different coders assign different codes for same condition
3. **Missing codes**: Under-coding leads to lost revenue, incomplete records
4. **Coding errors**: Wrong codes lead to billing errors, quality metrics issues
5. **Coder shortage**: Not enough certified coders to meet demand

**Example**: A discharge summary mentions "Type 2 Diabetes Mellitus with diabetic retinopathy". Manual coder must:
- Identify all codeable conditions (T2DM, diabetic retinopathy)
- Look up ICD-10 codes (E11.9 for T2DM, E11.319 for diabetic retinopathy)
- Assign codes correctly (primary vs secondary diagnosis)
- **Time**: 5-10 minutes per document

### Why Clinical Coding Matters

**Operational Value**:
- **Revenue cycle**: Accurate coding → correct billing → faster reimbursement
- **Quality metrics**: ICD-10 codes drive HEDIS, CMS quality measures
- **Clinical research**: Coded data enables cohort identification, outcomes research
- **Public health**: ICD-10 codes used for disease surveillance, registries

**Example Use Case**:
Hospital codes 1,000 discharge summaries per month. With automated coding:
- **Time savings**: 5 minutes/document × 1,000 = 83 hours/month saved
- **Revenue capture**: Identify missed codes → 5% revenue increase
- **Quality improvement**: Consistent coding → better quality scores

### Deployment Context

- **Platform**: Extends Clinical Care Tools Base Application
- **Users**: Clinical coders (review AI suggestions), Clinicians (view coded data), Admin (manage code libraries)
- **Data Source**: Clinical documents with ICD-10 codes extracted by CogStack-ModelServe
- **Integration**: CogStack-ModelServe `medcat_icd10` model

---

## Goals

### Primary Goals

1. **Automated ICD-10 Extraction** (P0)
   - Extract ICD-10 codes from clinical documents using CogStack-ModelServe `medcat_icd10` model
   - Support ICD-10-CM (Clinical Modification) for diagnoses
   - Show code descriptions and hierarchy
   - Confidence scoring for each code suggestion

2. **Clinical Coder Assistance UI** (P0)
   - Review AI-suggested codes (approve/reject/modify)
   - Search ICD-10 code library
   - Add codes not detected by AI
   - Reorder codes (primary vs secondary diagnosis)
   - Bulk coding workflow (code multiple documents in session)

3. **Code Validation** (P0)
   - Validate code format (valid ICD-10-CM code?)
   - Validate code combinations (can codes co-exist?)
   - Detect coding errors (invalid code, deprecated code)
   - Coding guidelines compliance (CMS coding rules)

4. **Coding Quality Metrics** (P0)
   - Track AI accuracy (precision, recall for code suggestions)
   - Track coder productivity (documents coded per hour)
   - Track coding consistency (inter-coder agreement)
   - Coding audit reports (errors, trends, training needs)

5. **Comprehensive Audit Logging** (P0)
   - Log all coding assignments (user, document, codes, timestamp)
   - Log code changes (added, removed, modified)
   - Log AI suggestions accepted/rejected
   - Query audit logs for compliance

### Secondary Goals

6. **Code Suggestion Explanations** (P1)
   - Show why AI suggested a code (context: sentence where condition mentioned)
   - Show evidence (matching text in document)
   - Show confidence score

7. **Coder Training Mode** (P1)
   - Practice coding on sample documents
   - Compare coder's codes vs expert gold standard
   - Feedback on errors
   - Track progress over time

8. **Integration with Billing Systems** (P1)
   - Export coded data to billing systems (HL7, CSV)
   - Map ICD-10 codes to DRGs (Diagnosis Related Groups)
   - Generate billing reports

---

## Non-Goals

1. **ICD-10-PCS** (Procedure Coding System) - Diagnoses only (procedures deferred to future)
2. **CPT/HCPCS Coding** - ICD-10 only
3. **Real-Time Coding** - Batch coding workflow only
4. **External Code Libraries** - Use ICD-10-CM official codes only
5. **Natural Language Queries** - Structured code search only
6. **Perfect AI Accuracy** - AI assists coders, doesn't replace them (95% precision target)

---

## User Stories

### Clinical Coder User Stories

#### US-CC1: Review AI-Suggested Codes
**As a** clinical coder
**I want to** review AI-suggested ICD-10 codes for a document
**So that** I can approve accurate codes and correct errors

**Acceptance Criteria**:
- [ ] Open document → AI-suggested codes displayed
- [ ] Each code shows:
  - ICD-10 code (e.g., E11.9)
  - Description (e.g., "Type 2 diabetes mellitus without complications")
  - Confidence score (e.g., 92%)
  - Evidence (sentence where condition mentioned)
- [ ] Actions: Approve (✓), Reject (✗), Modify (edit)
- [ ] Codes saved to database
- [ ] Audit log entry created

---

#### US-CC2: Add Missing Codes
**As a** clinical coder
**I want to** add ICD-10 codes not detected by AI
**So that** I can ensure complete coding

**Acceptance Criteria**:
- [ ] "Add Code" button
- [ ] Search ICD-10 library (autocomplete)
- [ ] Select code → added to document
- [ ] Reorder codes (drag-and-drop for primary vs secondary)
- [ ] Save → audit log entry created

---

#### US-CC3: Bulk Coding Workflow
**As a** clinical coder
**I want to** code multiple documents in one session
**So that** I can be productive

**Acceptance Criteria**:
- [ ] Queue of uncoded documents
- [ ] Code current document → auto-advance to next
- [ ] Progress tracker (X of Y documents coded)
- [ ] Session summary (total documents, codes assigned, time spent)

---

### Clinician User Stories

#### US-CL1: View Coded Data
**As a** clinician
**I want to** view ICD-10 codes assigned to patient documents
**So that** I can see coded diagnoses

**Acceptance Criteria**:
- [ ] Patient timeline shows ICD-10 codes
- [ ] Click code → show description and evidence
- [ ] Filter timeline by ICD-10 code

---

### Admin User Stories

#### US-A1: View Coding Quality Metrics
**As an** admin
**I want to** view coding quality metrics
**So that** I can assess coder performance and AI accuracy

**Acceptance Criteria**:
- [ ] Coding dashboard showing:
  - AI precision/recall (% of AI suggestions accepted)
  - Coder productivity (documents per hour)
  - Inter-coder agreement (kappa scores)
  - Top-coded diagnoses
  - Coding errors (invalid codes, deprecated codes)
- [ ] Filter by coder, date range
- [ ] Export metrics to CSV

---

## Requirements

### Functional Requirements

#### FR1: Automated ICD-10 Extraction
- **FR1.1**: Extract ICD-10-CM codes using CogStack-ModelServe `medcat_icd10` model
- **FR1.2**: Map SNOMED-CT concepts to ICD-10 codes (when direct ICD-10 not available)
- **FR1.3**: Show code hierarchy (parent codes, child codes)
- **FR1.4**: Confidence scoring (0.0 to 1.0)
- **FR1.5**: Context extraction (sentence where condition mentioned)

#### FR2: Clinical Coder Assistance UI
- **FR2.1**: Review AI-suggested codes (list view)
- **FR2.2**: Approve/reject/modify codes
- **FR2.3**: Add codes not detected by AI (search ICD-10 library)
- **FR2.4**: Reorder codes (primary diagnosis first)
- **FR2.5**: Bulk coding workflow (queue, auto-advance)
- **FR2.6**: Coding summary (document stats, session stats)

#### FR3: Code Validation
- **FR3.1**: Validate code format (valid ICD-10-CM regex: `^[A-TV-Z][0-9][A-Z0-9](\.[A-Z0-9]{1,4})?$`)
- **FR3.2**: Validate code exists in ICD-10-CM library
- **FR3.3**: Detect deprecated codes (codes no longer valid)
- **FR3.4**: Validate code combinations (excludes1/excludes2 rules)
- **FR3.5**: Coding guidelines compliance (CMS rules)

#### FR4: Coding Quality Metrics
- **FR4.1**: AI precision (% of AI suggestions accepted)
- **FR4.2**: AI recall (% of gold standard codes detected)
- **FR4.3**: Coder productivity (documents coded per hour)
- **FR4.4**: Inter-coder agreement (Cohen's kappa between coders)
- **FR4.5**: Coding error tracking (invalid codes, missing codes)

#### FR5: Audit Logging
- **FR5.1**: Log coding assignments (user, document, codes, timestamp)
- **FR5.2**: Log code changes (added, removed, modified with reason)
- **FR5.3**: Log AI suggestions (code, confidence, accepted/rejected)
- **FR5.4**: Query audit logs (filter by user, document, date range)
- **FR5.5**: Export audit logs to CSV

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: ICD-10 extraction: <2 seconds per document
- **NFR1.2**: Code validation: <100ms
- **NFR1.3**: Coder UI response time: <300ms for all actions
- **NFR1.4**: Bulk coding: Support 100+ documents in queue

#### NFR2: Accuracy
- **NFR2.1**: AI precision: ≥90% (90% of AI suggestions correct)
- **NFR2.2**: AI recall: ≥85% (find 85% of all valid codes)
- **NFR2.3**: Code validation: 100% accuracy (catch all invalid codes)

#### NFR3: Security
- **NFR3.1**: Authentication required for coding
- **NFR3.2**: Only certified coders can assign codes
- **NFR3.3**: Audit logging for all code assignments
- **NFR3.4**: Code libraries stored securely (PostgreSQL)

#### NFR4: Usability
- **NFR4.1**: Intuitive coder UI (minimal training required)
- **NFR4.2**: Keyboard shortcuts for efficiency (Tab, Enter, arrow keys)
- **NFR4.3**: WCAG 2.1 AA compliance

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ClinicalCodingView.vue                               │  │
│  │  - Document queue                                     │  │
│  │  - AI-suggested codes list                            │  │
│  │  - Code search/add interface                          │  │
│  │  - Coding summary                                     │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    REST API (FastAPI)
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Clinical Coding Service                              │  │
│  │  - GET /api/v1/coding/queue                           │  │
│  │  - GET /api/v1/coding/documents/{id}/suggestions      │  │
│  │  - POST /api/v1/coding/documents/{id}/codes           │  │
│  │  - GET /api/v1/coding/icd10/search                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  ICD-10 Code Validator                                │  │
│  │  - Format validation                                  │  │
│  │  - Code existence check                               │  │
│  │  - Combination validation                             │  │
│  │  - Guidelines compliance                              │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    CogStack-ModelServe
┌─────────────────────────────────────────────────────────────┐
│              CogStack-ModelServe (port 8001)                │
│  - medcat_icd10 model (ICD-10 code extraction)              │
│  - Confidence scoring                                       │
│  - Context extraction                                       │
└─────────────────────────────────────────────────────────────┘
```

### Backend Services

**ClinicalCodingService** (`app/services/coding_service.py`)
```python
class ClinicalCodingService:
    """Clinical coding service"""

    async def get_coding_queue(
        self,
        user: User,
        status: str = "uncoded"  # "uncoded", "in_progress", "coded"
    ) -> List[CodingQueueItem]:
        """Get coding queue for user"""
        # Return documents needing coding

    async def get_code_suggestions(
        self,
        document_id: str
    ) -> List[ICD10CodeSuggestion]:
        """Get AI-suggested ICD-10 codes"""
        # 1. Get document text
        # 2. Call CogStack-ModelServe medcat_icd10 model
        # 3. Parse ICD-10 codes with confidence scores
        # 4. Return suggestions

    async def assign_codes(
        self,
        document_id: str,
        codes: List[ICD10Code],
        user: User
    ) -> CodingResult:
        """Assign ICD-10 codes to document"""
        # 1. Validate codes
        # 2. Save to database
        # 3. Audit log
        # 4. Return result

    async def search_icd10_codes(
        self,
        query: str
    ) -> List[ICD10Code]:
        """Search ICD-10 library"""
        # Full-text search on code descriptions
```

**ICD10CodeValidator** (`app/validators/icd10_validator.py`)
```python
class ICD10CodeValidator:
    """Validate ICD-10-CM codes"""

    def validate_format(self, code: str) -> bool:
        """Check if code matches ICD-10-CM format"""
        pattern = r'^[A-TV-Z][0-9][A-Z0-9](\.[A-Z0-9]{1,4})?$'
        return re.match(pattern, code) is not None

    def validate_exists(self, code: str) -> bool:
        """Check if code exists in library"""
        return code in self.icd10_library

    def validate_combination(
        self,
        codes: List[str]
    ) -> List[ValidationError]:
        """Check if codes can co-exist"""
        # Check excludes1/excludes2 rules
        # Return list of errors
```

### Database Models

```python
class ICD10Code(BaseModel):
    code: str  # e.g., "E11.9"
    description: str  # e.g., "Type 2 diabetes mellitus without complications"
    category: Optional[str]  # e.g., "Endocrine"
    hierarchy: List[str]  # Parent codes

class ICD10CodeSuggestion(BaseModel):
    code: str
    description: str
    confidence: float  # 0.0 to 1.0
    evidence: str  # Sentence where condition mentioned
    position: int  # Character offset in document

class CodingAssignment(BaseModel):
    document_id: str
    codes: List[AssignedCode]
    coded_by: str  # User ID
    coded_at: datetime
    status: str  # "draft", "final"

class AssignedCode(BaseModel):
    code: str
    is_primary: bool  # Primary diagnosis
    source: str  # "ai", "manual"
    confidence: Optional[float]
```

### API Endpoints

#### GET `/api/v1/coding/queue`
Get coding queue.

**Response**:
```json
{
  "uncoded": [
    {
      "document_id": "doc-123",
      "title": "Discharge Summary",
      "patient_id": "patient-456",
      "date": "2023-11-15T00:00:00Z"
    }
  ],
  "in_progress": [],
  "coded": []
}
```

#### GET `/api/v1/coding/documents/{document_id}/suggestions`
Get AI-suggested codes.

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

#### POST `/api/v1/coding/documents/{document_id}/codes`
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

---

## Database Schema

### New Tables

#### `icd10_library` (ICD-10-CM Codes)
```sql
CREATE TABLE icd10_library (
    code VARCHAR(10) PRIMARY KEY,  -- e.g., "E11.9"
    description TEXT NOT NULL,
    category VARCHAR(100),
    parent_code VARCHAR(10),
    is_deprecated BOOLEAN DEFAULT FALSE,
    effective_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_icd10_description ON icd10_library USING gin(to_tsvector('english', description));
```

#### `coding_assignments` (Document Coding)
```sql
CREATE TABLE coding_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id),
    codes JSONB NOT NULL,  -- Array of AssignedCode objects
    coded_by UUID NOT NULL REFERENCES users(id),
    status VARCHAR(20) DEFAULT 'draft',  -- "draft", "final"
    coded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_coding_assignments_document ON coding_assignments(document_id);
CREATE INDEX idx_coding_assignments_coded_by ON coding_assignments(coded_by);
```

#### `coding_metrics` (Quality Metrics)
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

## ICD-10 Coding Workflow

```
1. Coder opens uncoded document
   ↓
2. AI extracts ICD-10 codes (CogStack-ModelServe medcat_icd10)
   ↓
3. AI-suggested codes displayed with confidence scores
   ↓
4. Coder reviews suggestions:
   - Approve (✓) → add to final codes
   - Reject (✗) → remove from suggestions
   - Modify → edit code
   ↓
5. Coder adds missing codes (search ICD-10 library)
   ↓
6. Coder reorders codes (primary diagnosis first)
   ↓
7. Validate codes (format, existence, combinations)
   ↓
8. Save final codes → audit log
   ↓
9. Auto-advance to next document
```

---

## Code Validation

### Validation Rules

1. **Format Validation**: `^[A-TV-Z][0-9][A-Z0-9](\.[A-Z0-9]{1,4})?$`
   - Examples: `E11.9`, `I10`, `Z79.4`

2. **Existence Check**: Code must exist in `icd10_library` table

3. **Deprecation Check**: Code must not be deprecated

4. **Combination Validation**: Check excludes1/excludes2 rules
   - **Excludes1**: Cannot code both (mutually exclusive)
   - **Excludes2**: Can code both but not typical

5. **Coding Guidelines**: CMS rules (e.g., sequence primary diagnosis first)

---

## Integration Points

### CogStack-ModelServe Integration
- **Model**: `medcat_icd10` (ICD-10 code extraction)
- **Endpoint**: `POST http://cogstack-modelserve:8000/api/process`
- **Input**: Document text
- **Output**: ICD-10 codes with confidence scores

### PostgreSQL Integration
- **Tables**: `icd10_library`, `coding_assignments`, `coding_metrics`, `audit_logs`

---

## Performance Requirements

- **ICD-10 extraction**: <2 seconds per document
- **Code validation**: <100ms
- **Coder UI actions**: <300ms
- **AI precision**: ≥90%
- **AI recall**: ≥85%

---

## Constraints

### Technical Constraints
1. **ICD-10-CM only** - Diagnoses (no procedures)
2. **English only** - ICD-10 library in English
3. **Batch workflow** - No real-time coding during document creation
4. **90% precision target** - AI assists, doesn't replace coders

### Regulatory Constraints
1. **HIPAA compliance** - Audit logging for all coding
2. **CMS coding guidelines** - Validate compliance
3. **Certified coders only** - Only users with "Clinical Coder" role can assign codes

---

## Acceptance Criteria

### Functional Acceptance

- [ ] AI extracts ICD-10 codes with ≥90% precision, ≥85% recall
- [ ] Coder can review, approve, reject, modify AI suggestions
- [ ] Coder can add missing codes (search ICD-10 library)
- [ ] Coder can reorder codes (primary first)
- [ ] Bulk coding workflow (queue, auto-advance)
- [ ] Code validation (format, existence, combinations)
- [ ] Coding quality metrics (precision, recall, productivity)
- [ ] Audit logging for all coding assignments

### Performance Acceptance

- [ ] ICD-10 extraction <2 seconds per document
- [ ] Code validation <100ms
- [ ] Coder UI response <300ms

### Security Acceptance

- [ ] Authentication required
- [ ] Only Clinical Coders can assign codes
- [ ] Audit logging

### Testing Acceptance

- [ ] Unit test coverage ≥80%
- [ ] Integration test coverage ≥70%
- [ ] E2E test for coding workflow

---

## Alignment with Constitution

### Principle 3: Evidence-Based Development
- **CogStack-ModelServe medcat_icd10**: Production-tested ICD-10 extraction model

### Principle 6: Transparency and Explainability
- **Confidence scores**: Show AI confidence for each suggestion
- **Evidence**: Show sentence where condition mentioned
- **Audit trails**: Track all coding decisions

### Principle 9: Clinical Workflow Integration
- **Bulk coding**: Efficient workflow for coders
- **Keyboard shortcuts**: Fast coding actions
- **Auto-advance**: Minimize clicks

---

## Testing Strategy

### Unit Tests (60%)

```python
@pytest.mark.asyncio
async def test_extract_icd10_codes(coding_service):
    # Arrange
    text = "Patient has Type 2 Diabetes Mellitus and Hypertension."

    # Act
    suggestions = await coding_service.get_code_suggestions(document_id="doc-123")

    # Assert
    assert len(suggestions) >= 2
    assert any(s.code == "E11.9" for s in suggestions)  # T2DM
    assert any(s.code == "I10" for s in suggestions)  # HTN

@pytest.mark.asyncio
async def test_validate_code_format(validator):
    assert validator.validate_format("E11.9") == True
    assert validator.validate_format("INVALID") == False
```

### Integration Tests (30%)

```python
@pytest.mark.asyncio
async def test_assign_codes_endpoint(async_client, auth_headers):
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
test('code document workflow', async ({ page }) => {
  await page.goto('http://localhost:8080/coding')
  await page.click('button:has-text("Start Coding")')
  await page.waitForSelector('.code-suggestion')
  await page.click('button:has-text("Approve All")')
  await page.click('button:has-text("Add Code")')
  await page.fill('input[name="code-search"]', 'diabetes')
  await page.click('text=E11.9')
  await page.click('button:has-text("Save Codes")')
  await page.waitForSelector('text=Codes Saved')
})
```

---

## Deployment Considerations

### Docker Compose Updates

```yaml
services:
  cogstack-modelserve:
    environment:
      - MODEL_ICD10_PATH=/models/medcat_icd10.zip
```

### Environment Variables

```bash
CODING_ENABLED=true
ICD10_LIBRARY_PATH=/app/data/icd10cm_library.csv
```

### Database Migrations

```bash
alembic revision --autogenerate -m "Add coding tables"
alembic upgrade head
```

---

## Open Questions

1. **ICD-10 Library Source**: Use CMS official library or custom?
2. **Code Combination Rules**: Implement full excludes1/excludes2 validation?
3. **Coder Training**: Include training mode in this sprint?
4. **Billing Integration**: Export to billing systems in this sprint or future?

---

**Status**: Ready for review and approval
**Next Steps**: Create Technical Plan for Sprint 5 (Clinical Coding) after specification approval
**Dependencies**: Base Application (MVP), CogStack-ModelServe `medcat_icd10` model
**Estimated Effort**: 120 hours over 4 weeks
