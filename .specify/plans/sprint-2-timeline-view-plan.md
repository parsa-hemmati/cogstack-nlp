# Technical Plan: Timeline View Module (Sprint 2)

**Version**: 1.0.0
**Date**: 2025-11-18
**Status**: Ready for Implementation
**Author**: AI Assistant (Claude Code - Autonomous Development)
**Based on Specification**: `.specify/specifications/sprint-2-timeline-view.md` (v1.0.0)

**Version History**:
- v1.0.0 (2025-11-18): Initial technical plan for Timeline View Module

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [API Design](#api-design)
4. [Database Schema](#database-schema)
5. [Component Design](#component-design)
6. [Timeline Visualization](#timeline-visualization)
7. [Export Functionality](#export-functionality)
8. [Testing Strategy](#testing-strategy)
9. [Deployment](#deployment)
10. [Performance Requirements](#performance-requirements)
11. [Risks & Mitigations](#risks--mitigations)
12. [Implementation Phases](#implementation-phases)

---

## Architecture Overview

### System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│ Timeline View Module (Sprint 2)                                      │
│                                                                       │
│  Frontend (Vue 3)                  Backend (FastAPI)                 │
│  ┌──────────────────────┐          ┌───────────────────────┐        │
│  │ TimelineView.vue     │◀────────▶│ /api/timeline         │        │
│  │ - Document timeline  │   HTTP   │ - Get timeline data   │        │
│  │ - Concept timeline   │          │ - Filter by date/type │        │
│  │ - Zoom/pan controls  │          │ - Temporal analysis   │        │
│  │ - Export controls    │          └───────────┬───────────┘        │
│  └──────────────────────┘                      │                     │
│           │                                     │                     │
│           │                                     ▼                     │
│           │                          ┌────────────────────┐          │
│           │                          │ PostgreSQL         │          │
│           │                          │ - documents table  │          │
│           │                          │ - annotations table│          │
│           │                          └────────────────────┘          │
│           │                                                           │
│           ▼                                                           │
│  ┌──────────────────────┐                                            │
│  │ D3.js Timeline       │                                            │
│  │ - SVG rendering      │                                            │
│  │ - Time scale axis    │                                            │
│  │ - Event markers      │                                            │
│  │ - Interactive zoom   │                                            │
│  └──────────────────────┘                                            │
│                                                                       │
│  Export Pipeline:                                                    │
│  Timeline Data → PDF/JSON/FHIR Exporter → Download                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Module Integration

**Dependencies**:
- Base Application (MVP): Authentication, audit logging, module registry
- Patient Search Module: Patient selection, document annotations
- CogStack-ModelServe: Clinical concept extraction (already integrated)
- PostgreSQL: Document and annotation storage
- Redis: Caching for timeline data

**Integration Points**:
1. **Patient Selection**: User selects patient from Patient Search → opens Timeline View
2. **Document Retrieval**: Fetch all documents for patient from PostgreSQL
3. **Annotation Retrieval**: Fetch clinical concepts (SNOMED-CT) with meta-annotations
4. **Timeline Rendering**: D3.js renders chronological visualization
5. **Export**: Generate PDF/JSON/FHIR export of timeline data

---

## Technology Stack

### Frontend Libraries

**Core**:
- Vue 3.5+ (Composition API, TypeScript)
- Vuetify 3.7+ (Material Design components)
- D3.js v7+ (Timeline visualization, SVG rendering)
- Pinia (State management for timeline data)

**Timeline Visualization**:
- D3.js scales (time scale for x-axis)
- D3.js axes (date axis rendering)
- D3.js selections (event marker manipulation)
- D3.js zoom behavior (pan and zoom controls)

**Export Libraries**:
- jsPDF (PDF generation)
- FHIR.js (FHIR R4 resource generation)
- FileSaver.js (Download handling)

### Backend Libraries

**Core**:
- FastAPI 0.115+ (Timeline API endpoints)
- SQLAlchemy 2.0 (ORM for documents/annotations)
- Pydantic (Timeline data models)

**Export Libraries**:
- ReportLab (Server-side PDF generation)
- fhir.resources (FHIR R4 Python library)

---

## API Design

### Timeline API Endpoints

#### 1. Get Patient Timeline

**Endpoint**: `GET /api/timeline/{patient_id}`

**Description**: Retrieve complete timeline data for a patient (documents + clinical concepts)

**Request Parameters**:
```typescript
interface TimelineQueryParams {
  patient_id: string;           // Patient UUID
  start_date?: string;          // Filter start date (ISO 8601)
  end_date?: string;            // Filter end date (ISO 8601)
  document_types?: string[];    // Filter by document type
  concept_types?: string[];     // Filter by concept type (condition/medication/procedure)
  include_negated?: boolean;    // Include negated concepts (default: false)
  include_family?: boolean;     // Include family history (default: false)
}
```

**Response**:
```typescript
interface TimelineResponse {
  patient_id: string;
  timeline: {
    documents: TimelineDocument[];
    concepts: TimelineConcept[];
    date_range: {
      earliest: string;         // ISO 8601
      latest: string;           // ISO 8601
    };
  };
  metadata: {
    document_count: number;
    concept_count: number;
    generated_at: string;       // ISO 8601
  };
}

interface TimelineDocument {
  id: string;
  title: string;
  type: string;                  // "clinical_note" | "lab_report" | "discharge_summary"
  date: string;                  // ISO 8601
  author?: string;
  department?: string;
  content_preview: string;       // First 200 characters
  annotation_count: number;      // Number of concepts in this document
}

interface TimelineConcept {
  id: string;
  cui: string;                   // SNOMED-CT CUI
  name: string;                  // Preferred term
  type: string;                  // "condition" | "medication" | "procedure"
  first_mentioned: string;       // ISO 8601 (first occurrence)
  last_mentioned: string;        // ISO 8601 (last occurrence)
  occurrences: ConceptOccurrence[];
  meta_annotations: {
    negation: string;            // "Affirmed" | "Negated"
    temporality: string;         // "Current" | "Past" | "Future" | "Hypothetical"
    experiencer: string;         // "Patient" | "Family" | "Other"
  };
}

interface ConceptOccurrence {
  document_id: string;
  date: string;                  // ISO 8601
  context: string;               // Sentence containing concept
  start_char: number;
  end_char: number;
}
```

**Example**:
```bash
GET /api/timeline/550e8400-e29b-41d4-a716-446655440000?start_date=2023-01-01&end_date=2023-12-31
```

**Status Codes**:
- `200 OK`: Timeline retrieved successfully
- `404 Not Found`: Patient not found
- `403 Forbidden`: User not authorized to view patient
- `500 Internal Server Error`: Server error

---

#### 2. Export Timeline

**Endpoint**: `POST /api/timeline/{patient_id}/export`

**Description**: Export timeline in specified format (PDF, JSON, FHIR R4)

**Request Body**:
```typescript
interface ExportRequest {
  format: "pdf" | "json" | "fhir";
  include_documents: boolean;   // Include full document text
  include_concepts: boolean;    // Include extracted concepts
  filters?: TimelineQueryParams;
}
```

**Response**:
```typescript
interface ExportResponse {
  export_id: string;
  format: string;
  download_url: string;          // Presigned URL or base64 data
  expires_at: string;            // ISO 8601 (24 hours from now)
  file_size_bytes: number;
}
```

**Example**:
```bash
POST /api/timeline/550e8400-e29b-41d4-a716-446655440000/export
{
  "format": "pdf",
  "include_documents": true,
  "include_concepts": true,
  "filters": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
  }
}
```

**Status Codes**:
- `200 OK`: Export generated successfully
- `404 Not Found`: Patient not found
- `400 Bad Request`: Invalid export format
- `500 Internal Server Error`: Export generation failed

---

## Database Schema

### New Tables

**None** - Timeline View uses existing tables from Base Application:
- `documents` (from MVP Phase 3)
- `annotations` (from MVP Phase 3)

### Existing Schema Used

```sql
-- documents table (from MVP)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    task_id UUID REFERENCES tasks(id) ON DELETE SET NULL,
    uploaded_by UUID NOT NULL REFERENCES users(id),

    -- Document metadata
    original_filename TEXT NOT NULL,
    file_type TEXT NOT NULL CHECK (file_type IN ('rtf', 'txt', 'docx')),
    file_hash TEXT UNIQUE NOT NULL,
    file_size_bytes INTEGER NOT NULL,

    -- Document content (BYTEA for RTF binary)
    content BYTEA NOT NULL,

    -- NLP processing status
    processing_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),

    -- Timestamps
    uploaded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,

    -- Audit
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- annotations table (from MVP)
CREATE TABLE annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,

    -- Annotation span
    start_char INTEGER NOT NULL,
    end_char INTEGER NOT NULL,
    text TEXT NOT NULL,

    -- Concept (SNOMED-CT)
    cui TEXT NOT NULL,
    preferred_name TEXT NOT NULL,
    concept_type TEXT NOT NULL, -- condition, medication, procedure

    -- Meta-annotations
    negation TEXT CHECK (negation IN ('Affirmed', 'Negated')),
    temporality TEXT CHECK (temporality IN ('Current', 'Past', 'Future', 'Hypothetical')),
    experiencer TEXT CHECK (experiencer IN ('Patient', 'Family', 'Other')),
    certainty TEXT CHECK (certainty IN ('Certain', 'Uncertain')),

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_annotations_document_id ON annotations(document_id);
CREATE INDEX idx_annotations_cui ON annotations(cui);
CREATE INDEX idx_annotations_concept_type ON annotations(concept_type);
```

### Timeline-Specific Queries

**Query 1: Get all documents for patient timeline**:
```sql
-- Get documents for patient (via project → task → document)
SELECT d.id, d.original_filename AS title, d.file_type AS type,
       d.uploaded_at AS date, u.full_name AS author,
       d.processing_status,
       COUNT(a.id) AS annotation_count
FROM documents d
JOIN tasks t ON d.task_id = t.id
JOIN projects p ON t.project_id = p.id
LEFT JOIN users u ON d.uploaded_by = u.id
LEFT JOIN annotations a ON a.document_id = d.id
WHERE p.patient_id = ?
  AND d.processing_status = 'completed'
  AND d.uploaded_at BETWEEN ? AND ?
GROUP BY d.id, u.full_name
ORDER BY d.uploaded_at ASC;
```

**Query 2: Get all concepts for patient timeline**:
```sql
-- Get concepts with first/last mention dates
SELECT a.cui, a.preferred_name, a.concept_type,
       MIN(d.uploaded_at) AS first_mentioned,
       MAX(d.uploaded_at) AS last_mentioned,
       a.negation, a.temporality, a.experiencer,
       COUNT(*) AS occurrence_count
FROM annotations a
JOIN documents d ON a.document_id = d.id
JOIN tasks t ON d.task_id = t.id
JOIN projects p ON t.project_id = p.id
WHERE p.patient_id = ?
  AND a.negation = 'Affirmed'
  AND a.experiencer = 'Patient'
  AND d.uploaded_at BETWEEN ? AND ?
GROUP BY a.cui, a.preferred_name, a.concept_type, a.negation, a.temporality, a.experiencer
ORDER BY first_mentioned ASC;
```

**Query 3: Get concept occurrences for detail view**:
```sql
-- Get all occurrences of a specific concept
SELECT a.id, a.document_id, d.uploaded_at AS date,
       a.text, a.start_char, a.end_char,
       -- Get surrounding context (sentence)
       SUBSTRING(d.content_text FROM GREATEST(1, a.start_char - 100) FOR 200) AS context
FROM annotations a
JOIN documents d ON a.document_id = d.id
JOIN tasks t ON d.task_id = t.id
JOIN projects p ON t.project_id = p.id
WHERE p.patient_id = ?
  AND a.cui = ?
ORDER BY d.uploaded_at ASC;
```

---

## Component Design

### Frontend Components

#### 1. TimelineView.vue (Main Container)

**Purpose**: Top-level component for timeline visualization

**State**:
```typescript
interface TimelineState {
  patient: Patient | null;
  timelineData: TimelineResponse | null;
  loading: boolean;
  error: string | null;
  filters: TimelineFilters;
  viewMode: "document" | "concept" | "combined";
  zoomLevel: number;
  selectedDateRange: { start: Date; end: Date };
}
```

**Methods**:
```typescript
async function loadTimeline(patientId: string): Promise<void>
function applyFilters(filters: TimelineFilters): void
function changeViewMode(mode: string): void
function handleZoom(scale: number): void
function exportTimeline(format: string): Promise<void>
```

**Template Structure**:
```vue
<template>
  <v-container fluid>
    <v-row>
      <!-- Patient Header -->
      <v-col cols="12">
        <PatientHeader :patient="patient" />
      </v-col>
    </v-row>

    <v-row>
      <!-- Timeline Controls -->
      <v-col cols="12">
        <TimelineControls
          :filters="filters"
          :view-mode="viewMode"
          @update:filters="applyFilters"
          @update:view-mode="changeViewMode"
          @export="exportTimeline"
        />
      </v-col>
    </v-row>

    <v-row>
      <!-- Timeline Visualization -->
      <v-col cols="12">
        <TimelineChart
          :timeline-data="timelineData"
          :view-mode="viewMode"
          :zoom-level="zoomLevel"
          @zoom="handleZoom"
          @select-document="showDocumentDetail"
          @select-concept="showConceptDetail"
        />
      </v-col>
    </v-row>
  </v-container>
</template>
```

---

#### 2. TimelineChart.vue (D3.js Visualization)

**Purpose**: Render interactive timeline using D3.js

**Props**:
```typescript
interface TimelineChartProps {
  timelineData: TimelineResponse;
  viewMode: "document" | "concept" | "combined";
  zoomLevel: number;
}
```

**D3.js Implementation**:
```typescript
import * as d3 from 'd3';

function renderTimeline() {
  // 1. Setup SVG canvas
  const svg = d3.select(chartRef.value)
    .append("svg")
    .attr("width", width)
    .attr("height", height);

  // 2. Create time scale
  const xScale = d3.scaleTime()
    .domain([
      new Date(timelineData.timeline.date_range.earliest),
      new Date(timelineData.timeline.date_range.latest)
    ])
    .range([0, width]);

  // 3. Create x-axis (date axis)
  const xAxis = d3.axisBottom(xScale)
    .ticks(10)
    .tickFormat(d3.timeFormat("%b %Y"));

  svg.append("g")
    .attr("class", "x-axis")
    .attr("transform", `translate(0, ${height - 30})`)
    .call(xAxis);

  // 4. Render document markers
  if (viewMode === "document" || viewMode === "combined") {
    renderDocuments(svg, xScale);
  }

  // 5. Render concept event markers
  if (viewMode === "concept" || viewMode === "combined") {
    renderConcepts(svg, xScale);
  }

  // 6. Add zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([1, 10])
    .on("zoom", handleZoomEvent);

  svg.call(zoom);
}

function renderDocuments(svg, xScale) {
  const documents = timelineData.timeline.documents;

  svg.selectAll(".document-marker")
    .data(documents)
    .enter()
    .append("circle")
    .attr("class", "document-marker")
    .attr("cx", d => xScale(new Date(d.date)))
    .attr("cy", 100)
    .attr("r", 8)
    .attr("fill", d => getDocumentColor(d.type))
    .on("click", (event, d) => emit("select-document", d))
    .on("mouseover", showTooltip)
    .on("mouseout", hideTooltip);
}

function renderConcepts(svg, xScale) {
  const concepts = timelineData.timeline.concepts;

  svg.selectAll(".concept-marker")
    .data(concepts)
    .enter()
    .append("rect")
    .attr("class", "concept-marker")
    .attr("x", d => xScale(new Date(d.first_mentioned)))
    .attr("y", d => getConceptY(d.type))
    .attr("width", d => {
      const start = xScale(new Date(d.first_mentioned));
      const end = xScale(new Date(d.last_mentioned));
      return Math.max(end - start, 5); // Minimum width 5px
    })
    .attr("height", 20)
    .attr("fill", d => getConceptColor(d.type))
    .attr("opacity", 0.7)
    .on("click", (event, d) => emit("select-concept", d))
    .on("mouseover", showConceptTooltip)
    .on("mouseout", hideTooltip);
}

function getConceptY(type: string): number {
  // Stack concepts by type
  const typePositions = {
    "condition": 150,
    "medication": 200,
    "procedure": 250
  };
  return typePositions[type] || 200;
}

function getConceptColor(type: string): string {
  const colors = {
    "condition": "#f44336",     // Red
    "medication": "#2196f3",    // Blue
    "procedure": "#4caf50"      // Green
  };
  return colors[type] || "#9e9e9e";
}
```

---

#### 3. TimelineControls.vue (Filters and Actions)

**Purpose**: Filter timeline and trigger exports

**Props**:
```typescript
interface TimelineControlsProps {
  filters: TimelineFilters;
  viewMode: string;
}
```

**Template**:
```vue
<template>
  <v-card>
    <v-card-title>Timeline Controls</v-card-title>
    <v-card-text>
      <v-row>
        <!-- View Mode -->
        <v-col cols="4">
          <v-btn-toggle v-model="localViewMode" mandatory>
            <v-btn value="document">Documents</v-btn>
            <v-btn value="concept">Concepts</v-btn>
            <v-btn value="combined">Combined</v-btn>
          </v-btn-toggle>
        </v-col>

        <!-- Date Range -->
        <v-col cols="4">
          <v-text-field
            v-model="localFilters.start_date"
            type="date"
            label="Start Date"
            @change="updateFilters"
          />
        </v-col>
        <v-col cols="4">
          <v-text-field
            v-model="localFilters.end_date"
            type="date"
            label="End Date"
            @change="updateFilters"
          />
        </v-col>

        <!-- Document Type Filter -->
        <v-col cols="6">
          <v-select
            v-model="localFilters.document_types"
            :items="documentTypes"
            label="Document Types"
            multiple
            chips
            @change="updateFilters"
          />
        </v-col>

        <!-- Concept Type Filter -->
        <v-col cols="6">
          <v-select
            v-model="localFilters.concept_types"
            :items="conceptTypes"
            label="Concept Types"
            multiple
            chips
            @change="updateFilters"
          />
        </v-col>

        <!-- Meta-annotation Filters -->
        <v-col cols="6">
          <v-checkbox
            v-model="localFilters.include_negated"
            label="Include negated concepts"
            @change="updateFilters"
          />
        </v-col>
        <v-col cols="6">
          <v-checkbox
            v-model="localFilters.include_family"
            label="Include family history"
            @change="updateFilters"
          />
        </v-col>
      </v-row>

      <!-- Export Actions -->
      <v-row>
        <v-col cols="12">
          <v-btn-group>
            <v-btn color="primary" @click="emit('export', 'pdf')">
              <v-icon left>mdi-file-pdf-box</v-icon>
              Export PDF
            </v-btn>
            <v-btn color="secondary" @click="emit('export', 'json')">
              <v-icon left>mdi-code-json</v-icon>
              Export JSON
            </v-btn>
            <v-btn color="info" @click="emit('export', 'fhir')">
              <v-icon left>mdi-hospital-box</v-icon>
              Export FHIR
            </v-btn>
          </v-btn-group>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>
```

---

### Backend Components

#### 1. TimelineService (Business Logic)

**Purpose**: Orchestrate timeline data retrieval and processing

**File**: `app/services/timeline_service.py`

```python
from typing import List, Optional
from datetime import datetime
from app.models import Document, Annotation
from app.schemas.timeline import TimelineResponse, TimelineDocument, TimelineConcept
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

class TimelineService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_patient_timeline(
        self,
        patient_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        document_types: Optional[List[str]] = None,
        concept_types: Optional[List[str]] = None,
        include_negated: bool = False,
        include_family: bool = False
    ) -> TimelineResponse:
        """
        Get comprehensive timeline for patient.

        Args:
            patient_id: Patient UUID
            start_date: Filter start date
            end_date: Filter end date
            document_types: Filter document types
            concept_types: Filter concept types
            include_negated: Include negated concepts
            include_family: Include family history

        Returns:
            TimelineResponse with documents and concepts
        """
        # Get documents
        documents = await self._get_timeline_documents(
            patient_id, start_date, end_date, document_types
        )

        # Get concepts
        concepts = await self._get_timeline_concepts(
            patient_id, start_date, end_date, concept_types,
            include_negated, include_family
        )

        # Calculate date range
        date_range = self._calculate_date_range(documents)

        return TimelineResponse(
            patient_id=patient_id,
            timeline={
                "documents": documents,
                "concepts": concepts,
                "date_range": date_range
            },
            metadata={
                "document_count": len(documents),
                "concept_count": len(concepts),
                "generated_at": datetime.utcnow().isoformat()
            }
        )

    async def _get_timeline_documents(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        document_types: Optional[List[str]]
    ) -> List[TimelineDocument]:
        """Get documents for timeline"""
        query = (
            select(
                Document.id,
                Document.original_filename.label("title"),
                Document.file_type.label("type"),
                Document.uploaded_at.label("date"),
                func.count(Annotation.id).label("annotation_count")
            )
            .join(Task, Document.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .outerjoin(Annotation, Annotation.document_id == Document.id)
            .where(Project.patient_id == patient_id)
            .where(Document.processing_status == "completed")
            .group_by(Document.id)
            .order_by(Document.uploaded_at.asc())
        )

        # Apply filters
        if start_date:
            query = query.where(Document.uploaded_at >= start_date)
        if end_date:
            query = query.where(Document.uploaded_at <= end_date)
        if document_types:
            query = query.where(Document.file_type.in_(document_types))

        result = await self.db.execute(query)
        rows = result.all()

        return [
            TimelineDocument(
                id=str(row.id),
                title=row.title,
                type=row.type,
                date=row.date.isoformat(),
                annotation_count=row.annotation_count
            )
            for row in rows
        ]

    async def _get_timeline_concepts(
        self,
        patient_id: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime],
        concept_types: Optional[List[str]],
        include_negated: bool,
        include_family: bool
    ) -> List[TimelineConcept]:
        """Get concepts for timeline"""
        query = (
            select(
                Annotation.cui,
                Annotation.preferred_name.label("name"),
                Annotation.concept_type.label("type"),
                func.min(Document.uploaded_at).label("first_mentioned"),
                func.max(Document.uploaded_at).label("last_mentioned"),
                Annotation.negation,
                Annotation.temporality,
                Annotation.experiencer,
                func.count().label("occurrence_count")
            )
            .join(Document, Annotation.document_id == Document.id)
            .join(Task, Document.task_id == Task.id)
            .join(Project, Task.project_id == Project.id)
            .where(Project.patient_id == patient_id)
            .group_by(
                Annotation.cui,
                Annotation.preferred_name,
                Annotation.concept_type,
                Annotation.negation,
                Annotation.temporality,
                Annotation.experiencer
            )
            .order_by(func.min(Document.uploaded_at).asc())
        )

        # Apply meta-annotation filters
        if not include_negated:
            query = query.where(Annotation.negation == "Affirmed")
        if not include_family:
            query = query.where(Annotation.experiencer == "Patient")

        # Apply other filters
        if start_date:
            query = query.where(Document.uploaded_at >= start_date)
        if end_date:
            query = query.where(Document.uploaded_at <= end_date)
        if concept_types:
            query = query.where(Annotation.concept_type.in_(concept_types))

        result = await self.db.execute(query)
        rows = result.all()

        return [
            TimelineConcept(
                id=row.cui,  # Use CUI as ID
                cui=row.cui,
                name=row.name,
                type=row.type,
                first_mentioned=row.first_mentioned.isoformat(),
                last_mentioned=row.last_mentioned.isoformat(),
                meta_annotations={
                    "negation": row.negation,
                    "temporality": row.temporality,
                    "experiencer": row.experiencer
                },
                occurrence_count=row.occurrence_count
            )
            for row in rows
        ]
```

---

## Export Functionality

### PDF Export

**Library**: ReportLab (Python) or jsPDF (JavaScript)

**Implementation Strategy**: **Server-side** (better formatting control, HIPAA compliance)

**Format**:
```
┌─────────────────────────────────────────────────────────────────┐
│ Patient Timeline Report                                          │
│                                                                   │
│ Patient ID: 550e8400-e29b-41d4-a716-446655440000                │
│ Generated: 2025-11-18 14:30:00                                   │
│ Date Range: 2023-01-01 to 2023-12-31                            │
├─────────────────────────────────────────────────────────────────┤
│ Documents (15 total)                                             │
│                                                                   │
│ 2023-01-15: Clinical Note - General Medicine                    │
│   - 8 clinical concepts extracted                                │
│                                                                   │
│ 2023-02-20: Lab Report - Pathology                              │
│   - 12 clinical concepts extracted                               │
│                                                                   │
│ ...                                                              │
├─────────────────────────────────────────────────────────────────┤
│ Clinical Concepts                                                 │
│                                                                   │
│ Conditions:                                                       │
│ - Hypertension (C0020538)                                        │
│   First mentioned: 2023-01-15                                    │
│   Last mentioned: 2023-11-30                                     │
│   Occurrences: 8                                                 │
│                                                                   │
│ Medications:                                                      │
│ - Amlodipine (C0051696)                                          │
│   First mentioned: 2023-03-10                                    │
│   Last mentioned: 2023-06-15                                     │
│   Occurrences: 3                                                 │
│                                                                   │
│ ...                                                              │
└─────────────────────────────────────────────────────────────────┘
```

**Code**: `app/services/timeline_export_service.py`

```python
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

class TimelineExportService:
    async def export_pdf(self, timeline_data: TimelineResponse) -> bytes:
        """Generate PDF export of timeline"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()

        # Title
        story.append(Paragraph("Patient Timeline Report", styles['Title']))
        story.append(Spacer(1, 12))

        # Metadata
        story.append(Paragraph(f"Patient ID: {timeline_data.patient_id}", styles['Normal']))
        story.append(Paragraph(f"Generated: {timeline_data.metadata['generated_at']}", styles['Normal']))
        story.append(Spacer(1, 12))

        # Documents section
        story.append(Paragraph(f"Documents ({timeline_data.metadata['document_count']} total)", styles['Heading2']))
        for doc in timeline_data.timeline['documents']:
            story.append(Paragraph(f"{doc.date}: {doc.title} - {doc.type}", styles['Normal']))
            story.append(Paragraph(f"  {doc.annotation_count} clinical concepts extracted", styles['Italic']))

        story.append(Spacer(1, 12))

        # Concepts section
        story.append(Paragraph(f"Clinical Concepts ({timeline_data.metadata['concept_count']} total)", styles['Heading2']))

        # Group by type
        concepts_by_type = {}
        for concept in timeline_data.timeline['concepts']:
            if concept.type not in concepts_by_type:
                concepts_by_type[concept.type] = []
            concepts_by_type[concept.type].append(concept)

        for concept_type, concepts in concepts_by_type.items():
            story.append(Paragraph(f"{concept_type.capitalize()}s:", styles['Heading3']))
            for concept in concepts:
                story.append(Paragraph(f"- {concept.name} ({concept.cui})", styles['Normal']))
                story.append(Paragraph(f"  First mentioned: {concept.first_mentioned}", styles['Italic']))
                story.append(Paragraph(f"  Last mentioned: {concept.last_mentioned}", styles['Italic']))
                story.append(Paragraph(f"  Occurrences: {concept.occurrence_count}", styles['Italic']))

        # Build PDF
        doc.build(story)

        return buffer.getvalue()
```

---

### FHIR R4 Export

**Format**: Bundle of DocumentReference + Condition + MedicationStatement resources

**Example**:
```json
{
  "resourceType": "Bundle",
  "type": "collection",
  "entry": [
    {
      "resource": {
        "resourceType": "DocumentReference",
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "current",
        "type": {
          "coding": [{
            "system": "http://loinc.org",
            "code": "11488-4",
            "display": "Consultation note"
          }]
        },
        "subject": {
          "reference": "Patient/550e8400"
        },
        "date": "2023-01-15T10:30:00Z",
        "author": [{
          "display": "Dr. Smith"
        }],
        "content": [{
          "attachment": {
            "contentType": "text/rtf",
            "data": "..." // Base64 encoded
          }
        }]
      }
    },
    {
      "resource": {
        "resourceType": "Condition",
        "id": "condition-1",
        "clinicalStatus": {
          "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "active"
          }]
        },
        "code": {
          "coding": [{
            "system": "http://snomed.info/sct",
            "code": "38341003",
            "display": "Hypertension"
          }]
        },
        "subject": {
          "reference": "Patient/550e8400"
        },
        "onsetDateTime": "2023-01-15"
      }
    }
  ]
}
```

**Code**: `app/services/fhir_export_service.py`

```python
from fhir.resources.bundle import Bundle
from fhir.resources.documentreference import DocumentReference
from fhir.resources.condition import Condition

class FHIRExportService:
    def export_timeline_fhir(self, timeline_data: TimelineResponse) -> dict:
        """Export timeline as FHIR R4 Bundle"""
        entries = []

        # Convert documents to DocumentReference resources
        for doc in timeline_data.timeline['documents']:
            doc_ref = DocumentReference(
                id=doc.id,
                status="current",
                type={
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "11488-4",
                        "display": doc.type
                    }]
                },
                subject={"reference": f"Patient/{timeline_data.patient_id}"},
                date=doc.date
            )
            entries.append({"resource": doc_ref.dict()})

        # Convert concepts to Condition/MedicationStatement resources
        for concept in timeline_data.timeline['concepts']:
            if concept.type == "condition":
                condition = Condition(
                    id=concept.id,
                    clinicalStatus={
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                            "code": "active"
                        }]
                    },
                    code={
                        "coding": [{
                            "system": "http://snomed.info/sct",
                            "code": concept.cui,
                            "display": concept.name
                        }]
                    },
                    subject={"reference": f"Patient/{timeline_data.patient_id}"},
                    onsetDateTime=concept.first_mentioned
                )
                entries.append({"resource": condition.dict()})

        bundle = Bundle(
            type="collection",
            entry=entries
        )

        return bundle.dict()
```

---

## Testing Strategy

### Unit Tests

**Frontend Tests** (Vitest):
```typescript
// tests/unit/components/TimelineChart.test.ts
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import TimelineChart from '@/components/TimelineChart.vue'

describe('TimelineChart', () => {
  it('should render timeline with documents', () => {
    const wrapper = mount(TimelineChart, {
      props: {
        timelineData: mockTimelineData,
        viewMode: 'document',
        zoomLevel: 1
      }
    })

    expect(wrapper.find('.timeline-chart').exists()).toBe(true)
    expect(wrapper.findAll('.document-marker')).toHaveLength(5)
  })

  it('should apply date filter correctly', async () => {
    const wrapper = mount(TimelineChart, {
      props: {
        timelineData: mockTimelineData,
        viewMode: 'document',
        zoomLevel: 1
      }
    })

    await wrapper.vm.applyDateFilter('2023-01-01', '2023-06-30')

    expect(wrapper.vm.filteredDocuments).toHaveLength(3)
  })

  it('should emit select-document event on click', async () => {
    const wrapper = mount(TimelineChart, {
      props: { timelineData: mockTimelineData }
    })

    await wrapper.find('.document-marker').trigger('click')

    expect(wrapper.emitted('select-document')).toBeTruthy()
  })
})
```

**Backend Tests** (pytest):
```python
# tests/unit/services/test_timeline_service.py
import pytest
from app.services.timeline_service import TimelineService
from datetime import datetime

@pytest.mark.asyncio
async def test_get_patient_timeline(timeline_service, mock_patient_id):
    """Test timeline retrieval"""
    result = await timeline_service.get_patient_timeline(
        patient_id=mock_patient_id,
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31)
    )

    assert result.patient_id == mock_patient_id
    assert len(result.timeline['documents']) > 0
    assert len(result.timeline['concepts']) > 0

@pytest.mark.asyncio
async def test_timeline_filters_negated_concepts(timeline_service, mock_patient_id):
    """Test that negated concepts are excluded by default"""
    result = await timeline_service.get_patient_timeline(
        patient_id=mock_patient_id,
        include_negated=False
    )

    for concept in result.timeline['concepts']:
        assert concept.meta_annotations['negation'] == 'Affirmed'

@pytest.mark.asyncio
async def test_timeline_export_pdf(export_service, mock_timeline_data):
    """Test PDF export generation"""
    pdf_bytes = await export_service.export_pdf(mock_timeline_data)

    assert len(pdf_bytes) > 0
    assert pdf_bytes.startswith(b'%PDF')  # PDF magic number
```

---

### Integration Tests

```python
# tests/integration/test_timeline_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_timeline_api_flow(async_client: AsyncClient, auth_headers, patient_id):
    """Test complete timeline API flow"""
    # Get timeline
    response = await async_client.get(
        f"/api/timeline/{patient_id}",
        headers=auth_headers,
        params={
            "start_date": "2023-01-01",
            "end_date": "2023-12-31"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data['patient_id'] == patient_id
    assert 'timeline' in data
    assert 'documents' in data['timeline']
    assert 'concepts' in data['timeline']

@pytest.mark.asyncio
async def test_timeline_export_pdf_flow(async_client: AsyncClient, auth_headers, patient_id):
    """Test PDF export flow"""
    response = await async_client.post(
        f"/api/timeline/{patient_id}/export",
        headers=auth_headers,
        json={
            "format": "pdf",
            "include_documents": True,
            "include_concepts": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert 'download_url' in data
    assert data['format'] == 'pdf'
```

---

## Performance Requirements

### Response Time Targets

| Operation | Target | Maximum |
|-----------|--------|---------|
| Load timeline (<100 docs) | <1 second | 2 seconds |
| Load timeline (100-500 docs) | <3 seconds | 5 seconds |
| Load timeline (>500 docs) | <5 seconds | 10 seconds |
| Apply filters | <500ms | 1 second |
| Export PDF | <3 seconds | 5 seconds |
| Export FHIR | <2 seconds | 4 seconds |

### Optimization Strategies

1. **Database Query Optimization**:
   - Use indexes on `uploaded_at`, `processing_status`
   - Use JOINs to minimize round trips
   - Limit concept query to top 100 concepts (pagination for more)

2. **Caching**:
   - Cache timeline data in Redis (5 minute TTL)
   - Cache key: `timeline:{patient_id}:{filters_hash}`
   - Invalidate on new document upload

3. **Frontend Rendering**:
   - Use D3.js virtualization for >500 markers
   - Debounce zoom events (100ms)
   - Lazy load document previews

4. **Export Optimization**:
   - Generate exports in background (Celery task for large timelines)
   - Store exports in temporary storage (S3 or local filesystem)
   - Presigned URLs with 24-hour expiration

---

## Deployment

### Docker Services (No Changes)

Timeline View module uses existing infrastructure:
- Frontend: Vue 3 app (already deployed)
- Backend: FastAPI (already deployed)
- PostgreSQL: Database (already deployed)
- Redis: Caching (already deployed)

### Environment Variables

Add to `.env`:
```bash
# Timeline settings
TIMELINE_MAX_DOCUMENTS=1000
TIMELINE_CACHE_TTL_SECONDS=300
TIMELINE_EXPORT_TEMP_DIR=/tmp/timeline_exports
TIMELINE_EXPORT_TTL_HOURS=24
```

### Database Migrations

**No migrations needed** - uses existing `documents` and `annotations` tables.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Performance with large datasets** (>1000 docs) | High | Pagination, caching, virtualization |
| **D3.js rendering complexity** | Medium | Use proven timeline libraries (vis-timeline) if D3 too complex |
| **PDF export formatting** | Low | Use ReportLab templates, test with sample data |
| **FHIR compliance** | Medium | Use fhir.resources library, validate against FHIR validator |
| **User confusion with timeline UI** | Medium | User testing, tooltips, help documentation |

---

## Implementation Phases

### Phase 1: Core Timeline API (30 hours)

**Tasks**:
1. Create timeline API endpoints (`GET /api/timeline/{patient_id}`)
2. Implement TimelineService (document/concept queries)
3. Add timeline schemas (Pydantic models)
4. Write unit tests for timeline service
5. Write integration tests for timeline API

**Deliverables**:
- Working timeline API returning JSON data
- 80% test coverage

---

### Phase 2: Frontend Timeline Visualization (40 hours)

**Tasks**:
1. Create TimelineView.vue component
2. Implement D3.js timeline chart
3. Add document markers rendering
4. Add concept event rendering
5. Implement zoom/pan controls
6. Add filters (date, type, meta-annotations)
7. Write frontend unit tests

**Deliverables**:
- Interactive timeline visualization
- Filtering and zoom working
- 75% test coverage

---

### Phase 3: Export Functionality (30 hours)

**Tasks**:
1. Implement PDF export (ReportLab)
2. Implement JSON export
3. Implement FHIR R4 export
4. Add export API endpoint (`POST /api/timeline/{patient_id}/export`)
5. Add export UI controls
6. Test exports with sample data

**Deliverables**:
- PDF, JSON, FHIR exports working
- Download functionality tested

---

### Phase 4: Testing & Polish (24 hours)

**Tasks**:
1. E2E testing (Playwright)
2. Performance testing (100, 500, 1000 documents)
3. Accessibility audit (WCAG 2.1 AA)
4. User acceptance testing
5. Bug fixes
6. Documentation (user guide)

**Deliverables**:
- Production-ready timeline module
- User documentation
- Performance benchmarks met

---

### Phase 5: Deployment & Monitoring (20 hours)

**Tasks**:
1. Deploy to staging environment
2. Configure monitoring (logs, metrics)
3. Run staging tests
4. Deploy to production
5. Post-deployment verification
6. User training session

**Deliverables**:
- Timeline View deployed to production
- Monitoring dashboards created
- Users trained

---

**Total Effort**: 144 hours (5 weeks with 20% buffer)

**Dependencies**: Base Application (MVP) must be complete

**Approval**: Ready to proceed upon approval of this plan

---

**Document Version**: 1.0.0
**Last Updated**: 2025-11-18
**Status**: ✅ Ready for Implementation
**Approval**: Pending stakeholder sign-off
