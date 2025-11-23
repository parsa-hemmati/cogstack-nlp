# Complete Branch Topology & Comparison - CogStack NLP

**Generated**: 2025-11-23
**Repository**: cogstack-nlp
**Purpose**: Comprehensive branch topology analysis with parent-child relationships

---

## Executive Summary

This repository has **10 branches** (including current) with a complex topology showing **parent-child branch relationships**, not just divergence from main.

### 🌳 Branch Family Tree

```
CogStack:main (upstream)
    │
    ├── [79213d5] fix/medcat-demo-model-config (OLDEST - 35 commits behind main)
    │
    ├── [971680ff] understand-codebase (OLD - merged from older main)
    │
    ├── [abec8f34] ← MAJOR DIVERGENCE POINT (older main commit)
    │   │
    │   ├── autonomous/mvp-execution (260 commits, +134 ahead)
    │   │   │
    │   │   └── development-on-ccweb-014 (361 commits, +235 ahead) ⚡ EXTENDS mvp-execution
    │   │
    │   └── develop-roadmap-phases (143 commits, +17 ahead)
    │
    └── [53dddde9] main (CURRENT - 132 commits)
        │
        ├── create-ccweb-dev-branch-014 (132 commits, +0 ahead) ← IDENTICAL to main
        │   │
        │   └── create-ccweb-dev-branch-015 (144 commits, +12 ahead) ⚡ EXTENDS 014
        │
        ├── setup-ai-agent-onboarding-015 (171 commits, +38 ahead) ⭐ RECOMMENDED
        │
        └── create-comparison-doc-011M46 (133 commits, +1 ahead) ← CURRENT BRANCH
```

### 🔑 Key Discoveries

1. **development-on-ccweb is NOT a sibling of mvp-execution**
   → It's a **child branch** that includes ALL of mvp-execution + 101 additional commits

2. **create-ccweb-015 is NOT a sibling of create-ccweb-014**
   → It's a **child branch** that includes ALL of 014 (which = main) + 12 timeline commits

3. **create-ccweb-014 is NOT actually a development branch**
   → It's **identical to main** (0 unique commits) - just a branch pointer

4. **Two distinct development lineages exist:**
   - **Lineage A** (newer, from main 53dddde9): setup-ai-agent, create-ccweb-015, comparison-doc
   - **Lineage B** (older, from abec8f34): mvp-execution → development-on-ccweb, develop-roadmap

---

## Detailed Branch Analysis

### Branch Topology Matrix

| Branch | Parent Branch | Merge-Base | Commits Ahead of Parent | Total Commits | Status |
|--------|---------------|------------|-------------------------|---------------|--------|
| **main** | CogStack:main | 53dddde9 | 0 | 132 | ✅ Current |
| **fix/medcat-demo** | old main | 79213d5 | -35 (behind) | 97 | ⚠️ Outdated |
| **understand-codebase** | old main | 971680ff | 5 | 131 | ⚠️ Old |
| **develop-roadmap** | old main (abec8f34) | abec8f34 | 17 | 143 | 📋 Planning |
| **mvp-execution** | old main (abec8f34) | abec8f34 | 134 | 260 | 🤖 CCPM |
| **development-on-ccweb** | **mvp-execution** | a624475 | 101 | 361 | 🔍 Most Complete |
| **create-ccweb-014** | main (53dddde9) | 53dddde9 | 0 | 132 | ⚠️ No work |
| **create-ccweb-015** | **create-ccweb-014** | 53dddde9 | 12 | 144 | 📊 Timeline |
| **setup-ai-agent-015** | main (53dddde9) | 53dddde9 | 38 | 171 | ⭐ MVP Base |
| **create-comparison-doc** | main (53dddde9) | 53dddde9 | 1 | 133 | 📝 This doc |

---

## Branch Lineages Explained

### Lineage A: Modern Development (from main 53dddde9)

```
main (53dddde9)
├── create-ccweb-dev-branch-014 (= main, no changes)
│   └── create-ccweb-dev-branch-015 (+12 timeline commits)
├── setup-ai-agent-onboarding-015 (+38 Clinical Care Tools commits)
└── create-comparison-doc-011M46 (+1 documentation commit)
```

**Characteristics**:
- ✅ Based on latest main (2025-11-19)
- ✅ Clean divergence points
- ✅ Focused feature development
- ✅ No merge conflicts between siblings

**Recommendation**: Use `setup-ai-agent-015` as primary, merge `create-ccweb-015` for timeline feature

---

### Lineage B: Autonomous Development (from old main abec8f34)

```
old main (abec8f34) [~2025-11-15 or earlier]
├── develop-roadmap-phases (+17 planning commits)
└── autonomous/mvp-execution (+134 CCPM + search commits)
    └── development-on-ccweb-014 (+101 more search/de-id/analytics commits)
```

