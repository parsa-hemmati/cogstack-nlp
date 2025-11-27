---
name: de-identification-module
status: backlog
created: 2025-11-21T16:59:47Z
progress: 0%
prd: .claude/ccpm/prds/de-identification-module.md
github:
---

# Epic: De-Identification Module

## Overview

Implement HIPAA-compliant de-identification of clinical notes by removing/masking 18 Safe Harbor PHI identifiers using MedCAT NLP. The module provides batch processing, quality assurance review, and comprehensive audit trails to enable secure data sharing for research.

**Key Innovation**: Leverage existing search module patterns (entity highlighting, sanitization) and integrate with Phase 3 MedCAT infrastructure for PHI detection.

**PRD**: `.claude/ccpm/prds/de-identification-module.md`
**Target**: 12 weeks (Sprint 6)
**Dependencies**: MedCAT Service (Phase 3), Search Module (Sprint 1-2)

## Architecture Decisions

### Decision 1: Reuse Search Module Patterns
**Rationale**: Search module already has entity highlighting and text sanitization
- Reuse `SearchResultItem.vue` highlighting patterns for PHI visualization
- Reuse `sanitize.ts` utility (extend for PHI-specific patterns)
- Reuse entity display components (color-coding, confidence scores)

### Decision 2: MedCAT Fine-tuning vs Custom NER
**Choice**: Fine-tune existing MedCAT model with PHI annotations
**Rationale**:
- MedCAT already recognizes medical entities (names, dates, locations)
- Fine-tuning faster than training custom model from scratch
- Existing infrastructure (Phase 3) supports model updates
- Target: 92% recall (acceptable with human review)

### Decision 3: Batch Processing Architecture
**Choice**: Celery + Redis for background job processing
**Rationale**:
- Handle large batches (1,000-10,000 notes) without blocking UI
- Scalable (add more workers as needed)
- Progress tracking and cancellation support
- Already used in MedCAT pipeline (consistent architecture)

### Decision 4: Quality Assurance Approach
**Choice**: Side-by-side review UI with manual annotation tool
**Rationale**:
- Human-in-the-loop catches 8% missed PHI (safety net)
- Builds trust with research coordinators
- Annotations feed back into model training (continuous improvement)
- Similar to MedCAT Trainer's annotation interface

### Decision 5: Storage Strategy
**Choice**: Separate Elasticsearch index for de-identified notes
**Rationale**:
- Lower security tier (no PHI) reduces compliance burden
- Keeps original notes intact (in case re-identification needed)
- Easy to query de-identified corpus for research
- Audit trail links original → de-identified

## Technical Approach

### Frontend Components

**Reuse from Search Module**:
- Entity highlighting logic (`SearchResultItem.vue` patterns)
- Sanitization utilities (`sanitize.ts` - extend for PHI)
- Confidence score display
- Filter UI patterns

**New Components** (minimize new code):
```
frontend/src/components/deidentification/
├── DeidentifyUpload.vue           # Batch upload (CSV or query)
├── DeidentifyReview.vue           # Side-by-side comparison
├── DeidentifyResults.vue          # Download results
└── PHIAnnotation.vue              # Manual PHI tagging
```

**Key Simplification**: Use existing `SearchResults` and `SearchResultItem` components for displaying de-identified notes (just pass different data).

### Backend Services

**API Endpoints** (minimal surface area):
```python
POST /api/v1/deidentify              # Single note
POST /api/v1/deidentify/batch        # Batch upload
GET  /api/v1/deidentify/job/{id}     # Job status
POST /api/v1/deidentify/review       # Save manual corrections
```

**Core Services**:
```python
backend/app/services/
├── phi_detection_service.py       # MedCAT integration for PHI detection
├── deidentification_service.py    # Apply de-identification methods
└── batch_processor.py             # Celery task for batches
```

**Key Simplification**: Reuse existing MedCAT service client from Phase 3 (no new service infrastructure).

### Database Schema

**Elasticsearch Indexes**:
- `clinical_notes` (existing - original PHI-containing notes)
- `deidentified_notes` (new - de-identified corpus)
- `phi_audit_log` (new - audit trail)

**PostgreSQL Tables** (minimal):
```sql
CREATE TABLE deidentification_jobs (
    job_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    status VARCHAR(20),  -- pending, processing, completed, failed
    total_notes INT,
    processed_notes INT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE phi_entities (
    entity_id UUID PRIMARY KEY,
    note_id UUID,
    entity_type VARCHAR(50),  -- name, date, mrn, etc.
    start_offset INT,
    end_offset INT,
    confidence FLOAT,
    manually_reviewed BOOLEAN,
    action VARCHAR(20)  -- remove, replace, generalize
);
```

