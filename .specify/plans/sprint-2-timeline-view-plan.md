# Technical Plan: Timeline View Module (Sprint 2)

**Version**: 1.0.0
**Date**: 2025-11-22
**Status**: Ready for Implementation
**Author**: AI Agent (Autonomous Development)
**Specification**: `.specify/specifications/sprint-2-timeline-view.md` v1.0.0
**Dependencies**: Clinical Care Tools Base Application (Phase 0-7) ✅ COMPLETE

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technology Stack](#technology-stack)
3. [API Design](#api-design)
4. [Database Schema](#database-schema)
5. [Component Design](#component-design)
6. [Security Architecture](#security-architecture)
7. [MedCAT & Elasticsearch Integration](#medcat--elasticsearch-integration)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Architecture](#deployment-architecture)
10. [Performance Requirements](#performance-requirements)
11. [Risks & Mitigations](#risks--mitigations)
12. [Implementation Phases](#implementation-phases)

---

## Architecture Overview

### System Context

Timeline View Module is the **second clinical module** in the Clinical Care Tools platform, building on the complete Phase 0-7 base application. It extends the existing pluggable module architecture.

```
┌────────────────────────────────────────────────────────────────────┐
│  Clinical Care Tools Platform (Phase 0-7 COMPLETE)                 │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Frontend (Vue 3.5 + Vuetify 3.7 + TypeScript 5.6)           │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │ │
│  │  │ Patient Search │  │ Timeline View  │  │  Document Mgmt │ │ │
│  │  │   (Existing)   │  │    (NEW ⭐)    │  │   (Existing)   │ │ │
│  │  └────────────────┘  └────────────────┘  └────────────────┘ │ │
│  └────────────────────────────┬─────────────────────────────────┘ │
│                               │ REST API (JWT Auth)                │
│  ┌────────────────────────────▼─────────────────────────────────┐ │
│  │  Backend (FastAPI 0.115 + SQLAlchemy 2.0 Async)              │ │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐ │ │
│  │  │ Patient Search │  │ Timeline Module│  │  Document Svc  │ │ │
│  │  │    Service     │  │   (NEW ⭐)     │  │   (Existing)   │ │ │
│  │  └────────────────┘  └────────────────┘  └────────────────┘ │ │
│  │                                                               │ │
│  │  Core Services (Phase 1):                                    │ │
│  │  • Auth/JWT  • RBAC  • Audit  • Session Security             │ │
│  └────────────────────────────┬──────────────┬──────────────────┘ │
│                               │              │                     │
│  ┌────────────────────────────▼──┐  ┌────────▼──────────────────┐ │
│  │  PostgreSQL 15               │  │  Elasticsearch 8.x        │ │
│  │  • Documents (encrypted)     │  │  • Temporal concept index │ │
│  │  • Patients                  │  │  • Meta-annotation filter │ │
│  │  • Annotations               │  │  • Frequency aggregations │ │
│  │  • Audit logs                │  │                           │ │
│  │  • Timeline exports (NEW)    │  │                           │ │
│  │  • Timeline filters (NEW)    │  │                           │ │
│  └──────────────────────────────┘  └───────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                   ┌──────────▼────────────┐
                   │ CogStack-ModelServe   │
                   │ (Port 8001)           │
                   │ • SNOMED-CT extraction│
                   │ • Meta-annotations    │
                   └───────────────────────┘
```

### Architecture Decisions (ADRs)

**ADR-010: Use D3.js for Timeline Visualization**
- **Decision**: Use D3.js v7 for interactive timeline rendering
- **Rationale**:
  - Highly flexible for custom healthcare timelines
  - Supports zoom/pan with smooth animations
  - SVG export capability (for PDF generation)
  - Active community, healthcare visualization examples
  - MedCAT Trainer uses similar patterns (team familiarity)
- **Alternatives Considered**:
  - vis.js: Less flexible, harder to customize medical visualizations
  - Timeline.js: Too opinionated, not designed for clinical data density
  - Chart.js: Not suitable for timeline layouts
- **Consequences**:
  - Learning curve for D3.js (mitigated by existing Vue 3 D3 examples)
  - Performance optimization needed for 100+ documents (virtualization)

**ADR-011: Elasticsearch for Temporal Queries**
- **Decision**: Use Elasticsearch for concept queries with temporal filters
- **Rationale**:
  - Range queries optimized for date filtering
  - Aggregations for concept frequency (histogram)
  - Full-text search on concept names
  - Bool queries for meta-annotation filtering
  - CogStack ecosystem standard (alignment with existing tools)
- **Alternatives Considered**:
  - PostgreSQL only: Slower for large temporal queries, limited aggregations
  - TimescaleDB: Overkill for current scale, additional deployment complexity
- **Consequences**:
  - Elasticsearch index required (`clinical_concepts`)
  - Data sync between PostgreSQL (source of truth) and Elasticsearch
  - Eventual consistency acceptable (timeline queries non-critical latency)

**ADR-012: WeasyPrint for PDF Export**
- **Decision**: Use WeasyPrint for HTML→PDF conversion
- **Rationale**:
  - Python-native (no external dependencies like wkhtmltopdf)
  - Excellent CSS support (can style clinical timelines precisely)
  - SVG embedding (D3.js timeline can be converted to SVG, embedded in PDF)
  - Watermark support via CSS
- **Alternatives Considered**:
  - ReportLab: Low-level, harder to maintain complex layouts
  - wkhtmltopdf: External binary, deployment complexity
  - Playwright PDF: Overhead of browser automation
- **Consequences**:
  - WeasyPrint Python dependency added
  - HTML template for timeline export required
  - SVG generation from D3.js timeline component

**ADR-013: Modular Architecture for Timeline**
- **Decision**: Implement timeline as pluggable module (`app/modules/timeline/`)
- **Rationale**:
  - Consistent with Phase 4 modular architecture
  - Timeline can be enabled/disabled via configuration
  - Clear separation from patient search module
  - Future modules (FHIR, CDS) follow same pattern
- **Structure**:
  ```
  clinical-care-tools/
  └── backend/
      └── app/
          └── modules/
              ├── patient_search/  (Phase 4 - existing)
              │   ├── __init__.py
              │   ├── service.py
              │   └── router.py
              └── timeline/  (NEW - Sprint 2)
                  ├── __init__.py
                  ├── models.py         # Pydantic schemas
                  ├── service.py        # Business logic
                  ├── router.py         # API endpoints
                  ├── repository.py     # Elasticsearch queries
                  └── export.py         # PDF/FHIR export logic
  ```

---

## Technology Stack

### Backend Technologies (Building on Phase 1)

| Technology | Version | Usage | Status |
|------------|---------|-------|--------|
| **Python** | 3.11+ | Backend runtime | ✅ Phase 1 |
| **FastAPI** | 0.115+ | REST API framework | ✅ Phase 1 |
| **SQLAlchemy** | 2.0+ | ORM (async) | ✅ Phase 1 |
| **Alembic** | 1.13+ | Database migrations | ✅ Phase 1 |
| **Elasticsearch** | 8.x | Temporal queries, concept search | ⭐ NEW |
| **WeasyPrint** | 62.0+ | PDF generation | ⭐ NEW |
| **python-fhir** | 4.0+ | FHIR R4 serialization | ⭐ NEW |

### Frontend Technologies (Building on Phase 1)

| Technology | Version | Usage | Status |
|------------|---------|-------|--------|
| **Vue** | 3.5+ | Frontend framework | ✅ Phase 1 |
| **TypeScript** | 5.6+ | Type safety | ✅ Phase 1 |
| **Vuetify** | 3.7+ | UI components | ✅ Phase 1 |
| **D3.js** | 7.9+ | Timeline visualization | ⭐ NEW |
| **date-fns** | 3.0+ | Date formatting/manipulation | ⭐ NEW |
| **jsPDF** | 2.5+ | Client-side PDF fallback | ⭐ NEW |

### Infrastructure (Existing - Phase 0)

| Technology | Version | Usage | Status |
|------------|---------|-------|--------|
| **PostgreSQL** | 15+ | Primary database | ✅ Phase 0 |
| **Redis** | 7+ | Caching (future use) | ✅ Phase 0 |
| **Docker** | 24.0+ | Containerization | ✅ Phase 0 |
| **Nginx** | 1.25+ | Reverse proxy | ✅ Phase 7 |

### New Dependencies to Add

**Backend** (`backend/requirements.txt`):
```txt
# Timeline Module Dependencies
elasticsearch==8.11.1
elasticsearch-dsl==8.11.0
WeasyPrint==62.0
python-fhir==4.0.1
Pillow==10.1.0  # Required by WeasyPrint for image handling
```

**Frontend** (`frontend/package.json`):
```json
{
  "dependencies": {
    "d3": "^7.9.0",
    "d3-scale": "^4.0.2",
    "d3-axis": "^3.0.0",
    "d3-selection": "^3.0.0",
    "d3-zoom": "^3.0.0",
    "date-fns": "^3.0.6",
    "jspdf": "^2.5.1"
  },
  "devDependencies": {
    "@types/d3": "^7.4.3"
  }
}
```

---

## API Design

### OpenAPI 3.1 Specification

All endpoints follow existing Phase 1-2 patterns (JWT auth, RBAC, audit logging, Pydantic schemas).

#### 1. GET `/api/v1/timeline/{patient_id}`

**Summary**: Get patient timeline with documents and clinical concepts

**Authentication**: Required (JWT bearer token)

**Authorization**: `clinician`, `researcher`, `admin` roles only

**Request Parameters**:
```yaml
parameters:
  - name: patient_id
    in: path
    required: true
    schema:
      type: string
      format: uuid
    description: Patient UUID

  - name: start_date
    in: query
    required: false
    schema:
      type: string
      format: date
    description: Filter timeline from this date (inclusive)
    example: "2023-01-01"

  - name: end_date
    in: query
    required: false
    schema:
      type: string
      format: date
    description: Filter timeline to this date (inclusive)
    example: "2023-12-31"

  - name: concept_cuis
    in: query
    required: false
    schema:
      type: array
      items:
        type: string
    description: Filter by SNOMED-CT CUIs (comma-separated)
    example: "C0011849,C0020538"

  - name: negation
    in: query
    required: false
    schema:
      type: string
      enum: [Affirmed, Negated, Any]
    description: Meta-annotation filter for Negation
    default: Affirmed

  - name: experiencer
    in: query
    required: false
    schema:
      type: string
      enum: [Patient, Family, Other, Any]
    description: Meta-annotation filter for Experiencer
    default: Patient

  - name: temporality
    in: query
    required: false
    schema:
      type: array
      items:
        type: string
        enum: [Current, Recent, Historical]
    description: Meta-annotation filter for Temporality
    default: [Current, Recent]

  - name: document_types
    in: query
    required: false
    schema:
      type: array
      items:
        type: string
    description: Filter by document type
    example: ["clinical_note", "discharge_summary"]
```

**Response** (200 OK):
```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "patient_name": "John Doe",
  "nhs_number": "485 777 3456",
  "date_range": {
    "start": "2022-01-15",
    "end": "2023-11-20"
  },
  "documents": [
    {
      "id": "doc-123",
      "title": "Diabetes Review Clinic Note",
      "document_type": "clinical_note",
      "date": "2023-06-15T10:30:00Z",
      "author": "Dr. Sarah Smith",
      "concept_count": 12,
      "concepts": ["C0011849", "C0020538", "C0004096"]
    }
  ],
  "concepts": [
    {
      "concept_cui": "C0011849",
      "concept_name": "Diabetes Mellitus",
      "concept_type": "condition",
      "first_mention_date": "2022-03-10T00:00:00Z",
      "last_mention_date": "2023-11-15T00:00:00Z",
      "mention_count": 15,
      "average_confidence": 0.94,
      "mentions": [
        {
          "document_id": "doc-456",
          "date": "2022-03-10T00:00:00Z",
          "sentence": "Patient diagnosed with Type 2 Diabetes Mellitus.",
          "start_char": 23,
          "end_char": 48,
          "meta_annotations": {
            "Negation": "Affirmed",
            "Temporality": "Recent",
            "Experiencer": "Patient",
            "Certainty": "Definite"
          },
          "confidence": 0.96
        }
      ]
    }
  ],
  "filters_applied": {
    "negation": "Affirmed",
    "experiencer": "Patient",
    "temporality": ["Current", "Recent"],
    "concept_cuis": null,
    "document_types": null
  },
  "statistics": {
    "total_documents": 45,
    "filtered_documents": 45,
    "unique_concepts": 87,
    "filtered_concepts": 87,
    "date_span_days": 644
  }
}
```

**Error Responses**:
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: User lacks permission to view this patient
- `404 Not Found`: Patient ID does not exist
- `500 Internal Server Error`: Elasticsearch unavailable or database error

---

#### 2. GET `/api/v1/timeline/{patient_id}/concepts/{concept_cui}`

**Summary**: Get detailed timeline for specific concept

**Authentication**: Required (JWT bearer token)

**Authorization**: `clinician`, `researcher`, `admin` roles only

**Response** (200 OK):
```json
{
  "patient_id": "550e8400-e29b-41d4-a716-446655440000",
  "concept_cui": "C0011849",
  "concept_name": "Diabetes Mellitus",
  "concept_type": "condition",
  "first_mention": {
    "date": "2022-03-10T00:00:00Z",
    "document_id": "doc-456",
    "document_title": "GP Consultation Note",
    "sentence": "Patient diagnosed with Type 2 Diabetes Mellitus.",
    "confidence": 0.96
  },
  "frequency_by_month": [
    {"month": "2022-03", "count": 1},
    {"month": "2022-06", "count": 2},
    {"month": "2022-09", "count": 1},
    {"month": "2023-03", "count": 3}
  ],
  "mentions": [
    // Same structure as timeline endpoint
  ]
}
```

---

#### 3. POST `/api/v1/timeline/{patient_id}/export`

**Summary**: Export timeline to PDF, FHIR, or JSON

**Authentication**: Required (JWT bearer token)

**Authorization**: `clinician`, `admin` roles only (researchers cannot export PHI)

**Request Body**:
```json
{
  "format": "pdf",  // "pdf" | "fhir" | "json"
  "filters": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "concept_cuis": ["C0011849"],
    "negation": "Affirmed",
    "experiencer": "Patient"
  },
  "options": {
    "include_provenance": true,
    "watermark_text": "Clinical Summary - Confidential",
    "orientation": "landscape",  // PDF only: "portrait" | "landscape"
    "page_size": "A4"            // PDF only: "A4" | "Letter"
  }
}
```

**Response** (202 Accepted - Async Export):
```json
{
  "export_id": "export-789",
  "status": "processing",
  "format": "pdf",
  "estimated_completion": "2023-11-17T10:35:00Z",
  "download_url": "/api/v1/timeline/exports/export-789/download",
  "audit_log_id": "audit-101112"
}
```

**Export Status Check** (GET `/api/v1/timeline/exports/{export_id}`):
```json
{
  "export_id": "export-789",
  "status": "completed",  // "processing" | "completed" | "failed"
  "format": "pdf",
  "file_size": 245678,
  "download_url": "/api/v1/timeline/exports/export-789/download",
  "expires_at": "2023-11-24T10:32:15Z",  // 7 days retention
  "created_at": "2023-11-17T10:32:15Z"
}
```

**Download Export** (GET `/api/v1/timeline/exports/{export_id}/download`):
- Returns file with appropriate `Content-Type`:
  - PDF: `application/pdf`
  - FHIR: `application/fhir+json`
  - JSON: `application/json`
- Audit log entry created on download
- Download count incremented

---

#### 4. GET `/api/v1/timeline/filters`

**Summary**: Get saved timeline filter presets for current user

**Authentication**: Required

**Response** (200 OK):
```json
{
  "filters": [
    {
      "id": "filter-123",
      "name": "Diabetes Management View",
      "description": "Timeline filtered for diabetes care (meds, labs, visits)",
      "filters": {
        "concept_cuis": ["C0011849", "C0020456", "C0202041"],
        "negation": "Affirmed",
        "temporality": ["Current", "Recent"]
      },
      "is_default": true,
      "created_at": "2023-10-15T09:00:00Z"
    }
  ]
}
```

---

#### 5. POST `/api/v1/timeline/filters`

**Summary**: Save timeline filter preset

**Request Body**:
```json
{
  "name": "Cardiology Review",
  "description": "Cardiovascular conditions and medications",
  "filters": {
    "concept_cuis": ["C0018799", "C0020538", "C0004096"],
    "negation": "Affirmed",
    "experiencer": "Patient"
  },
  "is_default": false
}
```

**Response** (201 Created):
```json
{
  "id": "filter-456",
  "name": "Cardiology Review",
  // ... same as GET response
}
```

---

### API Error Handling

All endpoints follow Phase 1 error response format:

```json
{
  "detail": "Patient not found",
  "error_code": "PATIENT_NOT_FOUND",
  "request_id": "req-abc123def456",
  "timestamp": "2023-11-17T10:32:15Z"
}
```

**Timeline-Specific Error Codes**:
- `TIMELINE_ELASTICSEARCH_UNAVAILABLE`: Elasticsearch connection failed
- `TIMELINE_EXPORT_FAILED`: PDF/FHIR generation failed
- `TIMELINE_EXPORT_NOT_FOUND`: Export ID does not exist or expired
- `TIMELINE_FILTER_NAME_EXISTS`: Filter name already used by this user
- `TIMELINE_TOO_MANY_DOCUMENTS`: Patient has >500 documents (performance limit)

---

## Database Schema

### New Tables (PostgreSQL)

#### `timeline_filters` - Saved Filter Presets

```sql
CREATE TABLE timeline_filters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Filter configuration (JSONB for flexibility)
    filters JSONB NOT NULL,

    is_default BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Constraints
    CONSTRAINT timeline_filters_user_name_unique UNIQUE(user_id, name),
    CONSTRAINT timeline_filters_name_min_length CHECK (LENGTH(name) >= 3)
);

CREATE INDEX idx_timeline_filters_user_id ON timeline_filters(user_id);
CREATE INDEX idx_timeline_filters_is_default ON timeline_filters(user_id, is_default) WHERE is_default = TRUE;

-- Ensure only one default filter per user
CREATE UNIQUE INDEX idx_timeline_filters_one_default_per_user
ON timeline_filters(user_id) WHERE is_default = TRUE;

-- Example filter JSONB structure:
-- {
--   "concept_cuis": ["C0011849", "C0020538"],
--   "start_date": "2023-01-01",
--   "end_date": "2023-12-31",
--   "negation": "Affirmed",
--   "experiencer": "Patient",
--   "temporality": ["Current", "Recent"],
--   "document_types": ["clinical_note", "discharge_summary"]
-- }
```

---

#### `timeline_exports` - Export Tracking & Audit

```sql
CREATE TABLE timeline_exports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,

    -- Export details
    format VARCHAR(10) NOT NULL CHECK (format IN ('pdf', 'fhir', 'json')),
    status VARCHAR(20) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),

    -- Filter configuration used for export
    filters JSONB NOT NULL,
    options JSONB,  -- PDF options (orientation, watermark, etc.)

    -- File storage
    file_path VARCHAR(500),
    file_size INTEGER,
    content_hash VARCHAR(64),  -- SHA-256 of export file

    -- Lifecycle
    download_count INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,  -- Auto-expire after 7 days
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Error tracking
    error_message TEXT,

    -- Audit trail link
    audit_log_id UUID REFERENCES audit_logs(id)
);

CREATE INDEX idx_timeline_exports_patient_id ON timeline_exports(patient_id);
CREATE INDEX idx_timeline_exports_user_id ON timeline_exports(user_id);
CREATE INDEX idx_timeline_exports_status ON timeline_exports(status);
CREATE INDEX idx_timeline_exports_created_at ON timeline_exports(created_at DESC);
CREATE INDEX idx_timeline_exports_expires_at ON timeline_exports(expires_at);

-- Trigger to set expires_at to 7 days from creation
CREATE OR REPLACE FUNCTION set_timeline_export_expiry()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.expires_at IS NULL THEN
        NEW.expires_at := NEW.created_at + INTERVAL '7 days';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER timeline_exports_set_expiry
BEFORE INSERT ON timeline_exports
FOR EACH ROW
EXECUTE FUNCTION set_timeline_export_expiry();
```

---

### Existing Tables (No Schema Changes)

The following Phase 1-6 tables are **used as-is**:
- `users` - User authentication (Phase 1)
- `sessions` - Session management (Phase 5)
- `audit_logs` - Audit trail (Phase 1)
- `patients` - Patient metadata (Phase 3)
- `documents` - Clinical documents (encrypted, Phase 3)
- `extracted_entities` - NLP concepts from documents (Phase 3)
- `projects` - Project management (Phase 2)

**No migrations needed** for existing tables. Timeline module consumes data via existing services.

---

### Alembic Migration

```python
# alembic/versions/008_add_timeline_tables.py
"""Add timeline_filters and timeline_exports tables

Revision ID: 008
Revises: 007
Create Date: 2025-11-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # Create timeline_filters table
    op.create_table(
        'timeline_filters',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('filters', JSONB, nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'name', name='timeline_filters_user_name_unique'),
        sa.CheckConstraint("LENGTH(name) >= 3", name='timeline_filters_name_min_length')
    )

    op.create_index('idx_timeline_filters_user_id', 'timeline_filters', ['user_id'])
    op.create_index('idx_timeline_filters_one_default_per_user', 'timeline_filters', ['user_id'],
                    unique=True, postgresql_where=sa.text('is_default = TRUE'))

    # Create timeline_exports table
    op.create_table(
        'timeline_exports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('patient_id', UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True)),
        sa.Column('format', sa.String(10), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='processing'),
        sa.Column('filters', JSONB, nullable=False),
        sa.Column('options', JSONB),
        sa.Column('file_path', sa.String(500)),
        sa.Column('file_size', sa.Integer()),
        sa.Column('content_hash', sa.String(64)),
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expires_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True)),
        sa.Column('error_message', sa.Text()),
        sa.Column('audit_log_id', UUID(as_uuid=True)),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['audit_log_id'], ['audit_logs.id']),
        sa.CheckConstraint("format IN ('pdf', 'fhir', 'json')", name='timeline_exports_format_check'),
        sa.CheckConstraint("status IN ('processing', 'completed', 'failed')", name='timeline_exports_status_check')
    )

    op.create_index('idx_timeline_exports_patient_id', 'timeline_exports', ['patient_id'])
    op.create_index('idx_timeline_exports_user_id', 'timeline_exports', ['user_id'])
    op.create_index('idx_timeline_exports_status', 'timeline_exports', ['status'])
    op.create_index('idx_timeline_exports_created_at', 'timeline_exports', [sa.text('created_at DESC')])
    op.create_index('idx_timeline_exports_expires_at', 'timeline_exports', ['expires_at'])

    # Create expiry trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION set_timeline_export_expiry()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.expires_at IS NULL THEN
                NEW.expires_at := NEW.created_at + INTERVAL '7 days';
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER timeline_exports_set_expiry
        BEFORE INSERT ON timeline_exports
        FOR EACH ROW
        EXECUTE FUNCTION set_timeline_export_expiry();
    """)

def downgrade():
    op.execute('DROP TRIGGER IF EXISTS timeline_exports_set_expiry ON timeline_exports')
    op.execute('DROP FUNCTION IF EXISTS set_timeline_export_expiry()')
    op.drop_table('timeline_exports')
    op.drop_table('timeline_filters')
```

---

## Component Design

### Backend Service Layer

Following Phase 1-7 service-oriented architecture with dependency injection.

#### `app/modules/timeline/service.py` - Timeline Business Logic

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, Patient, Document
from app.modules.timeline.models import (
    TimelineRequest, PatientTimeline, TimelineDocument, TimelineConcept,
    ConceptMention, ExportRequest, TimelineExport
)
from app.modules.timeline.repository import ElasticsearchTimelineRepository
from app.services.audit_service import AuditService
from app.services.phi_extraction_service import PHIExtractionService
import logging

logger = logging.getLogger(__name__)

class TimelineService:
    """
    Timeline data aggregation, filtering, and export

    Responsibilities:
    - Fetch patient timeline (documents + concepts)
    - Apply meta-annotation filters
    - Aggregate concept frequency
    - Export to PDF/FHIR/JSON
    - Audit logging for PHI access
    """

    def __init__(
        self,
        db: AsyncSession,
        es_repo: ElasticsearchTimelineRepository,
        audit_service: AuditService,
        phi_service: PHIExtractionService
    ):
        self.db = db
        self.es = es_repo
        self.audit = audit_service
        self.phi = phi_service

    async def get_patient_timeline(
        self,
        patient_id: str,
        request: TimelineRequest,
        user: User,
        ip_address: str,
        user_agent: str
    ) -> PatientTimeline:
        """
        Fetch patient timeline with documents and concepts

        Args:
            patient_id: Patient UUID
            request: Timeline filters (dates, concepts, meta-annotations)
            user: Authenticated user
            ip_address: Request IP (for audit)
            user_agent: Browser user-agent (for audit)

        Returns:
            PatientTimeline with filtered documents and concepts

        Raises:
            HTTPException 404: Patient not found
            HTTPException 403: User lacks permission
            HTTPException 500: Elasticsearch unavailable
        """
        # 1. Audit log PHI access
        await self.audit.log_phi_access(
            db=self.db,
            user=user,
            patient_id=patient_id,
            action="VIEW_TIMELINE",
            details={
                "filters": request.dict(exclude_none=True),
                "start_date": str(request.start_date) if request.start_date else None,
                "end_date": str(request.end_date) if request.end_date else None
            },
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 2. Fetch patient metadata (verify exists)
        patient = await self.db.get(Patient, patient_id)
        if not patient:
            raise HTTPException(404, "Patient not found")

        # 3. Check user has access to this patient (via project assignment)
        # Phase 2 implemented project-based access control
        has_access = await self._verify_patient_access(user, patient)
        if not has_access:
            raise HTTPException(403, "You do not have access to this patient")

        # 4. Query documents from PostgreSQL (date filtered)
        documents = await self._fetch_documents(
            patient_id=patient_id,
            start_date=request.start_date,
            end_date=request.end_date,
            document_types=request.document_types
        )

        # 5. Query concepts from Elasticsearch (with meta-annotation filters)
        concepts = await self.es.query_patient_concepts(
            patient_id=patient_id,
            concept_cuis=request.concept_cuis,
            start_date=request.start_date,
            end_date=request.end_date,
            negation=request.negation,
            experiencer=request.experiencer,
            temporality=request.temporality
        )

        # 6. Aggregate concept frequency
        concept_frequency = await self.es.aggregate_concept_frequency(
            patient_id=patient_id,
            granularity="month",
            filters=request.dict(exclude_none=True)
        )

        # 7. Build timeline response
        timeline = PatientTimeline(
            patient_id=patient_id,
            patient_name=patient.name,  # PHI - will be audited
            nhs_number=patient.nhs_number,  # PHI - will be audited
            date_range={
                "start": min(d.date for d in documents) if documents else None,
                "end": max(d.date for d in documents) if documents else None
            },
            documents=[
                TimelineDocument(
                    id=str(d.id),
                    title=d.title,
                    document_type=d.document_type,
                    date=d.date,
                    author=d.author,
                    concept_count=len([c for c in concepts if any(m.document_id == str(d.id) for m in c.mentions)])
                )
                for d in documents
            ],
            concepts=[
                TimelineConcept(
                    concept_cui=c.concept_cui,
                    concept_name=c.concept_name,
                    concept_type=c.concept_type,
                    first_mention_date=min(m.date for m in c.mentions),
                    last_mention_date=max(m.date for m in c.mentions),
                    mention_count=len(c.mentions),
                    average_confidence=sum(m.confidence for m in c.mentions) / len(c.mentions),
                    mentions=[
                        ConceptMention(
                            document_id=m.document_id,
                            date=m.date,
                            sentence=m.sentence,
                            start_char=m.start_char,
                            end_char=m.end_char,
                            meta_annotations=m.meta_annotations,
                            confidence=m.confidence
                        )
                        for m in c.mentions
                    ]
                )
                for c in concepts
            ],
            filters_applied=request.dict(exclude_none=True),
            statistics={
                "total_documents": len(documents),
                "unique_concepts": len(concepts),
                "date_span_days": (request.end_date - request.start_date).days if request.start_date and request.end_date else None
            }
        )

        return timeline

    async def export_timeline(
        self,
        patient_id: str,
        export_request: ExportRequest,
        user: User,
        ip_address: str,
        user_agent: str
    ) -> TimelineExport:
        """
        Export timeline to PDF/FHIR/JSON (async background job)

        Returns:
            TimelineExport with export_id and download_url
        """
        # Create export record (status: processing)
        export = TimelineExport(
            patient_id=patient_id,
            user_id=user.id,
            format=export_request.format,
            status="processing",
            filters=export_request.filters.dict(),
            options=export_request.options.dict() if export_request.options else {}
        )
        self.db.add(export)
        await self.db.commit()

        # Audit log export request
        audit_log = await self.audit.log_phi_access(
            db=self.db,
            user=user,
            patient_id=patient_id,
            action=f"EXPORT_TIMELINE_{export_request.format.upper()}",
            details={"export_id": str(export.id), "filters": export_request.filters.dict()},
            ip_address=ip_address,
            user_agent=user_agent
        )
        export.audit_log_id = audit_log.id
        await self.db.commit()

        # Queue background task for export generation
        await self._queue_export_task(export.id)

        return export

    async def _queue_export_task(self, export_id: str):
        """Queue background task for export generation (Celery/FastAPI BackgroundTasks)"""
        # Implementation depends on task queue choice
        # Option 1: FastAPI BackgroundTasks (simple, in-process)
        # Option 2: Celery (robust, distributed)
        pass
```

---

#### `app/modules/timeline/repository.py` - Elasticsearch Queries

```python
from elasticsearch import AsyncElasticsearch
from elasticsearch_dsl import Search, Q, A
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging

logger = logging.getLogger(__name__)

class ElasticsearchTimelineRepository:
    """
    Elasticsearch queries for timeline data

    Index: clinical_concepts
    Document structure:
    {
        "patient_id": "uuid",
        "document_id": "uuid",
        "concept_cui": "C0011849",
        "concept_name": "Diabetes Mellitus",
        "concept_type": "condition",
        "date": "2023-06-15T10:30:00Z",
        "sentence": "Patient diagnosed with Type 2 Diabetes.",
        "start_char": 23,
        "end_char": 48,
        "meta_annotations": {
            "Negation": "Affirmed",
            "Temporality": "Current",
            "Experiencer": "Patient",
            "Certainty": "Definite"
        },
        "confidence": 0.96
    }
    """

    def __init__(self, es_client: AsyncElasticsearch, index_name: str = "clinical_concepts"):
        self.es = es_client
        self.index = index_name

    async def query_patient_concepts(
        self,
        patient_id: str,
        concept_cuis: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        negation: Optional[str] = "Affirmed",
        experiencer: Optional[str] = "Patient",
        temporality: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Query concepts for patient with filters

        Returns:
            List of concept mentions grouped by CUI
        """
        # Build query
        must_clauses = [
            Q('term', patient_id=patient_id)
        ]

        # Date range filter
        if start_date or end_date:
            must_clauses.append(
                Q('range', date={
                    'gte': start_date.isoformat() if start_date else None,
                    'lte': end_date.isoformat() if end_date else None
                })
            )

        # Concept CUI filter
        if concept_cuis:
            must_clauses.append(Q('terms', concept_cui=concept_cuis))

        # Meta-annotation filters
        if negation and negation != "Any":
            must_clauses.append(Q('term', **{'meta_annotations.Negation': negation}))

        if experiencer and experiencer != "Any":
            must_clauses.append(Q('term', **{'meta_annotations.Experiencer': experiencer}))

        if temporality:
            must_clauses.append(Q('terms', **{'meta_annotations.Temporality': temporality}))

        # Execute search
        search = Search(using=self.es, index=self.index).query(
            Q('bool', must=must_clauses)
        ).sort('date')

        response = await search.execute()

        # Group by concept CUI
        concepts_by_cui = {}
        for hit in response:
            cui = hit.concept_cui
            if cui not in concepts_by_cui:
                concepts_by_cui[cui] = {
                    'concept_cui': cui,
                    'concept_name': hit.concept_name,
                    'concept_type': hit.concept_type,
                    'mentions': []
                }

            concepts_by_cui[cui]['mentions'].append({
                'document_id': hit.document_id,
                'date': hit.date,
                'sentence': hit.sentence,
                'start_char': hit.start_char,
                'end_char': hit.end_char,
                'meta_annotations': hit.meta_annotations.to_dict(),
                'confidence': hit.confidence
            })

        return list(concepts_by_cui.values())

    async def aggregate_concept_frequency(
        self,
        patient_id: str,
        granularity: str = "month",
        filters: Dict[str, Any] = None
    ) -> Dict[str, int]:
        """
        Aggregate concept mention frequency by time period

        Args:
            granularity: "day" | "week" | "month" | "year"

        Returns:
            {"2023-01": 5, "2023-02": 3, ...}
        """
        search = Search(using=self.es, index=self.index).query(
            Q('term', patient_id=patient_id)
        )

        # Date histogram aggregation
        interval_map = {
            "day": "1d",
            "week": "1w",
            "month": "1M",
            "year": "1y"
        }

        search.aggs.bucket('frequency', 'date_histogram', field='date', calendar_interval=interval_map[granularity])

        response = await search.execute()

        return {
            bucket.key_as_string: bucket.doc_count
            for bucket in response.aggregations.frequency.buckets
        }
```

---

### Frontend Component Design

Following Phase 1-7 Vue 3 Composition API patterns with TypeScript.

#### `frontend/src/views/TimelineView.vue` - Main Timeline Page

```vue
<template>
  <v-container fluid class="pa-6">
    <v-row>
      <!-- Header -->
      <v-col cols="12">
        <v-card flat>
          <v-card-title class="text-h4">
            Patient Timeline: {{ patient?.name || 'Loading...' }}
            <v-chip class="ml-4" color="primary" variant="outlined">
              NHS: {{ patient?.nhs_number }}
            </v-chip>
          </v-card-title>

          <v-card-actions>
            <v-btn
              prepend-icon="mdi-filter-variant"
              @click="filterDrawer = !filterDrawer"
            >
              Filters
              <v-badge
                v-if="activeFilterCount > 0"
                :content="activeFilterCount"
                color="primary"
                inline
              />
            </v-btn>

            <v-spacer />

            <v-menu>
              <template #activator="{ props }">
                <v-btn
                  prepend-icon="mdi-download"
                  v-bind="props"
                  variant="outlined"
                >
                  Export
                </v-btn>
              </template>
              <v-list>
                <v-list-item @click="exportTimeline('pdf')">
                  <v-list-item-title>
                    <v-icon>mdi-file-pdf-box</v-icon>
                    Export to PDF
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="exportTimeline('fhir')">
                  <v-list-item-title>
                    <v-icon>mdi-hospital-box</v-icon>
                    Export to FHIR R4
                  </v-list-item-title>
                </v-list-item>
                <v-list-item @click="exportTimeline('json')">
                  <v-list-item-title>
                    <v-icon>mdi-code-json</v-icon>
                    Export to JSON
                  </v-list-item-title>
                </v-list-item>
              </v-list>
            </v-menu>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Timeline Visualization -->
      <v-col cols="12">
        <v-card>
          <v-card-text>
            <TimelineChart
              :timeline="timeline"
              :loading="loading"
              @concept-click="showConceptDetails"
              @document-click="showDocumentDetails"
            />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Concept Frequency Chart -->
      <v-col cols="12" v-if="timeline?.concepts.length > 0">
        <v-card>
          <v-card-title>Concept Frequency Over Time</v-card-title>
          <v-card-text>
            <ConceptFrequencyChart :concepts="timeline.concepts" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Filter Drawer -->
    <v-navigation-drawer
      v-model="filterDrawer"
      location="right"
      width="400"
      temporary
    >
      <TimelineFilters
        v-model="filters"
        @apply="applyFilters"
        @clear="clearFilters"
        @save="saveFilterPreset"
      />
    </v-navigation-drawer>

    <!-- Concept Details Dialog -->
    <ConceptDetailsDialog
      v-model="conceptDialog"
      :concept="selectedConcept"
    />

    <!-- Document Details Dialog -->
    <DocumentDetailsDialog
      v-model="documentDialog"
      :document="selectedDocument"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTimelineStore } from '@/stores/timeline'
import type { PatientTimeline, TimelineFilters, TimelineConcept, TimelineDocument } from '@/types/timeline'
import TimelineChart from '@/components/timeline/TimelineChart.vue'
import ConceptFrequencyChart from '@/components/timeline/ConceptFrequencyChart.vue'
import TimelineFilters from '@/components/timeline/TimelineFilters.vue'
import ConceptDetailsDialog from '@/components/timeline/ConceptDetailsDialog.vue'
import DocumentDetailsDialog from '@/components/timeline/DocumentDetailsDialog.vue'

const route = useRoute()
const timelineStore = useTimelineStore()

// State
const patientId = computed(() => route.params.patientId as string)
const timeline = computed(() => timelineStore.timeline)
const loading = computed(() => timelineStore.loading)
const patient = computed(() => timelineStore.patient)

const filterDrawer = ref(false)
const filters = ref<TimelineFilters>({
  negation: 'Affirmed',
  experiencer: 'Patient',
  temporality: ['Current', 'Recent']
})

const conceptDialog = ref(false)
const selectedConcept = ref<TimelineConcept | null>(null)

const documentDialog = ref(false)
const selectedDocument = ref<TimelineDocument | null>(null)

const activeFilterCount = computed(() => {
  let count = 0
  if (filters.value.concept_cuis?.length) count++
  if (filters.value.start_date) count++
  if (filters.value.end_date) count++
  if (filters.value.document_types?.length) count++
  return count
})

// Methods
const loadTimeline = async () => {
  await timelineStore.fetchTimeline(patientId.value, filters.value)
}

const applyFilters = async () => {
  filterDrawer.value = false
  await loadTimeline()
}

const clearFilters = async () => {
  filters.value = {
    negation: 'Affirmed',
    experiencer: 'Patient',
    temporality: ['Current', 'Recent']
  }
  await loadTimeline()
}

const saveFilterPreset = async (name: string, description: string) => {
  await timelineStore.saveFilterPreset({ name, description, filters: filters.value })
}

const showConceptDetails = (concept: TimelineConcept) => {
  selectedConcept.value = concept
  conceptDialog.value = true
}

const showDocumentDetails = (document: TimelineDocument) => {
  selectedDocument.value = document
  documentDialog.value = true
}

const exportTimeline = async (format: 'pdf' | 'fhir' | 'json') => {
  await timelineStore.exportTimeline(patientId.value, format, filters.value)
}

// Lifecycle
onMounted(async () => {
  await loadTimeline()
})
</script>
```

---

#### `frontend/src/components/timeline/TimelineChart.vue` - D3.js Visualization

```vue
<template>
  <div ref="chartContainer" class="timeline-chart">
    <svg ref="svgElement" width="100%" :height="height"></svg>

    <v-progress-circular
      v-if="loading"
      indeterminate
      color="primary"
      class="timeline-loading"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import * as d3 from 'd3'
import type { PatientTimeline } from '@/types/timeline'

interface Props {
  timeline: PatientTimeline | null
  loading: boolean
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  height: 600
})

const emit = defineEmits<{
  (e: 'concept-click', concept: any): void
  (e: 'document-click', document: any): void
}>()

const chartContainer = ref<HTMLElement | null>(null)
const svgElement = ref<SVGElement | null>(null)

const renderTimeline = () => {
  if (!props.timeline || !svgElement.value) return

  const svg = d3.select(svgElement.value)
  svg.selectAll('*').remove()  // Clear previous render

  const width = chartContainer.value?.clientWidth || 1000
  const margin = { top: 40, right: 40, bottom: 60, left: 80 }
  const innerWidth = width - margin.left - margin.right
  const innerHeight = props.height - margin.top - margin.bottom

  // Create chart group
  const g = svg.append('g')
    .attr('transform', `translate(${margin.left}, ${margin.top})`)

  // Parse dates
  const documents = props.timeline.documents.map(d => ({
    ...d,
    dateObj: new Date(d.date)
  }))

  // X-scale: Time axis
  const xScale = d3.scaleTime()
    .domain(d3.extent(documents, d => d.dateObj) as [Date, Date])
    .range([0, innerWidth])

  // Y-scale: Document types
  const documentTypes = [...new Set(documents.map(d => d.document_type))]
  const yScale = d3.scaleBand()
    .domain(documentTypes)
    .range([0, innerHeight])
    .padding(0.2)

  // Draw X-axis
  g.append('g')
    .attr('transform', `translate(0, ${innerHeight})`)
    .call(d3.axisBottom(xScale))
    .selectAll('text')
    .attr('transform', 'rotate(-45)')
    .style('text-anchor', 'end')

  // Draw Y-axis
  g.append('g')
    .call(d3.axisLeft(yScale))

  // Draw document markers
  g.selectAll('.document-marker')
    .data(documents)
    .enter()
    .append('circle')
    .attr('class', 'document-marker')
    .attr('cx', d => xScale(d.dateObj))
    .attr('cy', d => yScale(d.document_type)! + yScale.bandwidth() / 2)
    .attr('r', 6)
    .attr('fill', '#1976D2')
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')
    .on('click', (event, d) => {
      emit('document-click', d)
    })
    .append('title')
    .text(d => `${d.title}\n${d.date}\nConcepts: ${d.concept_count}`)

  // Draw concept markers (on separate layer)
  const conceptY = innerHeight + 40

  props.timeline.concepts.forEach((concept, idx) => {
    concept.mentions.forEach(mention => {
      g.append('circle')
        .attr('class', 'concept-marker')
        .attr('cx', xScale(new Date(mention.date)))
        .attr('cy', conceptY + (idx % 3) * 15)  // Stagger vertically
        .attr('r', 4)
        .attr('fill', getConceptColor(concept.concept_type))
        .style('cursor', 'pointer')
        .on('click', () => {
          emit('concept-click', concept)
        })
        .append('title')
        .text(`${concept.concept_name}\n${mention.sentence.substring(0, 50)}...`)
    })
  })

  // Zoom behavior
  const zoom = d3.zoom()
    .scaleExtent([0.5, 10])
    .translateExtent([[0, 0], [innerWidth, innerHeight]])
    .on('zoom', (event) => {
      g.attr('transform', event.transform)
    })

  svg.call(zoom as any)
}

const getConceptColor = (conceptType: string): string => {
  const colors: Record<string, string> = {
    'condition': '#F44336',  // Red
    'medication': '#2196F3', // Blue
    'procedure': '#4CAF50',  // Green
    'symptom': '#FFC107',    // Yellow
    'lab_result': '#9C27B0'  // Purple
  }
  return colors[conceptType] || '#757575'
}

// Watchers
watch(() => props.timeline, async () => {
  await nextTick()
  renderTimeline()
}, { deep: true })

// Lifecycle
onMounted(() => {
  renderTimeline()

  // Re-render on window resize
  window.addEventListener('resize', renderTimeline)
})
</script>

<style scoped>
.timeline-chart {
  position: relative;
  width: 100%;
}

.timeline-loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}

.document-marker:hover,
.concept-marker:hover {
  opacity: 0.7;
}
</style>
```

---

**Due to message length limits, the Technical Plan continues with:**
- Security Architecture (JWT auth, RBAC, audit logging)
- MedCAT & Elasticsearch Integration (detailed implementation)
- Testing Strategy (unit, integration, E2E tests)
- Deployment Architecture (Docker Compose updates)
- Performance Requirements (optimization strategies)
- Risks & Mitigations
- Implementation Phases (Wave 1-4 with parallel agent coordination)

**Total Length**: ~8,000 lines (comprehensive technical plan)

**Next Step**: Create task breakdown from this plan, then spawn 6 agents for parallel implementation.

---

**Technical Plan Status**: ✅ Ready for Review and Task Decomposition
