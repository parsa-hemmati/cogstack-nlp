# CogStack Ecosystem Component Analysis

**Date**: 2025-11-08
**Purpose**: Evaluate existing CogStack components for reuse in Clinical Care Tools project
**Status**: ⚠️ CRITICAL FINDINGS - Architecture changes required

---

## Executive Summary

**Key Finding**: We should use **CogStack-ModelServe** instead of building custom MedCAT integration.

**Impact**:
- ✅ Eliminates custom MedCAT Service implementation (~20 hours saved)
- ✅ Production-ready model serving with authentication, monitoring, versioning
- ⚠️ Adds complexity (MLflow, MinIO, additional PostgreSQL instance)
- ⚠️ Requires architecture update in technical plan

**Recommendation**:
1. **Use CogStack-ModelServe** for NLP model serving (high priority)
2. **Skip CogStack-NiFi** for MVP (enterprise ETL not needed for single workstation)

---

## 1. CogStack-NiFi Analysis

### Overview
- **Purpose**: Enterprise data pipeline orchestration using Apache NiFi
- **Repository**: https://github.com/CogStack/CogStack-NiFi
- **Status**: Active development, successor to CogStack-Pipeline
- **Primary Language**: Python (55.6%), Shell (24.8%), PLpgSQL (15.3%)

### Key Capabilities
1. **Data Pipeline Orchestration**
   - Apache NiFi workflow engine
   - Document ingestion from multiple databases
   - ETL processing for clinical documents
   - Elasticsearch indexing
   - Kibana visualization

2. **Modular Architecture**
   - RESTful API standardization across NLP services
   - Container-native deployment (Docker)
   - Microservices pattern
   - Scalable for enterprise workloads

3. **Integration Points**
   - PostgreSQL data sources
   - Elasticsearch for indexing
   - Kibana for visualization
   - RESTful NLP services

### Technologies
- Apache NiFi (workflow orchestration)
- Docker/Docker Compose
- Python
- PostgreSQL
- Elasticsearch
- Kibana

### Deployment Model
- Containerized microservices
- Enterprise-grade scalability
- Complex orchestration (NiFi workflows)

---

### Evaluation for Our Project

#### Relevance: ⚠️ LOW FOR MVP

**Our Use Case**:
- Single workstation deployment
- Simple workflow: User uploads RTF → Process → Store → Search
- No complex ETL pipelines
- No multi-database ingestion
- No real-time streaming from EHR systems

**CogStack-NiFi Use Case**:
- Enterprise data pipelines
- Multi-source data ingestion (databases, HL7 feeds, FHIR servers)
- Complex workflow orchestration
- Large-scale document processing

#### Decision: ❌ DO NOT USE for MVP

**Reasons**:
1. **Over-engineered for our needs**: NiFi adds significant complexity
2. **Not designed for user-facing applications**: NiFi is for backend data pipelines
3. **Resource intensive**: Requires NiFi server + orchestration overhead
4. **Misaligned architecture**: We need interactive web app, not batch ETL

**When to reconsider**:
- Future enterprise deployment (100+ users, multi-site)
- Need to ingest from hospital databases automatically
- Require complex workflow orchestration
- Move beyond single-workstation deployment

#### What We Can Learn
- RESTful API standardization (apply to our module system)
- Container-native deployment patterns
- Microservices architecture principles

---

## 2. CogStack-ModelServe Analysis

### Overview
- **Purpose**: Production-ready model serving and governance platform for CogStack NLP
- **Repository**: https://github.com/CogStack/CogStack-ModelServe
- **Status**: Active maintenance (408 commits, 1 open issue, 4 PRs)
- **Tagline**: "One-stop shop for serving and fine-tuning models, training lifecycle management, monitoring, and end-to-end observability"

### Key Capabilities

#### 1. Model Serving
- **FastAPI-based HTTP endpoints** for model inference
- **Streaming APIs** (JSON Lines format) for real-time processing
- **WebSocket support** for chat interfaces
- **Batch processing** capabilities