**Key Simplification**: Minimal schema, leverage existing Elasticsearch infrastructure.

### Infrastructure

**Leverage Existing**:
- MedCAT Service (Phase 3) - already running
- Elasticsearch cluster - add 1 index
- PostgreSQL - add 2 tables
- Redis - already used by MedCAT pipeline

**New Requirements**:
- Celery workers (2-4 for batch processing)
- Additional storage: ~2GB per 10,000 de-identified notes

## Implementation Strategy

### Phase 1: PHI Detection Model (Week 1-3)
**Goal**: Fine-tune MedCAT for 18 HIPAA Safe Harbor identifiers

**Approach**:
1. Acquire annotated PHI corpus (1,000 notes from i2b2 dataset)
2. Fine-tune MedCAT NER model (transfer learning)
3. Validate on held-out test set
4. Target: Precision >95%, Recall >90% (F1 >0.92)

**Output**: Updated MedCAT model with PHI detection

### Phase 2: Backend API (Week 4-6)
**Goal**: De-identification API with batch processing

**Tasks**:
- Implement `phi_detection_service.py` (MedCAT client for PHI)
- Implement `deidentification_service.py` (apply Safe Harbor methods)
- Create REST API endpoints (single + batch)
- Set up Celery tasks for background processing
- Add audit logging (HIPAA compliance)
- Write comprehensive tests (unit + integration)

**Output**: Working API with batch processing

### Phase 3: Frontend UI (Week 7-9)
**Goal**: User-friendly batch upload and review interface

**Tasks**:
- Create upload component (CSV or database query)
- Build side-by-side review UI (reuse search patterns)
- Implement manual annotation tool (catch missed PHI)
- Add job status tracking and progress indicator
- Create download/export functionality
- Write component tests

**Output**: Complete UI workflow

### Phase 4: IRB & Validation (Week 10-11)
**Goal**: Validate accuracy and obtain IRB approval

**Tasks**:
- Validate against gold standard corpus (1,000 notes)
- Measure precision, recall, F1 score
- Write de-identification SOP document
- Submit to IRB for methodology review
- Conduct pilot with 3 research projects (500 notes each)
- Incorporate feedback

**Output**: IRB approval, validated accuracy

### Phase 5: Production Deployment (Week 12)
**Goal**: Deploy to production and train users

**Tasks**:
- Deploy backend API and Celery workers
- Deploy frontend UI
- Configure monitoring and alerts
- Train research coordinators (2-hour session)
- Monitor first week usage
- Create user documentation

**Output**: Production system with trained users

## Task Breakdown Preview

Simplified to **8 core tasks** (leveraging existing code):

- [ ] **Task 1** (ML): Fine-tune MedCAT for PHI detection (Week 1-3)
- [ ] **Task 2** (Backend): PHI detection service (MedCAT integration)
- [ ] **Task 3** (Backend): De-identification service (Safe Harbor methods)
- [ ] **Task 4** (Backend): Batch processing API + Celery tasks
- [ ] **Task 5** (Backend): Audit logging + database schema
- [ ] **Task 6** (Frontend): Upload & review UI (reuse search patterns)
- [ ] **Task 7** (Frontend): Manual annotation tool + job tracking
- [ ] **Task 8** (Validation): IRB submission + pilot study

**Simplification Strategies Applied**:
1. Reuse search module components (entity highlighting, sanitization)
2. Reuse MedCAT infrastructure (no new NLP service)
3. Minimal database schema (2 tables only)
4. Leverage existing Celery + Redis setup
5. Combine related tasks (upload + review in one UI task)

## Dependencies

### External Dependencies
1. **MedCAT Service**: Phase 3 NLP infrastructure (already deployed)
2. **PHI Training Dataset**: i2b2 2014 De-identification Challenge corpus (publicly available)
3. **Celery + Redis**: Background job processing (already used in MedCAT pipeline)
4. **IRB Approval**: Institutional Review Board must approve methodology (Week 10)

### Internal Dependencies
1. **Search Module** (Sprint 1-2): Reuse entity highlighting and sanitization patterns
2. **Timeline Module** (Sprint 4-5): De-identified notes can feed into timeline view
3. **DevOps**: Configure Celery workers for batch processing
4. **Compliance Team**: Review and approve de-identification SOP

### Timeline of Dependencies
- **Week 1**: Acquire i2b2 PHI corpus (publicly available dataset)
- **Week 4**: Celery workers configured by DevOps
- **Week 7**: Search module patterns available for reuse
- **Week 10**: IRB review scheduled (needs 2-week lead time)

