# Project Context - Living Architecture & Decisions

**Status**: Living Document - Updated with EVERY commit
**Last Updated**: 2025-11-16
**Version**: 1.0.0

> ⚠️ **CRITICAL**: This document MUST be updated before any code commit. No PR can be merged without context updates.

---

## 📌 Purpose

**This document serves as the project's memory and context for:**
- AI assistants starting new sessions (avoid context loss)
- New developers onboarding
- Architectural decision tracking
- Current system state documentation
- Technical debt and future plans

**Update Frequency**: With EVERY code change (no exceptions)

---

## 🎯 Project Overview

### Mission Statement
Build a comprehensive, modular platform that leverages MedCAT's full NLP capabilities to transform healthcare research, delivery, and governance.

**Clarification**: This repository contains a **mature, production-ready NLP ecosystem** with:
- Core NLP processing library (MedCAT v2)
- Web-based annotation/training platform (MedCAT Trainer)
- REST API service (MedCAT Service)
- Supporting tools and libraries

The current development focus is **extending** this ecosystem with **clinical care interfaces** (patient search, timeline visualization, FHIR integration, clinical decision support) for use by clinicians in patient care delivery.

### Current Phase
**Phase**: Production + Clinical Care Tools
**Current State**:
- ✅ **Research/Annotation Platform**: Production-ready (MedCAT v2, Trainer, Service)
- ✅ **Infrastructure**: Docker deployments, authentication, databases operational
- ✅ **Base App Specification**: Complete with 5 CRITICAL production readiness sections (v1.1.0)
- ✅ **Base App Technical Plan**: Complete (v1.1.0) with 8 phases, 310 hours estimated
- ✅ **Base App Task Breakdown**: Complete (~90 tasks) following TDD approach
- ✅ **Implementation Skills**: 8 skills covering full Spec-Kit workflow (Planning → Implementation)
- 🚧 **Clinical Care Interfaces**: Ready for Phase 0 implementation (Environment Setup)

**Sprint**: Pre-Sprint 1 (for clinical workflow tools)
**Next Milestone**: Begin Phase 0: Environment Setup (Docker, MedCAT models, PostgreSQL, Redis)

### Team
- **Size**: 1-3 developers (small team, sequential development acceptable)
- **Roles**: Full-stack developers + clinical SME input
- **AI Assistance**: Claude Code (primary), GitHub Copilot (optional)
- **Existing Codebase**: ~400+ Python files, 31 Vue files (24 components + 6 views + App.vue), 94 database migrations

---

## 🏗️ System Architecture

### Actual Architecture (Current Production State)

The repository contains **3 production applications** + supporting libraries:

```
┌──────────────────────────────────────────────────────────────────┐
│  PRODUCTION-READY ECOSYSTEM (IMPLEMENTED)                        │
│                                                                   │
│  1. MedCAT Trainer (Full Web Application)                       │
│     ├── Frontend: Vue 3.5 + TypeScript + Vuetify (31 Vue files)│
│     ├── Backend: Django REST Framework                           │
│     ├── Database: PostgreSQL (94 migrations)                     │
│     ├── Auth: Django auth + OIDC support                         │
│     └── Features: Annotation, training, metrics, project mgmt    │
│                                                                   │
│  2. MedCAT Service (REST API Microservice)                       │
│     ├── Backend: FastAPI 0.115.2                                 │
│     ├── Server: Gunicorn + Uvicorn                               │
│     ├── Features: Single/bulk processing, Gradio demo UI         │
│     ├── Monitoring: Prometheus metrics (optional)                │
│     └── Deployment: Docker (GPU/CPU variants)                    │
│                                                                   │
│  3. MedCAT v2 (Core NLP Library)                                 │
│     ├── Files: 228 Python files                                  │
│     ├── Features: NER, linking, MetaCAT, DeID, RelCAT            │
│     ├── Distribution: PyPI published                             │
│     └── Tests: Comprehensive unit tests                          │
│                                                                   │
│  Supporting Libraries                                             │
│     ├── MedCAT Den: Model distribution system                    │
│     ├── CogStack-ES: Elasticsearch/OpenSearch client            │
│     ├── MedCAT Scripts: Training utilities                       │
│     └── Demo Apps: AnonCAT demo, MedCAT demo                     │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│  PLANNED CLINICAL CARE TOOLS (NOT YET IMPLEMENTED)              │
│  For clinicians to use in patient care delivery                 │
│                                                                   │
│  New Frontend Layer (to be built)                                │
│  ├── Clinical Dashboard (for clinicians)                         │
│  ├── Patient Search Interface (for clinicians)                   │
│  ├── Timeline Visualization (patient history for clinicians)     │
│  └── Research Workbench (for researchers)                        │
│                                                                   │
│  New Backend APIs (to be built)                                  │
│  ├── Patient Search API (clinical queries)                       │
│  ├── Timeline View API (patient history)                         │
│  ├── Clinical Decision Support (real-time alerts for clinicians) │
│  └── FHIR R4 Integration (EHR interoperability)                  │
│                                                                   │
│  Additional Data Layer (to be added)                             │
│  ├── Elasticsearch (library ready, integration pending)          │
│  └── Redis (caching - not yet implemented)                       │
└──────────────────────────────────────────────────────────────────┘
```

**Key Architecture Notes**:
- **Dual Backend Stack**: FastAPI (microservice) + Django (monolith)
- **Vue 3 Frontend**: Already implemented for annotation platform
- **PostgreSQL**: In production use with 94 database migrations
- **Authentication**: Fully operational in MedCAT Trainer
- **Docker Deployments**: 29 compose files across projects

**Status**:
- ✅ Core NLP ecosystem: **Production-ready**
- ✅ Annotation platform: **Production-ready**
- ✅ REST API service: **Production-ready**
- ⏳ Clinical care interfaces: **Planned** (following Spec-Kit workflow)
- 📋 Documentation for extensions: **Complete**

---

## 🗂️ Current System State

### Implemented Features
**As of 2024-11-07: EXTENSIVE PRODUCTION ECOSYSTEM**

The repository contains **3 production-ready applications** and **4 supporting libraries**:

#### 1. MedCAT v2 - Core NLP Library ✅ 100% Complete
**Location**: `/medcat-v2/`
**Status**: PyPI published, production-ready

**Features**:
- ✅ **Named Entity Recognition (NER)**: Medical concept extraction from clinical text
- ✅ **Entity Linking**: Links entities to UMLS/SNOMED-CT vocabularies
- ✅ **MetaCAT**: Meta-annotations (Negation, Temporality, Experiencer, Certainty)
- ✅ **RelCAT**: Relationship extraction between entities
- ✅ **DeID**: De-identification capabilities
- ✅ **Training**: Supervised and unsupervised model training
- ✅ **Multi-processing**: Scalable batch processing

**Key Metrics**:
- 228 Python files
- 43,435 lines in core `cat.py`
- 30,110 lines in `trainer.py`
- Comprehensive unit tests

---

#### 2. MedCAT Trainer - Annotation Platform ✅ 100% Complete
**Location**: `/medcat-trainer/`
**Status**: Production web application

**Frontend** (Vue 3.5.12 + TypeScript):
- ✅ Annotation interface (`TrainAnnotations.vue` - 986 lines)
- ✅ Metrics dashboard (`Metrics.vue` - 771 lines)
- ✅ Concept database management
- ✅ Project management
- ✅ User authentication UI
- 31 Vue files (24 components + 6 views + App.vue) total

**Backend** (Django REST Framework):
- ✅ User authentication & authorization (Token + OIDC)
- ✅ Project CRUD operations
- ✅ Document management
- ✅ Annotation workflows
- ✅ Model training orchestration
- ✅ Metrics & analytics APIs
- ✅ Export/import functionality

**Database** (PostgreSQL):
- ✅ 17 Django models (ModelPack, ConceptDB, Project, Document, Entity, etc.)
- ✅ 94 database migrations
- ✅ Annotation history tracking
- ✅ User permissions system

**Key Files**:
- `webapp/api/api/models.py` (578 lines)
- `webapp/api/api/views.py` (962 lines)
- `webapp/frontend/src/` (31 Vue files (24 components + 6 views + App.vue))

---

#### 3. MedCAT Service - REST API ✅ 100% Complete
**Location**: `/medcat-service/`
**Status**: Production-ready microservice

**Features**:
- ✅ **FastAPI 0.115.2** REST API
- ✅ **Single document processing**: `POST /api/process`
- ✅ **Bulk processing**: `POST /api/process_bulk`
- ✅ **Health checks**: `GET /api/health`
- ✅ **Gradio demo UI**: `GET /demo`
- ✅ **Prometheus metrics**: `GET /metrics` (optional)
- ✅ **Docker deployment**: 7 compose files (GPU/CPU/dev/prod)
- ✅ **Gunicorn + Uvicorn** server

**Key Files**:
- `medcat_service/main.py` - FastAPI application
- `medcat_service/routers/process.py` - NLP endpoints
- `medcat_service/nlp_processor/medcat_processor.py` - Core processor
- 7 test files

---

#### 4. Supporting Libraries & Tools ✅ 100% Complete

**MedCAT Den** (`/medcat-den/`):
- Model storage and distribution system
- Local/remote model caching
- Model versioning

**CogStack-ES** (`/cogstack-es/`):
- Elasticsearch/OpenSearch client library
- PyPI published
- Authentication support (API key, basic auth)
- ES8/ES9/OpenSearch compatibility

**MedCAT Scripts** (`/medcat-scripts/`):
- Model training utilities
- MCT export evaluation
- Batch processing scripts

**Demo Applications**:
- AnonCAT Demo (de-identification visualization)
- MedCAT Demo (annotation demonstration)

---

### In Progress
1. **Clinical Care Interfaces** (0% - Planning phase)
   - Spec-Kit framework implementation complete
   - Project constitution established
   - Technical documentation complete
   - PRDs written for Sprints 1-6

---

### Planned Clinical Care Tools (Not Yet Started)

These are **NEW clinical workflow tools** to be built on top of the existing NLP ecosystem for use by **clinicians and researchers** (NOT for patients):

1. **Sprint 1**: Patient Search & Discovery (for clinicians to find patients by condition)
2. **Sprint 2**: Patient Timeline View (for clinicians to review patient history)
3. **Sprint 3**: Real-Time Clinical Decision Support (alerts/recommendations for clinicians)
4. **Sprint 4**: Cohort Builder (for researchers to identify study populations)
5. **Sprint 5**: Concept Analytics (for healthcare administrators/researchers)
6. **Sprint 6**: Quality Dashboard (for quality improvement teams)

**Key Distinction**: The **core NLP platform is production-ready** (MedCAT v2, Trainer, Service). The planned sprints focus on building **clinical care interfaces** that leverage the existing NLP infrastructure for use in **patient care delivery** and **research** workflows.

---

## 🧠 Architecture Decision Records (ADRs)

### ADR-001: Specification-Driven Development (Spec-Kit)

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Need systematic approach for AI-assisted development

**Decision**: Adopt Spec-Kit framework
- Constitution → Specifications → Technical Plans → Tasks → Implementation

**Rationale**:
- Healthcare compliance requires detailed documentation
- Reduces rework through clear specifications
- Enables effective AI-assisted development
- Maintains governance through constitutional principles

**Consequences**:
- ✅ Better alignment with stakeholders
- ✅ Clear audit trail for compliance
- ✅ Reduced context loss between AI sessions
- ⚠️ Additional upfront effort for specifications
- ⚠️ Must maintain discipline (no shortcuts)

**Alternatives Considered**:
- CCPM (Claude Code Project Manager): Too complex for small team
- No framework: Risk of chaos and context loss
- Traditional waterfall: Too rigid for iterative development

**Review Date**: 2025-04-07 (quarterly review)

---

### ADR-002: Technology Stack (Existing Implementation)

**Date**: 2024-11-07 (Documentation of existing choices)
**Status**: ✅ Implemented & Operational
**Context**: Repository contains mature codebase with established technology choices

**ACTUAL IMPLEMENTED STACK**:

| Component | Choice | Status | Evidence |
|-----------|--------|--------|----------|
| **Frontend** | Vue 3.5.12 + TypeScript 5.6 | ✅ Production | 31 Vue files in MedCAT Trainer |
| **UI Framework** | Vuetify 3.7.3 | ✅ Production | Material Design components |
| **Build Tool** | Vite 6.3.4 | ✅ Production | Fast HMR, optimized builds |
| **Backend (API)** | FastAPI 0.115.2 | ✅ Production | MedCAT Service REST API |
| **Backend (Web)** | Django REST Framework | ✅ Production | MedCAT Trainer application |
| **Database** | PostgreSQL | ✅ Production | 94 migrations, 17 models |
| **Search** | Elasticsearch | ⚠️ Library ready | CogStack-ES implemented, not integrated |
| **Caching** | Redis | ❌ Not implemented | Planned for future |
| **Container** | Docker + Compose | ✅ Production | 29 compose files |
| **Server** | Gunicorn + Uvicorn | ✅ Production | ASGI/WSGI serving |

**Key Finding**: The repository uses a **DUAL BACKEND ARCHITECTURE**:
- **FastAPI** for stateless NLP microservice (MedCAT Service)
- **Django** for stateful web application (MedCAT Trainer)

**Rationale** (inferred from existing implementation):
- Vue 3: Composition API, strong typing, excellent developer experience
- TypeScript: Type safety for large frontend codebase (34K+ line components)
- Vuetify: Comprehensive Material Design component library
- FastAPI: Async support, automatic OpenAPI docs, lightweight for microservices
- Django: Full-featured framework for complex web applications with auth/ORM
- PostgreSQL: ACID compliance, relational data integrity for annotations
- Docker: Multi-environment deployment (GPU/CPU, dev/prod)

**Alternatives** (historical decisions, not documented):
- React: More complex, larger ecosystem
- Express.js: Less Python integration
- MongoDB: Less suitable for relational annotation/healthcare data
- Solr: More complex than Elasticsearch for our use case
- Flask: Less feature-rich than Django for web applications

**Consequences**:
- ✅ **Proven in production**: All technologies battle-tested in existing applications
- ✅ **Strong typing**: TypeScript + Pydantic ensures code quality
- ✅ **Dual backend flexibility**: FastAPI for APIs, Django for complex web apps
- ✅ **Active Vue 3 codebase**: 65 existing components to learn from
- ✅ **Comprehensive Docker setup**: 29 compose files for various scenarios
- ⚠️ **Dual backend complexity**: Must maintain expertise in both FastAPI and Django
- ⚠️ **No Redis caching yet**: Performance optimization opportunity exists
- ⚠️ **Elasticsearch integration pending**: Library ready, application integration needed