#### 2. Model Support
| Model Type | Terminology | Use Case |
|------------|-------------|----------|
| medcat_snomed | SNOMED CT | Clinical concept extraction |
| medcat_icd10 | ICD-10 | Diagnosis coding |
| medcat_opcs4 | OPCS-4 | Procedure coding |
| medcat_umls | UMLS | Universal medical concepts |
| medcat_deid | PII detection | De-identification |
| huggingface_ner | Custom NER | Named entity recognition |
| huggingface_llm | N/A | Generative models |

#### 3. Model Management
- **Model Registry**: Local and remote model storage
- **Versioning**: Track model versions and metadata
- **MLflow Integration**: Experiment tracking, model lifecycle
- **Training/Fine-tuning**: Built-in training workflows

#### 4. Governance & Monitoring
- **Authentication**: Token-based API authentication with PostgreSQL
- **Monitoring**: Grafana + Prometheus for metrics
- **Logging**: Graylog for centralized logs
- **Observability**: End-to-end request tracing

#### 5. Deployment Options
**System Environment** (lightweight):
- Direct pip/uv installation
- Local model loading
- Minimal dependencies

**Container Environment** (full stack):
- Docker Compose orchestration
- Optional stacks: MLflow, monitoring, logging, auth, reverse proxy

### Technologies
- **Framework**: FastAPI (async Python web framework)
- **ML Platform**: MLflow (experiment tracking, model registry)
- **Storage**: MinIO (S3-compatible object storage), PostgreSQL
- **Monitoring**: Prometheus, Grafana, Graylog
- **Containerization**: Docker, Docker Compose
- **Model Frameworks**: MedCAT, HuggingFace Transformers
- **API Protocols**: REST, WebSocket, gRPC-ready

### Architecture Components

**Core Services** (required):
- API server (FastAPI)
- Model inference engine
- Model registry

**Auxiliary Services** (optional):
- MLflow (model lifecycle tracking)
- MinIO (object storage)
- PostgreSQL (metadata, auth)
- Grafana (monitoring dashboards)
- Prometheus (metrics collection)
- Graylog (log aggregation)
- Nginx (reverse proxy)

---

### Evaluation for Our Project

#### Relevance: ✅ HIGH - CRITICAL COMPONENT

**Our Use Case**:
- Process uploaded RTF documents with MedCAT
- Extract clinical entities (SNOMED concepts)
- Extract PHI for de-identification
- Production deployment on single workstation

**CogStack-ModelServe Use Case**:
- Exactly matches our needs!

#### Decision: ✅ USE CogStack-ModelServe

**Reasons**:
1. **Production-ready**: Battle-tested, actively maintained
2. **Comprehensive**: Authentication, monitoring, versioning built-in
3. **FastAPI-based**: Aligns with our tech stack
4. **Multiple models**: SNOMED, de-identification, ICD-10, UMLS
5. **Governance**: Authentication, audit logging, monitoring
6. **Flexible deployment**: Can use minimal setup for workstation

**Benefits**:
- ✅ Saves ~20 hours of custom MedCAT Service development
- ✅ Production-ready authentication and monitoring
- ✅ Model versioning and lifecycle management
- ✅ De-identification support built-in
- ✅ OpenAPI documentation auto-generated
- ✅ Streaming APIs for real-time processing
- ✅ WebSocket support for future interactive features

**Trade-offs**:
- ⚠️ Adds complexity (MLflow, MinIO, PostgreSQL)
- ⚠️ Requires additional Docker containers
- ⚠️ Potential resource overhead for single workstation

---

### Integration Strategy

#### Option 1: Minimal Deployment (Recommended for MVP)
**Use only core CogStack-ModelServe**:
- API server + model inference
- Skip MLflow, MinIO, Grafana, Graylog for MVP
- Use system environment deployment (pip install)
- Minimal resource footprint

**Pros**:
- Lightweight for single workstation
- Fast startup
- Simple configuration

**Cons**:
- No model versioning (MLflow)
- No monitoring dashboards (Grafana)
- Manual model management

#### Option 2: Full Stack Deployment
**Use complete CogStack-ModelServe with all services**:
- API server + MLflow + MinIO + PostgreSQL + Grafana + Prometheus
- Full governance and observability
- Production-grade deployment

