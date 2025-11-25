# Consolidation & Merge Plan

**Generated**: 2025-11-25
**Target Branch**: `ccpm-consolidated`
**Source Branches**: 25 (10 local + 15 remote myfork)

---

## Executive Summary

This plan consolidates **usable code from 5 key branches** containing Sprint 1-9 implementations into `ccpm-consolidated`. The consolidation follows a dependency-ordered merge strategy to minimize conflicts.

### Merge Priority Order

| Priority | Branch | Commits | Content | Risk |
|----------|--------|---------|---------|------|
| 1 | myfork/development | +32 | Base sprints 1-5.5, specs | Low |
| 2 | claude/sprint3-integration-* | +61 | Advanced search | Medium |
| 3 | claude/sprints-6-8-* | +246 | CDS, Sprint 6-8 | High |
| 4 | autonomous/mvp-execution | +134 | MVP v0.3.0 tasks | Medium |
| 5 | fix/medcat-demo-model-config | +1 | MedCAT config | Low |

---

## Phase 1: Baseline Merge (myfork/development)

### Purpose
Establish complete Sprint 1-5.5 implementations as the foundation.

### Code to Merge

**Backend Services (24 files)**:
```
clinical-care-tools/backend/app/services/
├── elasticsearch/           # Search infrastructure
│   ├── search_service.py
│   ├── search_query_builder.py
│   ├── query_cache.py
│   ├── query_optimizer.py
│   └── document_indexing_service.py
├── deidentification/        # Sprint 4
│   ├── deidentification_service.py
│   └── surrogate_service.py
├── coding/                  # Sprint 5
│   └── icd10_extraction_service.py
├── events/                  # Sprint 5.5
│   └── event_publisher.py
├── timeline_service.py      # Sprint 2
├── timeline_export_service.py
├── audit_service.py         # Sprint 1
├── medcat_service.py
└── critical_finding_service.py
```

**API Endpoints (13 files)**:
```
clinical-care-tools/backend/app/api/v1/
├── patients.py              # Sprint 1
├── search.py                # Sprint 3
├── timeline.py              # Sprint 2
├── auth.py                  # Sprint 1
├── clinical_coding.py       # Sprint 5
├── deidentify.py            # Sprint 4
├── phi.py                   # Sprint 4
└── endpoints/
    ├── cds.py               # Sprint 6 (skeletal)
    ├── fhir.py
    ├── alerting.py          # Sprint 7 (skeletal)
    ├── analytics.py         # Sprint 9 (skeletal)
    └── population_health.py # Sprint 8 (skeletal)
```

**Database Models (13 files)**:
```
clinical-care-tools/backend/app/models/
├── patient.py
├── document.py
├── annotation.py
├── user.py
├── audit_log.py
├── clinical_coding.py
├── deidentified_document.py
├── reidentification_mapping.py
├── critical_finding_alert.py
├── clinical_incident.py
├── saved_search.py
└── search_analytics.py
```

**Frontend (22+ files)**:
```
clinical-care-tools/frontend/src/
├── components/timeline/     # Sprint 2
├── components/search/       # Sprint 3
├── views/
│   ├── TimelineView.vue
│   ├── PatientSearchView.vue
│   └── DashboardView.vue
├── stores/
└── composables/
```

**Specifications & Plans (33 files)**:
```
.specify/
├── specifications/          # 11 sprint specs
├── plans/                   # 11 technical plans
└── tasks/                   # 11 task breakdowns
```

### Merge Commands

```bash
# Ensure on ccpm-consolidated
git checkout ccpm-consolidated

# Merge development branch
git merge myfork/development --no-ff -m "merge(phase-1): integrate myfork/development with Sprints 1-5.5

Merges complete implementations:
- Sprint 1: Patient Search & Discovery (100%)
- Sprint 2: Timeline View (100%)
- Sprint 3: Full-Text Search base (70%)
- Sprint 4: De-Identification (80%)
- Sprint 5: Clinical Coding (70%)
- Sprint 5.5: Event Bus (100%)
- Sprint 6-9: Skeletal architecture

Includes:
- 24 backend services
- 13 API endpoint files
- 13 database models
- 22+ frontend components
- 33 specification files
- 5 database migrations

🤖 Generated with Claude Code"

# Resolve any conflicts
# Priority: Keep development branch versions for Sprint implementations
```

