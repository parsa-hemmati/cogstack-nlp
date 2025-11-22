# Development Roadmap

**Last Updated**: 2025-11-22
**Environment**: Claude Code on Web (PostgreSQL 16, Redis 7.0, Node.js 22, Python 3.11)

---

## Current Priority (Start This Next)

### Phase 0: Environment Setup (Web-Adapted)
**Duration**: ~15 hours (adapted from 20 hours)
**Location**: .specify/tasks/clinical-care-tools-base-tasks.md
**Status**: 7 tasks, ready to start

**Environment Adaptations**:
- ✅ PostgreSQL 16: Available natively (no Docker needed)
- ✅ Redis 7.0: Available natively (no Docker needed)
- ❌ Docker: Not available in web environment
- ❌ CogStack-ModelServe: Cannot deploy in Docker
- ✅ Workaround: Mock MedCAT client for development/testing
- 📝 Documentation: Full Docker deployment guide for production

**Tasks**:
1. Create project structure (backend + frontend)
2. Setup PostgreSQL database (native)
3. Setup Redis (native)
4. Create FastAPI backend scaffold
5. Create Vue 3 frontend scaffold
6. Create MedCAT mock client
7. Create environment verification script

---

## After Current (In Order)

### 1. Sprint 1: Patient Search & Discovery
**Duration**: ~8 weeks (part of MVP)
**Location**: .specify/specifications/clinical-care-tools-base-app.md
**Depends on**: Phase 0 complete
**CogStack Products**: Clinical Language AI (80%), Enterprise Search (40%)

### 2. Sprint 2: Timeline View
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-2-timeline-view.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Enterprise Search (visualization)

### 3. Sprint 3: Full-Text Search
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-3-full-text-search.md
**Depends on**: Sprint 1 complete (can parallelize with Sprint 2)
**CogStack Products**: Enterprise Search (full-text)

### 4. Sprint 4: De-Identification
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-4-ehr-deidentification.md
**Depends on**: Sprint 1 complete
**CogStack Products**: EHR De-Identification

### 5. Sprint 5: Clinical Coding
**Duration**: 4 weeks
**Location**: .specify/specifications/sprint-5-clinical-coding.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Clinical Coding

### 6. Sprint 6: Clinical Decision Support
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-6-clinical-decision-support.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Clinical Language AI (decision support)

### 7. Sprint 7: Automated Alerting
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-7-automated-alerting.md
**Depends on**: Sprint 6 complete
**CogStack Products**: Automated Alerting

### 8. Sprint 8: Population Health Dashboards
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-8-population-health-dashboards.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Population Health Dashboards

### 9. Sprint 9: Advanced Analytics
**Duration**: 5 weeks
**Location**: .specify/specifications/sprint-9-advanced-analytics.md
**Depends on**: Sprint 1 complete
**CogStack Products**: Population Health Dashboards (analytics)

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