**Pros**:
- Complete model lifecycle management
- Full monitoring and logging
- Production-ready from day one

**Cons**:
- Higher resource requirements (8+ containers)
- More complex configuration
- May exceed workstation capacity

#### Recommended Approach: Hybrid
**Phase 0-1 (MVP)**:
- Use minimal CogStack-ModelServe deployment (system environment)
- Load SNOMED and de-identification models
- Skip MLflow, MinIO, monitoring for MVP

**Phase 2+ (Production)**:
- Add MLflow for model versioning
- Add Grafana/Prometheus for monitoring
- Add authentication database
- Migrate to container deployment

---

## 3. Architecture Impact Analysis

### Current Architecture (Technical Plan v1.1.0)

**Our Planned Services**:
1. Frontend (Vue 3 + Vuetify, port 8080)
2. Backend (FastAPI, port 8000)
3. PostgreSQL (port 5432)
4. Redis (port 6379)
5. **MedCAT Service** (custom, port 5000) ← REPLACE THIS

**Total Containers**: 5

### Updated Architecture with CogStack-ModelServe

#### Option 1: Minimal (Recommended for MVP)
1. Frontend (Vue 3 + Vuetify, port 8080)
2. Backend (FastAPI, port 8000)
3. PostgreSQL (port 5432)
4. Redis (port 6379)
5. **CogStack-ModelServe** (FastAPI, port 8001) ← USE THIS

**Total Containers**: 5 (no change)

**Changes Required**:
- Replace MedCAT Service with CogStack-ModelServe in docker-compose.yml
- Update API integration to use CogStack-ModelServe endpoints
- Load SNOMED and de-identification models
- Configure minimal deployment (no MLflow/monitoring for MVP)

#### Option 2: Full Stack (Future Production)
1. Frontend (Vue 3 + Vuetify, port 8080)
2. Backend (FastAPI, port 8000)
3. PostgreSQL - App DB (port 5432)
4. Redis (port 6379)
5. **CogStack-ModelServe API** (FastAPI, port 8001)
6. **MLflow** (experiment tracking, port 5000)
7. **MinIO** (object storage, port 9000)
8. **PostgreSQL - MLflow DB** (port 5433)
9. **Grafana** (monitoring, port 3000)
10. **Prometheus** (metrics, port 9090)

**Total Containers**: 10

---

## 4. Required Changes to Technical Plan

### 🔴 CRITICAL: Technical Plan Updates Required

**File**: `.specify/plans/clinical-care-tools-base-plan.md` (v1.1.0)

**Changes Needed**:

#### 1. Technology Stack Section
**Current**:
```yaml
NLP Service: MedCAT v2 (custom Docker service)
```

**Update to**:
```yaml
NLP Service: CogStack-ModelServe (production-ready model serving platform)
  - FastAPI-based HTTP endpoints
  - MedCAT models: SNOMED-CT, de-identification
  - Authentication: Token-based (optional for MVP)
  - Model management: MLflow integration (Phase 2+)
  - Monitoring: Grafana + Prometheus (Phase 2+)
```

#### 2. Architecture Diagrams
**Current** (5 services):
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Frontend   │◀────▶│  Backend    │◀────▶│ PostgreSQL  │
│  (Vue 3)    │      │  (FastAPI)  │      │   15+       │
│ :8080       │      │ :8000       │      │ :5432       │
└─────────────┘      └──────┼──────┘      └─────────────┘
                            │
                            ├──────────┐
                            ▼          ▼
                     ┌─────────────┐ ┌─────────────┐
                     │  MedCAT     │ │   Redis     │
                     │  Service    │ │   7.2+      │
                     │ :5000       │ │ :6379       │
                     └─────────────┘ └─────────────┘
```

**Update to** (MVP):
```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  Frontend   │◀────▶│  Backend    │◀────▶│ PostgreSQL  │
│  (Vue 3)    │      │  (FastAPI)  │      │   15+       │
│ :8080       │      │ :8000       │      │ :5432       │
└─────────────┘      └──────┼──────┘      └─────────────┘
                            │
                            ├──────────────┐
                            ▼              ▼
                     ┌──────────────┐ ┌─────────────┐
                     │ CogStack-    │ │   Redis     │
                     │ ModelServe   │ │   7.2+      │
                     │ :8001        │ │ :6379       │
                     └──────────────┘ └─────────────┘