**Characteristics**:
- ⚠️ Based on older main (before 53dddde9)
- ⚠️ Potential conflicts with Lineage A
- ✅ Most feature-complete (development-on-ccweb)
- ✅ Autonomous workflow infrastructure (mvp-execution)

**Recommendation**: Cherry-pick specific features, don't merge entire lineage due to divergence

---

## Complete Branch Comparison

### 1. `origin/main` (Baseline)

**Type**: Stable baseline
**Total Commits**: 132
**Parent**: CogStack:main (upstream fork)
**Last Updated**: 2025-11-19

**Key Contents**:
- MedCAT library core
- AnonCAT (anonymization)
- Documentation updates
- FAQ added recently

**Children Branches** (4):
- create-ccweb-dev-branch-014 (identical copy)
- create-ccweb-dev-branch-015 (via 014)
- setup-ai-agent-onboarding-015
- create-comparison-doc-011M46 (current)

---

### 2. `origin/autonomous/mvp-execution` 🤖

**Type**: CCPM Multi-Agent Workflow
**Total Commits**: 260 (134 ahead of old main)
**Parent**: Old main at commit abec8f34
**Last Updated**: 2025-11-20

**Key Features**:
- ✅ CCPM (Claude Code Project Manager) infrastructure
- ✅ Multi-agent orchestration (8 specialized agents)
- ✅ Autonomous task execution framework
- ✅ Query Builder implementation (Tasks 2.1-2.8)
- ✅ Boolean query parsing with Lark grammar
- ✅ Git hook orchestration

**Code Stats**:
- Files Changed: 360
- Lines Added: 804,607
- Lines Removed: 602

**Unique Files** (Sample):
```
.ccpm/
├── README.md                           # CCPM setup guide
└── ccpm.yaml                           # Multi-agent config

.claude/
├── autonomous/
│   ├── AUTONOMOUS_EXECUTION_FRAMEWORK.md
│   ├── YOLO_MODE_PROMPT.md
│   ├── mission-queue.yaml
│   ├── progress.json
│   └── reports/
│       ├── daily-2025-11-17.md
│       ├── phase-0-completion-report.md
│       └── phase-1-completion-report.md
├── agents.yaml                         # Agent definitions
├── agents/auditor.md
├── skills/autonomous-developer/SKILL.md
└── skills/document-management-patterns/SKILL.md

.git-hooks/
├── development-agent.sh                # Agent orchestration
└── load-next-task.sh                   # Task automation
```

**Children Branches** (1):
- **development-on-ccweb-014** (extends this branch)

**Pros**:
- ✅ Most advanced autonomous workflow
- ✅ Proven task execution (Search Query Builder complete)
- ✅ Comprehensive agent coordination
- ✅ Detailed progress tracking

**Cons**:
- ⚠️ Based on older main (potential merge conflicts)
- ⚠️ Complex setup (requires CCPM installation)
- ⚠️ High code volume (includes CCPM dependencies)

**Best For**:
Teams wanting to implement autonomous multi-agent development workflows.

---

### 3. `origin/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18` 🔍 ⚡ EXTENDS mvp-execution

**Type**: Comprehensive Feature Development (Child of mvp-execution)
**Total Commits**: 361 (235 ahead of old main, 101 ahead of parent mvp-execution)
**Parent**: **autonomous/mvp-execution** at commit a624475
**Last Updated**: 2025-11-22

**THIS IS THE MOST IMPORTANT DISCOVERY**: This branch is built **ON TOP OF** mvp-execution, not as a sibling!

**Relationship to mvp-execution**:
- ✅ Includes ALL 134 commits from mvp-execution
- ✅ Adds 101 additional commits on top
- ✅ Total = mvp commits + search + de-identification + analytics + timeline

**Key Features** (Beyond mvp-execution):
- ✅ **Sprint 3: Full-Text Search** (100%)
  - Visual query builder (drag-drop)
  - Lark parser (complex queries)
  - Saved searches + sharing
  - Export (CSV/JSON)
  - Analytics dashboard
  - Rate limiting

- ✅ **Sprint 4: De-identification** (100%)
  - Batch processing (Celery)
  - Manual annotation tool
  - Review dashboard
  - Audit logging

- ✅ **Sprint 2: Timeline View** (100%)
  - D3.js visualization
  - Export functionality
  - Comprehensive tests

- ✅ **Phase 5: Analytics** (100%)
  - Search analytics aggregation
  - Admin dashboard
  - User activity tracking

**Code Stats**:
- Files Changed: 667 (includes all of mvp-execution)
- Lines Added: 885,671
- Lines Removed: 2,347

