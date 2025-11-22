# Active TODOs

**Last Updated**: 2025-11-22
**Session**: Phase 0 Environment Setup (Web-Adapted)

---

## Critical (Block Release)

- [ ] **Environment**: Create web-adapted development environment
  - Phase: Phase 0
  - Assigned: Current session
  - Blocker: Cannot start Sprint 1 without environment

---

## High Priority (This Phase)

- [ ] **Infrastructure**: Setup PostgreSQL database schema
  - File: TBD (will create in backend/)
  - Impact: Required for all patient data storage
  - Assigned: Current session

- [ ] **Infrastructure**: Setup Redis caching layer
  - File: TBD (will create in backend/)
  - Impact: Required for session management
  - Assigned: Current session

- [ ] **Integration**: Create MedCAT mock client for testing
  - File: TBD (will create in backend/app/clients/)
  - Impact: Enables development without Docker
  - Assigned: Current session

---

## Medium Priority (Next Phase)

- [ ] **Documentation**: Create Docker deployment guide
  - File: docs/deployment/docker-deployment.md
  - Impact: Production deployment reference
  - Assigned: Future session

- [ ] **Documentation**: Document environment adaptations
  - File: CONTEXT.md
  - Impact: Future developers understand web vs production differences
  - Assigned: Current session

---

## Low Priority (Backlog)

None yet - will populate as development progresses

---

## Discovered During Codebase Scan

None yet - will run scan after initial structure created

---

## Notes

**Environment Context**:
- Web environment: PostgreSQL 16, Redis 7.0, Python 3.11, Node.js 22
- Limitations: No Docker, no system packages, limited network
- Strategy: Build with native tools, document Docker for production
