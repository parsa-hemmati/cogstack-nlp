# Development Roadmap

**Last Updated**: 2025-11-22 (Phase 0 complete)
**Environment**: Claude Code on Web (PostgreSQL 16, Redis 7.0, Node.js 22, Python 3.11)

---

## Current Priority (Start This Next)

### Sprint 1: Patient Search & Discovery
**Duration**: ~8 weeks (part of MVP)
**Location**: .specify/specifications/clinical-care-tools-base-app.md
**Status**: Starting implementation
**CogStack Products**: Clinical Language AI (80%), Enterprise Search (40%)

**Prerequisites**: ✅ Phase 0 complete

**Next Task**: Implement patient search API endpoint (Sprint 1, Task 1.1)

---

## After Current (In Order)

### 1. Sprint 2: Timeline View
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-2-timeline-view.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Enterprise Search (visualization)

### 2. Sprint 3: Full-Text Search
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-3-full-text-search.md
**Depends on**: Sprint 1 complete (can parallelize with Sprint 2)
**CogStack Products**: Enterprise Search (full-text)

### 3. Sprint 4: De-Identification
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-4-ehr-deidentification.md
**Depends on**: Sprint 1 complete
**CogStack Products**: EHR De-Identification

### 4. Sprint 5: Clinical Coding
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-5-clinical-coding.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Clinical Coding

### 5. Sprint 6: Clinical Decision Support
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-6-clinical-decision-support.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Clinical Language AI (decision support)

### 6. Sprint 7: Automated Alerting
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-7-automated-alerting.md
**Depends on**: Sprint 6 complete
**CogStack Products**: Automated Alerting

### 7. Sprint 8: Population Health Dashboards
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-8-population-health-dashboards.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Population Health Dashboards

### 8. Sprint 9: Advanced Analytics
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-9-advanced-analytics.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Population Health Dashboards (analytics)

---

## Completed

### Phase 0: Environment Setup (Web-Adapted) ✅
**Completed**: 2025-11-22
**Duration**: ~15 hours
**Status**: All tasks complete

**Deliverables**:
- Backend: FastAPI + PostgreSQL + Redis + MedCAT mock (23 files)
- Frontend: Vue 3 + Vite + TypeScript + Vuetify (32 files)
- Database `clinical_care_tools` created and verified
- Health check endpoint: All services operational
- CONTEXT.md updated with Phase 0 entry

---

## Backlog

- Production Docker deployment setup
- CogStack-ModelServe integration (production environment)
- CogStack-NiFi integration (enterprise deployment)
- CI/CD pipeline setup
- Automated testing infrastructure
- HIPAA compliance audit

---

## Timeline Overview

**MVP (Phase 0 + Sprint 1)**: 11 weeks (~310 hours)
**Sprints 2-9**: 36 weeks (~1,100 hours)
**Total**: 47 weeks (~1,410 hours)

---

## Continuation Instructions

**When Phase 0 completes**:
1. Move Phase 0 to "Completed" section
2. Move "Sprint 1: Patient Search & Discovery" to "Current Priority"
3. Start Sprint 1 task 1.1 **immediately** (NO STOPPING)
4. Update CONTEXT.md with Phase 0 completion notes

**When Sprint 1 completes**:
1. Check this roadmap
2. Move Sprint 1 to "Completed"
3. Choose next sprint based on priority/dependencies
4. Start next sprint **immediately** (NO STOPPING)

**NEVER ask "What's next?" - Just read this file and continue!**