**Unique Files** (Beyond mvp-execution):
```
clinical-care-tools/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── search.py
│   │   │   ├── saved_searches.py
│   │   │   ├── analytics.py
│   │   │   ├── manual_annotations.py
│   │   │   └── batch_processing.py
│   │   ├── services/
│   │   │   ├── search_service.py
│   │   │   ├── query_builder.py                # From mvp-execution
│   │   │   ├── export_service.py
│   │   │   ├── analytics_service.py
│   │   │   └── deidentification_service.py
│   │   └── tasks/
│   │       └── celery_tasks.py                 # Background tasks
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── SearchBar.vue
│   │   │   ├── QueryBuilder.vue
│   │   │   ├── SavedSearches.vue
│   │   │   ├── SearchAnalytics.vue
│   │   │   ├── PHIAnnotation.vue
│   │   │   └── BatchProcessing.vue
└── docs/
    ├── CHANGELOG.md
    └── DEPLOYMENT.md
```

**Technical Stack** (Adds to mvp-execution):
- **Backend**: +Celery, +Redis
- **Frontend**: +D3.js enhancements
- **Infrastructure**: +Celery workers

**Pros**:
- ✅ **Most feature-complete** (includes mvp-execution + 3 more sprints)
- ✅ Production features (rate limiting, analytics, batch)
- ✅ Comprehensive documentation
- ✅ Battle-tested (many bug fixes)

**Cons**:
- ⚠️ **Based on older main** (abec8f34 via mvp-execution)
- ⚠️ **Largest codebase** (885k+ lines)
- ⚠️ **Complex dependencies** (Celery, Redis on top of CCPM)
- ⚠️ **Merge conflicts likely** with Lineage A branches

**Best For**:
Feature reference - cherry-pick specific features rather than merge entire branch.

**Recommended Approach**:
1. Use `setup-ai-agent-015` as base (Lineage A)
2. **Selectively cherry-pick** features from this branch:
   - Search functionality (avoid CCPM dependencies)
   - De-identification (adapt to newer base)
   - Analytics (standalone feature)
3. **Avoid** merging entire branch due to divergence

---

### 4. `origin/claude/create-ccweb-dev-branch-014NeWxCVzNfcbd6R6RFpo18`

**Type**: Branch Pointer (No Unique Work)
**Total Commits**: 132 (0 ahead of main)
**Parent**: main at commit 53dddde9
**Last Updated**: 2025-11-19 (same as main)

**THIS IS IMPORTANT**: This is **NOT** a development branch - it's **identical to main**!

**Analysis**:
```bash
git diff origin/main origin/claude/create-ccweb-dev-branch-014NeWxCVzNfcbd6R6RFpo18
# Result: NO DIFFERENCES
```

**Purpose**:
- Created as a starting point for development
- No actual work committed to this branch
- All work went to child branch `create-ccweb-015`

**Children Branches** (1):
- **create-ccweb-dev-branch-015** (extends this = main)

**Recommendation**:
- ⚠️ Can be safely deleted (redundant with main)
- ✅ Use `create-ccweb-015` instead (has actual work)

---

### 5. `origin/claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A` 📊 ⚡ EXTENDS 014 (= main)

**Type**: Timeline Feature Implementation (Child of create-ccweb-014)
**Total Commits**: 144 (12 ahead of main/014)
**Parent**: **create-ccweb-dev-branch-014** (which = main 53dddde9)
**Last Updated**: 2025-11-22

**Relationship to 014**:
- ✅ Includes ALL commits from 014 (which = main)
- ✅ Adds 12 timeline feature commits on top
- ✅ Clean linear history

**Key Features**:
- ✅ **Sprint 2: Patient Timeline View** (100%)
  - D3.js interactive timeline
  - Timeline API (FastAPI endpoints)
  - Export (PDF, CSV, JSON)
  - Filters (date range, event type, meta-annotations)
  - Comprehensive tests (unit, integration, E2E, performance, accessibility)
  - Deployment infrastructure (Docker, Nginx, CI/CD)

**Code Stats**:
- Files Changed: 270
- Lines Added: 68,532
- Lines Removed: 5

**Unique Files** (Beyond main):
```
.specify/
├── plans/sprint-2-timeline-view-plan.md
└── tasks/sprint-2-timeline-view-tasks.md

clinical-care-tools/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/timeline.py
│   │   ├── repositories/timeline_repository.py  # Elasticsearch
│   │   ├── services/timeline_service.py
│   │   └── services/export_service.py           # PDF/CSV/JSON
│   └── tests/
│       ├── unit/test_timeline_service.py
│       ├── integration/test_timeline_api.py
│       └── e2e/test_timeline_workflow.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TimelineView.vue                 # D3.js visualization
│   │   │   ├── TimelineFilters.vue
│   │   │   └── EventDetailModal.vue
│   │   ├── stores/timeline.ts                   # Pinia store
│   │   └── views/PatientTimelinePage.vue
│   └── tests/
│       └── e2e/timeline-workflow.spec.ts
└── docker/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    └── nginx.conf
```

**Technical Highlights**:
- D3.js Visualization: Interactive, zoom, pan, filtering
- Elasticsearch: Event storage and retrieval
- Export: PDF with templates, CSV, JSON
- Performance: Optimized for 1000+ events
- Accessibility: WCAG 2.1 AA compliant