### Expected Conflicts
- `.specify/` files (use development versions)
- `CONTEXT.md` (merge both)
- Frontend components (use development versions)

---

## Phase 2: Advanced Search Merge (claude/sprint3-integration-*)

### Purpose
Add Sprint 3 Phase 2 advanced query features not in development.

### Code to Cherry-Pick

**New Features**:
```
backend/app/services/elasticsearch/
├── search_query_builder.py  # Enhanced with 7 query types
│   ├── Boolean operators (AND/OR/NOT)
│   ├── Wildcard queries (* and ?)
│   ├── Fuzzy matching (~N)
│   ├── Proximity search (NEAR/W/ADJ)
│   ├── Range queries
│   └── Regex support
├── query_cache.py           # Redis caching (73% hit rate)
└── query_optimizer.py       # 40% performance improvement
```

**New Skills**:
```
.claude/skills/
├── elasticsearch-query-expert/SKILL.md
├── redis-caching-patterns/SKILL.md
├── search-performance-optimizer/SKILL.md
└── test-coverage-analyzer/SKILL.md
```

**Tests** (80+ files):
```
tests/
├── unit/search/             # 45+ unit tests
├── integration/search/      # 15+ integration tests
└── e2e/search/              # 20+ E2E tests
```

### Merge Commands

```bash
# List unique commits not in ccpm-consolidated
git log ccpm-consolidated..myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK --oneline

# Cherry-pick key feature commits (in order)
git cherry-pick <commit-sha-1>  # Boolean operators
git cherry-pick <commit-sha-2>  # Wildcard queries
git cherry-pick <commit-sha-3>  # Fuzzy matching
git cherry-pick <commit-sha-4>  # Proximity search
git cherry-pick <commit-sha-5>  # Range queries
git cherry-pick <commit-sha-6>  # Regex support
git cherry-pick <commit-sha-7>  # Query caching
git cherry-pick <commit-sha-8>  # Query optimizer
git cherry-pick <commit-sha-9>  # Skills

# Or merge entire branch if conflicts manageable
git merge myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK --no-ff -m "merge(phase-2): Sprint 3 Phase 2 Advanced Query Parsing

Adds advanced search capabilities:
- 7 query types (boolean, wildcard, fuzzy, proximity, range, regex)
- Redis query caching (73% hit rate)
- Query optimizer (40% performance gain)
- 4 new skills for search development
- 80+ tests (92% coverage)

🤖 Generated with Claude Code"
```

### Expected Conflicts
- `search_query_builder.py` (use sprint3-integration version - more complete)
- `query_cache.py` (use sprint3-integration version)
- Test files (merge both)

### Conflict Resolution Strategy
```bash
# For search_query_builder.py conflicts
# Keep sprint3-integration version (has all 7 query types)
git checkout --theirs backend/app/services/elasticsearch/search_query_builder.py
git add backend/app/services/elasticsearch/search_query_builder.py
```

---

## Phase 3: CDS & Sprint 6-8 Merge (claude/sprints-6-8-*)

### Purpose
Add Sprint 6 CDS implementation and Sprint 7-8 skeletal code.

### Code to Cherry-Pick

**Sprint 6 CDS (Complete Phase 6.1)**:
```
backend/app/
├── models/
│   ├── cds_guideline.py         # Guidelines database model
│   ├── cds_rule.py              # Rules with JSONB
│   └── cds/
│       ├── drug_interaction.py  # Drug interaction model
│       └── nhs_dmd_medication.py
├── services/cds/
│   ├── rules_engine.py          # Rules execution engine
│   ├── guidelines_service.py    # Guidelines CRUD
│   ├── fhir_resource_mapper.py  # FHIR R4 mapping
│   └── nhs_fhir_validator.py    # NHS validation
└── api/v1/endpoints/
    ├── cds_guidelines.py        # Guidelines API
    └── cds_rules.py             # Rules API
```

**Database Migrations**:
```
migrations/
├── 015_add_cds_guidelines.py
└── 016_add_cds_rules.py
```

**Sprint 7-8 Skeletal** (if useful):
```
backend/app/
├── schemas/alerting.py          # Sprint 7 alert schemas
├── schemas/population_health.py # Sprint 8 dashboard schemas
└── api/v1/endpoints/
    ├── alerting.py              # Sprint 7 endpoints
    └── population_health.py     # Sprint 8 endpoints
```

### Merge Commands