## Success Criteria (Technical)

### Performance Benchmarks
- **Single note**: De-identify 10-page clinical note in <2 minutes
- **Batch processing**: 1,000 notes in <2 hours
- **API response time**: <3 seconds for single note
- **Concurrent jobs**: Support 50 simultaneous de-identification jobs
- **Throughput**: 100,000 notes per month

### Quality Gates
- **PHI Detection**: Precision >95%, Recall >90%, F1 >0.92
- **False Negative Rate**: <10% (acceptable with human review)
- **Code Coverage**: >90% backend, >85% frontend
- **Security Audit**: Zero critical vulnerabilities (HIPAA compliance)
- **Load Testing**: Handle 1,000 concurrent API requests

### Acceptance Criteria
- [ ] Research coordinator can upload 5,000 notes and receive de-identified results in <2 hours
- [ ] Side-by-side review catches missed PHI (human-in-the-loop works)
- [ ] Audit log tracks every de-identification action (HIPAA compliant)
- [ ] IRB accepts methodology without additional questions
- [ ] Validation metrics meet targets (F1 >0.92)
- [ ] Zero PHI found in 10% manual review sample

## Estimated Effort

### Overall Timeline: 12 weeks

**Phase Breakdown**:
1. PHI Detection Model (Week 1-3): 3 weeks × 0.5 FTE ML engineer = 1.5 person-weeks
2. Backend API (Week 4-6): 3 weeks × 1 FTE developer = 3 person-weeks
3. Frontend UI (Week 7-9): 3 weeks × 1 FTE developer = 3 person-weeks
4. IRB & Validation (Week 10-11): 2 weeks × 0.5 FTE (all team) = 1 person-week
5. Production Deployment (Week 12): 1 week × 0.5 FTE = 0.5 person-weeks

**Total Effort**: 9 person-weeks across 12 calendar weeks

### Resource Requirements
- **ML Engineer**: Part-time (50%) for model fine-tuning
- **Full-stack Developer**: Full-time for backend + frontend
- **Clinical Advisor**: Part-time (10%) for validation and IRB
- **Compliance Officer**: Part-time (10%) for SOP review
- **DevOps**: 1 week for Celery worker setup

### Critical Path Items
1. **Week 1-3**: PHI model training (blocks backend development)
2. **Week 10**: IRB approval (blocks production deployment)
3. **Week 7-9**: Frontend UI (depends on backend API completion)

**Risk Buffer**: 2-week buffer built into 12-week timeline (actual work: 10 weeks)

## Testing Strategy

### Unit Tests
- PHI detection service (mock MedCAT responses)
- De-identification methods (test Safe Harbor rules)
- API endpoints (request/response validation)
- Frontend components (user interactions)
- Target: >90% coverage

### Integration Tests
- MedCAT integration (actual PHI detection)
- Celery task execution (batch processing flow)
- Database queries (Elasticsearch + PostgreSQL)
- End-to-end API workflow
- Target: All critical paths covered

### Validation Tests
- Gold standard corpus (1,000 manually annotated notes)
- Precision, recall, F1 score calculation
- Inter-annotator agreement (>0.90 Cohen's kappa)
- Red team testing (attempt re-identification)

### Security Tests
- HIPAA compliance audit (external auditor)
- Penetration testing (PHI leakage attempts)
- Audit trail completeness verification
- Access control enforcement

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| PHI recall <90% | Human review catches missed PHI, continuous model improvement |
| IRB rejects methodology | Early engagement, pilot study validation, external expert consultation |
| Performance too slow | Optimize NLP pipeline, parallel processing, caching |
| MedCAT model drift | Monthly retraining, validation dataset monitoring |
| Compliance audit failure | External audit before production, document everything |

## Simplifications from Original PRD

To keep task count ≤10, we simplified:

1. **No Expert Determination initially**: Focus on Safe Harbor (simpler, covers 80% of use cases)
2. **Reuse existing UI patterns**: Leverage search module instead of building from scratch
3. **Minimal schema**: 2 tables only (vs 5+ in original design)
4. **Single de-identification method**: Start with replacement method (extend later)
5. **Batch-only processing**: No real-time API initially (simpler infrastructure)
6. **Combined tasks**: Upload + review UI in one task (not separate)

**Result**: 8 tasks instead of 20-30, faster time-to-value, easier maintenance.

---

**Created**: 2025-11-21T16:59:47Z
**Status**: Backlog
**Next Command**: `/pm:epic-decompose de-identification-module`