**Pros**:
- ✅ **Clean lineage** (based on current main)
- ✅ **Complete feature** (Sprint 2 done)
- ✅ **Production-ready** (Docker, tests, docs)
- ✅ **No merge conflicts** with setup-ai-agent (both from main)

**Cons**:
- ⚠️ **Single feature only** (timeline)
- ⚠️ **Missing base infrastructure** (should merge with setup-ai-agent)

**Best For**:
Adding patient timeline to an existing Clinical Care Tools base.

**Recommended Approach**:
1. Start with `setup-ai-agent-015` (base infrastructure)
2. **Cherry-pick** timeline commits from this branch
3. Integrate timeline into setup-ai-agent base

---

### 6. `origin/claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat` ⭐ **RECOMMENDED PRIMARY**

**Type**: Complete MVP Base Infrastructure
**Total Commits**: 171 (38 ahead of main)
**Parent**: main at commit 53dddde9
**Last Updated**: 2025-11-23 (MOST RECENT!)

**Key Features**:
- ✅ **Phase 0**: Project structure (backend + frontend)
- ✅ **Phase 1**: Authentication, RBAC, Audit Logging, User Management
- ✅ **Phase 2**: Projects, Tasks, User Management UI
- ✅ **Phase 3**: Document Management (upload, encryption, deduplication)
- ✅ **PHI Processing**: CogStack-ModelServe client
- ✅ **Patient Aggregation**: Fuzzy matching
- ✅ **Module Registry**: Dynamic module loading
- ✅ **Security**: PHI de-identification, log sanitization

**Code Stats**:
- Files Changed: 145
- Lines Added: 25,862
- Lines Removed: 8

**Complete Infrastructure**:
```
clinical-care-tools/
├── backend/
│   ├── alembic/                        # 9 migrations
│   ├── app/
│   │   ├── api/v1/endpoints/
│   │   │   ├── auth.py                 # JWT auth
│   │   │   ├── users.py                # User CRUD
│   │   │   ├── projects.py             # Project management
│   │   │   ├── tasks.py                # Task tracking
│   │   │   ├── documents.py            # Document upload
│   │   │   └── health.py               # Health check
│   │   ├── clients/
│   │   │   ├── medcat_client.py
│   │   │   └── modelserve_client.py    # CogStack-ModelServe
│   │   ├── models/
│   │   │   ├── user.py                 # Bcrypt hashing
│   │   │   ├── session.py              # JWT sessions
│   │   │   ├── audit_log.py            # HIPAA audit
│   │   │   ├── project.py
│   │   │   ├── task.py
│   │   │   ├── document.py             # Encrypted storage
│   │   │   ├── extracted_entity.py     # PHI/clinical entities
│   │   │   ├── patient.py              # Aggregated records
│   │   │   └── module.py               # Dynamic registry
│   │   └── services/
│   │       ├── auth_service.py
│   │       ├── audit_service.py        # Immutable audit trail
│   │       ├── document_service.py     # Background processing
│   │       ├── phi_classifier.py       # PHI type mapping
│   │       ├── deduplication_service.py
│   │       └── encryption_service.py    # AES-256
│   └── tests/                          # Unit + integration
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── DocumentUpload.vue
    │   │   ├── UserManagement.vue
    │   │   ├── ProjectManagement.vue
    │   │   └── TaskList.vue
    │   ├── router/                     # Vue Router
    │   ├── stores/                     # Pinia stores
    │   └── views/
    └── tests/
```

**Database Models** (9):
1. `User` - Bcrypt password hashing, RBAC roles
2. `Session` - JWT session management
3. `AuditLog` - HIPAA-compliant immutable audit trail
4. `Project` - Project management
5. `Task` - Task tracking with status
6. `Document` - Encrypted document storage (AES-256)
7. `ExtractedEntity` - PHI and clinical entities from NLP
8. `Patient` - Aggregated patient records with fuzzy matching
9. `Module` - Dynamic module registry for plugins