```bash
# Identify CDS-specific commits
git log myfork/claude/sprints-6-8-implementation-011M46D5vbdi9FbGxSzThebK --oneline --grep="cds\|CDS\|Sprint 6" | head -20

# Cherry-pick Sprint 6 Phase 6.1 commits
git cherry-pick c3766031  # Phase 6.1 CDS Rules API complete
git cherry-pick dbbce72c  # Guidelines API and Rules Engine
git cherry-pick 6ebda03a  # CDS rules database schema
git cherry-pick 2b7c481b  # CDS guidelines database schema
git cherry-pick 44d5376e  # FHIR models and NHS validation

# Cherry-pick Sprint 6 Phase 6.2-6.3 (skeletal)
git cherry-pick 518e7568  # NHS validation, FHIR mapping, pagination
git cherry-pick ff021dad  # Drug interaction infrastructure

# Or selective merge
git merge myfork/claude/sprints-6-8-implementation-011M46D5vbdi9FbGxSzThebK --no-ff -m "merge(phase-3): Sprint 6-8 CDS and skeletal implementations

Adds Clinical Decision Support:
- CDS Guidelines API (complete)
- CDS Rules Engine with JSONB (complete)
- FHIR R4 resource mapping
- NHS number validation
- Drug interaction checking (skeletal)
- Sprint 7 alerting schemas
- Sprint 8 population health schemas

Database migrations:
- 015: CDS Guidelines table
- 016: CDS Rules table

🤖 Generated with Claude Code"
```

### Expected Conflicts
- `api/v1/endpoints/cds.py` (use sprints-6-8 version)
- `schemas/clinical_decision_support.py` (merge carefully)
- Migration files (ensure sequential ordering)

### Conflict Resolution Strategy
```bash
# For CDS endpoints - use sprints-6-8 (more complete)
git checkout --theirs backend/app/api/v1/endpoints/cds.py

# For migrations - may need to renumber
# Check existing migrations first
ls -la backend/app/migrations/versions/
# Rename if conflicts: 015 -> 020, 016 -> 021
```

---

## Phase 4: Autonomous MVP Selective Merge

### Purpose
Cherry-pick any unique task implementations not covered by previous merges.

### Code to Review

**Unique in autonomous/mvp-execution**:
```
clinical-care-tools/
├── backend/app/
│   ├── services/patient_aggregation_service.py  # May be unique
│   ├── services/data_retention_service.py       # May be unique
│   └── api/v1/break_glass.py                    # Emergency access
└── frontend/src/
    └── components/                               # Additional UI components
```

### Merge Strategy

```bash
# Compare what's unique in autonomous vs ccpm-consolidated
git log ccpm-consolidated..myfork/autonomous/mvp-execution --oneline -- clinical-care-tools/ | head -30

# Cherry-pick only unique implementations
# Focus on:
# 1. Patient aggregation service (if not in development)
# 2. Break glass emergency access (likely unique)
# 3. Any additional UI components

# Example cherry-picks
git cherry-pick <patient-aggregation-commit>
git cherry-pick <break-glass-commit>
```

### Skip List
- MVP Phase 0-5 commits (already in development)
- Timeline commits (already in development)
- Search commits (already in sprint3-integration)

---

## Phase 5: MedCAT Config Fix

### Purpose
Apply MedCAT demo model configuration fix.

### Code to Cherry-Pick

```
fix/medcat-demo-model-config:
└── MedCAT configuration path and dependency fix
```

### Merge Commands

```bash
git cherry-pick 79213d50  # fix(medcat-demo): Configure MedCAT model path
```

---

## Post-Merge Validation

### 1. Run Tests

```bash
# Backend tests
cd clinical-care-tools/backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd ../frontend
npm test

# E2E tests
npm run test:e2e
```

### 2. Check Database Migrations

```bash
# List all migrations
alembic history

# Verify no gaps in migration chain
alembic check

# Test upgrade path
alembic upgrade head
```

### 3. Verify API Endpoints

```bash
# Start backend
uvicorn app.main:app --reload

# Check OpenAPI docs
curl http://localhost:8000/docs

# Verify all endpoints respond
curl http://localhost:8000/api/v1/health
```

### 4. Frontend Build

```bash
cd clinical-care-tools/frontend
npm run build
npm run preview
```

---

## Consolidation Checklist

