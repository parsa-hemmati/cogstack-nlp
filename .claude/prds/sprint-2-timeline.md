# Specification: Timeline View Module (Sprint 2)

**Version**: 1.0.0
**Date**: 2025-11-17
**Status**: Draft
**Author**: AI Assistant (Claude Code)
**Reviewers**: [To be assigned]
**Sprint Duration**: 4 weeks (~120 hours)

**Version History**:
- **1.0.0** (2025-11-17): Initial specification for Timeline View Module

---

## Table of Contents

1. [Context](#context)
2. [Goals](#goals)
3. [Non-Goals](#non-goals)
4. [User Stories](#user-stories)
5. [Requirements](#requirements)
6. [Architecture](#architecture)
7. [Database Schema](#database-schema)
8. [UI/UX Design](#uiux-design)
9. [Integration Points](#integration-points)
10. [Performance Requirements](#performance-requirements)
11. [Constraints](#constraints)
12. [Acceptance Criteria](#acceptance-criteria)
13. [Alignment with Constitution](#alignment-with-constitution)
14. [Testing Strategy](#testing-strategy)
15. [Deployment Considerations](#deployment-considerations)
16. [Open Questions](#open-questions)

---

## Context

### Background

The **Timeline View Module** is the second module in the Clinical Care Tools platform, building on the base application (MVP) and Patient Search module (Sprint 1).

**CogStack Product Alignment**: Enterprise-grade Search (visualization component)

### The Problem

Clinicians need to:
- **Visualize patient history chronologically** (documents, events, conditions)
- **Identify temporal patterns** (when did symptoms start? progression over time?)
- **Understand disease trajectories** (onset → diagnosis → treatment → outcome)
- **Discover relationships** between events (medication changes before symptom onset)
- **Export clinical summaries** for referrals, discharge planning, audits

**Current Gap**: Patient Search returns results but doesn't show temporal relationships or disease progression.

### Why Timeline View Matters

**Clinical Value**:
- Faster clinical decision-making (see patient history at a glance)
- Pattern recognition (identify trends: worsening symptoms, medication adherence)
- Handover quality (comprehensive timeline for covering clinicians)
- Research insights (cohort phenotyping, outcome tracking)

**Example Use Case**:
A patient presents with chest pain. The clinician opens Timeline View and sees:
- 2023-01: First mention of "hypertension" (diagnosis)
- 2023-03: Started "amlodipine" (treatment)
- 2023-06: Noted "ankle edema" (side effect)
- 2023-08: Changed to "lisinopril" (medication switch)
- 2023-11: "Chest pain" mentioned (current presentation)

**Insight**: Chest pain might be related to recent medication change (lisinopril-induced cough mistaken for cardiac pain).

### Deployment Context

- **Platform**: Extends Clinical Care Tools Base Application (MVP)
- **Users**: Clinicians (view timelines), Admin (configure timeline settings)
- **Data Source**: Documents and annotations from base application
- **Integration**: CogStack-ModelServe for concept extraction, Elasticsearch for temporal queries

---

## Goals

### Primary Goals

1. **Chronological Document Timeline** (P0)
   - Display all patient documents in chronological order
   - Visual timeline with date axis (horizontal or vertical)
   - Filter by document type (notes, reports, letters, lab results)
   - Zoom/pan for long patient histories (10+ years)
   - Click document to view full text with annotations

2. **Clinical Concept Timeline** (P0)
   - Extract key clinical concepts (conditions, medications, procedures)
   - Display as event markers on timeline
   - Color-coded by concept type (red=condition, blue=medication, green=procedure)
   - Meta-annotation filtering (Negation, Temporality, Experiencer)
   - Hover to see context (sentence where concept was mentioned)

3. **Temporal Pattern Detection** (P0)
   - Identify concept first mention vs recurring mentions
   - Show concept frequency over time (bar chart overlay)
   - Highlight temporal relationships (medication start → symptom onset)
   - Annotation confidence scores (visual indicator: high/medium/low)

4. **Export Capabilities** (P0)
   - Export timeline to PDF (for referrals, discharge summaries)
   - Export to FHIR R4 (Composition resource with embedded Observations/Conditions)
   - Export to JSON (for research datasets)
   - Include provenance (which documents concepts came from)

5. **Comprehensive Audit Logging** (P0)
   - Log all timeline views (WHO viewed WHICH patient timeline WHEN)
   - Log exports (PDF, FHIR, JSON) - clinical governance requirement
   - Log filter changes (what concepts were searched)
   - Query audit logs for compliance reporting

### Secondary Goals

6. **Interactive Filters** (P1)
   - Filter by concept type (conditions, medications, procedures)
   - Filter by date range (last 3 months, last year, custom)
   - Filter by meta-annotations (only affirmed, only patient, only current)
   - Filter by document type (clinical notes, discharge summaries, lab reports)
   - Save filter presets (e.g., "Diabetes Management View")

7. **Concept Grouping** (P1)
   - Group related concepts (e.g., "Type 2 Diabetes", "T2DM", "Diabetes Mellitus Type 2")
   - Use SNOMED-CT hierarchies for grouping
   - Collapse/expand concept groups
   - Show all variations of same concept

8. **Collaborative Annotations** (P1)
   - Clinicians can add manual annotations to timeline (important events not auto-detected)
   - Mark key milestones (diagnosis date, surgery date, discharge date)
   - Share annotations with project team
   - Audit trail for manual annotations

---

## Non-Goals

1. **Real-Time Updates** - No WebSocket live updates (future consideration)
2. **Multi-Patient Comparison** - Single patient timeline only (cohort comparison in Sprint 8)
3. **Predictive Analytics** - No forecasting/predictions (future consideration)
4. **Mobile Optimization** - Desktop browser only (consistent with base app)
5. **3D Visualization** - 2D timeline sufficient for clinical use
6. **External Data Integration** - Uses only documents in base application (no HL7/FHIR import yet)
7. **Natural Language Queries** - Structured filters only (no "show me when patient had chest pain")

---

## User Stories

### Clinician User Stories

#### US-C1: View Patient Timeline
**As a** clinician
**I want to** open a patient's timeline view
**So that** I can see their clinical history chronologically

**Acceptance Criteria**:
- [ ] Select patient from Patient Search results → "Open Timeline" button
- [ ] Timeline loads in <2 seconds for patients with <100 documents
- [ ] Documents displayed chronologically (oldest to newest OR newest to oldest toggle)
- [ ] Visual timeline with date axis (month/year granularity)
- [ ] Scroll/zoom for long histories (10+ years)

---

#### US-C2: Filter Timeline by Concept
**As a** clinician
**I want to** filter the timeline to show only specific concepts (e.g., "diabetes")
**So that** I can focus on relevant clinical history

**Acceptance Criteria**:
- [ ] Search box for concept filtering (autocomplete from SNOMED-CT)
- [ ] Multi-select concepts (show "diabetes" AND "hypertension")
- [ ] Timeline updates in <500ms after filter change
- [ ] Show count of documents matching filter
- [ ] Clear all filters button

---

#### US-C3: View Concept Details
**As a** clinician
**I want to** click on a concept marker to see details
**So that** I can understand the context

**Acceptance Criteria**:
- [ ] Click concept marker → popover with:
  - Concept name and SNOMED CUI
  - Sentence where concept was mentioned
  - Meta-annotations (Negation, Temporality, Experiencer, Certainty)
  - Confidence score (percentage)
  - Document name and date
- [ ] "View Document" link to open full text
- [ ] Close popover by clicking outside

---

#### US-C4: Export Timeline to PDF
**As a** clinician
**I want to** export the timeline to PDF
**So that** I can include it in referral letters or discharge summaries

**Acceptance Criteria**:
- [ ] "Export to PDF" button in toolbar
- [ ] PDF includes:
  - Patient demographics (name, MRN, DOB)
  - Timeline visualization (dates + concept markers)
  - Key concepts list (with dates of first mention)
  - Document list (chronological, with types)
  - Export metadata (exported by, export date)
- [ ] PDF generation <5 seconds
- [ ] Watermark: "Clinical Summary - Do Not Share Without Authorization"
- [ ] Audit log entry created for export

---

#### US-C5: Identify Temporal Patterns
**As a** clinician
**I want to** see when concepts first appeared vs recurring mentions
**So that** I can identify disease onset and progression

**Acceptance Criteria**:
- [ ] Concept markers differentiated: first mention (large marker) vs recurring (small marker)
- [ ] Concept frequency chart (bar chart showing mentions per month/year)
- [ ] Hover on bar → tooltip showing count and documents
- [ ] Toggle frequency chart on/off

---

### Admin User Stories

#### US-A1: Configure Timeline Settings
**As an** admin
**I want to** configure default timeline settings
**So that** clinicians have consistent experience

**Acceptance Criteria**:
- [ ] Admin panel for timeline configuration:
  - Default timeline orientation (horizontal/vertical)
  - Default date range (all time, last year, last 3 months)
  - Default concept types to show (conditions, medications, procedures)
  - Max documents to load (performance tuning)
- [ ] Settings saved to database
- [ ] Settings apply to all users

---

#### US-A2: View Timeline Usage Audit Logs
**As an** admin
**I want to** view audit logs for timeline access
**So that** I can ensure compliance with clinical governance

**Acceptance Criteria**:
- [ ] Admin panel shows timeline audit logs:
  - User who accessed timeline
  - Patient whose timeline was viewed
  - Timestamp
  - Filters applied
  - Exports performed (PDF, FHIR, JSON)
- [ ] Filter logs by user, patient, date range
- [ ] Export logs to CSV for reporting

---

## Requirements

### Functional Requirements

#### FR1: Timeline Rendering
- **FR1.1**: Display documents chronologically on visual timeline (date axis)
- **FR1.2**: Support horizontal OR vertical timeline orientation
- **FR1.3**: Zoom in/out for long patient histories (1 year → 10+ years)
- **FR1.4**: Pan/scroll smoothly (no lag for <100 documents)
- **FR1.5**: Click document → view full text with annotations highlighted

#### FR2: Concept Extraction and Display
- **FR2.1**: Extract clinical concepts using CogStack-ModelServe (SNOMED-CT)
- **FR2.2**: Display concepts as event markers on timeline
- **FR2.3**: Color-code by concept type:
  - Red: Conditions/Diagnoses
  - Blue: Medications
  - Green: Procedures
  - Yellow: Symptoms
  - Purple: Lab Results
- **FR2.4**: Filter concepts by meta-annotations:
  - Negation: Affirmed (exclude negated)
  - Temporality: Current, Recent, Historical
  - Experiencer: Patient (exclude family history)
  - Certainty: High, Medium, Low
- **FR2.5**: Show concept confidence score (percentage)

#### FR3: Filtering and Search
- **FR3.1**: Search concepts by name (autocomplete from SNOMED-CT)
- **FR3.2**: Multi-select concepts (AND logic: show documents with ALL selected concepts)
- **FR3.3**: Filter by date range (absolute dates OR relative: "last 3 months")
- **FR3.4**: Filter by document type (clinical notes, discharge summaries, lab reports, radiology)
- **FR3.5**: Save filter presets (named filters for reuse)

#### FR4: Temporal Pattern Analysis
- **FR4.1**: Identify first mention of concept (distinct visual marker)
- **FR4.2**: Show concept frequency over time (bar chart overlay)
- **FR4.3**: Highlight temporal relationships (e.g., medication start → symptom onset within 30 days)
- **FR4.4**: Concept timeline (show all mentions of specific concept with context)

#### FR5: Export Capabilities
- **FR5.1**: Export to PDF:
  - Patient demographics
  - Timeline visualization (SVG embedded in PDF)
  - Key concepts list (chronological with dates)
  - Document list (chronological with types)
  - Export metadata (user, timestamp)
  - Watermark for privacy protection
- **FR5.2**: Export to FHIR R4:
  - Composition resource (timeline summary)
  - Embedded Observations (concepts as structured data)
  - Embedded Conditions (diagnoses)
  - Provenance (source documents)
- **FR5.3**: Export to JSON:
  - Machine-readable format
  - Include all timeline data (documents, concepts, annotations)
  - Research dataset compatible

#### FR6: Audit Logging
- **FR6.1**: Log timeline access (user, patient, timestamp, IP address)
- **FR6.2**: Log filters applied (what concepts were searched)
- **FR6.3**: Log exports (format: PDF/FHIR/JSON, timestamp, user)
- **FR6.4**: Query audit logs (filter by user, patient, date range)
- **FR6.5**: Export audit logs to CSV for compliance reporting

### Non-Functional Requirements

#### NFR1: Performance
- **NFR1.1**: Timeline loads in <2 seconds for patients with <100 documents
- **NFR1.2**: Filter updates apply in <500ms
- **NFR1.3**: Zoom/pan operations at 60fps (smooth animations)
- **NFR1.4**: Concurrent users: 10 clinicians viewing timelines simultaneously
- **NFR1.5**: PDF export completes in <5 seconds

#### NFR2: Usability
- **NFR2.1**: Intuitive timeline visualization (minimal training required)
- **NFR2.2**: Keyboard shortcuts for common actions (zoom, filter, export)
- **NFR2.3**: Responsive design (works on 1920x1080 and 1366x768 displays)
- **NFR2.4**: Accessible (WCAG 2.1 AA compliance: keyboard navigation, screen readers, color contrast)

#### NFR3: Security
- **NFR3.1**: All timeline access requires authentication (session token)
- **NFR3.2**: Role-based access: Clinicians can view timelines for assigned patients only
- **NFR3.3**: Audit logging for all PHI access (timeline views, exports)
- **NFR3.4**: Exported PDFs watermarked to prevent unauthorized sharing
- **NFR3.5**: HTTPS only (TLS 1.3 for data in transit)

#### NFR4: Reliability
- **NFR4.1**: 99% uptime for timeline service
- **NFR4.2**: Graceful degradation if CogStack-ModelServe unavailable (show documents only, no concepts)
- **NFR4.3**: Error messages user-friendly (no stack traces)
- **NFR4.4**: Automatic retry for transient failures (network timeouts)

#### NFR5: Maintainability
- **NFR5.1**: Modular codebase (timeline component reusable in other modules)
- **NFR5.2**: Unit test coverage ≥80%
- **NFR5.3**: Integration test coverage ≥70%
- **NFR5.4**: Code documentation (TSDoc for TypeScript, docstrings for Python)
- **NFR5.5**: Logging for debugging (structured logs with correlation IDs)

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Vue 3 + Vuetify)               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  TimelineView.vue                                     │  │
│  │  - Timeline component (D3.js visualization)           │  │
│  │  - Concept filter sidebar                             │  │
│  │  - Export toolbar (PDF, FHIR, JSON)                   │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
└────────────────────────────────────────────────────────────-┘
                             ↓ ↑
                    REST API (FastAPI)
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Timeline Service                                     │  │
│  │  - GET /api/v1/timeline/{patient_id}                  │  │
│  │  - GET /api/v1/timeline/{patient_id}/concepts         │  │
│  │  - POST /api/v1/timeline/{patient_id}/export          │  │
│  └───────────────────────────────────────────────────────┘  │
│                            ↓ ↑                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Data Access Layer                                    │  │
│  │  - PostgreSQL (documents, annotations, audit logs)    │  │
│  │  - Elasticsearch (temporal queries, concept search)   │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                             ↓ ↑
                    CogStack-ModelServe
┌─────────────────────────────────────────────────────────────┐
│              CogStack-ModelServe (port 8001)                │
│  - SNOMED-CT concept extraction                             │
│  - Meta-annotation classification                           │
│  - Confidence scoring                                       │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Frontend Components

**TimelineView.vue** (Main component)
- Timeline visualization using D3.js
- Responsive SVG rendering
- Zoom/pan controls
- Event handlers for concept clicks

**ConceptFilterSidebar.vue**
- Search box with autocomplete
- Multi-select concept list
- Meta-annotation filters
- Date range picker
- Save/load filter presets

**TimelineExportToolbar.vue**
- Export buttons (PDF, FHIR, JSON)
- Export options dialog
- Progress indicator
- Download link

**ConceptPopover.vue**
- Displays concept details on hover/click
- Shows context (sentence)
- Meta-annotations display
- Confidence score
- Link to source document

#### Backend Services

**TimelineService** (`app/services/timeline_service.py`)
```python
class TimelineService:
    """Timeline data aggregation and processing"""

    async def get_patient_timeline(
        self,
        patient_id: str,
        filters: TimelineFilters,
        user: User
    ) -> PatientTimeline:
        """Fetch patient timeline with documents and concepts"""
        # 1. Audit log access
        # 2. Query documents from PostgreSQL
        # 3. Query concepts from Elasticsearch
        # 4. Filter by meta-annotations
        # 5. Aggregate into timeline structure
        # 6. Return PatientTimeline model

    async def get_timeline_concepts(
        self,
        patient_id: str,
        concept_filter: str
    ) -> List[TimelineConcept]:
        """Get specific concepts for patient timeline"""
        # 1. Query Elasticsearch for concept mentions
        # 2. Group by date
        # 3. Identify first mention vs recurring
        # 4. Return chronological list

    async def export_timeline_pdf(
        self,
        patient_id: str,
        filters: TimelineFilters,
        user: User
    ) -> bytes:
        """Export timeline to PDF"""
        # 1. Get timeline data
        # 2. Render to HTML template
        # 3. Convert HTML to PDF (using WeasyPrint)
        # 4. Add watermark
        # 5. Audit log export
        # 6. Return PDF bytes

    async def export_timeline_fhir(
        self,
        patient_id: str,
        filters: TimelineFilters,
        user: User
    ) -> Dict[str, Any]:
        """Export timeline to FHIR R4 Composition"""
        # 1. Get timeline data
        # 2. Map to FHIR resources:
        #    - Composition (timeline summary)
        #    - Observation (concepts)
        #    - Condition (diagnoses)
        #    - Provenance (source documents)
        # 3. Audit log export
        # 4. Return FHIR JSON
```

**ElasticsearchTimelineRepository** (`app/repositories/elasticsearch_timeline_repo.py`)
```python
class ElasticsearchTimelineRepository:
    """Elasticsearch queries for timeline data"""

    async def query_concepts_by_patient(
        self,
        patient_id: str,
        concept_filter: Optional[str] = None,
        date_range: Optional[DateRange] = None,
        meta_annotations: Optional[MetaAnnotationFilter] = None
    ) -> List[ConceptMention]:
        """Query concepts with temporal and meta-annotation filters"""

    async def aggregate_concepts_by_date(
        self,
        patient_id: str,
        granularity: str = "month"
    ) -> Dict[str, int]:
        """Aggregate concept frequency by date"""
```

#### Database Models

**PatientTimeline** (Pydantic response model)
```python
class PatientTimeline(BaseModel):
    patient_id: str
    documents: List[TimelineDocument]
    concepts: List[TimelineConcept]
    date_range: DateRange
    filters_applied: TimelineFilters

class TimelineDocument(BaseModel):
    document_id: str
    title: str
    document_type: str  # "clinical_note", "discharge_summary", "lab_report"
    date: datetime
    author: Optional[str]
    concepts: List[str]  # Concept CUIs mentioned in this document

class TimelineConcept(BaseModel):
    concept_cui: str
    concept_name: str
    concept_type: str  # "condition", "medication", "procedure"
    first_mention_date: datetime
    mention_count: int
    mentions: List[ConceptMention]

class ConceptMention(BaseModel):
    document_id: str
    date: datetime
    sentence: str  # Context where concept was mentioned
    meta_annotations: MetaAnnotations
    confidence: float  # 0.0 to 1.0
```

### API Endpoints

#### GET `/api/v1/timeline/{patient_id}`
Get patient timeline with documents and concepts.

**Request**:
```json
{
  "filters": {
    "concepts": ["C0011849", "C0020538"],  // Diabetes, Hypertension (SNOMED CUIs)
    "date_range": {
      "start": "2023-01-01T00:00:00Z",
      "end": "2023-12-31T23:59:59Z"
    },
    "meta_annotations": {
      "Negation": "Affirmed",
      "Experiencer": "Patient",
      "Temporality": ["Current", "Recent"]
    },
    "document_types": ["clinical_note", "discharge_summary"]
  }
}
```

**Response**:
```json
{
  "patient_id": "patient-123",
  "documents": [
    {
      "document_id": "doc-456",
      "title": "Diabetes Clinic Note",
      "document_type": "clinical_note",
      "date": "2023-06-15T10:30:00Z",
      "author": "Dr. Smith",
      "concepts": ["C0011849", "C0020538"]
    }
  ],
  "concepts": [
    {
      "concept_cui": "C0011849",
      "concept_name": "Diabetes Mellitus",
      "concept_type": "condition",
      "first_mention_date": "2022-03-10T00:00:00Z",
      "mention_count": 12,
      "mentions": [
        {
          "document_id": "doc-123",
          "date": "2022-03-10T00:00:00Z",
          "sentence": "Patient diagnosed with Type 2 Diabetes.",
          "meta_annotations": {
            "Negation": "Affirmed",
            "Temporality": "Recent",
            "Experiencer": "Patient",
            "Certainty": "High"
          },
          "confidence": 0.95
        }
      ]
    }
  ],
  "date_range": {
    "start": "2022-01-01T00:00:00Z",
    "end": "2023-12-31T23:59:59Z"
  },
  "filters_applied": { /* ... */ }
}
```

#### POST `/api/v1/timeline/{patient_id}/export`
Export timeline to PDF, FHIR, or JSON.

**Request**:
```json
{
  "format": "pdf",  // "pdf", "fhir", "json"
  "filters": { /* same as GET /timeline */ },
  "options": {
    "include_provenance": true,
    "watermark": "Clinical Summary - Confidential"
  }
}
```

**Response**:
```json
{
  "export_id": "export-789",
  "format": "pdf",
  "download_url": "/api/v1/timeline/exports/export-789/download",
  "expires_at": "2023-11-17T12:00:00Z",
  "audit_log_id": "audit-101112"
}
```

---

## Database Schema

### New Tables

#### `timeline_filters` (Save/Load Filter Presets)
```sql
CREATE TABLE timeline_filters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,  -- "Diabetes Management View"
    description TEXT,
    filters JSONB NOT NULL,  -- Stored filter configuration
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, name)
);

CREATE INDEX idx_timeline_filters_user ON timeline_filters(user_id);
```

#### `timeline_exports` (Track Exports for Audit)
```sql
CREATE TABLE timeline_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id),
    user_id UUID NOT NULL REFERENCES users(id),
    format VARCHAR(10) NOT NULL,  -- "pdf", "fhir", "json"
    filters JSONB NOT NULL,
    file_path VARCHAR(500),  -- Path to exported file
    download_count INTEGER DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_timeline_exports_patient ON timeline_exports(patient_id);
CREATE INDEX idx_timeline_exports_user ON timeline_exports(user_id);
CREATE INDEX idx_timeline_exports_created ON timeline_exports(created_at);
```

### Existing Tables (No Changes Needed)

- `documents` - Already stores clinical documents
- `annotations` - Already stores extracted concepts
- `audit_logs` - Already logs PHI access
- `patients` - Already stores patient metadata

---

## UI/UX Design

### Timeline Visualization

**Horizontal Timeline** (Default)
```
Timeline: Patient-123 | Diabetes Management View ▼ | [Export ▼] [Settings]

Filter: [🔍 Search concepts...] [Diabetes (C0011849) ×] [Hypertension (C0020538) ×]

Date Range: [Jan 2023] ────────────────────────────────── [Dec 2023]
                          ↓                    ↓
Documents:    ●───────────●────────────●───────●────────●
              │           │            │       │        │
              Jan         Mar          Jun     Sep      Dec

Concepts:     🔴─────────🔴───────────🔴──────🔴────────🔴  Diabetes
              🔵─────────🔵───────────🔵──────🔵────────🔵  Medications

Legend: 🔴 Condition  🔵 Medication  🟢 Procedure  🟡 Symptom
```

**Concept Popover** (On Click)
```
┌─────────────────────────────────────────┐
│ Diabetes Mellitus (C0011849)            │
│─────────────────────────────────────────│
│ Context:                                │
│ "Patient diagnosed with Type 2          │
│  Diabetes. HbA1c 8.5%."                 │
│─────────────────────────────────────────│
│ Meta-Annotations:                       │
│ • Negation: Affirmed ✓                  │
│ • Temporality: Recent                   │
│ • Experiencer: Patient ✓                │
│ • Certainty: High (95%)                 │
│─────────────────────────────────────────│
│ Document: Diabetes Clinic Note          │
│ Date: 2023-06-15                        │
│ [View Document →]                       │
└─────────────────────────────────────────┘
```

### Filter Sidebar

```
┌─────────────────────────────────┐
│ Filters                         │
│─────────────────────────────────│
│ Concept Search                  │
│ [🔍 Search SNOMED concepts...]  │
│                                 │
│ Selected Concepts:              │
│ • Diabetes (C0011849) [×]       │
│ • Hypertension (C0020538) [×]   │
│                                 │
│ Date Range                      │
│ ○ All time                      │
│ ○ Last 3 months                 │
│ ● Custom:                       │
│   From: [Jan 1, 2023]           │
│   To:   [Dec 31, 2023]          │
│                                 │
│ Meta-Annotations                │
│ ☑ Affirmed (exclude negated)    │
│ ☑ Patient (exclude family)      │
│ ☑ Current/Recent only           │
│                                 │
│ Document Types                  │
│ ☑ Clinical Notes                │
│ ☑ Discharge Summaries           │
│ ☐ Lab Reports                   │
│ ☐ Radiology Reports             │
│                                 │
│ [Save as Preset...]             │
│ [Clear All Filters]             │
└─────────────────────────────────┘
```

---

## Integration Points

### CogStack-ModelServe Integration
- **Purpose**: Extract clinical concepts from documents
- **Endpoint**: `POST http://cogstack-modelserve:8000/api/process`
- **Model**: `medcat_snomed` for SNOMED-CT concept extraction
- **Input**: Document text
- **Output**: List of concepts with meta-annotations and confidence scores

### Elasticsearch Integration
- **Purpose**: Temporal queries and concept search
- **Index**: `clinical_concepts` (stores extracted concepts with timestamps)
- **Queries**:
  - Range queries for date filtering
  - Term queries for concept filtering
  - Aggregations for concept frequency
  - Bool queries for meta-annotation filtering

### PostgreSQL Integration
- **Purpose**: Document storage and audit logging
- **Tables**:
  - `documents` - Clinical documents with metadata
  - `annotations` - Extracted concepts linked to documents
  - `audit_logs` - Timeline access logs
  - `timeline_exports` - Export tracking
  - `timeline_filters` - Saved filter presets

### FHIR R4 Export
- **Resources**:
  - `Composition` - Timeline summary document
  - `Observation` - Clinical concepts as structured data
  - `Condition` - Diagnoses
  - `Provenance` - Source document references

---

## Performance Requirements

### Load Time Targets
- **Timeline rendering**: <2 seconds for <100 documents
- **Filter updates**: <500ms
- **Zoom/pan**: 60fps (16.67ms per frame)
- **PDF export**: <5 seconds
- **FHIR export**: <3 seconds

### Scalability Targets
- **Concurrent users**: 10 clinicians viewing timelines simultaneously
- **Patient documents**: Support up to 500 documents per patient
- **Concepts per document**: Support up to 100 concepts per document
- **Timeline history**: Support 20+ years of patient history

### Optimization Strategies
- **Lazy loading**: Load visible timeline range first, lazy-load offscreen
- **Elasticsearch caching**: Cache concept aggregations (5-minute TTL)
- **Frontend virtualization**: Render only visible timeline segment
- **Background export**: Queue PDF/FHIR exports for async processing

---

## Constraints

### Technical Constraints
1. **Single workstation deployment** - No distributed caching or load balancing
2. **10 concurrent users** - Performance tuned for small teams
3. **Desktop browsers only** - No mobile optimization
4. **SNOMED-CT only** - No ICD-10 or UMLS in this sprint (Sprint 5)
5. **Local data only** - No external FHIR server integration yet

### Regulatory Constraints
1. **HIPAA compliance** - All PHI access audited
2. **GDPR compliance** - Export watermarks prevent unauthorized sharing
3. **21 CFR Part 11** - Audit trails for clinical governance
4. **NHS retention** - Exports retained for 8 years

### Resource Constraints
1. **RAM**: Timeline service must run in <2GB RAM
2. **Disk**: Exported PDFs stored for 30 days (automatic cleanup)
3. **CPU**: Timeline rendering must not block other services

---

## Acceptance Criteria

### Functional Acceptance

- [ ] **Timeline Visualization**:
  - [ ] Chronological document timeline with date axis
  - [ ] Zoom in/out for long patient histories (1 year to 20+ years)
  - [ ] Pan/scroll smoothly (60fps)
  - [ ] Click document to view full text

- [ ] **Concept Display**:
  - [ ] Clinical concepts extracted using CogStack-ModelServe
  - [ ] Color-coded by type (red=condition, blue=medication, green=procedure)
  - [ ] Meta-annotation filtering (Negation, Temporality, Experiencer)
  - [ ] Concept popover shows context, confidence, meta-annotations

- [ ] **Filtering**:
  - [ ] Search concepts by name (SNOMED-CT autocomplete)
  - [ ] Multi-select concepts (AND logic)
  - [ ] Filter by date range (absolute or relative)
  - [ ] Filter by document type
  - [ ] Save/load filter presets

- [ ] **Export**:
  - [ ] Export to PDF with watermark
  - [ ] Export to FHIR R4 (Composition + Observations)
  - [ ] Export to JSON
  - [ ] Audit log entry created for all exports

- [ ] **Audit Logging**:
  - [ ] All timeline views logged (user, patient, timestamp)
  - [ ] All filters logged
  - [ ] All exports logged
  - [ ] Admin can query audit logs

### Performance Acceptance

- [ ] Timeline loads in <2 seconds for <100 documents
- [ ] Filter updates in <500ms
- [ ] Zoom/pan at 60fps
- [ ] PDF export in <5 seconds
- [ ] Supports 10 concurrent users

### Security Acceptance

- [ ] Authentication required for all timeline access
- [ ] Role-based access (clinicians see assigned patients only)
- [ ] Audit logging for all PHI access
- [ ] Exported PDFs watermarked
- [ ] HTTPS only (TLS 1.3)

### Usability Acceptance

- [ ] Intuitive timeline visualization (no training manual needed)
- [ ] Keyboard shortcuts documented
- [ ] WCAG 2.1 AA compliance (keyboard navigation, screen readers, color contrast)
- [ ] Responsive design (1920x1080 and 1366x768)

### Testing Acceptance

- [ ] Unit test coverage ≥80%
- [ ] Integration test coverage ≥70%
- [ ] E2E test for full timeline workflow (open → filter → export)
- [ ] Performance tests verify targets

---

## Alignment with Constitution

### Principle 1: Patient Safety First
- **Timeline accuracy**: Meta-annotation filtering ensures 95% precision (vs 60% without)
- **Visual clarity**: Color-coding and confidence scores help clinicians identify reliable information
- **Audit trails**: Track all timeline access for clinical governance

### Principle 2: Privacy by Design
- **Access control**: Clinicians see timelines for assigned patients only
- **Audit logging**: All PHI access logged (WHO, WHAT, WHEN, WHERE)
- **Export watermarks**: Prevent unauthorized sharing of clinical summaries
- **Data retention**: Exports auto-deleted after 30 days

### Principle 3: Evidence-Based Development
- **CogStack-ModelServe**: Production-tested NLP model serving
- **D3.js**: Industry-standard timeline visualization library
- **FHIR R4**: Open standard for healthcare data exchange
- **WCAG 2.1 AA**: Accessibility standard compliance

### Principle 5: Open Standards and Interoperability
- **FHIR R4 export**: Enables integration with EHR systems
- **SNOMED-CT**: Standard medical terminology
- **JSON export**: Machine-readable format for research

### Principle 6: Transparency and Explainability
- **Confidence scores**: Show NLP confidence for each concept
- **Context display**: Show sentence where concept was mentioned
- **Provenance**: Link concepts to source documents

### Principle 9: Clinical Workflow Integration
- **Fast load times**: <2 seconds (doesn't disrupt clinical workflow)
- **Intuitive filters**: Minimal clicks to focus on relevant history
- **PDF export**: Integrates with referral/discharge workflows

---

## Testing Strategy

### Unit Tests (60% of test effort)

**Frontend Components**:
```typescript
// tests/unit/components/TimelineView.test.ts
describe('TimelineView', () => {
  it('should render timeline with documents', async () => {
    const wrapper = mount(TimelineView, {
      props: { patientId: 'patient-123' }
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.timeline-axis').exists()).toBe(true)
    expect(wrapper.findAll('.timeline-document')).toHaveLength(5)
  })

  it('should filter timeline by concept', async () => {
    const wrapper = mount(TimelineView)
    await wrapper.vm.applyFilter({ concepts: ['C0011849'] })
    expect(wrapper.vm.filteredDocuments).toHaveLength(3)
  })
})
```

**Backend Services**:
```python
# tests/unit/services/test_timeline_service.py
@pytest.mark.asyncio
async def test_get_patient_timeline(timeline_service, mock_elasticsearch):
    # Arrange
    patient_id = "patient-123"
    filters = TimelineFilters(concepts=["C0011849"])

    # Act
    timeline = await timeline_service.get_patient_timeline(
        patient_id, filters, user=mock_user
    )

    # Assert
    assert timeline.patient_id == patient_id
    assert len(timeline.documents) > 0
    assert all(concept.concept_cui == "C0011849" for concept in timeline.concepts)

@pytest.mark.asyncio
async def test_export_timeline_pdf_creates_audit_log(timeline_service, mock_audit_logger):
    # Arrange
    patient_id = "patient-123"

    # Act
    pdf_bytes = await timeline_service.export_timeline_pdf(
        patient_id, TimelineFilters(), user=mock_user
    )

    # Assert
    mock_audit_logger.log_export.assert_called_once()
    assert len(pdf_bytes) > 0
```

### Integration Tests (30% of test effort)

**API Endpoints**:
```python
# tests/integration/api/test_timeline_api.py
@pytest.mark.asyncio
async def test_get_timeline_endpoint(async_client, auth_headers):
    # Act
    response = await async_client.get(
        "/api/v1/timeline/patient-123",
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["patient_id"] == "patient-123"
    assert "documents" in data
    assert "concepts" in data

@pytest.mark.asyncio
async def test_export_timeline_pdf_endpoint(async_client, auth_headers):
    # Act
    response = await async_client.post(
        "/api/v1/timeline/patient-123/export",
        json={"format": "pdf", "filters": {}},
        headers=auth_headers
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["format"] == "pdf"
    assert "download_url" in data
```

### E2E Tests (10% of test effort)

**Full Timeline Workflow**:
```typescript
// tests/e2e/timeline-workflow.spec.ts
test('clinician can view and export patient timeline', async ({ page }) => {
  // Login
  await page.goto('http://localhost:8080/login')
  await page.fill('input[name="username"]', 'clinician1')
  await page.fill('input[name="password"]', 'password123')
  await page.click('button[type="submit"]')

  // Search for patient
  await page.goto('http://localhost:8080/patients/search')
  await page.fill('input[name="search"]', 'patient-123')
  await page.click('button:has-text("Search")')

  // Open timeline
  await page.click('button:has-text("Open Timeline")')
  await page.waitForSelector('.timeline-axis')

  // Apply filter
  await page.fill('input[name="concept-search"]', 'diabetes')
  await page.click('text=Diabetes Mellitus (C0011849)')
  await page.waitForSelector('.timeline-document', { state: 'visible' })

  // Export to PDF
  await page.click('button:has-text("Export")')
  await page.click('text=Export to PDF')
  const downloadPromise = page.waitForEvent('download')
  await page.click('button:has-text("Download")')
  const download = await downloadPromise
  expect(download.suggestedFilename()).toContain('timeline')
  expect(download.suggestedFilename()).toContain('.pdf')
})
```

### Performance Tests

**Load Testing**:
```python
# tests/performance/test_timeline_performance.py
import asyncio
import time

@pytest.mark.performance
async def test_timeline_load_time_under_2_seconds():
    """Timeline should load in <2 seconds for 100 documents"""
    start = time.time()

    timeline = await timeline_service.get_patient_timeline(
        "patient-with-100-docs", TimelineFilters(), mock_user
    )

    elapsed = time.time() - start
    assert elapsed < 2.0
    assert len(timeline.documents) == 100

@pytest.mark.performance
async def test_concurrent_timeline_access():
    """Support 10 concurrent users"""
    async def access_timeline(user_id):
        return await timeline_service.get_patient_timeline(
            "patient-123", TimelineFilters(), User(id=user_id)
        )

    tasks = [access_timeline(f"user-{i}") for i in range(10)]
    results = await asyncio.gather(*tasks)

    assert len(results) == 10
    assert all(r.patient_id == "patient-123" for r in results)
```

---

## Deployment Considerations

### Docker Compose Updates

**Add timeline service to `docker-compose.yml`**:
```yaml
services:
  backend:
    # Existing backend service
    environment:
      - TIMELINE_ENABLED=true
      - TIMELINE_PDF_EXPORT_DIR=/app/exports/timeline
    volumes:
      - timeline_exports:/app/exports/timeline

volumes:
  timeline_exports:
    driver: local
```

### Environment Variables

```bash
# Timeline Service Configuration
TIMELINE_ENABLED=true
TIMELINE_MAX_DOCUMENTS=500
TIMELINE_CACHE_TTL=300  # 5 minutes
TIMELINE_PDF_EXPORT_DIR=/app/exports/timeline
TIMELINE_EXPORT_RETENTION_DAYS=30
```

### Database Migrations

```bash
# Create timeline tables
alembic revision --autogenerate -m "Add timeline_filters and timeline_exports tables"
alembic upgrade head
```

### Elasticsearch Index

```bash
# Create timeline concepts index
PUT /clinical_concepts
{
  "mappings": {
    "properties": {
      "patient_id": { "type": "keyword" },
      "document_id": { "type": "keyword" },
      "concept_cui": { "type": "keyword" },
      "concept_name": { "type": "text" },
      "concept_type": { "type": "keyword" },
      "date": { "type": "date" },
      "meta_annotations": {
        "properties": {
          "Negation": { "type": "keyword" },
          "Temporality": { "type": "keyword" },
          "Experiencer": { "type": "keyword" },
          "Certainty": { "type": "keyword" }
        }
      },
      "confidence": { "type": "float" },
      "sentence": { "type": "text" }
    }
  }
}
```

---

## Open Questions

1. **Timeline Orientation Preference**:
   - Q: Should default be horizontal or vertical timeline?
   - A: [To be decided based on user feedback] - Propose horizontal (more familiar)

2. **Concept Grouping Strategy**:
   - Q: How to group concept synonyms (e.g., "Type 2 Diabetes", "T2DM", "Diabetes Mellitus Type 2")?
   - A: [To be decided] - Propose SNOMED-CT parent concept grouping

3. **Export Retention Policy**:
   - Q: How long to keep exported PDFs?
   - A: [To be decided] - Propose 30 days (configurable by admin)

4. **Temporal Relationship Detection**:
   - Q: What time window for "related" events (e.g., medication start → symptom onset within X days)?
   - A: [To be decided] - Propose 30 days (configurable)

5. **D3.js vs Alternative**:
   - Q: Use D3.js or alternative (vis.js, Timeline.js)?
   - A: [To be decided] - Propose D3.js (most flexible, widely used)

---

**Status**: Ready for review and approval
**Next Steps**: Create Technical Plan for Sprint 2 (Timeline View) after specification approval
**Dependencies**: Base Application (MVP), Patient Search Module (Sprint 1)
**Estimated Effort**: 120 hours over 4 weeks