**API Endpoints**:
- `POST /api/v1/auth/login` - JWT authentication
- `GET /api/v1/auth/me` - Current user
- `GET /api/v1/users` - List users (RBAC: admin)
- `POST /api/v1/users` - Create user
- `GET /api/v1/projects` - List projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/tasks` - List tasks
- `POST /api/v1/documents` - Upload document (encrypted)
- `GET /api/v1/health` - Health check

**Compliance Features**:
- ✅ HIPAA audit logging (immutable, append-only)
- ✅ PHI de-identification in logs
- ✅ Document encryption at rest (AES-256)
- ✅ RBAC authorization
- ✅ Session management with JWT

**Pros**:
- ✅ **Production-ready MVP** - Complete base
- ✅ **Clean codebase** (+25k lines, organized)
- ✅ **HIPAA-compliant** from day 1
- ✅ **Modular architecture** - Plugin system ready
- ✅ **Comprehensive testing** (unit + integration)
- ✅ **Recent activity** (2025-11-23)
- ✅ **No merge conflicts** with create-ccweb-015

**Cons**:
- ⚠️ Missing timeline (add from create-ccweb-015)
- ⚠️ Missing search (cherry-pick from development-on-ccweb)
- ⚠️ Missing analytics (cherry-pick from development-on-ccweb)

**Best For**:
**PRIMARY BASE BRANCH** - Start here, add features from other branches.

**Migration Strategy**:
1. ✅ Use this as base (Week 1)
2. ✅ Merge timeline from `create-ccweb-015` (Week 2)
3. ✅ Cherry-pick search from `development-on-ccweb` (Week 3-4)
4. ✅ Cherry-pick analytics from `development-on-ccweb` (Week 5)

---

### 7. `origin/claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL` 📋

**Type**: Strategic Planning & Skeletal Implementation
**Total Commits**: 143 (17 ahead of old main)
**Parent**: Old main at commit abec8f34
**Last Updated**: 2025-11-18

**Key Features**:
- ✅ **Sprints 2-9.5 Planning** - Complete plans and tasks
- ✅ **Skeletal implementations** for Sprints 2-5.5
- ✅ **Event Bus Infrastructure** (Sprint 5.5)
- ✅ **ICD-10 Clinical Coding** (Sprint 5, skeletal)

**Code Stats**:
- Files Changed: 166
- Lines Added: 30,740
- Lines Removed: 6

**Roadmap Coverage**:
- Sprint 2: Timeline View (skeletal)
- Sprint 3: Full-Text Search (skeletal)
- Sprint 4: De-identification (skeletal)
- Sprint 5: Clinical Coding (skeletal)
- Sprint 5.5: Event Bus (skeletal)
- Sprint 6-9.5: Planning only

**Pros**:
- ✅ **Complete roadmap** vision
- ✅ **Well-structured** plans
- ✅ **Event-driven architecture** foundation

**Cons**:
- ⚠️ Based on older main (abec8f34)
- ⚠️ Mostly planning/skeletal (limited working code)

**Best For**:
Strategic planning reference - use plans, not code.

---

### 8. `origin/claude/understand-codebase-01Snfj6ziqMUNHxa6sBuv9eB` 📚

**Type**: Documentation
**Total Commits**: 131 (5 unique)
**Parent**: Old main at commit 971680ff
**Last Updated**: 2025-11-17

**Key Features**:
- ✅ NHS Windows RDP deployment guide
- ✅ HTTPS/TLS configuration (Nginx)
- ✅ Large-scale deployment strategies
- ✅ Workflow robustness enhancements

**Best For**:
Reference documentation for production deployment.

---

### 9. `origin/fix/medcat-demo-model-config` 🔧

**Type**: Bugfix (Outdated)
**Total Commits**: 97 (35 behind main)
**Parent**: Very old main at commit 79213d5
**Last Updated**: 2025-11-17

**Status**: ⚠️ **OUTDATED** - 35 commits behind main

**Recommendation**:
- ⚠️ Do not use - superseded by newer work
- ✅ Cherry-pick fix if needed

---

### 10. `origin/claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK` 📝

**Type**: Documentation (This Branch)
**Total Commits**: 133 (1 ahead of main)
**Parent**: main at commit 53dddde9
**Last Updated**: 2025-11-23 (NOW)

**Purpose**: This comprehensive branch comparison document.

---

## Parent-Child Relationship Details

### Relationship 1: mvp-execution → development-on-ccweb

```
autonomous/mvp-execution (134 commits)
    │
    │ Contains:
    │ - CCPM infrastructure
    │ - Query Builder (Tasks 2.1-2.8)
    │ - Boolean parsing with Lark
    │ - Multi-agent workflow
    │
    └── development-on-ccweb-014 (+101 commits)
        │
        │ Adds:
        │ - Search (Sprint 3 complete)
        │ - De-identification (Sprint 4 complete)
        │ - Analytics (Phase 5 complete)
        │ - Timeline (Sprint 2 complete)
        │
        Total: 235 commits ahead of old main
```

**How to verify**:
```bash
# development-on-ccweb includes ALL of mvp-execution
git log --oneline origin/autonomous/mvp-execution..origin/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18 | wc -l
# Result: 101 (commits ADDED by development-on-ccweb)