### Phase 1: Development Merge
- [ ] Merge myfork/development into ccpm-consolidated
- [ ] Resolve conflicts (favor development for Sprint code)
- [ ] Verify all 24 services present
- [ ] Verify all 13 API files present
- [ ] Verify all 13 models present
- [ ] Verify all 33 spec files present
- [ ] Run tests (expect 85%+ pass)

### Phase 2: Sprint3-Integration Merge
- [ ] Cherry-pick/merge advanced search commits
- [ ] Verify 7 query types in SearchQueryBuilder
- [ ] Verify Redis caching implemented
- [ ] Verify query optimizer present
- [ ] Verify 4 new skills added
- [ ] Run search tests (expect 92% coverage)

### Phase 3: Sprints-6-8 Merge
- [ ] Cherry-pick CDS Phase 6.1 commits
- [ ] Verify CDS models (guidelines, rules)
- [ ] Verify CDS services (rules engine, FHIR mapper)
- [ ] Verify CDS API endpoints
- [ ] Apply database migrations (015, 016)
- [ ] Run CDS tests

### Phase 4: Autonomous Selective Merge
- [ ] Identify unique code not in other branches
- [ ] Cherry-pick patient aggregation service
- [ ] Cherry-pick break glass endpoint
- [ ] Verify no duplicate code introduced

### Phase 5: Final Validation
- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] E2E tests pass
- [ ] Database migrations apply cleanly
- [ ] API documentation complete
- [ ] No TypeScript errors
- [ ] No linting errors

---

## Rollback Plan

If merge fails or introduces breaking changes:

```bash
# Record current HEAD before each phase
git rev-parse HEAD > .merge-checkpoint

# If phase fails, rollback to checkpoint
git reset --hard $(cat .merge-checkpoint)

# Or rollback to specific commit
git reset --hard c7e95ae0  # Original ccpm-consolidated HEAD
```

---

## Expected Final State

After all phases complete, `ccpm-consolidated` will contain:

### Sprint Coverage

| Sprint | Status | Components |
|--------|--------|------------|
| Sprint 1 | ✅ 100% | Auth, Patient Search, Audit |
| Sprint 2 | ✅ 100% | Timeline API, D3.js UI, Export |
| Sprint 3 | ✅ 100% | 7 query types, caching, optimizer |
| Sprint 4 | ✅ 80% | PHI detection, de-identification |
| Sprint 5 | ✅ 70% | ICD-10 extraction |
| Sprint 5.5 | ✅ 100% | Event bus infrastructure |
| Sprint 6 | ✅ 50% | CDS Phase 6.1 complete |
| Sprint 7 | 📋 30% | Alerting schemas |
| Sprint 8 | 📋 25% | Population health schemas |
| Sprint 9 | 📋 25% | Analytics schemas |

### Code Statistics

| Category | Files | Est. Lines |
|----------|-------|------------|
| Backend Services | 30+ | 10,000+ |
| API Endpoints | 15+ | 4,500+ |
| Database Models | 15+ | 2,500+ |
| Frontend Components | 25+ | 6,000+ |
| Tests | 150+ | 15,000+ |
| Specifications | 35+ | 20,000+ |

### Test Coverage Target

| Area | Target | Current |
|------|--------|---------|
| Backend | 80% | ~75% |
| Frontend | 70% | ~65% |
| Critical Paths | 100% | ~90% |
| E2E | 50% | ~40% |

---

## Execution Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 | 30 min | None |
| Phase 2 | 45 min | Phase 1 |
| Phase 3 | 60 min | Phase 1 |
| Phase 4 | 30 min | Phases 1-3 |
| Phase 5 | 15 min | Phase 1 |
| Validation | 60 min | All phases |
| **Total** | **4 hours** | |

---

## Commands Quick Reference

```bash
# Phase 1
git checkout ccpm-consolidated
git merge myfork/development --no-ff

# Phase 2
git merge myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK --no-ff

# Phase 3
git cherry-pick c3766031 dbbce72c 6ebda03a 2b7c481b 44d5376e 518e7568 ff021dad

# Phase 4
git log ccpm-consolidated..myfork/autonomous/mvp-execution --oneline -- clinical-care-tools/
# Cherry-pick unique commits

# Phase 5
git cherry-pick 79213d50

# Validation
cd clinical-care-tools/backend && pytest tests/ -v
cd ../frontend && npm test
```

---

*Plan generated from analysis of 25 branches with 500+ unique commits.*