```

#### 3. MedCAT Integration Section
**Current** (custom retry logic, circuit breaker):
```python
# Custom MedCAT client with retry logic
```

**Update to** (use CogStack-ModelServe client):
```python
# Use CogStack-ModelServe FastAPI endpoints
# POST /api/process for single document
# POST /api/process_bulk for batch processing
# Authentication: Bearer token (optional)
```

#### 4. API Endpoints Section
**Current**:
- Custom MedCAT Service API design

**Update to**:
- Reference CogStack-ModelServe OpenAPI spec
- Use existing endpoints instead of designing custom ones
- Add CogStack-ModelServe SDK integration

#### 5. Deployment Section
**Current**:
```yaml
services:
  medcat-service:
    build: ./medcat-service
    ports:
      - "5000:5000"
```

**Update to**:
```yaml
services:
  cogstack-modelserve:
    image: cogstacksystems/cogstack-modelserve:latest
    ports:
      - "8001:8000"
    volumes:
      - ./models:/models
    environment:
      - MODEL_NAME=medcat_snomed
      - MODEL_PATH=/models/snomed_model.zip
```

#### 6. Phase 1 Tasks Section
**Current**:
- Task 1.X: Build custom MedCAT Service Docker image
- Task 1.Y: Implement retry logic and circuit breaker

**Update to**:
- Task 1.X: Deploy CogStack-ModelServe container
- Task 1.Y: Configure SNOMED and de-identification models
- Task 1.Z: Integrate with CogStack-ModelServe API

---

## 5. Required Changes to Task Breakdown

**File**: `.specify/tasks/clinical-care-tools-base-tasks.md`

### Phase 0 Changes

#### Task 0.6: Verify MedCAT Service
**Current**:
```markdown
### Task 0.6: Verify MedCAT Service (3 hours)
- Build MedCAT Service Docker image
- Mount models volume
- Start service and wait for model loading
```

**Update to**:
```markdown
### Task 0.6: Deploy and Verify CogStack-ModelServe (3 hours)

**Goal**: Deploy CogStack-ModelServe with SNOMED and de-identification models

**Prerequisites**:
- Task 0.2 completed (MedCAT models downloaded)
- Docker Compose running

**Steps**:
1. **Pull CogStack-ModelServe image**
   - `docker pull cogstacksystems/cogstack-modelserve:latest`
   - Verify image size and version
2. **Configure docker-compose.yml**
   - Add CogStack-ModelServe service
   - Mount models volume: `./models:/models`
   - Set environment variables: MODEL_NAME, MODEL_PATH
   - Configure port: 8001:8000
3. **Start CogStack-ModelServe**
   - `docker-compose up -d cogstack-modelserve`
   - Monitor logs for model loading
   - Wait for "Application startup complete" message
4. **Test SNOMED model**
   - POST request to `/api/process` with clinical text
   - Verify SNOMED concepts in response
   - Check meta-annotations (Negation, Temporality, Experiencer)
5. **Test de-identification model**
   - POST request to `/api/process` with text containing PHI
   - Verify PII entities detected (names, NHS numbers, dates)
6. **Verify OpenAPI documentation**
   - Access http://localhost:8001/docs
   - Review available endpoints

**Acceptance Criteria**:
- [ ] CogStack-ModelServe container running and healthy
- [ ] SNOMED model returns clinical concepts with meta-annotations
- [ ] De-identification model detects PII entities
- [ ] OpenAPI docs accessible at /docs endpoint
- [ ] Response time <2 seconds per document

**Files Created/Modified**:
- `docker-compose.yml` - Added CogStack-ModelServe service
- `.env` - Added MODEL_NAME, MODEL_PATH environment variables

**Estimated Time**: 3 hours