# mvp-execution has NOTHING that development-on-ccweb doesn't
git log --oneline origin/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18..origin/autonomous/mvp-execution | wc -l
# Result: 0 (no commits unique to mvp-execution)
```

**Merge-base**:
```bash
git merge-base origin/autonomous/mvp-execution origin/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18
# Result: a624475 (last commit of mvp-execution)
```

**Implications**:
- ✅ **development-on-ccweb is a strict superset** of mvp-execution
- ✅ All CCPM infrastructure is included
- ⚠️ Cannot use mvp-execution alone - development-on-ccweb has more features
- ⚠️ Both based on old main (merge conflicts with Lineage A)

---

### Relationship 2: create-ccweb-014 → create-ccweb-015

```
create-ccweb-dev-branch-014 (= main 53dddde9, 0 unique commits)
    │
    │ Contains:
    │ - Identical to main
    │ - No unique work
    │
    └── create-ccweb-dev-branch-015 (+12 commits)
        │
        │ Adds:
        │ - Timeline API (backend)
        │ - Timeline UI (D3.js visualization)
        │ - Timeline Export (PDF/CSV/JSON)
        │ - Timeline Tests (unit/integration/E2E)
        │ - Timeline Deployment (Docker/Nginx)
        │
        Total: 12 commits ahead of main
```

**How to verify**:
```bash
# create-ccweb-014 is identical to main
git diff origin/main origin/claude/create-ccweb-dev-branch-014NeWxCVzNfcbd6R6RFpo18
# Result: (empty - no differences)

# create-ccweb-015 adds 12 commits
git log --oneline origin/claude/create-ccweb-dev-branch-014NeWxCVzNfcbd6R6RFpo18..origin/claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A | wc -l
# Result: 12
```

**Implications**:
- ✅ **create-ccweb-014 can be deleted** (redundant with main)
- ✅ **create-ccweb-015 is effectively main + timeline**
- ✅ Clean merge with setup-ai-agent-015 (both from main)

---

## Feature Availability Matrix

| Feature | main | mvp-exec | dev-on-ccweb | ccweb-014 | ccweb-015 | setup-ai-agent | roadmap | understand | fix/demo |
|---------|------|----------|--------------|-----------|-----------|----------------|---------|-----------|----------|
| **Base Infrastructure** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ Complete | ⚠️ Skeletal | ❌ | ❌ |
| **Authentication (JWT)** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ Complete | ⚠️ Skeletal | ❌ | ❌ |
| **RBAC Authorization** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ Complete | ⚠️ Skeletal | ❌ | ❌ |
| **HIPAA Audit Logging** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ Complete | ⚠️ Skeletal | ❌ | ❌ |
| **User Management** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ Full CRUD | ⚠️ Skeletal | ❌ | ❌ |
| **Document Upload** | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ + Encryption | ⚠️ Skeletal | ❌ | ❌ |
| **Timeline View** | ❌ | ❌ | ✅ D3.js | ❌ | ✅ Complete | ❌ | ⚠️ Skeletal | ❌ | ❌ |
| **Full-Text Search** | ❌ | ✅ Query Builder | ✅ Complete | ❌ | ❌ | ❌ | ⚠️ Skeletal | ❌ | ❌ |
| **Saved Searches** | ❌ | ❌ | ✅ Complete | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Search Analytics** | ❌ | ❌ | ✅ Complete | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **De-identification** | ⚠️ AnonCAT | ❌ | ✅ + Manual | ❌ | ❌ | ✅ PHI Classifier | ⚠️ Skeletal | ❌ | ❌ |
| **Batch Processing** | ❌ | ❌ | ✅ Celery | ❌ | ❌ | ✅ Background | ⚠️ Skeletal | ❌ | ❌ |
| **Patient Aggregation** | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ Fuzzy Match | ❌ | ❌ | ❌ |
| **Module Registry** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ Dynamic | ❌ | ❌ | ❌ |
| **ICD-10 Coding** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ Skeletal | ❌ | ❌ |
| **Event Bus** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ⚠️ Skeletal | ❌ | ❌ |
| **CCPM Workflow** | ❌ | ✅ Complete | ✅ (inherited) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Lark Query Parser** | ❌ | ✅ Complete | ✅ (inherited) | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Deployment Docs** | ⚠️ Basic | ⚠️ Partial | ✅ Complete | ❌ | ✅ Complete | ⚠️ Partial | ✅ Complete | ✅ NHS | ❌ |

---

## Code Statistics Comparison

| Branch | Total Commits | Ahead of Parent | Files Changed | Lines Added | Lines Removed | Net Change |
|--------|--------------|-----------------|---------------|-------------|---------------|------------|
| main | 132 | - | - | - | - | (baseline) |
| mvp-execution | 260 | +134 (vs old main) | 360 | 804,607 | 602 | +804,005 |
| development-on-ccweb | 361 | +101 (vs mvp) <br> +235 (vs old main) | 667 | 885,671 | 2,347 | +883,324 |
| ccweb-014 | 132 | 0 (= main) | 0 | 0 | 0 | 0 |
| ccweb-015 | 144 | +12 (vs 014/main) | 270 | 68,532 | 5 | +68,527 |
| setup-ai-agent | 171 | +38 (vs main) | 145 | 25,862 | 8 | +25,854 |
| develop-roadmap | 143 | +17 (vs old main) | 166 | 30,740 | 6 | +30,734 |
| understand-codebase | 131 | +5 (vs very old main) | - | - | - | (small docs) |
| fix/medcat-demo | 97 | -35 (behind main) | - | - | - | (bugfix) |

---

## Complexity Analysis

| Branch | Setup Complexity | Runtime Dependencies | External Services | Maintenance | Merge Difficulty |
|--------|-----------------|---------------------|------------------|-------------|------------------|
| **setup-ai-agent** ⭐ | 🟢 Low | FastAPI, PostgreSQL | CogStack-ModelServe | 🟢 Low | 🟢 Easy (from main) |
| **ccweb-015** | 🟢 Low | +D3.js, +Elasticsearch | +Elasticsearch | 🟡 Medium | 🟢 Easy (from main) |
| **development-on-ccweb** | 🔴 Very High | +Celery, +Redis, +CCPM | +Celery, +Redis, +ES, +CCPM | 🔴 Very High | 🔴 Hard (old main) |
| **mvp-execution** | 🔴 Very High | +CCPM, +agents | +CCPM server | 🔴 Very High | 🔴 Hard (old main) |
| **develop-roadmap** | 🟢 Low | Minimal (skeletal) | None | 🟢 Low | 🔴 Hard (old main) |

---

## Recommended Merge Strategy

### 🎯 Option 1: Incremental Feature Addition (RECOMMENDED)

**Base**: `setup-ai-agent-onboarding-015` ⭐

**Week 1: Establish Base**
```bash
git checkout -b main-development origin/claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat
cd clinical-care-tools/backend && pytest
cd ../frontend && npm run test
```

**Week 2: Add Timeline**
```bash
# Cherry-pick timeline commits from ccweb-015
git log --oneline origin/claude/create-ccweb-dev-branch-014NeWxCVzNfcbd6R6RFpo18..origin/claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A