**For Clinical Care Tools**: Leverage existing Vue 3 + TypeScript frontend patterns from MedCAT Trainer, and choose FastAPI or Django backend based on requirements (stateless API = FastAPI, stateful web app with user sessions = Django)

**Review Date**: Not needed (stack is operational; review only if major issues arise)

---

### ADR-003: Healthcare Standards Adoption (FHIR R4)

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Need interoperability with EHR systems

**Decision**: Adopt FHIR R4 as primary integration standard
- SNOMED-CT for concept coding
- LOINC for lab/observation codes
- CDS Hooks for clinical decision support

**Rationale**:
- FHIR R4 is industry standard (Epic, Cerner, AllScripts support)
- Vendor-neutral interoperability
- ONC interoperability rules compliance
- Future-proof architecture

**Consequences**:
- ✅ Wide ecosystem compatibility
- ✅ Regulatory alignment
- ✅ No vendor lock-in
- ⚠️ Complex specification (learning curve)
- ⚠️ FHIR R5 migration eventually needed

**Alternatives Considered**:
- HL7 v2: Legacy, limited structure
- Proprietary APIs: Vendor lock-in
- FHIR R5: Too new, limited adoption

**Implementation Status**: Documented, not yet implemented

---

### ADR-004: Compliance Framework (HIPAA + GDPR)

**Date**: 2025-01-07
**Status**: ✅ Accepted
**Context**: Healthcare application must comply with regulations

**Decisions**:
- HIPAA Security Rule compliance mandatory
- GDPR/UK GDPR compliance for EU/UK deployments
- 21 CFR Part 11 if used for clinical trials
- Audit logging for ALL PHI access
- Encryption: TLS 1.3 (transit), AES-256 (rest)
- Access Control: RBAC with MFA

**Rationale**:
- Legal requirement (not optional)
- Patient privacy and safety
- Avoid regulatory fines
- Build trust with healthcare organizations

**Consequences**:
- ✅ Regulatory compliance
- ✅ Competitive advantage (certified system)
- ⚠️ Increased development complexity
- ⚠️ Ongoing compliance maintenance required
- ⚠️ Cannot take shortcuts with security

**Documentation**: [docs/compliance/healthcare-compliance-framework.md]

---

### ADR-005: Documentation of Actual Implementation State

**Date**: 2025-11-07
**Status**: ✅ Accepted (Corrective Documentation)
**Context**: CONTEXT.md was created in January 2025 with assumption of greenfield project, but comprehensive codebase analysis revealed extensive production implementations

**Discovery**:
Used Claude Code's Explore agent to analyze entire repository structure. Found:
- 3 production-ready applications (MedCAT v2, MedCAT Trainer, MedCAT Service)
- ~400+ Python files across projects
- 31 Vue 3 files (24 components + 6 views + App.vue) in production
- 95 PostgreSQL database migrations
- Dual backend architecture (FastAPI + Django)
- 29 Docker compose files
- 122+ test files
- Comprehensive documentation

**Critical Misalignment**:
- **CONTEXT.md claimed**: "NONE (Documentation Phase)" and "Implementation NOT started"
- **Actual reality**: Production-ready NLP ecosystem with mature codebase

**Decision**: Correct CONTEXT.md to accurately reflect:
1. **Existing Production Systems** (what IS implemented):
   - MedCAT v2: Core NLP library (PyPI published)
   - MedCAT Trainer: Full web application (Vue 3 + Django + PostgreSQL)
   - MedCAT Service: REST API (FastAPI)
   - Supporting libraries: MedCAT Den, CogStack-ES, scripts, demos

2. **Planned Clinical Care Tools** (what is NOT yet implemented):
   - Patient Search (for clinicians to query by condition)
   - Timeline View (for clinicians to review patient history)
   - Clinical Decision Support (alerts for clinicians)
   - FHIR R4 integration (EHR interoperability)

**Rationale**:
- **Prevent context loss**: AI assistants must understand they're extending a mature platform, not building from scratch
- **Accurate onboarding**: New developers need to know production systems exist
- **Appropriate decisions**: Architecture choices should leverage existing patterns (Vue 3, TypeScript, dual backend)
- **Resource allocation**: Don't reinvent wheels that already exist (annotation platform, NLP processing, authentication)

**Consequences**:
- ✅ **AI assistants have accurate context**: Can leverage existing code patterns
- ✅ **Reduced duplicated effort**: Won't reimplement existing functionality
- ✅ **Better architecture decisions**: Will extend existing systems appropriately
- ✅ **Clear scope boundaries**: Distinguish research platform (done) from clinical tools (planned)
- ⚠️ **Must study existing codebase**: Need to understand 65+ Vue components, Django models, FastAPI patterns
- ⚠️ **Technology choices constrained**: Must use Vue 3 + TypeScript (already implemented)
- ⚠️ **Backend choice needed**: Decide FastAPI vs Django for clinical care interfaces

**For AI Assistants**:
When implementing clinical care tools (for clinicians/researchers, not patients):
1. **Study existing patterns**: Read MedCAT Trainer code for Vue 3 + TypeScript examples
2. **Reuse components**: 65 existing Vue components may be adaptable
3. **Follow authentication patterns**: Django auth system is operational
4. **Leverage NLP service**: MedCAT Service API is ready to use
5. **Follow Docker patterns**: 29 compose files show deployment strategies

**Review Date**: Not needed (corrective documentation, not a new decision)

---

### ADR-006: Adopt CogStack-ModelServe for NLP Model Serving

**Date**: 2025-11-08
**Status**: ✅ Accepted
**Context**: Need production-ready NLP model serving for Clinical Care Tools Base Application

**Problem**: Original plan specified custom MedCAT Service implementation (~20 hours development). Before implementation, conducted due diligence review of CogStack ecosystem components (CogStack-NiFi, CogStack-ModelServe) to avoid reinventing the wheel.

