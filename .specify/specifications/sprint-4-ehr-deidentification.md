# Specification: EHR De-Identification Module (Sprint 4)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 4 weeks (~120 hours)

**Version History**:
- **1.0.0** (2025-11-17): Initial specification for EHR De-Identification Module

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Database Schema](#database-schema)
8. [De-Identification Strategies](#de-identification-strategies)
9. [Pseudonymization Algorithm](#pseudonymization-algorithm)
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

The **EHR De-Identification Module** is the fourth module in the Clinical Care Tools platform, building on:
- **Sprint 1**: Patient Search
- **Sprint 2**: Timeline View
- **Sprint 3**: Full-Text Search

**CogStack Product Alignment**: EHR De-Identification (removes PII while preserving clinical meaning)

### The Problem

Researchers and quality improvement teams need access to clinical data but face barriers:
1. **Privacy regulations**: HIPAA, GDPR prohibit sharing PHI without authorization
2. **Manual redaction**: Time-consuming (hours per document)
3. **Over-redaction**: Removing too much context makes data useless
4. **Under-redaction**: Missing PHI creates privacy breaches
5. **Inconsistent methods**: Manual processes vary between reviewers

### Why De-Identification Matters

**Research Enablement**:
- **Secondary use of clinical data**: Enable research without individual consent
- **Multi-site collaborations**: Share de-identified data across organizations
- **Public datasets**: Create de-identified corpora for NLP model training
- **Quality improvement**: Analyze care patterns without exposing patient identities

**Regulatory Compliance**:
- **HIPAA Safe Harbor**: Remove 18 identifiers → data no longer PHI
- **HIPAA Expert Determination**: Statistician certifies re-identification risk <threshold
- **GDPR pseudonymization**: Replace identifiers with consistent tokens

**Example Use Case**:
A diabetes research team wants to analyze 10,000 clinical notes to identify risk factors for complications.

**Without de-identification**: Cannot share data (HIPAA violation)

**With de-identification**:
```
Original: "Patient John Smith (DOB: 1975-05-15, MRN: 12345678)
           visited St. Mary's Hospital on 2023-06-20..."

De-identified: "Patient [PERSON_1] (DOB: [DATE_1], MRN: [ID_1])
                visited [LOCATION_1] on [DATE_2]..."

Pseudonymized: "Patient Jane Doe (DOB: 1980-03-10, MRN: 87654321)
                visited General Hospital on 2023-07-15..."
```

Research can proceed while protecting patient privacy.

### Deployment Context

- **Platform**: Extends Clinical Care Tools Base Application
- **Users**: Researchers (de-identify datasets), Clinicians (preview de-identified notes), Admin (configure de-ID settings)
- **Data Source**: Clinical documents from base application
- **Integration**: CogStack-ModelServe `medcat_deid` model for PHI detection

---

## Goals

### Primary Goals

1. **Automated PHI Detection** (P0)
   - Detect PHI/PII using CogStack-ModelServe `medcat_deid` model
   - Classify entity types: Names, Dates, NHS Numbers, Addresses, Phone Numbers, Email, URLs
   - Show confidence scores for detected PHI
   - Manual review interface (add/remove PHI annotations)

2. **De-Identification Strategies** (P0)
   - **Redaction**: Replace PHI with `[ENTITY_TYPE]` (e.g., `[NAME]`, `[DATE]`)
   - **Safe Harbor**: Remove 18 HIPAA identifiers
   - **Masking**: Replace with asterisks (e.g., `John Smith` → `**** *****`)
   - **Generalization**: Replace with less specific value (e.g., `1975-05-15` → `1975`)
   - Preview mode: Show before/after side-by-side

3. **Pseudonymization** (P0)
   - Replace PHI with consistent fake values
   - Preserve relationships (same patient → same pseudonym across documents)
   - Realistic fake data (names from name database, dates with same day-of-week)
   - Hash-based consistency (deterministic pseudonyms for same patient)

4. **De-Identified Dataset Export** (P0)
   - Export de-identified corpus (all documents for patient cohort)
   - Export formats: Plain text, JSON, FHIR R4
   - Include metadata (de-ID method, date, user)
   - Audit trail (track who exported what)

5. **Comprehensive Audit Logging** (P0)
   - Log all de-identification jobs (user, documents, strategy)
   - Log PHI detections (what PHI was found, was it redacted?)
   - Log manual reviews (did user add/remove PHI annotations?)
   - Log exports (who exported de-identified data?)
   - Query audit logs for compliance

### Secondary Goals

6. **Quality Assurance** (P1)
   - De-identification quality metrics (precision, recall, F1 for PHI detection)
   - Manual review workflow (assign documents to reviewers)
   - Inter-reviewer agreement (kappa scores)
   - Re-identification risk assessment (statistical disclosure control)

7. **Context Preservation** (P1)
   - Maintain clinical meaning during de-identification
   - Preserve temporal relationships (dates shifted by same offset)
   - Preserve spatial relationships (all locations in same city masked together)
   - Readability score (ensure de-identified text readable)

8. **Batch Processing** (P1)
   - Queue de-identification jobs for large datasets
   - Background processing (don't block UI)
   - Progress tracking (show % complete)
   - Resume failed jobs (automatic retry)

---

## Non-Goals

1. **Perfect PHI Detection** - Acknowledge 95-98% recall (some PHI may remain)
2. **Re-Identification Prevention Guarantee** - Provide tools, not certification (Expert Determination requires statistician)
3. **External Data Sources** - De-identify documents in base application only
4. **Real-Time De-Identification** - Batch processing only (no streaming)
5. **Multi-Language Support** - English only
6. **Audio/Video De-Identification** - Text documents only
7. **Blockchain Provenance** - Standard audit logging (no distributed ledger)

---

## User Stories

### Researcher User Stories

#### US-R1: De-Identify Patient Cohort
**As a** researcher
**I want to** de-identify all documents for a patient cohort
**So that** I can share data for multi-site research

**Acceptance Criteria**:
- [ ] Select patient cohort (from Patient Search results)
- [ ] Choose de-identification strategy (Redaction, Safe Harbor, Pseudonymization)
- [ ] Preview de-identified sample (5 random documents)
- [ ] Start de-identification job (batch processing)
- [ ] Monitor progress (% complete, estimated time remaining)
- [ ] Download de-identified corpus (ZIP file with all documents)
- [ ] Audit log entry created

---

#### US-R2: Manual Review of PHI Detection
**As a** researcher
**I want to** review PHI detected by automated system
**So that** I can correct false positives/negatives

**Acceptance Criteria**:
- [ ] View document with PHI highlighted
- [ ] See confidence score for each PHI annotation
- [ ] Add missing PHI (false negative: system missed it)
- [ ] Remove incorrect PHI (false positive: system flagged non-PHI)
- [ ] Save corrections → apply to de-identification
- [ ] Audit log tracks manual corrections

---

#### US-R3: Export De-Identified Dataset
**As a** researcher
**I want to** export de-identified dataset in multiple formats
**So that** I can use it for research

**Acceptance Criteria**:
- [ ] Export formats:
  - Plain text (one file per document)
  - JSON (structured format with metadata)
  - FHIR R4 (DocumentReference bundle)
- [ ] Include de-identification metadata:
  - Method used (Redaction, Safe Harbor, Pseudonymization)
  - PHI types detected and removed
  - Export date and user
  - Re-identification risk assessment (if available)
- [ ] Audit log entry created for export

---

### Clinician User Stories

#### US-C1: Preview De-Identified Note
**As a** clinician
**I want to** preview what a de-identified clinical note looks like
**So that** I can ensure clinical meaning is preserved

**Acceptance Criteria**:
- [ ] Select document → "Preview De-Identification"
- [ ] Choose strategy (Redaction, Safe Harbor, Pseudonymization)
- [ ] Side-by-side view:
  - Left: Original text
  - Right: De-identified text
- [ ] PHI highlighted in both views (color-coded by type)
- [ ] Toggle between strategies (see different methods)

---

### Admin User Stories

#### US-A1: Configure De-Identification Settings
**As an** admin
**I want to** configure de-identification strategies and PHI types
**So that** de-identification meets organizational policies

**Acceptance Criteria**:
- [ ] Admin panel for de-ID configuration:
  - Enable/disable strategies (Redaction, Safe Harbor, Pseudonymization)
  - Configure PHI types to detect (Names, Dates, IDs, Locations, etc.)
  - Set confidence threshold (only remove PHI with confidence >X%)
  - Configure pseudonymization (fake name database, date shift range)
- [ ] Settings saved to database
- [ ] Settings apply to all de-identification jobs

---

#### US-A2: View De-Identification Audit Logs
**As an** admin
**I want to** view audit logs for de-identification jobs
**So that** I can ensure compliance

**Acceptance Criteria**:
- [ ] Admin panel shows de-ID audit logs:
  - User who ran job
  - Documents de-identified
  - Strategy used
  - PHI types detected
  - Manual reviews performed
  - Exports performed
  - Timestamp
- [ ] Filter logs by user, date range, strategy
- [ ] Export logs to CSV for compliance reporting

---

## Requirements

### Functional Requirements

#### FR1: PHI Detection
- **FR1.1**: Detect PHI using CogStack-ModelServe `medcat_deid` model
- **FR1.2**: Classify PHI types:
  - Names (patients, doctors, family members)
  - Dates (DOB, admission dates, discharge dates)
  - NHS Numbers / Medical Record Numbers
  - Addresses (street, city, postal code)
  - Phone Numbers
  - Email Addresses
  - URLs
  - Other identifiers (license plates, device IDs)
- **FR1.3**: Show confidence score for each PHI annotation (0.0 to 1.0)
- **FR1.4**: Manual review interface (add/remove PHI annotations)
- **FR1.5**: Track false positives/negatives (quality metrics)

#### FR2: De-Identification Strategies
- **FR2.1**: **Redaction** - Replace PHI with `[ENTITY_TYPE]` tags
  - Example: `John Smith` → `[NAME]`
  - Configurable tag format (`[NAME]`, `[NAME_1]`, `***`)
- **FR2.2**: **Safe Harbor** (HIPAA) - Remove 18 identifiers:
  1. Names
  2. Geographic subdivisions smaller than state
  3. Dates (except year)
  4. Telephone numbers
  5. Fax numbers
  6. Email addresses
  7. Social Security numbers
  8. Medical record numbers
  9. Health plan beneficiary numbers
  10. Account numbers
  11. Certificate/license numbers
  12. Vehicle identifiers
  13. Device identifiers
  14. URLs
  15. IP addresses
  16. Biometric identifiers
  17. Full face photos
  18. Any other unique identifying number
- **FR2.3**: **Masking** - Replace with asterisks
  - Example: `John Smith` → `**** *****`
- **FR2.4**: **Generalization** - Replace with less specific value
  - Dates: `1975-05-15` → `1975` (year only)
  - Ages: `47 years old` → `40-50 years old` (age range)
  - Locations: `123 Main St, London` → `London` (city only)
- **FR2.5**: Preview mode (before/after side-by-side)

#### FR3: Pseudonymization
- **FR3.1**: Replace names with realistic fake names
  - Use name database (first names, last names)
  - Gender-matched (John → Michael, not John → Sarah)
  - Ethnicity-matched if detectable
- **FR3.2**: Replace dates with shifted dates
  - Shift by random offset (±180 days)
  - Same offset for all dates in same document
  - Preserve day-of-week (Tuesday → Tuesday)
- **FR3.3**: Replace IDs with fake IDs
  - NHS numbers: generate valid checksum
  - MRNs: generate unique fake IDs
- **FR3.4**: Replace locations with fake locations
  - Addresses: generate realistic addresses in same region
  - Hospitals: replace with fake hospital names
- **FR3.5**: Hash-based consistency
  - Same patient → same pseudonym across documents
  - Use HMAC-SHA256(patient_id, secret_key) for determinism

#### FR4: Batch Processing
- **FR4.1**: Queue de-identification jobs for large datasets
- **FR4.2**: Background processing (Celery task queue)
- **FR4.3**: Progress tracking (show % complete, documents processed, time remaining)
- **FR4.4**: Resume failed jobs (automatic retry on transient errors)
- **FR4.5**: Cancel jobs (user can stop long-running jobs)

#### FR5: Export De-Identified Data
- **FR5.1**: Export to plain text (one .txt file per document in ZIP)
- **FR5.2**: Export to JSON:
  ```json
  {
    "document_id": "doc-123",
    "original_title": "Clinical Note",
    "de_identified_content": "Patient [NAME] visited on [DATE]...",
    "phi_detected": [
      {"type": "NAME", "original": "John Smith", "replacement": "[NAME]"}
    ],
    "metadata": {
      "strategy": "Redaction",
      "phi_types_removed": ["NAME", "DATE", "ID"],
      "de_identified_at": "2023-11-17T10:30:00Z",
      "de_identified_by": "researcher-1"
    }
  }
  ```
- **FR5.3**: Export to FHIR R4 (DocumentReference bundle)
- **FR5.4**: Include de-identification metadata in export
- **FR5.5**: Audit log entry for all exports

#### FR6: Quality Assurance
- **FR6.1**: Calculate PHI detection metrics (precision, recall, F1)
- **FR6.2**: Manual review workflow (assign documents to reviewers)
- **FR6.3**: Inter-reviewer agreement (Cohen's kappa)
- **FR6.4**: Re-identification risk assessment (k-anonymity, l-diversity)
- **FR6.5**: Quality report export (CSV with metrics)

#### FR7: Audit Logging
- **FR7.1**: Log de-identification jobs (user, documents, strategy, timestamp)
- **FR7.2**: Log PHI detections (type, location, confidence)
- **FR7.3**: Log manual reviews (added/removed PHI annotations)
- **FR7.4**: Log exports (format, documents, user, timestamp)
- **FR7.5**: Query audit logs (filter by user, date range, strategy)

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: PHI detection: <500ms per document (<1000 words)
- **NFR1.2**: De-identification: <1 second per document
- **NFR1.3**: Batch processing: 100 documents per minute
- **NFR1.4**: Large datasets: Support de-identifying 10,000+ documents
- **NFR1.5**: Export: <5 seconds for <100 documents

#### NFR2: Accuracy
- **NFR2.1**: PHI detection recall: ≥95% (find 95% of PHI)
- **NFR2.2**: PHI detection precision: ≥90% (90% of detections are true PHI)
- **NFR2.3**: Pseudonymization consistency: 100% (same entity → same pseudonym)
- **NFR2.4**: Context preservation: 90% readability score (de-identified text still readable)

#### NFR3: Security
- **NFR3.1**: All de-identification requires authentication
- **NFR3.2**: Role-based access: Only Researchers can de-identify
- **NFR3.3**: Audit logging for all de-identification jobs
- **NFR3.4**: Pseudonymization secret key stored securely (environment variable, never logged)
- **NFR3.5**: De-identified exports watermarked ("De-Identified Data - Not for Clinical Use")

#### NFR4: Reliability
- **NFR4.1**: 99% success rate for de-identification jobs
- **NFR4.2**: Automatic retry for transient failures (network errors)
- **NFR4.3**: Graceful handling of malformed documents
- **NFR4.4**: Error messages user-friendly (no stack traces)

#### NFR5: Maintainability
- **NFR5.1**: Modular codebase (PHI detection, de-ID strategies, pseudonymization as separate modules)
- **NFR5.2**: Unit test coverage ≥80%
- **NFR5.3**: Integration test coverage ≥70%
- **NFR5.4**: Documentation for each de-ID strategy

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  DeIdentificationView.vue                             │  │
│  │  - Select documents/cohort                            │  │
│  │  - Choose de-ID strategy                              │  │
│  │  - Preview de-identified sample                       │  │
│  │  - Start batch job                                    │  │
│  │  - Monitor progress                                   │  │
│  │  - Download export                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    REST API (FastAPI)
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  De-Identification Service                            │  │
│  │  - POST /api/v1/deid/jobs                             │  │
│  │  - GET /api/v1/deid/jobs/{job_id}                     │  │
│  │  - GET /api/v1/deid/preview                           │  │
│  │  - POST /api/v1/deid/export                           │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  De-ID Strategies                                     │  │
│  │  - Redaction                                          │  │
│  │  - Safe Harbor                                        │  │
│  │  - Masking                                            │  │
│  │  - Generalization                                     │  │
│  │  - Pseudonymization                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    CogStack-ModelServe
┌─────────────────────────────────────────────────────────────┐
│              CogStack-ModelServe (port 8001)                │
│  - medcat_deid model (PHI/PII detection)                    │
│  - Classify: Names, Dates, IDs, Locations, etc.            │
│  - Confidence scoring                                       │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    Task Queue (Celery + Redis)
┌─────────────────────────────────────────────────────────────┐
│                  Celery Workers (Background Processing)     │
│  - De-identification batch jobs                             │
│  - Progress tracking                                        │
│  - Export generation                                        │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Backend Services

**DeIdentificationService** (`app/services/deid_service.py`)
```python
class DeIdentificationService:
    """De-identification service orchestrator"""

    async def create_deid_job(
        self,
        document_ids: List[str],
        strategy: DeIDStrategy,
        user: User
    ) -> DeIDJob:
        """Create de-identification batch job"""
        # 1. Validate documents exist
        # 2. Create job record in database
        # 3. Queue Celery task for background processing
        # 4. Audit log job creation
        # 5. Return DeIDJob model

    async def get_job_status(
        self,
        job_id: str
    ) -> DeIDJobStatus:
        """Get de-identification job progress"""
        # 1. Query job from database
        # 2. Return status (queued, processing, completed, failed)

    async def preview_deidentification(
        self,
        document_id: str,
        strategy: DeIDStrategy
    ) -> DeIDPreview:
        """Preview de-identified document"""
        # 1. Get document from database
        # 2. Detect PHI using CogStack-ModelServe
        # 3. Apply de-ID strategy
        # 4. Return before/after preview

    async def export_deid_corpus(
        self,
        job_id: str,
        format: str,  # "text", "json", "fhir"
        user: User
    ) -> bytes:
        """Export de-identified corpus"""
        # 1. Get de-identified documents from job
        # 2. Format as text/JSON/FHIR
        # 3. Create ZIP file
        # 4. Audit log export
        # 5. Return ZIP bytes
```

**PHIDetectionService** (`app/services/phi_detection_service.py`)
```python
class PHIDetectionService:
    """PHI detection using CogStack-ModelServe"""

    async def detect_phi(
        self,
        text: str
    ) -> List[PHIAnnotation]:
        """Detect PHI in text"""
        # 1. Call CogStack-ModelServe medcat_deid model
        # 2. Parse entities (Names, Dates, IDs, etc.)
        # 3. Return PHIAnnotation list

    async def classify_phi_type(
        self,
        entity: Dict[str, Any]
    ) -> PHIType:
        """Classify PHI type"""
        # Map MedCAT entity types to PHI types
        # (PERSON → NAME, DATE → DATE, ID → ID, etc.)
```

**De-ID Strategy Implementations**

```python
class RedactionStrategy:
    """Replace PHI with [ENTITY_TYPE] tags"""
    def apply(self, text: str, phi_annotations: List[PHIAnnotation]) -> str:
        # Sort annotations by start position (reverse order)
        # Replace each PHI span with [TYPE] tag
        # Return modified text

class SafeHarborStrategy:
    """HIPAA Safe Harbor: Remove 18 identifiers"""
    IDENTIFIERS = [
        "NAME", "LOCATION", "DATE", "PHONE", "EMAIL",
        "SSN", "MRN", "ACCOUNT", "LICENSE", "VEHICLE",
        "DEVICE", "URL", "IP", "BIOMETRIC", "PHOTO", "OTHER"
    ]

    def apply(self, text: str, phi_annotations: List[PHIAnnotation]) -> str:
        # Filter annotations: only keep types in IDENTIFIERS
        # Replace with [TYPE] tags
        # Generalize dates (keep year only)

class PseudonymizationStrategy:
    """Replace PHI with consistent fake values"""
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.name_database = NameDatabase()  # Fake names
        self.location_database = LocationDatabase()  # Fake locations

    def apply(self, text: str, phi_annotations: List[PHIAnnotation]) -> str:
        # For each PHI annotation:
        #   - Generate pseudonym (hash-based for consistency)
        #   - Replace original with pseudonym
        # Return modified text

    def generate_pseudonym(self, original: str, phi_type: PHIType) -> str:
        # Create hash: HMAC-SHA256(original, secret_key)
        # Use hash to select fake value from database
        # (same original → same hash → same fake value)
```

#### Database Models

**DeIDJob** (Batch Job Tracking)
```python
class DeIDJob(BaseModel):
    id: str
    user_id: str
    document_ids: List[str]
    strategy: DeIDStrategy
    status: DeIDJobStatus  # "queued", "processing", "completed", "failed"
    progress: DeIDJobProgress
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class DeIDJobProgress(BaseModel):
    total_documents: int
    processed_documents: int
    failed_documents: int
    percent_complete: float
    estimated_time_remaining_seconds: Optional[int]

class DeIDJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
```

**PHIAnnotation** (Detected PHI)
```python
class PHIAnnotation(BaseModel):
    phi_type: PHIType  # "NAME", "DATE", "ID", "LOCATION", etc.
    start: int  # Character offset in text
    end: int
    text: str  # Original PHI text
    confidence: float  # 0.0 to 1.0
    replacement: Optional[str]  # Replacement value (for pseudonymization)

class PHIType(str, Enum):
    NAME = "NAME"
    DATE = "DATE"
    ID = "ID"
    LOCATION = "LOCATION"
    PHONE = "PHONE"
    EMAIL = "EMAIL"
    URL = "URL"
    OTHER = "OTHER"
```

### API Endpoints

#### POST `/api/v1/deid/jobs`
Create de-identification batch job.

**Request**:
```json
{
  "document_ids": ["doc-1", "doc-2", "doc-3"],
  "strategy": "pseudonymization",  // "redaction", "safe_harbor", "masking", "pseudonymization"
  "options": {
    "confidence_threshold": 0.8,  // Only remove PHI with confidence ≥0.8
    "pseudonym_secret_key": "my-secret-key-123"  // For pseudonymization
  }
}
```

**Response**:
```json
{
  "job_id": "job-789",
  "status": "queued",
  "progress": {
    "total_documents": 3,
    "processed_documents": 0,
    "failed_documents": 0,
    "percent_complete": 0.0
  },
  "created_at": "2023-11-17T10:30:00Z"
}
```

#### GET `/api/v1/deid/jobs/{job_id}`
Get job status and progress.

**Response**:
```json
{
  "job_id": "job-789",
  "status": "processing",
  "progress": {
    "total_documents": 3,
    "processed_documents": 2,
    "failed_documents": 0,
    "percent_complete": 66.7,
    "estimated_time_remaining_seconds": 30
  },
  "started_at": "2023-11-17T10:31:00Z"
}
```

#### GET `/api/v1/deid/preview`
Preview de-identification for single document.

**Request**: `?document_id=doc-123&strategy=redaction`

**Response**:
```json
{
  "document_id": "doc-123",
  "original_text": "Patient John Smith (DOB: 1975-05-15, MRN: 12345678) visited St. Mary's Hospital...",
  "de_identified_text": "Patient [NAME] (DOB: [DATE], MRN: [ID]) visited [LOCATION]...",
  "phi_detected": [
    {"type": "NAME", "start": 8, "end": 18, "text": "John Smith", "confidence": 0.95},
    {"type": "DATE", "start": 25, "end": 35, "text": "1975-05-15", "confidence": 0.98},
    {"type": "ID", "start": 42, "end": 50, "text": "12345678", "confidence": 0.92},
    {"type": "LOCATION", "start": 60, "end": 78, "text": "St. Mary's Hospital", "confidence": 0.89}
  ]
}
```

#### POST `/api/v1/deid/export`
Export de-identified corpus.

**Request**:
```json
{
  "job_id": "job-789",
  "format": "json",  // "text", "json", "fhir"
  "include_metadata": true
}
```

**Response**:
```json
{
  "export_id": "export-101",
  "download_url": "/api/v1/deid/exports/export-101/download",
  "expires_at": "2023-11-17T12:00:00Z",
  "audit_log_id": "audit-202"
}
```

---

## Database Schema

### New Tables

#### `deid_jobs` (De-Identification Batch Jobs)
```sql
CREATE TABLE deid_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    document_ids UUID[] NOT NULL,  -- Array of document IDs
    strategy VARCHAR(50) NOT NULL,  -- "redaction", "safe_harbor", "masking", "pseudonymization"
    options JSONB,  -- Strategy-specific options
    status VARCHAR(20) NOT NULL,  -- "queued", "processing", "completed", "failed"
    total_documents INTEGER NOT NULL,
    processed_documents INTEGER DEFAULT 0,
    failed_documents INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_deid_jobs_user ON deid_jobs(user_id);
CREATE INDEX idx_deid_jobs_status ON deid_jobs(status);
CREATE INDEX idx_deid_jobs_created ON deid_jobs(created_at);
```

#### `deid_documents` (De-Identified Documents)
```sql
CREATE TABLE deid_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES deid_jobs(id) ON DELETE CASCADE,
    original_document_id UUID NOT NULL REFERENCES documents(id),
    de_identified_content TEXT NOT NULL,
    phi_detected JSONB NOT NULL,  -- Array of PHIAnnotation objects
    manual_review_status VARCHAR(20) DEFAULT 'pending',  -- "pending", "reviewed", "approved"
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_deid_documents_job ON deid_documents(job_id);
CREATE INDEX idx_deid_documents_original ON deid_documents(original_document_id);
CREATE INDEX idx_deid_documents_review_status ON deid_documents(manual_review_status);
```

#### `deid_exports` (Export Tracking)
```sql
CREATE TABLE deid_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES deid_jobs(id),
    user_id UUID NOT NULL REFERENCES users(id),
    format VARCHAR(10) NOT NULL,  -- "text", "json", "fhir"
    file_path VARCHAR(500),
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_deid_exports_job ON deid_exports(job_id);
CREATE INDEX idx_deid_exports_user ON deid_exports(user_id);
```

---

## De-Identification Strategies

### Strategy Comparison

| Strategy | Use Case | Privacy Level | Context Preservation | Reversible |
|----------|----------|---------------|---------------------|------------|
| **Redaction** | Public datasets, publications | High | Medium | No |
| **Safe Harbor** | HIPAA compliance | High | Low-Medium | No |
| **Masking** | Quick anonymization | Medium | Low | No |
| **Generalization** | Statistical analysis | Medium-High | Medium-High | No |
| **Pseudonymization** | Research with longitudinal data | Medium-High | High | Yes (with key) |

### Implementation Examples

#### Redaction
```
Original: "Patient John Smith (DOB: 1975-05-15, MRN: 12345678) visited on 2023-06-20."

Redacted: "Patient [NAME] (DOB: [DATE], MRN: [ID]) visited on [DATE]."
```

#### Safe Harbor (HIPAA)
```
Original: "John Smith, 47 yo male, DOB 1975-05-15, lives at 123 Main St, London SW1A 1AA."

Safe Harbor: "[REDACTED], age range 40-50, DOB 1975, lives in London."
```
*(Name removed, age generalized, DOB year only, address city only)*

#### Pseudonymization
```
Original: "Patient John Smith (DOB: 1975-05-15, MRN: 12345678) visited on 2023-06-20."

Pseudonymized: "Patient Michael Johnson (DOB: 1980-03-10, MRN: 87654321) visited on 2023-07-15."
```
*(Same patient in other documents → same pseudonym)*

---

## Pseudonymization Algorithm

### Hash-Based Consistency

```python
def generate_pseudonym_name(original_name: str, secret_key: str) -> str:
    """Generate consistent fake name"""
    # Step 1: Create hash
    hash_value = hmac.new(
        secret_key.encode(),
        original_name.encode(),
        hashlib.sha256
    ).hexdigest()

    # Step 2: Use hash to select fake name from database
    hash_int = int(hash_value[:8], 16)  # First 8 hex chars → integer
    fake_name = FAKE_NAMES_DATABASE[hash_int % len(FAKE_NAMES_DATABASE)]

    return fake_name

# Example:
# generate_pseudonym_name("John Smith", "my-secret") → "Michael Johnson" (always)
# generate_pseudonym_name("Jane Doe", "my-secret") → "Sarah Williams" (always)
```

### Date Shifting

```python
def generate_pseudonym_date(original_date: datetime, patient_id: str, secret_key: str) -> datetime:
    """Shift date by consistent offset"""
    # Step 1: Generate patient-specific offset (±180 days)
    hash_value = hmac.new(
        secret_key.encode(),
        patient_id.encode(),
        hashlib.sha256
    ).hexdigest()
    hash_int = int(hash_value[:8], 16)
    offset_days = (hash_int % 361) - 180  # -180 to +180 days

    # Step 2: Shift date
    shifted_date = original_date + timedelta(days=offset_days)

    return shifted_date

# Example (patient-123, offset = +45 days):
# 1975-05-15 → 1975-06-29
# 2023-06-20 → 2023-08-04
# (All dates for patient-123 shifted by +45 days)
```

---

## Integration Points

### CogStack-ModelServe Integration
- **Model**: `medcat_deid` (De-identification model)
- **Endpoint**: `POST http://cogstack-modelserve:8000/api/process`
- **Input**: Document text
- **Output**: PHI entities with types and confidence scores

### Celery Task Queue (Redis)
- **Purpose**: Background processing for batch de-identification jobs
- **Tasks**:
  - `deid_process_batch_job` - Process all documents in job
  - `deid_export_corpus` - Generate export file (ZIP)

### PostgreSQL Integration
- **Tables**: `deid_jobs`, `deid_documents`, `deid_exports`, `audit_logs`

---

## Performance Requirements

### Load Time Targets
- **PHI detection**: <500ms per document (<1000 words)
- **De-identification**: <1 second per document
- **Batch processing**: 100 documents per minute
- **Preview generation**: <2 seconds
- **Export generation**: <5 seconds for <100 documents

### Scalability Targets
- **Total documents**: Support de-identifying 10,000+ documents per job
- **Concurrent jobs**: 5 jobs running simultaneously
- **Celery workers**: 4 workers processing de-ID tasks

---

## Constraints

### Technical Constraints
1. **Single workstation deployment** - No distributed Celery cluster
2. **English only** - PHI detection trained on English text
3. **Text documents only** - No images, audio, video
4. **95-98% recall** - Some PHI may remain (manual review recommended)
5. **Batch processing only** - No real-time de-identification

### Regulatory Constraints
1. **HIPAA compliance** - Safe Harbor method meets HIPAA standards
2. **GDPR pseudonymization** - Pseudonymization meets GDPR Article 4(5)
3. **Audit logging** - All de-ID jobs logged for compliance
4. **No re-identification guarantee** - Expert Determination requires statistician certification

### Resource Constraints
1. **RAM**: Celery workers must run in <2GB RAM each
2. **Disk**: De-identified documents stored for 90 days (automatic cleanup)
3. **CPU**: De-ID processing must not block other services

---

## Acceptance Criteria

### Functional Acceptance

- [ ] **PHI Detection**:
  - [ ] Detect Names, Dates, IDs, Locations, Phone, Email, URLs
  - [ ] Show confidence scores
  - [ ] Manual review interface (add/remove PHI)
  - [ ] Recall ≥95%, Precision ≥90%

- [ ] **De-Identification Strategies**:
  - [ ] Redaction (replace with [TYPE] tags)
  - [ ] Safe Harbor (remove 18 HIPAA identifiers)
  - [ ] Masking (replace with asterisks)
  - [ ] Generalization (less specific values)
  - [ ] Pseudonymization (consistent fake values)
  - [ ] Preview mode (before/after side-by-side)

- [ ] **Batch Processing**:
  - [ ] Queue jobs for large datasets
  - [ ] Background processing (Celery)
  - [ ] Progress tracking (% complete, time remaining)
  - [ ] Resume failed jobs (automatic retry)

- [ ] **Export**:
  - [ ] Export to text, JSON, FHIR R4
  - [ ] Include de-ID metadata
  - [ ] Audit log entry created

- [ ] **Quality Assurance**:
  - [ ] Calculate precision, recall, F1
  - [ ] Manual review workflow
  - [ ] Inter-reviewer agreement

- [ ] **Audit Logging**:
  - [ ] Log jobs, PHI detections, manual reviews, exports
  - [ ] Admin can query logs

### Performance Acceptance

- [ ] PHI detection <500ms per document
- [ ] De-identification <1 second per document
- [ ] Batch processing 100 documents per minute
- [ ] Recall ≥95%, Precision ≥90%

### Security Acceptance

- [ ] Authentication required for de-ID
- [ ] Only Researchers can create de-ID jobs
- [ ] Audit logging for all jobs
- [ ] Pseudonymization key stored securely
- [ ] Exports watermarked

### Usability Acceptance

- [ ] Intuitive de-ID interface
- [ ] Preview mode easy to use
- [ ] Progress tracking visible
- [ ] WCAG 2.1 AA compliance

### Testing Acceptance

- [ ] Unit test coverage ≥80%
- [ ] Integration test coverage ≥70%
- [ ] E2E test for de-ID workflow
- [ ] Performance tests verify targets

---

## Alignment with Constitution

### Principle 2: Privacy by Design
- **De-identification**: Enable research while protecting patient privacy
- **Audit logging**: Track all de-ID jobs for compliance
- **Export watermarks**: Prevent misuse of de-identified data

### Principle 3: Evidence-Based Development
- **CogStack-ModelServe**: Production-tested PHI detection model
- **HIPAA Safe Harbor**: Regulatory-compliant method
- **Pseudonymization**: Established technique in research

### Principle 5: Open Standards and Interoperability
- **FHIR R4 export**: Standard format for healthcare data
- **JSON export**: Machine-readable for research

### Principle 6: Transparency and Explainability
- **Confidence scores**: Show reliability of PHI detection
- **Preview mode**: Show users exactly what will be removed
- **Audit trails**: Full provenance of de-identified data

---

## Testing Strategy

### Unit Tests (60%)

```python
@pytest.mark.asyncio
async def test_detect_phi(phi_detection_service):
    # Arrange
    text = "Patient John Smith (DOB: 1975-05-15) visited on 2023-06-20."

    # Act
    phi_annotations = await phi_detection_service.detect_phi(text)

    # Assert
    assert len(phi_annotations) == 3  # Name, DOB, visit date
    assert phi_annotations[0].phi_type == PHIType.NAME
    assert phi_annotations[0].text == "John Smith"
    assert phi_annotations[1].phi_type == PHIType.DATE

@pytest.mark.asyncio
async def test_redaction_strategy():
    # Arrange
    text = "Patient John Smith visited on 2023-06-20."
    phi = [PHIAnnotation(phi_type=PHIType.NAME, start=8, end=18, text="John Smith")]
    strategy = RedactionStrategy()

    # Act
    result = strategy.apply(text, phi)

    # Assert
    assert result == "Patient [NAME] visited on 2023-06-20."

@pytest.mark.asyncio
async def test_pseudonymization_consistency():
    # Arrange
    strategy = PseudonymizationStrategy(secret_key="test-key")

    # Act
    pseudonym1 = strategy.generate_pseudonym("John Smith", PHIType.NAME)
    pseudonym2 = strategy.generate_pseudonym("John Smith", PHIType.NAME)

    # Assert
    assert pseudonym1 == pseudonym2  # Consistency
```

### Integration Tests (30%)

```python
@pytest.mark.asyncio
async def test_create_deid_job_endpoint(async_client, auth_headers):
    # Act
    response = await async_client.post(
        "/api/v1/deid/jobs",
        json={
            "document_ids": ["doc-1", "doc-2"],
            "strategy": "redaction"
        },
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    assert data["progress"]["total_documents"] == 2
```

### E2E Tests (10%)

```typescript
test('de-identify patient cohort', async ({ page }) => {
  await page.goto('http://localhost:8080/deid')

  // Select documents
  await page.click('button:has-text("Select Cohort")')
  await page.fill('input[name="search"]', 'diabetes')
  await page.click('button:has-text("Search")')
  await page.click('button:has-text("Select All")')

  // Choose strategy
  await page.click('select[name="strategy"]')
  await page.click('option[value="pseudonymization"]')

  // Preview
  await page.click('button:has-text("Preview")')
  await page.waitForSelector('.preview-before')
  await page.waitForSelector('.preview-after')

  // Start job
  await page.click('button:has-text("De-Identify")')
  await page.waitForSelector('text=Job Created')

  // Monitor progress
  await page.waitForSelector('text=100% Complete', { timeout: 60000 })

  // Export
  await page.click('button:has-text("Export")')
  const downloadPromise = page.waitForEvent('download')
  await page.click('option[value="json"]')
  await page.click('button:has-text("Download")')
  const download = await downloadPromise
  expect(download.suggestedFilename()).toContain('.zip')
})
```

---

## Deployment Considerations

### Docker Compose Updates

```yaml
services:
  backend:
    environment:
      - DEID_ENABLED=true
      - DEID_SECRET_KEY=${DEID_SECRET_KEY}
      - CELERY_BROKER_URL=redis://redis:6379/0

  celery:
    image: clinical-care-tools-backend
    command: celery -A app.celery_app worker --loglevel=info --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DEID_SECRET_KEY=${DEID_SECRET_KEY}
    depends_on:
      - redis
      - postgres

  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
```

### Environment Variables

```bash
# De-Identification Configuration
DEID_ENABLED=true
DEID_SECRET_KEY=your-secret-key-for-pseudonymization
DEID_CONFIDENCE_THRESHOLD=0.8
DEID_EXPORT_DIR=/app/exports/deid
DEID_EXPORT_RETENTION_DAYS=90

# Celery Configuration
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKERS=4
```

---

## Open Questions

1. **Pseudonymization Secret Key Management**:
   - Q: How to manage secret key securely?
   - A: [To be decided] - Propose: environment variable (not in code), rotate annually

2. **De-Identification Quality Threshold**:
   - Q: What is acceptable recall/precision?
   - A: [To be decided] - Propose: ≥95% recall, ≥90% precision (with manual review for critical use cases)

3. **Re-Identification Risk Assessment**:
   - Q: Should we implement k-anonymity/l-diversity calculations?
   - A: [To be decided] - Propose: Phase 2 (requires statistical expertise)

4. **Export Retention Policy**:
   - Q: How long to keep de-identified exports?
   - A: [To be decided] - Propose: 90 days (configurable by admin)

5. **Manual Review Workflow**:
   - Q: Should manual review be mandatory or optional?
   - A: [To be decided] - Propose: optional (recommended for high-risk use cases)

---

**Status**: Ready for review and approval
**Next Steps**: Create Technical Plan for Sprint 4 (De-Identification) after specification approval
**Dependencies**: Base Application (MVP), CogStack-ModelServe `medcat_deid` model
**Estimated Effort**: 120 hours over 4 weeks