# Cherry-pick the 12 timeline commits
git cherry-pick d585be2..e22661d

# Resolve conflicts (minimal, both from main)
# Test integration
pytest && npm run test
```

**Week 3-4: Add Search (Selective)**
```bash
# From development-on-ccweb, cherry-pick ONLY search (avoid CCPM)
# Focus on:
# - backend/app/services/search_service.py
# - backend/app/services/query_builder.py (includes Lark parser)
# - frontend/src/components/SearchBar.vue
# - frontend/src/components/QueryBuilder.vue

# Skip:
# - CCPM infrastructure (too complex)
# - Celery dependencies (not needed for search MVP)

git cherry-pick <search-commits-only>
```

**Week 5: Add Analytics**
```bash
# Cherry-pick analytics from development-on-ccweb
git cherry-pick <analytics-commits>

# Files:
# - backend/app/services/analytics_service.py
# - backend/app/api/v1/endpoints/analytics.py
# - frontend/src/components/SearchAnalytics.vue
```

**Result**: Clean MVP with timeline, search, and analytics, based on solid foundation.

---

### 🎯 Option 2: Start from Development-on-ccweb (High Risk)

**Only if**: You want ALL features immediately and can handle complexity.

**Risks**:
- ⚠️ Based on old main (merge conflicts)
- ⚠️ Complex dependencies (CCPM, Celery, Redis)
- ⚠️ High maintenance burden
- ⚠️ May include experimental code

**Approach**:
```bash
git checkout -b full-featured origin/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18

# Merge main to get latest CogStack updates
git merge origin/main  # Expect conflicts!

# Resolve conflicts carefully
# Test everything
```

---

### 🎯 Option 3: Parallel Development (Advanced)

**For teams**: Multiple developers working simultaneously.

**Strategy**:
```
Team A: Continues on setup-ai-agent-015 (base infrastructure)
Team B: Works on ccweb-015 timeline (feature branch)
Team C: Extracts search from development-on-ccweb (refactoring)