**Analysis Results**:
1. **CogStack-NiFi** (https://github.com/CogStack/CogStack-NiFi):
   - Apache NiFi-based enterprise data pipeline orchestration
   - **Decision**: ❌ DEFER - Over-engineered for single-workstation MVP
   - Reconsider for future enterprise deployment (100+ users, multi-site)

2. **CogStack-ModelServe** (https://github.com/CogStack/CogStack-ModelServe):
   - Production-ready model serving platform (FastAPI-based)
   - **Decision**: ✅ ADOPT - Perfect fit for MVP + production

**Decision**: Replace custom MedCAT Service with **CogStack-ModelServe**

**Why CogStack-ModelServe**:
- ✅ **Production-tested**: Battle-tested, actively maintained (408 commits, 4 PRs)
- ✅ **Comprehensive**: Built-in authentication, monitoring (Grafana), model versioning (MLflow)
- ✅ **Multiple models**: SNOMED-CT, ICD-10, UMLS, de-identification (PII detection)
- ✅ **FastAPI-based**: Auto-generated OpenAPI docs, async support, aligns with our tech stack
- ✅ **Flexible deployment**: Minimal (core API only) for MVP, full stack (+ MLflow/Grafana) for production
- ✅ **Time savings**: ~20 hours saved (no custom retry logic, circuit breaker, auth needed)
- ✅ **Better accuracy**: Separate DeID model for PHI detection (vs heuristic-based classification)

**Architecture Changes**:
1. **Technical Plan**: v1.1.0 → v1.2.0
   - Replaced "MedCAT Service (port 5000)" with "CogStack-ModelServe (port 8001)"
   - Updated integration code (CogStackModelServeClient vs MedCATClient)
   - Added CogStack-NiFi compatibility layer (RESTful API standardization)
   - Updated docker-compose.yml configuration

2. **Task Breakdown**:
   - Task 0.6: "Setup MedCAT Service" → "Setup CogStack-ModelServe" (3 hours)
   - Task 3.5: "Create MedCAT Client Service" → "Create CogStack-ModelServe Client Service" (2.5 hours, reduced from 3)
   - Task 3.6: "Create PHI Classifier Service" → "Create PHI Classifier Service (Simplified)" (1 hour, reduced from 2)
   - **Time saved**: 1.5 hours in implementation + ~20 hours avoiding custom development = **21.5 hours total**

3. **Resource Requirements**:
   - **MVP (minimal deployment)**: 8GB RAM, 5 CPU cores - NO CHANGE ✅
   - **Future (full stack)**: 12GB RAM, 8 CPU cores - defer to Phase 2+

4. **Future CogStack-NiFi Compatibility**:
   - Added RESTful API standardization layer (`/api/v1/nifi/process_document`)
   - Standardized request/response formats (NiFi-compatible)
   - **Migration path**: MVP (direct REST) → Enterprise (Apache NiFi orchestration)
   - Our APIs remain unchanged when NiFi is added

**Deployment Strategy**:
- **Phase 0-1 (MVP)**: Minimal CogStack-ModelServe (core API + SNOMED + DeID models)
- **Phase 2+ (Production)**: Full stack (+ MLflow, Grafana, Prometheus, authentication)

**Models Used**:
- `medcat_snomed`: SNOMED-CT clinical concept extraction
- `medcat_deid`: PHI/PII detection (names, NHS numbers, dates, addresses)

**Rationale**:
- **Don't reinvent the wheel**: Leverage existing CogStack ecosystem
- **Production-ready from day one**: Proven in healthcare deployments
- **Future-proof**: Easy convergence with CogStack-NiFi for enterprise deployments
- **Better PHI detection**: Trained DeID model vs heuristic-based classification
- **Time efficiency**: 21.5 hours saved for other features
- **Maintenance**: CogStack team handles updates, security patches

**Consequences**:
- ✅ **21.5 hours saved** (implementation + avoided custom development)
- ✅ **Production-ready**: Authentication, monitoring, versioning built-in
- ✅ **Better accuracy**: Trained DeID model for PHI detection
- ✅ **Future-proof**: CogStack-NiFi convergence path documented
- ✅ **Active support**: CogStack community + institutional backing
- ⚠️ **Learning curve**: Team must learn CogStack-ModelServe APIs (mitigated by OpenAPI docs)
- ⚠️ **External dependency**: Relying on CogStack maintenance (mitigated: active project, can fork if needed)
- ⚠️ **Full stack complexity**: MLflow/Grafana add complexity (mitigated: defer to Phase 2+, MVP uses minimal deployment)

**Alternatives Considered**:
1. **Custom MedCAT Service**: Original plan, ~20 hours development, missing governance features
2. **Direct MedCAT library integration**: No REST API, tight coupling, harder to scale
3. **Third-party NLP APIs**: Vendor lock-in, PHI data sharing concerns, compliance issues

**Documentation Updates**:
- Technical Plan: v1.2.0 (updated architecture, integration patterns, NiFi compatibility)
- Task Breakdown: Phase 0 Task 0.6, Phase 3 Tasks 3.5-3.6 (updated)
- CogStack Ecosystem Analysis: COGSTACK_ECOSYSTEM_ANALYSIS.md (850 lines, comprehensive evaluation)

**Implementation Status**: ✅ Documented, ready for Phase 0 implementation

**Review Date**: 2025-12-08 (1 month after MVP deployment, evaluate performance/satisfaction)

**References**:
- CogStack-ModelServe: https://github.com/CogStack/CogStack-ModelServe
- Analysis Document: COGSTACK_ECOSYSTEM_ANALYSIS.md
- Technical Plan v1.2.0: .specify/plans/clinical-care-tools-base-plan.md

---

## 💾 Data Architecture

### Database Schema (Planned, Not Implemented)

```sql
-- NOT YET CREATED - PLANNED SCHEMA

-- Users and Authentication
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'clinician', 'researcher', 'admin'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Patients (minimal demographics, PHI)
CREATE TABLE patients (
    id UUID PRIMARY KEY,
    mrn VARCHAR(100) UNIQUE NOT NULL,
    -- Additional fields TBD based on requirements
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clinical Documents
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    patient_id UUID REFERENCES patients(id),
    document_type VARCHAR(100), -- 'progress_note', 'discharge_summary', etc.
    content TEXT, -- Encrypted at rest
    created_at TIMESTAMP DEFAULT NOW()
);

-- NLP Annotations (from MedCAT)
-- Stored in Elasticsearch, not PostgreSQL
```

**Status**: Schema design phase, no tables created yet

**Encryption**:
- `documents.content`: Encrypted at rest using database-level encryption
- `patients.*`: All fields encrypted, access logged

---

### Elasticsearch Indices (Planned, Not Implemented)

```json
// NOT YET CREATED - PLANNED INDEX

{
  "patients": {
    "mappings": {
      "properties": {
        "patient_id": { "type": "keyword" },
        "document_id": { "type": "keyword" },
        "concepts": {
          "type": "nested",
          "properties": {
            "cui": { "type": "keyword" },
            "pretty_name": { "type": "text" },
            "source_value": { "type": "text" },
            "confidence": { "type": "float" },
            "negation": { "type": "keyword" },
            "temporality": { "type": "keyword" },
            "experiencer": { "type": "keyword" },
            "certainty": { "type": "keyword" }
          }
        },
        "indexed_at": { "type": "date" }
      }
    }
  }
}
```

**Status**: Index design phase, not created yet

---

## 🔐 Security Architecture

### Authentication & Authorization (Planned)

**Not Yet Implemented**

**Planned Approach**:
- JWT tokens (1 hour expiry, refresh tokens 7 days)
- Role-Based Access Control (RBAC): Clinician, Researcher, Admin, Auditor
- Multi-Factor Authentication (MFA) for production
- OAuth 2.0 / SMART-on-FHIR for EHR integration

**Security Principles** (from Constitution):
1. Privacy by Design (not bolted on)
2. Minimum necessary access
3. Audit logging for all PHI access
4. Encryption everywhere (TLS 1.3, AES-256)

**Reference**: [docs/compliance/healthcare-compliance-framework.md]

---

### API Security (Planned)

**Not Yet Implemented**

**Planned Controls**:
- Rate limiting: 100 req/min per user
- Input validation: Pydantic schemas on all endpoints
- Output sanitization: Prevent XSS
- CORS: Whitelist allowed origins
- CSRF protection: SameSite cookies

---

## 🧪 Testing Strategy

### Test Pyramid (Target Coverage)

```
      /\
     /  \    E2E (10%)      - Critical user workflows
    /----\
   /      \  Integration (30%) - API contracts, service interactions
  /--------\
 /          \ Unit (60%)      - Business logic, pure functions
```

**Minimum Coverage**: 80% overall, 100% for critical paths

**Critical Paths** (require 100% coverage):
- Authentication/authorization
- PHI access and audit logging
- Meta-annotation filtering (clinical decision support)
- De-identification (AnonCAT)
- FHIR resource mapping

**Status**: No tests written yet (no code implemented)

---

## 📊 Performance Requirements

### Response Time Targets

| Operation | Target (P95) | Rationale |
|-----------|--------------|-----------|
| Patient Search | <500ms | User expectation for interactive search |
| API Endpoints | <200ms | Keep UI responsive |
| Document Processing (MedCAT) | <2s | Acceptable for batch processing |
| Dashboard Load | <2s | Initial page load |
| FHIR Resource Creation | <500ms | Real-time integration |

**Status**: Targets defined, no benchmarking done yet

**Validation**: Load testing required before production (500 concurrent users)

---

## 🔌 Integration Points

### MedCAT Service

**Status**: External dependency, assumed available

**Integration**:
- REST API: `http://medcat-service:5000`
- Input: Raw clinical text
- Output: JSON with entities + meta-annotations
- Expected Response Time: <2 seconds per document

**Configuration**:
```python
# Planned configuration (not implemented)
MEDCAT_SERVICE_URL = os.getenv("MEDCAT_SERVICE_URL", "http://localhost:5000")
MEDCAT_API_KEY = os.getenv("MEDCAT_API_KEY")
MEDCAT_TIMEOUT = 5  # seconds
```

**Meta-Annotations Required**:
- Negation (Affirmed/Negated)
- Temporality (Current/Historical/Future)
- Experiencer (Patient/Family/Other)
- Certainty (Confirmed/Suspected/Hypothetical)

**Reference**: [docs/advanced/meta-annotations-guide.md]

---

### FHIR Server (Optional)

**Status**: Planned, not implemented

**Integration Options**:
1. HAPI FHIR (Java, open source)
2. Firely Server (.NET, open source)
3. Epic FHIR API (if integrating with Epic)

**Planned Usage**:
- Read: DocumentReference (clinical notes)
- Write: Observation (NLP-extracted concepts)
- Hooks: CDS Hooks for real-time alerts

**Reference**: [docs/integration/fhir-integration-guide.md]

---

## 🐛 Known Issues & Technical Debt

### Current Issues
**None** (no code implemented yet)

### Technical Debt Register

| ID | Issue | Impact | Priority | Plan |
|----|-------|--------|----------|------|
| DEBT-001 | No implementation yet | N/A | - | Start with Sprint 1 |

**Future Debt Tracking**: Update this section when code is implemented

---

## 🚧 Work In Progress

### Active Development

**As of 2025-11-08**: Planning phase complete, ready for implementation

**Current Activity**:
1. ✅ Planning Phase 100% Complete
   - Constitution established (10 core principles)
   - Specification complete (v1.1.0 with 5 production sections)
   - Technical plan complete (v1.1.0, 8 phases, 310 hours)
   - Task breakdown complete (~90 tasks)
   - 8 implementation skills ready
   - Git hooks enforcing quality
   - Session management enhanced (v1.4.0)
   - NEXT_STEPS.md created for session continuity

2. ⏳ **Next: Phase 0 - Environment Setup** (7 tasks, ~20 hours)
   - Docker Desktop installation and configuration
   - MedCAT model download and verification (2-5 GB)
   - Docker Compose configuration (5 services)
   - PostgreSQL and Redis initialization
   - MedCAT Service verification
   - Environment verification script

**Next Steps for Clinical Care Tools**:
1. **Immediate**: Begin Phase 0 (Environment Setup) - see NEXT_STEPS.md
2. Install Docker Desktop with 8GB RAM, 4 CPU cores
3. Download MedCAT SNOMED-CT models (2-5 GB)
4. Create docker-compose.yml with 5 services
5. Initialize PostgreSQL database
6. Initialize Redis caching
7. Verify MedCAT Service operational

---

## 🗺️ Roadmap & Future Plans

### Phase 1: Foundation (Weeks 1-8) - NOT STARTED
- [ ] Sprint 1: Patient Search & Discovery
- [ ] Sprint 2: Patient Timeline View
- [ ] Sprint 3: Real-Time Clinical Decision Support
- [ ] Sprint 4: Authentication & Authorization

### Phase 2: Research & Analytics (Weeks 9-16) - PLANNED
- [ ] Sprint 5: Cohort Builder
- [ ] Sprint 6: Concept Analytics Dashboard
- [ ] Sprint 7: Clinical Trial Recruitment
- [ ] Sprint 8: Export & Integration Tools

### Phase 3: Governance & Quality (Weeks 17-22) - PLANNED
- [ ] Sprint 9: Quality Dashboard
- [ ] Sprint 10: Clinical Coding Assistant
- [ ] Sprint 11: Privacy & Compliance Monitor
- [ ] Sprint 12: Adverse Event Surveillance

### Phase 4: Polish & Launch (Weeks 23-24) - PLANNED
- [ ] Sprint 13: Performance Optimization
- [ ] Sprint 14: Documentation & Training

**Reference**: [docs/PROJECT_PLAN.md]

---

## 🔄 Recent Changes

### Change Log Format

```markdown
## [Date] - [Commit SHA] - [Author]
### Added
- What was added

### Changed
- What was changed

### Removed
- What was removed

### Why
- Rationale for changes

### Impact
- How this affects the system

### Migration Notes
- What users/developers need to do
```

---

### 2025-11-16 - Large-Scale Deployment Guide (10,000+ Documents, Overlapping Batches)

**Commits**: [Current] - docs(deployment): Add large-scale multi-clinician deployment with overlapping batches

**Added**:
- **scripts/split_rtf_batches.py** - Python script to split large RTF datasets into overlapping batches
- **scripts/LARGE_SCALE_DEPLOYMENT_README.md** - Comprehensive guide for deploying 5,000-10,000+ documents with 5+ clinicians

**Why**:
- **Scale requirements**: User clarified 10,000 documents (not 150), 5+ clinicians, asynchronous work
- **Poor communication**: Can't rely on manual coordination ("Dr. Smith does docs 1-2000")
- **Quality validation needed**: Overlap acceptable for inter-rater reliability checks
- **Flexibility required**: Clinicians work different schedules, need to help each other if someone is slow

**Impact**:
- ✅ **Overlapping batch strategy**: Automatic boundaries (no coordination), 20% quality validation, flexibility
- ✅ **No custom development**: Uses existing MedCAT Trainer features (separate datasets, separate projects)
- ✅ **Automated splitting**: Python script calculates optimal batch ranges with configurable overlap
- ✅ **Quality analysis**: Overlap zones (500 docs per pair) enable inter-rater reliability calculation (Cohen's Kappa)
- ✅ **Load balancing**: Admin can add fast clinicians to slow clinicians' projects mid-validation

**Batch Design** (Example: 10,000 docs, 5 clinicians, 500-doc overlap):
```
Batch A (Dr. Smith):   Docs 1-2500     (2,500 docs)
Batch B (Dr. Jones):   Docs 2001-4500  (2,500 docs, 500 overlap with A)
Batch C (Dr. Brown):   Docs 4001-6500  (2,500 docs, 500 overlap with B)
Batch D (Dr. White):   Docs 6001-8500  (2,500 docs, 500 overlap with C)
Batch E (Dr. Green):   Docs 8001-10000 (2,000 docs, 500 overlap with D)

Total unique docs: 10,000
Total overlap docs: 2,000 (20% validation rate)
Total validations: 12,000
```

**Overlap Zones** (Quality Validation):
- Docs 2001-2500: Validated by Dr. Smith AND Dr. Jones (inter-rater reliability check)
- Docs 4001-4500: Validated by Dr. Jones AND Dr. Brown
- Docs 6001-6500: Validated by Dr. Brown AND Dr. White
- Docs 8001-8500: Validated by Dr. White AND Dr. Green

**Key Technical Features**:
- **Automated batch calculation**: Script computes optimal ranges for N batches with M overlap
- **Alphabetical sorting**: RTF files sorted alphabetically for consistent batch assignment
- **Zero-padded naming**: Patient-0001.rtf (not Patient-1.rtf) for correct sorting
- **Configurable parameters**: `--num-batches` (5-10), `--overlap` (0-1000), `--batch-prefix`
- **Progress tracking**: Each project shows completion rate (1,250/2,500 = 50%)

**Migration Notes**:
- **For 10,000+ docs**: Use overlapping batches (this guide), NOT single ProjectGroup
- **For <1,000 docs**: Single ProjectGroup with manual coordination is OK
- **Overlap tuning**: 500 docs (20%) for quality, 1000 docs (40%) for high confidence, 0 for max efficiency
- **Load balancing**: Admin adds fast clinicians to slow projects mid-validation (Members field)
- **Quality analysis**: Export all projects, calculate Cohen's Kappa for overlap zones (IRR check)

**Workflow**:
1. Organize RTF files with zero-padded names (Patient-0001.rtf to Patient-10000.rtf)
2. Run `split_rtf_batches.py` → Generates 5 CSV files (batch_A.csv to batch_E.csv)
3. Upload 5 datasets to MedCAT Trainer
4. Create 5 separate ProjectAnnotateEntities (one per clinician)
5. Clinicians work independently on their batches (2,500 docs each)
6. Admin monitors progress, redistributes if needed
7. Export all projects, analyze overlap zones for quality

**Performance Estimates**:
- Batch preparation: 2 hours (10,000 RTF → 5 CSV files)
- User setup: 1 hour (5 accounts, 5 projects)
- Validation work: ~200 hours total (12,000 validations × 1 min/doc average)
- Timeline: ~6 weeks (5 clinicians × 8 hours/day × 5 days/week)

**Customization Options**:
- Increase overlap: `--overlap 1000` (40% validation, slower but higher confidence)
- More clinicians: `--num-batches 10` (1,250 docs each, faster completion)
- No overlap: `--overlap 0` (max efficiency, no quality checks)

**Troubleshooting**:
- Uneven batches: Last batch may be smaller (10,000 ÷ 5 = 2,000 remainder)
- Clinician finishes early: Add to another project (Members field) to help
- Clinician too slow: Redistribute remaining docs to fast clinicians
- Too much duplicate work: Reduce overlap to 250 docs (10% validation rate)

---

### 2025-11-16 - HTTPS/TLS Security Guide for NHS Deployment

**Commits**: 17767ef - docs(security): Add comprehensive HTTPS/TLS configuration guide with Nginx

**Added**:
- **docs/deployment/https-tls-nginx-guide.md** - Comprehensive HTTPS/TLS educational guide (31KB, 9 parts)

**Why**:
- **HIPAA/GDPR requirement**: PHI must be encrypted in transit (TLS 1.2+ mandatory)
- **Educational request**: User asked to "learn HTTPS/TLS configuration guide (Nginx reverse proxy)"
- **Production security**: Self-signed certificates insufficient for NHS deployment with real PHI
- **NHS CA workflow**: Document NHS Enterprise CA certificate request process for internal deployments

**Impact**:
- ✅ **Educational resource**: Explains WHY (HTTPS concepts), HOW (implementation), WHAT (reverse proxy)
- ✅ **3 deployment scenarios**: Self-signed (testing), Let's Encrypt (internet), NHS Enterprise CA (recommended for RDP)
- ✅ **Production-ready**: Nginx configs with TLS 1.2+, strong ciphers, HSTS, rate limiting, security headers
- ✅ **Monitoring guidance**: Certificate expiration alerts, brute-force detection, SSL Labs testing
- ✅ **NHS-specific**: NHS CA certificate request workflow (CSR generation, IT submission, installation)

**Key Content**:
- Part 1: Understanding HTTPS/TLS (encryption, TLS handshake, certificates, reverse proxy)
- Part 2: Certificate Options (4 types with pros/cons: self-signed, Let's Encrypt, NHS CA, commercial)
- Part 3: Implementation (3 step-by-step scenarios with full Nginx configs)
- Part 4: Security Hardening (TLS 1.2+, cipher suites, HSTS, OCSP stapling, DH params, headers)
- Part 5: Testing (SSL Labs, OpenSSL CLI, browser testing, certificate verification)
- Part 6: Troubleshooting (cert errors, protocol errors, mixed content, expiration)
- Part 7: Monitoring (expiration scripts, log monitoring, brute-force detection)
- Part 8: NHS Production Checklist (16 items for go-live)
- Part 9: Summary + Resources + FAQs

**NHS CA Workflow** (Recommended for RDP Deployment):
1. Generate CSR: `openssl req -new -newkey rsa:2048 -nodes -keyout private.key -out request.csr`
2. Submit CSR to NHS IT Certificate Services
3. Receive: server.crt + intermediate.crt + root.crt
4. Create fullchain: `cat server.crt intermediate.crt root.crt > fullchain.crt`
5. Configure Nginx: `ssl_certificate fullchain.crt; ssl_certificate_key private.key;`
6. Verify: No browser warnings on NHS computers (NHS Root CA pre-trusted)

**Migration Notes**:
- **For NHS RDP**: Use Scenario 3 (NHS Enterprise CA) - trusted by NHS devices, 1-2 year validity
- **Docker Compose**: Add Nginx service, bind MedCAT Trainer to 127.0.0.1:8000 (localhost only)
- **Firewall**: Open ports 80, 443; block 8000 externally (only Nginx forwards to it)
- **Complements**: docs/deployment/nhs-windows-rdp-deployment.md Phase 6 (Network Access)

---

### 2025-11-16 - NHS Hospital Deployment Guidance (RTF Support + RDP Multi-User)

**Commits**: f5e23e4 - docs(deployment): Add NHS Windows RDP deployment guide and RTF converter

**Added**:
- **scripts/rtf_to_csv_converter.py** - Python script to convert RTF clinical documents to CSV for MedCAT Trainer upload
- **scripts/requirements-rtf.txt** - Dependencies for RTF converter (`striprtf==0.0.26`)
- **scripts/RTF_CONVERTER_README.md** - User guide for RTF conversion workflow
- **docs/deployment/nhs-windows-rdp-deployment.md** - Comprehensive 6-phase deployment guide for NHS hospital Windows workstation with RDP multi-user access

**Why**:
- **Real-world NHS use case**: NHS hospital needs to deploy MedCAT Trainer on Windows workstation for multiple clinicians via RDP
- **RTF file format**: Clinical documents stored as RTF files (~50KB each), but MedCAT Trainer only accepts CSV/XLSX (medcat-trainer/webapp/api/api/models.py:237-242)
- **RDP multi-user architecture**: Multiple clinicians RDP to same Windows workstation with different Windows credentials, need to access shared MedCAT Trainer instance
- **No development needed**: Existing MedCAT Trainer supports use case 100% (Dataset upload, ProjectGroup for document distribution, OIDC auth) - only preprocessing and infrastructure configuration required

**Impact**:
- ✅ **RTF support via preprocessing**: Converts RTF → CSV without modifying MedCAT Trainer codebase
- ✅ **Multi-user RDP architecture clarified**: Docker containers bind to `localhost:8000` shared across all RDP sessions on same physical machine
- ✅ **Production deployment guide**: 6 phases covering Windows configuration, Docker setup, RTF conversion, ProjectGroup configuration, auto-start, network access
- ✅ **No Spec-Kit workflow needed**: Existing functionality covers 100% of NHS requirements (ProjectGroup feature is perfect for document distribution)
- ⚠️ **Windows 10 limitation**: Only 1 simultaneous RDP session (clinicians take turns); recommend Windows Server 2019/2022 for true multi-user (2-10+ simultaneous sessions)

**Use Case Validation**:
The NHS hospital scenario validates that existing MedCAT Trainer production features fully support:
1. **Windows Docker deployment**: Works on Windows 10/Server with Docker Desktop
2. **Admin user management**: Django admin interface for creating clinician accounts
3. **Document upload**: Dataset model accepts CSV (RTF preprocessing script provided)
4. **Document distribution**: **ProjectGroup model** automatically creates one ProjectAnnotateEntities per clinician, sharing same dataset
5. **Multi-user access**: Docker containers on `localhost:8000` accessible from all RDP sessions
6. **Progress tracking**: Admin monitors validation progress via Django admin
7. **Annotation workflow**: Clinicians validate documents independently via MedCAT Trainer UI

**Migration Notes**:
- **For NHS deployments**: Use preprocessing workflow (RTF → CSV → Dataset upload) - no code changes needed
- **For future RTF native support**: Would require Spec-Kit workflow to extend Dataset model (estimated 8-12 hours)
- **RDP architecture**: Admin installs Docker, runs containers once, disconnects RDP; clinicians RDP and access `localhost:8000`
- **Production checklist**: See docs/deployment/nhs-windows-rdp-deployment.md Phase 6 (16-item checklist for go-live)

**Key Technical Findings**:
- **ProjectGroup.create_associated_projects**: When `True`, automatically creates one ProjectAnnotateEntities for each annotator (medcat-trainer/webapp/api/api/admin/models.py:126-131)
- **All share same dataset**: All clinicians see same 150 documents, validate independently until quota met
- **DatasetForm validation**: Explicitly rejects non-CSV/XLSX files (medcat-trainer/webapp/api/api/models.py:242)
- **RDP localhost sharing**: Windows localhost is physical machine, not RDP session - all RDP users access same Docker containers

**Documentation Structure**:
```
docs/deployment/nhs-windows-rdp-deployment.md
├── Phase 1: Admin Workstation Preparation (Windows config, Docker install, service mode)
├── Phase 2: MedCAT Trainer Installation (clone, env config, docker-compose)
├── Phase 3: Multi-User RDP Access Configuration (test clinician access)
├── Phase 4: RTF Clinical Document Upload (convert RTF → CSV, upload Dataset)
├── Phase 5: Auto-Start Configuration (Task Scheduler, startup scripts)
└── Phase 6: Network Access (optional - direct access without RDP, firewall, security)
```

**Workflow Testing Result**:
- **Question**: "Do we need to follow our workflow to add any functionality?"
- **Answer**: **NO** - Existing MedCAT Trainer functionality is 100% sufficient
- **Conclusion**: Spec-Kit workflow is for **new feature development only**; use existing features when they already solve the problem

---

### 2025-11-16 - Correction of Codebase Metrics in CONTEXT.md

**Commits**: [Pending] - docs: Fix incorrect codebase metrics in CONTEXT.md

**Changed**:
- **Vue component count**: Corrected from "65 components" to "31 Vue files (24 components + 6 views + App.vue)"
- **TrainAnnotations.vue size**: Corrected from "34,490 lines" to "986 lines"
- **Metrics.vue size**: Corrected from "25,991 lines" to "771 lines"
- **Database migrations count**: Corrected from "95 migrations" to "94 migrations"
- **Last Updated date**: Updated from 2025-11-08 to 2025-11-16

**Why**:
- **Accuracy**: CONTEXT.md contained incorrect metrics introduced on 2025-11-07
- **Verification**: Manual verification revealed actual codebase counts differ significantly
  - Actual Vue files: 31 total (find medcat-trainer/webapp/frontend/src -name "*.vue" | wc -l)
  - Actual TrainAnnotations.vue: 986 lines (wc -l TrainAnnotations.vue)
  - Actual Metrics.vue: 771 lines (wc -l Metrics.vue)
  - Actual migrations: 94 files (find medcat-trainer -path "*/migrations/*.py" -name "[0-9]*.py" | wc -l)
- **Root cause**: November 7th Explore agent incorrectly counted components and file sizes
- **Impact**: Incorrect metrics could mislead developers about codebase complexity

**Impact**:
- ✅ **Accurate documentation**: CONTEXT.md now reflects actual codebase metrics
- ✅ **Developer expectations**: Correct understanding of component library size (24 reusable components)
- ✅ **File size clarity**: Vue files are ~1,000 lines each, not 30,000+ (manageable complexity)
- ✅ **Resource planning**: Can accurately assess reuse opportunities from 24 components
- ⚠️ **Internal inconsistency resolved**: Line 1604 previously had "24 components" while other sections claimed "65"

**Migration Notes**:
- No code changes required (documentation-only correction)
- AI assistants: Use corrected count of 31 Vue files (24 components) when recommending component reuse
- Developers: MedCAT Trainer has 24 reusable components in /components/ directory

**Verification Commands**:
```bash
# Vue files count
find medcat-trainer/webapp/frontend/src -name "*.vue" | wc -l  # Returns: 31

# TrainAnnotations.vue size
wc -l medcat-trainer/webapp/frontend/src/views/TrainAnnotations.vue  # Returns: 986

# Metrics.vue size
wc -l medcat-trainer/webapp/frontend/src/views/Metrics.vue  # Returns: 771

# Migrations count
find medcat-trainer -path "*/migrations/*.py" -name "[0-9]*.py" | wc -l  # Returns: 94
```

---

### 2025-11-08 - Next Steps Documentation for Future Sessions

**Commits**:
- [Current] - docs: Create NEXT_STEPS.md for session continuity

**Added**:
- **NEXT_STEPS.md** - Comprehensive guide for starting new coding sessions
  - What's been completed (planning phase 100% complete)
  - Phase 0 detailed breakdown (7 tasks, 20 hours)
  - Key files reference (planning docs, guides, skills)
  - Starting a new session checklist (4 steps)
  - Important constraints & requirements
  - Phase overview (8 phases total)
  - AI assistant checklist for new sessions
  - Quick start command
  - Success criteria for Phase 0

**Changed**:
- None

**Removed**:
- None

**Why**:
- **User request**: "Include a next steps section in a file for future reference and new coding sessions"
- **Session continuity**: Provide clear starting point for new sessions
- **Onboarding efficiency**: New developers/AI assistants can quickly understand current state
- **Context preservation**: Complement CONTEXT.md with actionable next steps
- **Clear milestones**: Define success criteria for Phase 0

**Impact**:
- ✅ Single file provides complete "where are we, what's next" overview
- ✅ New sessions can start immediately with clear direction
- ✅ Phase 0 tasks clearly outlined with acceptance criteria
- ✅ Key files referenced for easy navigation
- ✅ AI assistant checklist ensures consistent session start
- ✅ Quick start command for rapid context loading

**Migration Notes**:
- Read NEXT_STEPS.md at the start of every new session
- Use it alongside CONTEXT.md (CONTEXT = history, NEXT_STEPS = future)
- Update NEXT_STEPS.md as phases complete

**Design Pattern Introduced**:
- **Session Continuity Pattern**: CONTEXT.md (history) + NEXT_STEPS.md (future) = complete context

**Key Files**:
- NEXT_STEPS.md - Session starting guide

---

### 2025-11-08 - Enhanced Session Management Guidance in CLAUDE.md (v1.4.0)

**Commits**:
- a0d97d4f - docs(claude): Enhance session context management (v1.4.0)

**Added**:
- **"BEFORE Starting ANY Big Task - CHECK CONTEXT FIRST!" section** in CLAUDE.md
  - Mandatory context check before starting significant tasks (plans, task breakdowns, implementations)
  - Decision tree: 70%+ = new session, 50-70% = caution, <50% = safe
  - Specific examples of "big tasks" (3,000+ line plans, 2,000+ line breakdowns, etc.)
  - Prevents running out of context mid-task
- **Updated thresholds** to be more proactive:
  - 70% used: DO NOT start big tasks, recommend new session
  - 80% used: CREATE SUMMARY NOW
  - 90% used: URGENT
  - 95% used: CRITICAL

**Changed**:
- **CLAUDE.md version**: 1.3.0 → 1.4.0
- **Session management approach**: From reactive (summarize at 80%) to proactive (check before big tasks)
- **Threshold enforcement**: Added 70% threshold for blocking big tasks

**Removed**:
- None

**Why**:
- **User feedback**: "This is second time reaching 0% context... should summarize and start new session PRIOR to big task"
- **Prevent mid-task context loss**: Running out mid-task loses work, frustrates user, requires re-explaining
- **Proactive vs reactive**: Check context BEFORE committing to large work, not during
- **Better user experience**: Provide continuation prompt upfront when context is insufficient

**Impact**:
- ✅ AI assistants will check context before big tasks (mandatory)
- ✅ Users will receive recommendation to start new session if <30% context remains
- ✅ Prevents frustrating mid-task context loss (happened twice already)
- ✅ Clearer decision tree: 70% threshold added
- ✅ Comprehensive continuation prompts provided to users
- ✅ Reduces wasted tokens on large tasks that can't complete

**Migration Notes**:
- AI assistants should follow new "BEFORE Big Task" workflow
- Check system messages for token usage before starting plans, task breakdowns, features
- If ≥70% used, recommend new session to user with detailed continuation prompt

**Lessons Learned**:
- **Reactive summarization at 80% is too late** for big tasks (3,000+ lines)
- **Proactive checking at 70%** allows graceful session transition
- **User experience matters**: Better to start fresh than run out mid-task
- **Continuation prompts essential**: Detailed handoff prevents context loss

**Design Pattern Introduced**:
- **Proactive Context Management**: Check → Decide → Inform user → Provide continuation prompt
- **Decision Tree Pattern**: Clear thresholds with specific actions (70%, 80%, 90%, 95%)
- **Big Task Definition**: Explicit examples (plans 3,000+ lines, task breakdowns 2,000+ lines)

**Key Files**:
- CLAUDE.md (v1.4.0) - Session Management & Context Preservation section enhanced

---

### 2025-11-08 - Task Breakdown for Clinical Care Tools Base Application

**Commits**:
- a5def8d4 - docs(tasks): Create detailed task breakdown from technical plan (~90 tasks, 310 hours)

**Added**:
- **Task Breakdown File**: `.specify/tasks/clinical-care-tools-base-tasks.md` (~2,750 lines, ~90 tasks)
  - Phase 0: Environment Setup (7 tasks, 20 hours)
    - Docker Desktop installation and configuration
    - MedCAT model download and verification (2-5 GB)
    - Initial Docker Compose configuration
    - PostgreSQL and Redis initialization
    - MedCAT Service verification
    - Environment verification script
    - Troubleshooting documentation
  - Phase 1: Core Infrastructure (12 tasks, 60 hours)
    - Database setup (PostgreSQL 15+, Alembic migrations)
    - JWT authentication service
    - User management API
    - RBAC implementation
    - Immutable audit logging
    - Backend infrastructure
  - Phase 2: User & Project Management (7 tasks, 30 hours)
    - User CRUD operations
    - Project management system
    - Role assignment
    - Admin dashboard
  - Phase 3: Document Upload & PHI Extraction (12 tasks, 40 hours)
    - Document encryption (AES-256-GCM)
    - MedCAT integration with retry logic
    - PHI extraction workflow
    - Patient aggregation (NHS number matching)
    - Document deduplication (SHA-256 + Redis)
  - Phase 4: Module System & Patient Search (4+ tasks, 50 hours)
    - Module registry and loader
    - Patient search module (first pluggable module)
    - Elasticsearch integration
  - Phase 5: Session Security & Break-Glass (6 tasks, 30 hours)
    - Session binding (IP + user-agent)
    - Concurrent session limits
    - Break-glass emergency access
    - Security notifications
  - Phase 6: Data Retention & Clinical Safety (5 tasks, 30 hours)
    - Automated purging scripts
    - Clinical override tracking
    - Critical findings alerts
  - Phase 7: Testing & Deployment (10 tasks, 50 hours)
    - Integration tests (≥25% coverage)
    - E2E tests (critical user flows)
    - Load testing (500 concurrent users)
    - Production deployment validation

**Changed**:
- **CONTEXT.md**: Updated "Next Milestone" from "Create Task Breakdown from Technical Plan" to "Begin Phase 0: Environment Setup"
- **Current Phase**: Clinical Care Interfaces moved from "Technical Plan Complete" to "Task Breakdown Complete, Ready for Implementation"

**Removed**:
- None

**Why**:
- **Spec-Kit Workflow**: Following Constitution → Specification → Technical Plan → Tasks → Code
- **TDD Approach**: Each task follows Test-Driven Development (write tests → implement → verify)
- **Granular Breakdown**: Tasks sized at 1-2 hours each for manageable implementation
- **Clear Dependencies**: Tasks organized with prerequisites clearly marked
- **Parallel Execution**: Independent tasks can be done in any order within phases
- **Implementation Readiness**: Complete roadmap from environment setup to production deployment

**Impact**:
- ✅ Complete task breakdown ready (310 hours across 8 phases)
- ✅ Each task has: Goal, Prerequisites, TDD steps, Acceptance criteria, Files, Time estimate
- ✅ Clear dependency graph enables efficient execution
- ✅ TDD approach enforced (write tests first for every task)
- ✅ Average task time: ~3.4 hours (manageable chunks)
- ✅ Phases can be validated independently (clear milestones)
- ✅ Ready to begin Phase 0: Environment Setup
- ⏭️ **Next Step**: Begin implementation of Phase 0 tasks (environment setup)

**Migration Notes**:
- No migration needed (task breakdown document only)
- Ready to begin implementation
- Review task breakdown at `.specify/tasks/clinical-care-tools-base-tasks.md`

**Task Breakdown Principles Applied**:
1. **Granularity**: 1-2 hour tasks (90 tasks total)
2. **TDD Workflow**: Write tests → Implement → Verify → Commit (every task)
3. **Clear Dependencies**: Prerequisites listed for each task
4. **Independence**: Tasks within phases can be parallelized when possible
5. **Acceptance Criteria**: Specific, measurable, testable criteria for each task
6. **File Tracking**: Lists all files created/modified per task
7. **Time Estimates**: Realistic estimates based on task complexity

**Phase Summary**:
```
Phase 0: Environment Setup         - 7 tasks,  20 hours (0.5 weeks)
Phase 1: Core Infrastructure       - 12 tasks, 60 hours (1.5 weeks)
Phase 2: User & Project Management - 7 tasks,  30 hours (1 week)
Phase 3: Document Upload & PHI     - 12 tasks, 40 hours (1 week)
Phase 4: Module System & Search    - 4+ tasks, 50 hours (1.5 weeks)
Phase 5: Session Security          - 6 tasks,  30 hours (1 week)
Phase 6: Data Retention & Safety   - 5 tasks,  30 hours (1 week)
Phase 7: Testing & Deployment      - 10 tasks, 50 hours (1.5 weeks)
────────────────────────────────────────────────────────────────
Total: ~90 tasks, ~310 hours (11 weeks for 1 developer)
```

**Key Files**:
- Task Breakdown: `.specify/tasks/clinical-care-tools-base-tasks.md`
- Based on Plan: `.specify/plans/clinical-care-tools-base-plan.md` (v1.1.0)
- Based on Spec: `.specify/specifications/clinical-care-tools-base-app.md` (v1.1.0)

---

### 2025-11-08 - Technical Plan for Clinical Care Tools Base Application (v1.1.0)

**Commits**:
- 012f8447 - docs(plan): Create comprehensive technical plan for base app (v1.0.0)
- 46c14586 - Merge technical plan for Clinical Care Tools Base Application (v1.1.0)

**Added** (v1.1.0):
- **Phase 0: Environment Setup & MedCAT Model Preparation** (~20 hours, 7 tasks)
  - Development workstation setup (Docker, 8GB RAM, 4 CPU cores)
  - MedCAT model download and verification (2-5 GB downloads)
  - Initial Docker Compose configuration (all 5 services)
  - PostgreSQL and Redis setup
  - MedCAT Service verification
  - Environment verification script
  - Common issues and troubleshooting guide
- **Redis Integration** (7.2+)
  - Added to technology stack and architecture diagrams
  - Component responsibilities: Session store, caching, job queue
  - Document deduplication tracking (SHA-256 hashes)
  - Pub/sub for future real-time notifications
  - RDB + AOF persistence configuration
- **Document Deduplication Strategy**
  - SHA-256 hash-based duplicate detection
  - Redis cache for fast lookups (30-day TTL)
  - Database fallback with unique constraint
  - Many-to-many document-projects link table
  - Force re-upload option for admins
  - Metrics: deduplication rate, cache hit rate, savings
- **PHI De-Identification Validation Tests** (~100 lines of test examples)
  - PHI Identification Tests (NHS numbers, names, DOB, addresses)
  - PHI Protection Tests (encryption, separate storage)
  - PHI Logging Tests (no PHI in application logs, audit trail verification)
  - De-Identification Tests (patient aggregation, search API exclusions)
- **Scaling Strategy: 3-Tier Upgrade Path**
  - Tier 1: Vertical Scaling (20-30 users, ~$2k, 1-2 days)
  - Tier 2: Multi-Node Deployment (50-100 users, ~$10k, 4 weeks)
  - Tier 3: Cloud-Native (500+ users, ~$5k/month, 8-12 weeks)
  - Backward compatibility maintained across all tiers
  - Migration steps documented for each tier

**Added** (v1.0.0):
- **Technical Plan**: `.specify/plans/clinical-care-tools-base-plan.md` (~3,700 lines)
  - Architecture overview with system context diagrams
  - Technology stack decisions with rationale
  - Complete API design (OpenAPI 3.1 specifications for all endpoints)
  - Database schema with 13 core tables and Alembic migration strategy
  - Component design patterns (backend services, frontend components)
  - Security architecture (JWT, RBAC, session binding, break-glass access)
  - MedCAT integration with retry logic and circuit breaker patterns
  - PHI extraction workflow (4-step process with code examples)
  - Testing strategy (test pyramid: 70% unit, 25% integration, 5% E2E)
  - Deployment architecture (production-ready docker-compose.yml)
  - Performance requirements (response time targets, concurrent users)
  - Risks & mitigations (10 identified risks with impact/probability/mitigation)
  - 8 implementation phases over 11 weeks (~310 hours: Phase 0 + Phases 1-7)

**Changed**:
- **CONTEXT.md**: Updated "Next Milestone" from "Create Technical Plan" to "Create Task Breakdown from Technical Plan"
- **Current Phase**: Clinical Care Interfaces moved from "Ready for Technical Plan phase" to "Technical Plan Complete"

**Removed**:
- None

**Why**:
- **User Request**: "Create technical plan"
- **Spec-Kit Workflow**: Following Constitution → Specification → Technical Plan → Tasks → Code
- **Implementation Readiness**: Convert high-level spec (v1.1.0) to actionable technical details
- **Risk Mitigation**: Identify 10 risks upfront (MedCAT downtime, DB migration failure, JWT leak, etc.)
- **Team Alignment**: Provide complete blueprint for 290 hours of development work
- **Technology Decisions**: Document rationale for FastAPI vs Django, PostgreSQL vs MongoDB, Vue vs React

**Impact**:
- ✅ Complete blueprint for implementation ready
- ✅ API specifications defined (OpenAPI 3.1 for all endpoints)
- ✅ Database schema designed (13 tables with indexes and partitioning)
- ✅ Security architecture detailed (JWT, RBAC, break-glass, session binding)
- ✅ Testing strategy clear (test pyramid with coverage targets)
- ✅ Deployment approach defined (Docker Compose for single workstation)
- ✅ Timeline estimated (10 weeks, 7 phases)
- ✅ Risks identified and mitigated
- ⏭️ **Next Step**: Create task breakdown using `tech-plan-to-tasks` skill

**Migration Notes**:
- No migration needed (planning document only)
- Ready for task breakdown phase
- Review technical plan at `.specify/plans/clinical-care-tools-base-plan.md`

**Technical Decisions Documented**:

1. **FastAPI over Django** for new backend:
   - Rationale: Async performance, automatic OpenAPI generation, Pydantic validation
   - Keeps existing Django (MedCAT Trainer) separate

2. **PostgreSQL 15+** for data storage:
   - Rationale: JSONB support, full-text search, ACID compliance, mature ecosystem
   - Rejected: MongoDB (schema flexibility not needed, ACID compliance critical)

3. **Vue 3.5 + Composition API** for frontend:
   - Rationale: Consistency with MedCAT Trainer, TypeScript support, mature ecosystem
   - Rejected: React (unfamiliar to team, no existing codebase)

4. **JWT with 8-hour expiry**:
   - Rationale: Stateless auth, mobile-friendly, industry standard
   - Security: Session binding (IP hash + user-agent hash) prevents hijacking

5. **AES-256 for document encryption**:
   - Rationale: FIPS 140-2 compliant, HIPAA recommended, strong encryption
   - Key management: Environment variables (DEV), HSM/KMS (PROD)

6. **Test Pyramid (70/25/5)**:
   - Rationale: Fast feedback (unit), integration coverage (API), critical paths (E2E)
   - Target: ≥80% overall, ≥90% for auth/PHI/clinical paths

7. **Alembic for migrations**:
   - Rationale: SQLAlchemy integration, version control, rollback support
   - Pattern: Forward + backward migrations, data migrations separate

8. **Pinia for state management**:
   - Rationale: Vue 3 official state management, TypeScript support, DevTools integration
   - Rejected: Vuex (deprecated for Vue 3)

9. **Docker Compose for deployment**:
   - Rationale: Single workstation deployment, simple orchestration, no K8s overhead
   - Services: Frontend (8080), Backend (8000), PostgreSQL (5432), MedCAT (5000)

10. **Tenacity for MedCAT retry logic**:
    - Rationale: Exponential backoff, configurable retries, circuit breaker pattern
    - Configuration: 3 attempts, 4-10s exponential wait

**Implementation Phases**:
0. **Phase 0**: Environment Setup & MedCAT Model Preparation (Week 0, ~20 hours) ⭐ NEW
1. **Phase 1**: Core Infrastructure (Week 1-2, ~60 hours)
2. **Phase 2**: User & Project Management (Week 3, ~30 hours)
3. **Phase 3**: Document Upload & PHI Extraction (Week 4, ~40 hours)
4. **Phase 4**: Module System & Patient Search (Week 5-6, ~50 hours)
5. **Phase 5**: Session Security & Break-Glass (Week 7, ~30 hours)
6. **Phase 6**: Data Retention & Clinical Safety (Week 8, ~30 hours)
7. **Phase 7**: Testing & Deployment (Week 9-10, ~50 hours)

**Key Files**:
- Technical Plan: `.specify/plans/clinical-care-tools-base-plan.md`
- Based on Spec: `.specify/specifications/clinical-care-tools-base-app.md` (v1.1.0)
- Constitution: `.specify/constitution/project-constitution.md`

---

### 2025-11-08 - Session Management Guidance in CLAUDE.md

**Commits**:
- [Current] - docs(claude): Add session management and context preservation guidance

**Added**:
- **Session Management & Context Preservation Section** in CLAUDE.md (~200 lines)
  - When to summarize: ≥80% context usage (≤20% remaining)
  - How to create session summary (8-section template)
  - How to create continuation prompt (following Claude 4 best practices)
  - Best practices for continuation prompts (DOs and DON'Ts)
  - Example workflow for handling low context
  - Context usage checking (thresholds: 80%, 90%, 95%)
  - Preventing context loss strategies

- **Session Summary Template** with 8 sections:
  1. Current Objective
  2. Work Completed This Session
  3. Current State
  4. Files Modified/Created
  5. Immediate Next Steps
  6. Important Context (decisions, constraints)
  7. Open Questions/Blockers
  8. References (key files/docs)

- **Continuation Prompt Template** following Claude 4 best practices
  - Includes previous session summary
  - Immediate next steps
  - Important constraints and requirements
  - Clear ask for user confirmation

**Changed**:
- **CLAUDE.md version**: 1.2.0 → 1.3.0

**Removed**:
- None

**Why**:
- **User Request**: "We should be prompting Claude in CLAUDE.md to summarize the session, and create a prompt for next session when less than 20% of context is left"
- **Prevent Context Loss**: Sessions running out of context lose critical information
- **Claude 4 Best Practices**: Follow recommended prompt engineering patterns for continuity
- **Proactive Management**: Check context at 80%, 90%, 95% thresholds
- **Structured Handoff**: 8-section template ensures no information loss
- **Team Consistency**: All AI assistants follow same session management approach

**Impact**:
- ✅ Prevents abrupt session cutoffs
- ✅ Maintains continuity across sessions
- ✅ Preserves decisions, context, and state
- ✅ Reduces repeated questions and work
- ✅ Clear handoff between sessions
- ✅ Follows Claude 4 prompt engineering best practices
- ✅ Team members can continue work seamlessly

**Migration Notes**:
- No migration needed (documentation only)
- AI assistants should check context usage regularly
- Create summary at 80% context usage
- Save summaries to `.specify/sessions/` directory (optional)

**Design Patterns Introduced**:
- **Progressive Context Warning**: 80% (warn), 90% (urgent), 95% (critical)
- **8-Section Summary Template**: Comprehensive session state capture
- **Continuation Prompt Pattern**: Structured handoff with clear next steps
- **Context Usage Calculation**: Used/Total ratio with percentage thresholds

**Best Practices Referenced**:
- [Claude 4 Best Practices](https://docs.claude.com/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- Specific guidance: Be specific, provide structure, reference artifacts, state current phase, list decisions

---

### 2025-11-08 - Implementation Workflow Skills for Spec-Kit Development

**Commits**:
- [Current] - feat(skills): Add 3 implementation workflow skills

**Added**:
- **3 New Implementation Workflow Skills** (~4,000 lines total):

  1. **spec-to-tech-plan** (~1,300 lines)
     - Guides conversion of specifications to technical plans
     - OpenAPI API design templates
     - Database schema design patterns (PostgreSQL, UUID, JSONB)
     - Authentication/authorization architecture
     - Testing strategy (unit, integration, E2E)
     - Docker Compose deployment architecture
     - Risk identification and mitigation planning

  2. **tech-plan-to-tasks** (~1,400 lines)
     - Breaks technical plans into 1-2 hour tasks
     - Enforces Test-Driven Development (TDD) workflow
     - Defines clear acceptance criteria
     - Creates dependency graphs for parallel execution
     - Task templates for common patterns (models, APIs, components, migrations)
     - Example: 8-task breakdown for user authentication feature

  3. **infrastructure-expert** (~1,300 lines)
     - Production-ready Docker Compose configurations
     - PostgreSQL security hardening (SCRAM-SHA-256, connection pooling)
     - JWT authentication with session management
     - Immutable audit logging implementation
     - HIPAA/GDPR compliance checklists
     - Automated backup/restore procedures
     - Retry logic, circuit breakers, error handling patterns

- **Updated .claude/skills/README.md**:
  - Added "Implementation Workflow Skills" category
  - Updated activation triggers table (3 new skills)
  - Updated integration flow diagram showing full lifecycle
  - Updated metrics: 5 → 8 skills, ~2,500 → ~6,500 lines

**Changed**:
- **Skills count**: 5 → 8 (60% increase)
- **Total guidance**: ~2,500 → ~6,500 lines (160% increase)
- **Coverage**: Now spans full Spec-Kit workflow (Planning → Implementation)

**Removed**:
- None

**Why**:
- **User Request**: "Make sure we have Agent Skills to create technical plans for MedCAT, to do task breakdowns, to implement core infrastructure with Docker, database, authentication, and audit expertise"
- **Workflow Completion**: Previous skills covered planning (spec-kit-enforcer, prd-to-spec), architecture knowledge (medcat-architecture, medcat-ui-patterns), but lacked implementation guidance
- **Bridge Spec to Code**: Fill gap between approved specification and working implementation
- **Consistency**: Ensure all implementations follow same patterns (Docker, PostgreSQL, auth, audit)
- **Efficiency**: Reduce decision paralysis with battle-tested patterns

**Impact**:
- ✅ Complete skill coverage for Spec-Kit workflow
- ✅ Implementation skills guide from spec → plan → tasks → code
- ✅ Infrastructure patterns ensure security from day one
- ✅ TDD approach enforced in task breakdown
- ✅ Parallel execution enabled via dependency graphs
- ✅ Healthcare-specific patterns (HIPAA, GDPR, audit logging)
- ✅ Ready to proceed with base app implementation

**Migration Notes**:
- No migration needed (skill files only)
- Skills activate automatically based on context
- Next step: Use spec-to-tech-plan to create technical plan from base app specification

**Design Patterns Introduced**:
- **Skill Progressive Disclosure**: Metadata → SKILL.md → Reference files (load only what's needed)
- **TDD Task Structure**: Write tests → Implement → Verify → Commit (enforced in tech-plan-to-tasks)
- **Infrastructure as Code**: Complete Docker Compose with health checks, security hardening
- **Immutable Audit Logs**: PostgreSQL rules prevent UPDATE/DELETE on audit_logs
- **JWT Session Binding**: IP + user-agent hashing for session hijack detection

**Skill Activation Triggers**:
- `spec-to-tech-plan`: "create technical plan", "architecture design", "API design"
- `tech-plan-to-tasks`: "break down plan", "create tasks", "estimate work"
- `infrastructure-expert`: "setup Docker", "PostgreSQL", "authentication", "audit logging"

---

### 2025-11-08 - Enhanced Base App Specification with Production Readiness Sections

**Commits**:
- [Current] - feat(spec): Add 5 CRITICAL sections for production readiness

**Added**:
- **5 CRITICAL Production Readiness Sections** (~1,150 lines) to base app specification:

  1. **Data Retention & Purging Policy** (~190 lines)
     - Retention periods: Documents (8 years), Audit logs (7 years), Sessions (90 days)
     - Legal hold workflow with `legal_hold` flag on documents
     - Automated purging scripts for sessions and tasks
     - Semi-automated document purging with 30-day grace period
     - Anonymization workflow for research use after retention

  2. **Disaster Recovery & Business Continuity** (~250 lines)
     - RTO: 4 hours, RPO: 24 hours, MTTR: <8 hours
     - Daily automated backup script (PostgreSQL dump, encryption, offsite storage)
     - Monthly restore testing procedure
     - Failover procedures for 3 scenarios: hardware failure, data corruption, ransomware
     - Business continuity communication plan

  3. **Clinical Safety Mechanisms** (~350 lines)
     - `clinical_overrides` table for tracking clinician disagreements with system
     - `critical_findings` table for urgent alerts (sepsis, acute MI, critical labs)
     - `clinical_incidents` table for incident reporting integration
     - Weekly override review process
     - Auto-escalation for unacknowledged critical findings (4 hours)
     - Patient Safety Dashboard with alert thresholds

  4. **Enhanced Authentication - Break-Glass Access** (~200 lines)
     - `break_glass_events` table for emergency access tracking
     - Emergency 60-minute access workflow with immediate security notification
     - Post-access review within 24 hours (justified/questionable/inappropriate)
     - Auto-revocation of expired access
     - Comprehensive audit logging

  5. **Session Security Enhancements** (~160 lines)
     - Session binding to IP and user-agent (session hijack detection)
     - Concurrent session limits (max 2 per user)
     - Idle timeout (15 minutes of inactivity)
     - Admin force logout capability
     - Suspicious session flagging and security team alerts

- **Version History Section**: Added to specification header tracking changes
- **Updated Table of Contents**: Renumbered sections to include 5 new sections (15-19)

**Changed**:
- **Specification Version**: 1.0.0 → 1.1.0
- **Specification Size**: ~69KB → ~85KB (~23% increase)
- **Total Sections**: 15 → 20

**Removed**:
- None

**Why**:
- **Regulatory Compliance**: GDPR Article 5(1)(e) requires data retention policies
- **HIPAA Requirements**: §164.316(b)(2)(i) requires retention documentation (6 years minimum)
- **NHS Compliance**: Records Management Code specifies 8-year retention for clinical records
- **Clinical Safety**: NHS DCB0129 and ISO 14971 require risk management and incident tracking
- **Production Readiness**: Cannot deploy healthcare system without DR/BC plan
- **Emergency Care**: Break-glass access required for life-threatening scenarios
- **Security Hardening**: Session hijacking is primary attack vector for healthcare applications

**Impact**:
- ✅ Specification now production-ready for healthcare deployment
- ✅ Addresses all 19 user recommendations (CRITICAL + HIGH priority)
- ✅ Comprehensive compliance framework (GDPR, HIPAA, NHS, ISO)
- ✅ Patient safety mechanisms align with clinical governance requirements
- ✅ Security enhancements meet healthcare industry standards
- ⚠️ Implementation complexity increased (additional 8 database tables, 3 cron jobs)
- ⚠️ Requires security team integration (email/SMS notifications)
- ⚠️ Requires clinical governance lead involvement (override reviews)

**Migration Notes**:
- No migration needed (specification phase only)
- Next step: Create Technical Plan incorporating all 5 sections
- Implementation priority: Core security first, then clinical safety, then DR/BC
- Estimated implementation time: +15-20 hours for all 5 sections

**Technical Debt**:
- None (specification phase)

**Design Patterns Introduced**:
- **Legal Hold Pattern**: Prevent purging of legally-required data with flag + reason + owner
- **Break-Glass Pattern**: Time-limited emergency access with immediate notification + post-review
- **Session Binding Pattern**: IP + user-agent hashing for hijack detection
- **Clinical Override Tracking**: Document when humans disagree with system (quality improvement)
- **Critical Finding Auto-Escalation**: 4-hour unacknowledged threshold → escalate to director

**Compliance Frameworks Referenced**:
- GDPR Article 5(1)(e): Storage limitation
- HIPAA §164.316(b)(2)(i): Documentation retention
- NHS Records Management Code: Clinical records 8 years, audit trails 7 years
- NHS DCB0129: Clinical Safety Risk Management
- ISO 14971: Medical Devices Risk Management

**Database Schema Additions**:
- `deidentified_mappings` - Research data anonymization
- `deidentified_documents` - De-identified content for research
- `clinical_overrides` - Clinician disagreements with system
- `critical_findings` - Urgent clinical alerts
- `clinical_incidents` - Incident reporting
- `break_glass_events` - Emergency access tracking

---

### 2025-11-08 - Base App Specification with PHI Extraction Workflow

**Commits**:
- [Current] - feat(spec): Add base app specification with PHI extraction workflow

**Added**:
- **Complete Base App Specification** (`.specify/specifications/clinical-care-tools-base-app.md`) - 69KB
  - 13 core database tables (10 core + 3 PHI/document tables)
  - Comprehensive PHI extraction workflow (document upload → MedCAT processing → patient aggregation)
  - Multi-user architecture (workstation deployment, remote desktop access)
  - JWT authentication, RBAC, audit logging
  - Module system design (Core + pluggable modules)
  - Docker Compose deployment model

- **3 New Database Tables** for PHI handling:
  - `documents` - Encrypted RTF files (~50KB, AES-256)
  - `extracted_entities` - Structured data from MedCAT (PHI + clinical concepts)
  - `patients` - Aggregated patient records (NHS number, demographics)

- **PHI Extraction Workflow Section** (4-step process):
  1. Document upload (encrypt RTF, audit log)
  2. MedCAT processing (extract entities, classify PHI vs clinical)
  3. Patient aggregation (NHS number matching, fuzzy name/DOB matching)
  4. Search & timeline access (SQL query patterns)

**Changed**:
- **Architecture**: Confirmed workstation deployment (not cloud SaaS)
- **Storage Model**: RTF files in PostgreSQL BYTEA (not file system)
- **PHI Approach**: Store identifiable PHI (for clinical care), extract to structured data
- **Model Storage**: Shared Docker volume (all users share MedCAT models)

**Removed**:
- None

**Why**:
- **User Requirements**: Clarified deployment scenario (RDP to workstation, multiple users, shared resources)
- **PHI Handling**: Documents contain NHS #, name, address, DOB → need extraction pipeline
- **Data Size**: RTF files ~50KB → perfect for PostgreSQL BYTEA (<1MB recommendation)
- **Clinical Workflow**: Transform unstructured letters → structured searchable patient data

**Impact**:
- ✅ Complete database schema for PHI-aware system
- ✅ Security requirements defined (AES-256 encryption, audit logging, RBAC)
- ✅ MedCAT integration workflow documented (document → entities → patients)
- ✅ Patient matching algorithm specified (NHS number primary, name+DOB fallback)
- ✅ SQL query patterns for patient search and timeline modules
- ⚠️ Requires encryption key management (KMS or HSM)
- ⚠️ Requires background worker (Celery or FastAPI BackgroundTasks) for async processing

**Migration Notes**:
- No migration needed (spec phase only)
- Next step: Create Technical Plan (API design, architecture diagrams, testing strategy)
- Then: Create Task breakdown (implementation steps)
- Then: Implement core infrastructure (Docker Compose, database, auth, audit)

**Technical Debt**:
- None (specification phase)

**Design Patterns Introduced**:
- **Encrypted-at-Rest Documents**: AES-256 encryption of PHI documents in PostgreSQL BYTEA
- **Entity Extraction Pipeline**: MedCAT async processing with structured data storage
- **Patient Aggregation**: NHS number-based record matching with confidence scoring
- **Audit-First PHI Access**: All PHI queries logged before execution

**Architecture Decisions Confirmed**:
1. **Q1 (MedCAT Models)**: Shared volume - all users share models ✅
2. **Q2 (Document Storage)**: PostgreSQL BYTEA for RTF files (~50KB) ✅
3. **Q3 (PHI Storage)**: Store identifiable PHI, extract to structured data via MedCAT ✅

---

### 2025-11-08 - Architecture & Planning Skills + Modular App Design

**Commits**:
- [Current] - feat(skills): Add 4 architecture/planning skills for modular app development

**Added**:
- **4 New Architecture & Planning Skills** (`.claude/skills/`) - 3,800+ lines

  **medcat-architecture** (Expert knowledge of existing MedCAT ecosystem):
  - Documents MedCAT v2 core library architecture (228 files, PyPI package)
  - Documents MedCAT Trainer architecture (Django REST + Vue 3, 94 migrations, 24 components)
  - Documents MedCAT Service architecture (FastAPI microservice, bulk processing)
  - Provides 3 integration patterns (REST API, Direct Library, Trainer Extension)
  - Explains model loading strategies (Model Pack, Component Loading, MedCAT Den)
  - Documents database schemas, authentication flows, deployment patterns
  - Guides choosing integration approach for new clinical care tools

  **medcat-ui-patterns** (Vue 3 + Vuetify patterns from MedCAT Trainer):
  - Documents 24 production Vue components (ClinicalText, ConceptPicker, etc.)
  - Provides reusable patterns for annotated text display, concept autocomplete, data tables
  - Shows Django REST API integration patterns (axios, interceptors, service layer)
  - Explains Token and OIDC/Keycloak authentication flows
  - Demonstrates Vuetify component usage (v-data-table, v-card, v-chip)
  - Includes Plotly chart patterns for metrics visualization
  - Prevents rebuilding components that exist in MedCAT Trainer

  **prd-to-spec** (Convert PRDs to Spec-Kit specifications):
  - Converts Product Requirement Documents to Spec-Kit format
  - Extracts Context, Goals, Non-Goals, User Stories, Requirements, Constraints
  - Validates constitutional alignment (Patient Safety, Privacy, Evidence-Based, etc.)
  - Ensures acceptance criteria are SMART (Specific, Measurable, Achievable, Relevant, Time-bound)
  - Documents open questions with status tracking
  - Guides spec → plan → tasks workflow
  - Provides Sprint 1 PRD → Spec conversion example

  **modular-app-architect** (Design extensible module/plugin system):
  - Designs Core + Modules architecture pattern
  - Defines module independence principles (separate routes, components, APIs)
  - Plans shared infrastructure (auth, audit, config, module registry)
  - Provides complete directory structure (frontend/backend)
  - Shows module registration and loading patterns
  - Demonstrates module communication (event bus, shared state)
  - Documents OIDC authentication and audit logging integration
  - Guides building base app with pluggable modules (patient search, timeline, CDS, etc.)

**Changed**:
- **Development Approach**: From "implement Sprint 1 immediately" to "design base modular app first, then add modules"
- **Architecture Pattern**: Established Core + Modules pattern for clinical care tools
- **Skills Count**: 5 → 9 total skills (5 original + 4 new architecture/planning skills)

**Removed**:
- None

**Why**:
- **Strategic Alignment**: User requested "basic app which later will have extra functionalities with modules"
- **Architecture First**: Need to design extensible foundation before implementing features
- **Knowledge Capture**: Existing MedCAT ecosystem (Trainer, Service, v2) has valuable patterns to reuse
- **Spec-Driven Development**: Enable PRD → Spec → Plan → Tasks → Code workflow
- **Module Independence**: Enable parallel development of features (patient search, timeline, CDS)

**Impact**:
- ✅ Team can now design modular architecture using `modular-app-architect` skill
- ✅ Team can understand existing MedCAT components using `medcat-architecture` skill
- ✅ Team can reuse MedCAT Trainer UI patterns using `medcat-ui-patterns` skill
- ✅ Team can convert Sprint PRDs to specifications using `prd-to-spec` skill
- ✅ Foundation for building base app + modules approach (vs monolithic Sprint implementation)
- ⚠️ Requires architectural planning phase before Sprint 1 implementation
- ⚠️ Base app infrastructure must be built first (auth, audit, module loader)

**Migration Notes**:
- No immediate action required (planning phase)
- Next step: Use `prd-to-spec` to convert Sprint 1 PRD → base app specification
- Then: Use `modular-app-architect` to design core infrastructure
- Then: Implement patient search as first pluggable module

**Technical Debt**:
- None (planning phase)

**Design Pattern Introduced**:
- **Core + Modules Architecture**: Core app provides shared infrastructure (auth, audit, config, module registry), modules provide features (patient search, timeline, CDS) as independent plugins
- **Module Registration**: Frontend modules export `ModuleDefinition` with routes, permissions, components; backend modules export FastAPI routers
- **Shared Infrastructure**: OIDC authentication, audit logging, configuration store, HTTP client, database connections shared across modules
- **Module Independence**: Each module has own directory, routes, components, API endpoints; can be disabled without affecting core or other modules

**Architecture Decision Added**: See ADR-006 below

---

### ADR-006: Core + Modules Architecture for Clinical Care Tools

**Date**: 2025-11-08
**Status**: ✅ Accepted
**Context**: Planning clinical care tools platform with multiple features (patient search, timeline view, clinical decision support, cohort builder, etc.)

**Problem**:
- Sprint PRDs define 6-9 features to implement
- Traditional monolithic approach: all features in single codebase
- Risk: tight coupling, difficult parallel development, hard to disable features

**Decision**: Adopt **Core + Modules** architecture pattern

**Architecture**:
```
Clinical Care Tools Platform
├── Core App (Vue 3 frontend + FastAPI backend)
│   ├── Authentication (OIDC/Keycloak)
│   ├── Authorization (RBAC)
│   ├── Audit Logging
│   ├── Configuration Management
│   ├── Module Registry & Loader
│   └── Shared UI Shell (header, sidebar, routing)
│
└── Modules (Pluggable Features)
    ├── Patient Search Module
    ├── Timeline View Module
    ├── Clinical Decision Support Module
    ├── Cohort Builder Module
    └── (Future modules)
```

**Rationale**:
1. **Module Independence**: Features developed and deployed independently
2. **Parallel Development**: Small team (1-3 devs) can work on modules sequentially without blocking
3. **Constitutional Alignment**: "Modularity and Composability" principle (Constitution Principle #4)
4. **Customer Flexibility**: Enable/disable modules per deployment
5. **Clear Ownership**: Each module has defined scope and API contract
6. **Gradual Rollout**: Deploy modules incrementally (patient search first, then timeline, etc.)

**Alternatives Considered**:
1. **Monolithic App**: All features in single codebase
   - ❌ Rejected: Tight coupling, difficult to disable features, merge conflicts
2. **Microservices**: Each feature as separate service with own database
   - ❌ Rejected: Too complex for small team, operational overhead, distributed transactions
3. **Hybrid (Core + Modules)**: Shared infrastructure, feature modules
   - ✅ **Chosen**: Balance of modularity and simplicity

**Consequences**:
- ✅ **Positive**:
  - Clear separation of concerns (core vs features)
  - Easy to add/remove modules
  - Modules can be open-sourced independently
  - Testing isolation (module tests don't affect core)

- ⚠️ **Trade-offs**:
  - Requires upfront core infrastructure implementation
  - Module communication via defined APIs (not direct imports)
  - Module versioning and compatibility tracking needed

- ❌ **Risks**:
  - Over-engineering if only 1-2 modules ever built (mitigated: start simple, add complexity as needed)
  - Module API changes break compatibility (mitigated: semantic versioning, deprecation policy)

**Implementation**:
- **Phase 1** (2 weeks): Build core infrastructure (auth, audit, module loader)
- **Phase 2** (2 weeks): Implement patient search as first module (validates pattern)
- **Phase 3+**: Add modules incrementally (timeline, CDS, cohort builder)

**For AI Assistants**:
When implementing clinical care tools:
1. **Always check**: Is this core infrastructure or a feature module?
2. **Core changes**: Rare, require team discussion (affects all modules)
3. **Module changes**: Common, independent (don't affect other modules)
4. **New features**: Default to new module unless strong reason to add to core
5. **Module template**: Use `modular-app-architect` skill for structure

**References**:
- Constitution Principle #4: Modularity and Composability
- `.claude/skills/modular-app-architect/SKILL.md`
- `.claude/skills/medcat-architecture/SKILL.md` (existing MedCAT ecosystem patterns)

---

### 2025-11-07 - Custom Healthcare NLP Skills + Git Hook Installation

**Commits**:
- 31ee1567 - feat(skills): Add 5 custom healthcare NLP skills for team
- [Current] - Install pre-commit hook and update CONTEXT.md

**Added**:
- **5 Custom Skills** (`.claude/skills/`) - 2,719 lines of specialized guidance

  **Priority 1 (Critical)**:
  - `healthcare-compliance-checker` - HIPAA/GDPR compliance validation
    - Catches PHI in logs, missing audit trails, weak encryption
    - Validates RBAC, input sanitization, access controls
    - Prevents regulatory violations and patient privacy breaches

  - `medcat-meta-annotations` - NLP accuracy improvement (60% → 95%)
    - Explains 4 meta-annotations (Negation, Experiencer, Temporality, Certainty)
    - Provides filtering patterns to eliminate false positives
    - Shows real-world impact with clinical examples

  **Priority 2 (Highly Recommended)**:
  - `vue3-component-reuse` - Leverage existing 31 Vue files (24 components + 6 views + App.vue)
    - Searches MedCAT Trainer for reusable patterns
    - Provides Composition API + TypeScript templates
    - Prevents rebuilding components that already exist

  - `fhir-r4-mapper` - FHIR R4 integration patterns
    - Maps MedCAT output to FHIR resources (Observations, Conditions)
    - Converts meta-annotations to FHIR qualifiers
    - Provides CDS Hooks integration for real-time clinical decision support

  **Priority 3 (Quality Assurance)**:
  - `spec-kit-enforcer` - Workflow enforcement
    - Ensures Spec-Kit framework followed (Constitution → Spec → Plan → Tasks → Code)
    - Prevents "code first, document later" anti-pattern
    - Verifies constitution alignment before implementation

- **Git Pre-Commit Hook** - Enforces CONTEXT.md updates
  - Installed via `scripts/install-git-hooks.sh`
  - Blocks commits with code changes if CONTEXT.md not modified
  - Validates meaningful updates (not just date changes)
  - Warns about console.log, debugger, TODO statements
  - Located at `.git/hooks/pre-commit`

- **Skills README** (`.claude/skills/README.md`)
  - Comprehensive usage guide
  - Activation triggers for each skill
  - Testing scenarios
  - Troubleshooting guide

**Changed**:
- **Development Workflow**: Skills now automatically activate based on context
  - Code with patient data → healthcare-compliance-checker activates
  - NLP processing → medcat-meta-annotations activates
  - UI development → vue3-component-reuse activates
  - FHIR work → fhir-r4-mapper activates
  - New features → spec-kit-enforcer activates

**Why**:
- **Domain expertise**: Generic skills don't cover healthcare-specific needs (compliance, MedCAT, FHIR)
- **Safety critical**: Healthcare development requires compliance validation and NLP accuracy
- **Efficiency**: Reusing existing patterns (31 Vue files (24 components + 6 views + App.vue)) saves development time
- **Quality**: Enforcing Spec-Kit workflow prevents rework and ensures documentation
- **Team knowledge**: Skills provide consistent expertise across all AI-assisted sessions
- **Context preservation**: Skills bundle domain knowledge, reducing context repetition

**Impact**:
- ✅ **Compliance protection**: Prevents PHI leaks, missing audit logs, weak encryption
- ✅ **NLP accuracy**: Meta-annotation filtering improves precision by 35% (60% → 95%)
- ✅ **Development speed**: Reusing Vue components saves hours per feature
- ✅ **EHR integration ready**: FHIR R4 mapping patterns available for Sprint 3+
- ✅ **Quality assurance**: Spec-Kit enforcement prevents "code without spec" mistakes
- ✅ **Consistent workflow**: Pre-commit hook ensures CONTEXT.md stays current
- ⚠️ **Learning curve**: Team needs to understand skill activation patterns
- ⚠️ **Discipline required**: Hook can be bypassed with --no-verify (should be rare)

**Skill Activation Examples**:

Example 1: Implementing patient search
```
User: "Add API endpoint to search patients by condition"
→ spec-kit-enforcer: Checks for specification
→ healthcare-compliance-checker: Validates PHI handling, audit logging
→ medcat-meta-annotations: Suggests filtering (Negation=Affirmed, Experiencer=Patient)
Result: AI guides through compliant, accurate implementation
```

Example 2: Building UI component
```
User: "Create a patient list table"
→ vue3-component-reuse: Searches existing components
→ Finds: v-data-table patterns in MedCAT Trainer
Result: Reuses proven pattern, saves 2-3 hours
```

Example 3: FHIR export
```
User: "Export NLP results to FHIR format"
→ fhir-r4-mapper: Provides Observation/Condition mapping
→ medcat-meta-annotations: Ensures filtering before export
Result: Correct FHIR resources with meta-annotation qualifiers
```

**Technical Details**:
- Skills use progressive disclosure (Level 1: metadata, Level 2: SKILL.md, Level 3: references)
- Average skill size: ~500 lines (stays under token budget)
- Model-invoked (automatic activation based on description triggers)
- Third-person descriptions (suitable for system prompt injection)
- One level deep references (no nested files)
- Team-shareable via git (`.claude/skills/` in repository)

**Pre-Commit Hook Behavior**:
```bash
# Code change without CONTEXT.md update
git add patient_search.py
git commit -m "add search"
→ ❌ Blocked: "CONTEXT.md must be updated with code changes!"

# Code change WITH CONTEXT.md update
git add patient_search.py CONTEXT.md
git commit -m "add search"
→ ✅ Allowed: CONTEXT.md was modified

# Documentation-only change
git add README.md
git commit -m "update docs"
→ ✅ Allowed: No code changes detected
```

**Migration Notes**:
- **For AI assistants**: Skills automatically activate - no explicit invocation needed
- **For developers**: Run `scripts/install-git-hooks.sh` if hook not installed
- **Skill updates**: Edit SKILL.md files and commit - team gets updates via git pull
- **Bypass hook**: Use `--no-verify` only for emergencies (not recommended)
- **Testing skills**: Try scenarios in `.claude/skills/README.md`

**Documentation Updated**:
- Created `.claude/skills/README.md` with comprehensive usage guide
- Each skill has detailed SKILL.md with examples and patterns
- Git hook documented in `.git-hooks/README.md`

---

### 2025-11-07 - MAJOR CONTEXT.md Correction: Documentation of Actual Production State

**Commits**:
- [Current] - Comprehensive update to CONTEXT.md reflecting actual codebase reality

**Changed**:
- **Project Overview**: Changed phase from "Planning & Foundation" → "Production + Clinical Care Tools"
- **System Architecture**: Completely rewritten to document 3 production applications
  - MedCAT v2 (228 Python files, PyPI published)
  - MedCAT Trainer (Vue 3 + Django + PostgreSQL, 31 Vue files, 94 migrations)
  - MedCAT Service (FastAPI REST API, Docker deployment)
  - Supporting libraries (MedCAT Den, CogStack-ES, scripts, demos)

- **Implemented Features**: Changed from "NONE (Documentation Phase)" to comprehensive listing of production systems
  - Detailed breakdown of all 3 applications
  - Feature lists, file locations, key metrics
  - Distinction between research/annotation platform vs planned clinical care tools

- **Technology Stack (ADR-002)**: Updated to reflect actual dual backend architecture
  - Documented Vue 3.5.12 + TypeScript 5.6 (production)
  - FastAPI 0.115.2 (MedCAT Service) + Django (MedCAT Trainer)
  - PostgreSQL with 94 migrations (operational)
  - Elasticsearch library ready (integration pending)

- **Planned Features**: Clarified these are NEW clinical care tools for clinicians/researchers, not the first implementations

- **Work In Progress**: Updated to reflect current documentation maintenance activity

**Added**:
- **ADR-005**: "Documentation of Actual Implementation State"
  - Documents the discovery of mature codebase using Explore agent
  - Explains critical misalignment between docs and reality
  - Provides guidance for AI assistants on leveraging existing code
  - Emphasizes studying 31 Vue files (24 components + 6 views + App.vue), Django models, FastAPI patterns

**Why**:
- **CRITICAL context loss prevention**: CONTEXT.md claimed "no implementation" but 3 production apps exist
- **Accurate AI assistance**: AI assistants need to know they're extending a mature platform
- **Prevent duplicated work**: Don't reimplement annotation platform, NLP service, authentication
- **Enable proper architecture**: New features should leverage Vue 3, TypeScript, dual backend patterns
- **Correct onboarding**: New developers need accurate picture of codebase state
- **Terminology correction**: "Patient-facing" is misleading - these are tools FOR CLINICIANS, not for patients

**Impact**:
- ✅ **Massive context improvement**: AI assistants now understand production ecosystem
- ✅ **Better architecture decisions**: Will extend existing systems, not start from scratch
- ✅ **Clearer scope**: Distinguish research/annotation platform from planned clinical care tools
- ✅ **Terminology clarity**: "Clinical care tools" accurately describes tools for clinicians, not patients
- ✅ **Technology constraints clear**: Must use Vue 3 + TypeScript (already implemented)
- ✅ **Resource efficiency**: Can reuse 31 Vue files (24 components + 6 views + App.vue), Django auth, FastAPI patterns
- ⚠️ **Learning curve**: Must study substantial existing codebase (~400+ Python files)
- ⚠️ **Architecture decision needed**: FastAPI microservice vs Django extension for clinical tools

**Discovery Method**:
Used Claude Code's Explore agent with "very thorough" analysis to:
- Map entire directory structure (13 major directories)
- Inventory all services and components
- Verify technology stack claims
- Count files, components, migrations
- Identify discrepancies between docs and reality

**Migration Notes**:
- **For AI assistants**: Read updated sections CAREFULLY - project is NOT greenfield
- **Terminology correction**: "Patient-facing" → "Clinical care tools" (for clinicians, not patients)
- **Before implementing clinical tools**: Study MedCAT Trainer code for Vue 3 patterns
- **Architecture decisions**: Consult ADR-005 for guidance on leveraging existing systems
- **Don't reinvent**: Check existing 31 Vue files (24 components + 6 views + App.vue) for reusable patterns

---

### 2025-01-07 - CONTEXT.md Integration into CLAUDE.md Workflow

**Commits**:
- [Current] - Integrate CONTEXT.md as Step 0 and Step 7 in CLAUDE.md workflow

**Changed**:
- **CLAUDE.md** - Major workflow restructure to make CONTEXT.md central
  - **Added Step 0**: "Read CONTEXT.md FIRST (Every Session!)" - now the first step before Constitution
  - Renumbered workflow from Step 1-6 to Step 0-7
  - Prominent warning: "⚠️ STEP ZERO - ALWAYS START HERE"
  - Lists what CONTEXT.md tells you (15-20 minute time investment)

  - **Added Step 7**: "Update CONTEXT.md (Before Committing!)" - mandatory before every commit
  - Detailed checklist of what to update in CONTEXT.md
  - Example good update (comprehensive, detailed format)
  - Example bad update (what to avoid)
  - Emphasis on git hook enforcement

  - **Updated Commit Message Format**:
  - Added "CONTEXT.md Updates" section (mandatory for code commits)
  - Must document what was updated in CONTEXT.md
  - Git hook verification note

**Why**:
- **Make CONTEXT.md non-optional** in the AI assistant workflow
- **Prevent context loss** by ensuring every session starts with CONTEXT.md
- **Enforce living documentation** through both workflow and git hooks
- **Provide clear examples** of what good CONTEXT.md updates look like
- **Integrate context updates** into commit message format for visibility

**Impact**:
- ✅ AI assistants will always read CONTEXT.md as first action
- ✅ Developers have clear checklist for CONTEXT.md updates
- ✅ Commit messages now document what changed in CONTEXT.md
- ✅ Workflow is now: Read CONTEXT → Plan → Code → Update CONTEXT → Commit
- ⚠️ Adds ~5 minutes to commit process (for CONTEXT.md updates)

**Migration Notes**:
- AI assistants should follow new Step 0-7 workflow in CLAUDE.md
- All commits should include "CONTEXT.md Updates" section in commit message
- This is the first commit following the new format!

---

### 2025-01-07 - Living Context Document + Git Hooks

**Commits**:
- [Current] - CONTEXT.md + enforcement hooks

**Added**:
- **CONTEXT.md** - Living architecture and decisions document
  - System architecture (current and planned)
  - Architecture Decision Records (ADR framework)
  - Current system state (features implemented/planned)
  - Integration points and dependencies
  - Technical debt register
  - Recent changes log
  - Design patterns and conventions
  - Context for AI assistants (prevents context loss!)

- **Git Hooks** - Enforce CONTEXT.md updates
  - Pre-commit hook requires CONTEXT.md update with code changes
  - Warns about console.log/debugger statements
  - Warns about TODOs without tasks
  - Installation script: `scripts/install-git-hooks.sh`
  - Documentation: `.git-hooks/README.md`

**Changed**:
- **CLAUDE.md** - Added mandatory CONTEXT.md section
  - Prominent warning at top to read CONTEXT.md first
  - Added to code review checklist (mandatory)
  - "NO COMMIT WITHOUT CONTEXT.MD UPDATE" rule

**Why**:
- **Solve context loss problem** between AI-assisted coding sessions
- **Create institutional memory** that persists across team changes
- **Enable better AI assistance** by providing complete system context
- **Document architectural decisions** with rationale (ADRs)
- **Track system evolution** through living documentation

**Impact**:
- ✅ AI assistants have complete context at start of each session
- ✅ New developers can onboard by reading CONTEXT.md
- ✅ Architectural decisions documented with rationale
- ✅ Technical debt tracked systematically
- ✅ System state always up-to-date
- ⚠️ Requires discipline to update CONTEXT.md (enforced by git hook)

**Migration Notes**:
- Install git hooks: `./scripts/install-git-hooks.sh`
- Read CONTEXT.md before making any changes
- Update CONTEXT.md with EVERY code commit

---

### 2025-01-07 - Initial Setup

**Commits**:
- `da363edf` - Documentation merge
- `84ba0193` - Enhanced documentation + Spec-Kit
- `840084bf` - Quick start guide + workflow comparison
- `0952bd4a` - CLAUDE.md AI assistant guide

**Added**:
- Spec-Kit framework (`.specify/`)
- Project constitution with 10 core principles
- Comprehensive documentation (Meta-annotations, FHIR, Compliance)
- Enhancement analysis (40+ identified gaps)
- Workflow frameworks comparison guide
- AI assistant guide (CLAUDE.md)

**Changed**:
- README.md with quick start guides
- Documentation structure (added advanced/, integration/, compliance/)

**Why**:
- Establish systematic development workflow
- Leverage MedCAT's full potential
- Ensure compliance with healthcare regulations
- Enable effective AI-assisted development

**Impact**:
- Foundation laid for systematic feature development
- Clear governance through constitution
- Reduced context loss for AI assistants
- Improved onboarding for developers

**Migration Notes**: None (initial setup)

---

## 📝 Key Design Patterns

### Not Yet Established (No Code Implemented)

**Planned Patterns**:

#### Backend
- Repository Pattern (data access abstraction)
- Service Layer Pattern (business logic separation)
- Dependency Injection (FastAPI dependencies)
- Async/Await (non-blocking I/O)

#### Frontend
- Composition API (Vue 3)
- Composables (reusable stateful logic)
- Pinia Stores (state management)
- Component-based architecture

**Update when implemented**: Add examples and rationale

---

## 🧩 Module Dependencies

### Not Yet Established (No Code Implemented)

**Planned Structure**:

```
frontend/
├── src/
│   ├── components/ (UI components)
│   ├── composables/ (reusable logic)
│   ├── services/ (API clients)
│   ├── stores/ (state management)
│   └── views/ (page components)

backend/
├── app/
│   ├── api/ (endpoints)
│   ├── services/ (business logic)
│   ├── models/ (database models)
│   ├── schemas/ (Pydantic schemas)
│   └── clients/ (external service clients)
```

**Update when implemented**: Document actual dependencies

---

## 🔍 Debugging & Troubleshooting

### Common Issues (To Be Populated)

**This section will be updated as issues are discovered during development**

Format:
```markdown
### Issue: [Description]
**Symptoms**: What you see
**Cause**: Root cause
**Solution**: How to fix
**Prevention**: How to avoid
```

---

## 📚 Important Resources

### Internal Documentation
- [Constitution](.specify/constitution/project-constitution.md) - Core principles
- [Spec-Kit Guide](.specify/README.md) - Development workflow
- [CLAUDE.md](CLAUDE.md) - AI assistant guide
- [Project Plan](docs/PROJECT_PLAN.md) - Sprint breakdown
- [Workflow Frameworks](docs/WORKFLOW_FRAMEWORKS_GUIDE.md) - Spec-Kit vs CCPM

### Domain Knowledge
- [Meta-Annotations Guide](docs/advanced/meta-annotations-guide.md)
- [FHIR Integration Guide](docs/integration/fhir-integration-guide.md)
- [Compliance Framework](docs/compliance/healthcare-compliance-framework.md)

### External Resources
- [MedCAT GitHub](https://github.com/CogStack/MedCAT)
- [FHIR R4 Spec](https://hl7.org/fhir/R4/)
- [Vue 3 Docs](https://vuejs.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

## 🤝 Contributing to This Document

### Update Guidelines

**MANDATORY**: Update CONTEXT.md with EVERY code commit

**What to Update**:

1. **Architecture changes**: Update "System Architecture" section
2. **New features**: Update "Implemented Features" and add ADR if needed
3. **Tech stack changes**: Update "Technology Stack" and create ADR
4. **Dependencies**: Update "Module Dependencies" and "Integration Points"
5. **Issues found**: Add to "Known Issues & Technical Debt"
6. **Performance data**: Update "Performance Requirements" with actuals
7. **Security changes**: Update "Security Architecture"
8. **Recent changes**: Add entry to "Change Log" with every commit

**Format for ADRs**:
```markdown
### ADR-XXX: [Title]

**Date**: YYYY-MM-DD
**Status**: ✅ Accepted / ⏳ Proposed / ❌ Rejected / 🔄 Superseded by ADR-YYY
**Context**: Why this decision is needed

**Decision**: What we decided

**Rationale**:
- Why this decision was made
- What problem it solves

**Consequences**:
- ✅ Positive impacts
- ⚠️ Negative impacts / trade-offs

**Alternatives Considered**:
- Option A: Why rejected
- Option B: Why rejected

**Review Date**: When to re-evaluate
```

---

## ✅ Pre-Commit Checklist

**Before committing code, verify:**

- [ ] CONTEXT.md updated with relevant changes
- [ ] New ADR added if architecture decision made
- [ ] "Recent Changes" section updated
- [ ] "Implemented Features" or "In Progress" updated
- [ ] Technical debt noted if shortcuts taken
- [ ] Integration points documented if new service added
- [ ] Performance data added if benchmarking done
- [ ] Security implications documented
- [ ] Module dependencies updated if new modules added

**Enforce with pre-commit hook** (see [.git/hooks/pre-commit.sample])

---

## 🎯 Context for AI Assistants

### Quick Onboarding (Read This First!)

**Project State**: Documentation complete, no code implemented yet

**What Exists**:
- ✅ Spec-Kit framework and constitution
- ✅ Detailed specifications for 14 sprints
- ✅ Comprehensive documentation (compliance, FHIR, meta-annotations)
- ✅ CLAUDE.md guide for AI assistants

**What Doesn't Exist**:
- ❌ No frontend code
- ❌ No backend code
- ❌ No database
- ❌ No tests

**Your First Task Should Be**:
1. Read CLAUDE.md (AI assistant guide)
2. Read constitution (.specify/constitution/project-constitution.md)
3. Read this CONTEXT.md file completely
4. Check for specification of feature you're implementing
5. Follow Spec-Kit workflow (spec → plan → tasks → implement)

**Critical Requirements**:
- Patient safety first (validate accuracy >90% for safety-critical)
- Privacy by design (audit log ALL PHI access)
- Use meta-annotations (Negation, Temporality, Experiencer) - required!
- Write tests first (TDD approach, 80% coverage minimum)
- Update CONTEXT.md with EVERY commit

**Healthcare-Specific Context**:
- Meta-annotations prevent false positives (60% → 95% precision)
- Always filter: Negation=Affirmed, Experiencer=Patient, Temporality=Current
- FHIR R4 is the integration standard (not R5, not HL7 v2)
- HIPAA compliance is non-negotiable (audit everything)
- Confidence scores must be displayed to users (transparency principle)

---

## 🔗 Cross-References

**This document is part of the project knowledge base:**

- **CLAUDE.md**: How AI assistants should work (references this doc for context)
- **Spec-Kit**: Workflow framework (this doc tracks implementation state)
- **Constitution**: Principles (this doc ensures compliance via ADRs)
- **Documentation**: Domain guides (this doc links to them for context)

**Update Cascade**: Changes here may require updates to other documents

---

## 📊 Metrics & KPIs

### Development Metrics (To Be Tracked)

**Code Quality**:
- Test Coverage: Target >80% (Not yet measurable - no code)
- Code Review: 100% of PRs reviewed before merge
- Security Vulnerabilities: Target 0 critical (Will track via Snyk)

**Performance** (Once Implemented):
- API Response Time (P95): Target <500ms
- Search Latency (P95): Target <500ms
- Page Load Time (P95): Target <2s
- Uptime: Target >99.5%

**Adoption** (Post-Launch):
- Active Users: Target 50+ within 6 months
- Daily Searches: Target 1000+
- NPS Score: Target >50

**Status**: Baselines will be established during Sprint 1

---

## 🚨 Breaking Changes & Migrations

### Migration History

**This section will track breaking changes that require migration steps**

Format:
```markdown
### [Date] - [Version] - [Description]

**Breaking Change**: What broke
**Migration Steps**: How to migrate
**Timeline**: Deadline for migration
**Support**: Who to contact for help
```

**Current Status**: No migrations needed (no code implemented)

---

## 🎓 Lessons Learned

### Development Lessons (To Be Populated)

**This section will capture lessons learned during development**

Format:
```markdown
### Lesson: [Title]
**Context**: What happened
**What Went Wrong**: The mistake
**What We Learned**: The lesson
**Action**: How we'll prevent this
```

**Example (Placeholder)**:
```markdown
### Lesson: Importance of Meta-Annotations

**Context**: Initial cohort query without meta-annotation filtering
**What Went Wrong**: 60% precision, many false positives (family history included)
**What We Learned**: Meta-annotations are CRITICAL for healthcare NLP
**Action**: Always filter by Negation, Experiencer, Temporality (now in CLAUDE.md)
```

---

## 📞 Support & Escalation

### When You Need Help

**Stuck on implementation?**
1. Check this CONTEXT.md (system state, ADRs, design patterns)
2. Check CLAUDE.md (code standards, common pitfalls)
3. Check specifications (.specify/specifications/)
4. Check domain guides (docs/advanced/, docs/integration/)
5. Ask user with specific context

**Found a gap in documentation?**
- Update the relevant document
- Add clarification
- Commit with descriptive message

**Major architecture decision needed?**
- Create ADR in this file
- Discuss with user/team
- Get approval before implementing
- Reference ADR in code comments

---

## 📅 Review Schedule

### Regular Reviews

**Weekly** (During Active Development):
- Update "Work In Progress" section
- Update "Recent Changes" log
- Review technical debt register

**Monthly**:
- Review ADRs (still valid?)
- Update roadmap status
- Assess performance metrics

**Quarterly**:
- Full architecture review
- Constitution review (any principles need updating?)
- Technology stack review (any major changes needed?)

**Next Scheduled Review**: TBD (when development starts)

---

**END OF CONTEXT DOCUMENT**

---

## 📝 Meta Information

**Document Owner**: Tech Lead / Development Team
**Maintained By**: All developers + AI assistants
**Update Frequency**: With EVERY code commit
**Version Control**: Git (committed with code)
**Enforcement**: Pre-commit hook (recommended)

**Questions about this document?**
- Check CLAUDE.md for AI assistant guidance
- Ask the team lead
- Open a discussion issue

**Remember**: This document is only valuable if it's kept up-to-date. Update it religiously! 🙏