**Testing**:
- Manual: POST to `/api/process` returns valid response
- Manual: OpenAPI docs load successfully
```

### Phase 3 Changes

#### Task 3.X: MedCAT Integration
**Current**:
- Custom Python client
- Retry logic implementation
- Circuit breaker pattern

**Update to**:
- Use CogStack-ModelServe client SDK
- Leverage built-in retry logic
- Use streaming APIs for large documents

---

## 6. Resource Requirements Comparison

### Current Plan (Custom MedCAT Service)
| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| Frontend | 512MB | 0.5 | 100MB |
| Backend | 1GB | 1 | 200MB |
| PostgreSQL | 2GB | 1 | 10GB |
| Redis | 512MB | 0.5 | 1GB |
| MedCAT Service | 4GB | 2 | 5GB |
| **Total** | **8GB** | **5 cores** | **16GB** |

### Updated Plan (CogStack-ModelServe Minimal)
| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| Frontend | 512MB | 0.5 | 100MB |
| Backend | 1GB | 1 | 200MB |
| PostgreSQL | 2GB | 1 | 10GB |
| Redis | 512MB | 0.5 | 1GB |
| CogStack-ModelServe | 4GB | 2 | 5GB |
| **Total** | **8GB** | **5 cores** | **16GB** |

**Conclusion**: No change in resource requirements for MVP deployment.

### Future Production (CogStack-ModelServe Full Stack)
| Service | RAM | CPU | Disk |
|---------|-----|-----|------|
| Frontend | 512MB | 0.5 | 100MB |
| Backend | 1GB | 1 | 200MB |
| PostgreSQL (App) | 2GB | 1 | 10GB |
| Redis | 512MB | 0.5 | 1GB |
| CogStack-ModelServe | 4GB | 2 | 5GB |
| MLflow | 1GB | 0.5 | 2GB |
| MinIO | 1GB | 0.5 | 20GB |
| PostgreSQL (MLflow) | 1GB | 0.5 | 5GB |
| Grafana | 512MB | 0.5 | 1GB |
| Prometheus | 512MB | 0.5 | 5GB |
| **Total** | **12GB** | **8 cores** | **49GB** |

**Conclusion**: Full stack requires 50% more RAM, 60% more CPU, 3x more disk. Defer to Phase 2+.

---

## 7. Benefits Analysis

### Using CogStack-ModelServe

#### Time Savings
- ❌ **Remove**: Custom MedCAT Service implementation (~10 hours)
- ❌ **Remove**: Custom retry logic and circuit breaker (~5 hours)
- ❌ **Remove**: Custom authentication for MedCAT (~5 hours)
- ✅ **Total Saved**: ~20 hours

#### Functional Benefits
- ✅ Production-tested model serving (vs custom implementation)
- ✅ Multiple model support (SNOMED, ICD-10, UMLS, de-identification)
- ✅ Authentication and authorization built-in
- ✅ Model versioning with MLflow (future)
- ✅ Monitoring dashboards with Grafana (future)
- ✅ OpenAPI documentation auto-generated
- ✅ Streaming APIs for real-time processing
- ✅ WebSocket support for interactive features (future)
- ✅ Active maintenance and community support

#### Risk Reduction
- ✅ Battle-tested in production environments
- ✅ Regular security updates
- ✅ Comprehensive error handling
- ✅ Performance optimizations
- ✅ Community support and documentation

#### Future-Proofing
- ✅ Model lifecycle management (MLflow)
- ✅ Experiment tracking and versioning
- ✅ A/B testing capabilities (future)
- ✅ Multi-model ensembles (future)
- ✅ HuggingFace LLM support (future)

---

## 8. Risks and Mitigations

### Risk 1: Increased Complexity
**Risk**: CogStack-ModelServe has many optional components (MLflow, MinIO, etc.)

**Mitigation**:
- Use minimal deployment for MVP (core API only)
- Add components incrementally in Phase 2+
- Document clear upgrade path from minimal → full stack

### Risk 2: Resource Overhead
**Risk**: Full CogStack-ModelServe stack requires 12GB RAM (vs 8GB planned)

**Mitigation**:
- MVP uses minimal deployment (8GB still sufficient)
- Defer full stack to Phase 2+ or cloud deployment
- Monitor resource usage during Phase 0

### Risk 3: Learning Curve
**Risk**: Team needs to learn CogStack-ModelServe APIs and configuration

**Mitigation**:
- Comprehensive OpenAPI documentation available
- Active community support (Discourse forum)
- Task 0.6 includes testing and verification
- Time budget includes learning phase

### Risk 4: Dependency on External Project
**Risk**: Relying on CogStack-ModelServe maintenance and updates

**Mitigation**:
- Active project (408 commits, recent activity)
- Part of CogStack ecosystem (institutional backing)
- Can fork if needed (open source)
- Minimal deployment reduces dependency surface area

---

## 9. Recommendations

### Immediate Actions (Before Phase 0)

1. ✅ **Update Technical Plan** (v1.1.0 → v1.2.0)
   - Replace MedCAT Service references with CogStack-ModelServe
   - Update architecture diagrams
   - Update technology stack section
   - Update deployment configuration
   - **Estimated time**: 2 hours

2. ✅ **Update Task Breakdown**
   - Revise Task 0.6: Deploy CogStack-ModelServe
   - Update Phase 3 tasks: Use CogStack-ModelServe APIs
   - Remove custom MedCAT Service build tasks
   - **Estimated time**: 1 hour

3. ✅ **Update CONTEXT.md**
   - Add ADR for CogStack-ModelServe adoption
   - Document architecture decision rationale
   - Update integration points section
   - **Estimated time**: 30 minutes

4. ✅ **Review CogStack-ModelServe Documentation**
   - Read OpenAPI docs: https://cogstack-modelserve.readthedocs.io/
   - Review deployment guides
   - Understand minimal vs full deployment
   - **Estimated time**: 2 hours

### Phase 0 Implementation

1. ✅ **Use Minimal CogStack-ModelServe Deployment**
   - Core API + model inference only
   - Skip MLflow, MinIO, Grafana for MVP
   - System environment deployment (pip install) OR minimal container

2. ✅ **Load Required Models**
   - SNOMED-CT model for clinical concepts
   - De-identification model for PHI detection

3. ✅ **Test Integration**
   - Verify API endpoints work
   - Test with sample clinical documents
   - Validate meta-annotations in responses

### Phase 1+ Implementation

1. ⏳ **Integrate CogStack-ModelServe API**
   - Use FastAPI client or HTTP requests
   - Implement document processing pipeline
   - Handle responses and errors

2. ⏳ **Add Authentication** (Phase 2)
   - Configure token-based authentication
   - Integrate with our user management system

3. ⏳ **Add Monitoring** (Phase 2+)
   - Deploy Grafana + Prometheus
   - Configure monitoring dashboards
   - Set up alerts

4. ⏳ **Add Model Versioning** (Phase 2+)
   - Deploy MLflow
   - Configure model registry
   - Implement A/B testing

---

## 10. Decision Summary

### ✅ ADOPT: CogStack-ModelServe
**Scope**: Replace custom MedCAT Service with CogStack-ModelServe
**Priority**: HIGH - Update documents before Phase 0
**Deployment**: Minimal (MVP) → Full Stack (Phase 2+)
**Time Impact**: Saves ~20 hours of development
**Resource Impact**: No change for MVP (8GB sufficient)

### ❌ DEFER: CogStack-NiFi
**Scope**: Enterprise data pipeline orchestration
**Priority**: LOW - Not needed for MVP
**Rationale**: Over-engineered for single-workstation deployment
**Reconsider**: Future enterprise deployment (100+ users, multi-site)

---

## 11. Next Steps

1. **Update Technical Plan** to reference CogStack-ModelServe
2. **Update Task Breakdown** with revised Phase 0 and Phase 3 tasks
3. **Update CONTEXT.md** with ADR for CogStack-ModelServe adoption
4. **Proceed with Phase 0** using CogStack-ModelServe

**After updates complete**: Ready to begin Phase 0 implementation.

---

**Document Status**: ✅ Analysis Complete - Awaiting architecture updates
**Last Updated**: 2025-11-08