Integration Point: Merge all into main-development after testing
```

---

## Migration Checklist

### Before Merging Any Branch

- [ ] **Read CONTEXT.md** in target branch
- [ ] **Verify parent branch** - Is it based on current main or old main?
- [ ] **Check dependencies** - Python packages, npm packages compatible?
- [ ] **Database migrations** - Alembic versions compatible?
- [ ] **Test suite runs** - All tests pass?
- [ ] **Review git history** - Any concerning commits?
- [ ] **Check for conflicts** - File-level conflicts with destination?
- [ ] **Validate compliance** - HIPAA audit logging intact?
- [ ] **Review parent-child relationships** - Does branch include parent's commits?

### After Merging

- [ ] **Update CONTEXT.md** with merge details
- [ ] **Run full test suite** (unit + integration + E2E)
- [ ] **Update dependencies** - `pip install -r requirements.txt`, `npm install`
- [ ] **Run migrations** - `alembic upgrade head`
- [ ] **Smoke test** - Basic functionality works?
- [ ] **Update README** if structure changed
- [ ] **Tag release** - `git tag -a v0.2.0 -m "Merged timeline feature"`
- [ ] **Document parent branch** in merge commit

---

## Conflict Resolution Strategy

### Expected Conflicts

**Between Lineage A branches** (setup-ai-agent, ccweb-015, comparison-doc):
- ✅ **Minimal conflicts** - all based on same main (53dddde9)
- Files: `CONTEXT.md` (manual merge)
- Database: May need to renumber migration versions

**Between Lineage A and Lineage B** (setup-ai-agent vs development-on-ccweb):
- ⚠️ **Major conflicts** - different base commits (53dddde9 vs abec8f34)
- Files: `CONTEXT.md`, models, API endpoints, frontend routes
- Database: Significant schema differences
- Resolution: Cherry-pick specific commits, don't merge branches

**Between development-on-ccweb and mvp-execution**:
- ✅ **No conflicts** - development-on-ccweb includes ALL of mvp-execution
- Note: development-on-ccweb is strict superset

---

## Branch Lifecycle Recommendations

### Keep (Active Development)

| Branch | Action | Priority |
|--------|--------|----------|
| **setup-ai-agent-015** | PRIMARY BASE | 🔴 CRITICAL |
| **ccweb-015** | Merge timeline into primary | 🟠 HIGH |
| **development-on-ccweb** | Cherry-pick features | 🟠 HIGH |
| **develop-roadmap** | Use for planning reference | 🟡 MEDIUM |

### Archive (Superseded)

| Branch | Reason | Action |
|--------|--------|--------|
| **ccweb-014** | Identical to main, no work | Delete after merging 015 |
| **mvp-execution** | Superseded by development-on-ccweb | Archive (included in dev-on-ccweb) |
| **fix/medcat-demo** | 35 commits behind, outdated | Archive (fix likely in main) |

### Review (Case-by-Case)

| Branch | Review Needed | Decision |
|--------|---------------|----------|
| **understand-codebase** | Deployment docs useful? | Keep for NHS deployment reference |
| **comparison-doc** | This branch | Merge into main after review |

---

## Conclusion & Next Steps

### 🎯 Recommended Primary Strategy

**Step 1: Establish Base** (Week 1)
```bash
git checkout -b clinical-care-tools-main origin/claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat
# This is your new main development branch
```

**Step 2: Add Timeline** (Week 2)
```bash
# Clean merge - both from main 53dddde9
git merge origin/claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A
# or cherry-pick: git cherry-pick d585be2..e22661d
```

**Step 3: Add Search** (Week 3-4)
```bash
# Selective cherry-pick from development-on-ccweb
# Skip CCPM infrastructure, focus on search features
git cherry-pick <search-service-commits>
git cherry-pick <query-builder-commits>
git cherry-pick <search-ui-commits>
```

**Step 4: Add Analytics** (Week 5)
```bash
# Cherry-pick analytics from development-on-ccweb
git cherry-pick <analytics-commits>
```

**Result**:
- ✅ Production-ready base (setup-ai-agent)
- ✅ Timeline visualization (ccweb-015)
- ✅ Full-text search (development-on-ccweb, selective)
- ✅ Analytics dashboard (development-on-ccweb)
- ✅ No CCPM complexity
- ✅ Based on current main (no old conflicts)

---

### 📊 Branch Relationship Summary

**Lineage A** (Modern, from main 53dddde9):
```
main
├── setup-ai-agent-015 ⭐ (PRIMARY BASE)
├── ccweb-014 → ccweb-015 (TIMELINE FEATURE)
└── comparison-doc (THIS DOCUMENT)
```

**Lineage B** (Older, from abec8f34):
```
old main
├── mvp-execution (CCPM)
│   └── development-on-ccweb (MOST COMPLETE) ← includes mvp-execution
└── develop-roadmap (PLANNING)
```

**Strategy**:
- Use Lineage A as foundation
- Cherry-pick features from Lineage B
- Avoid merging entire Lineage B (conflicts + complexity)

---

### 🚀 Final Recommendation

**Start with**: `setup-ai-agent-onboarding-015` ⭐

**Add from**:
1. **ccweb-015** → Timeline (clean merge)
2. **development-on-ccweb** → Search (cherry-pick)
3. **development-on-ccweb** → Analytics (cherry-pick)
4. **develop-roadmap** → Plans (documentation only)

**Avoid**:
- ❌ Merging entire development-on-ccweb (too complex)
- ❌ Merging mvp-execution separately (included in development-on-ccweb)
- ❌ Using ccweb-014 (redundant with main)
- ❌ Using old branches (fix/medcat-demo, understand-codebase)

**Timeline**:
- Week 1: Base establishment (setup-ai-agent)
- Week 2: Timeline integration (ccweb-015)
- Weeks 3-4: Search extraction (development-on-ccweb)
- Week 5: Analytics addition (development-on-ccweb)
- Week 6: Testing & documentation

---

**Questions? Review this document and CONTEXT.md in each branch for detailed information.**

**Last Updated**: 2025-11-23
**Version**: 2.0.0 (Complete Topology Analysis)
