# Branch Comparison Analysis

**Generated:** November 23, 2025  
**Repository:** parsa-hemmati/cogstack-nlp

## Overview

This document compares all active development branches in the fork against the `main` branch.

---

## Branch Summary

### 1. **development** (Current Branch - Just Pushed)
**Last Updated:** 2 days ago  
**Status:** Active development  
**Purpose:** Main development branch with new skills and sprint planning

**Key Changes:**
- Added 4 new Claude skills:
  - `elasticsearch-query-expert` - Elasticsearch query optimization
  - `redis-caching-patterns` - Redis caching strategies
  - `search-performance-optimizer` - Search performance tuning
  - `test-coverage-analyzer` - Test coverage analysis
- Added comprehensive sprint planning docs (Sprints 2-9.5)
- Removed deprecated GitHub workflow for medcat-demo-app
- **Total Changes:** ~10,000+ lines added

**Changed Areas:**
- `.claude/skills/` - New skill definitions
- `.specify/plans/` - Sprint planning documents
- `.specify/tasks/` - Sprint task breakdowns

---

### 2. **autonomous/mvp-execution**
**Last Updated:** 3 days ago  
**Status:** Experimental autonomous agent framework  
**Purpose:** Autonomous AI agent execution system with YOLO mode

**Key Changes:**
- CCPM (Claude Code Project Manager) framework (~900 lines)
- Autonomous execution framework with validation safeguards
- Git hook orchestration for automated workflows
- Mission queue system for autonomous task management
- Blocker tracking system
- Agent configuration and auditor definitions
- **Total Changes:** ~15,000+ lines added

**Key Files:**
- `.ccpm/` - CCPM configuration and documentation
- `.claude/autonomous/` - Autonomous mode frameworks
- `.claude/agents/` - Agent definitions
- Blocker documentation for Docker and MedCAT models

**Notable Features:**
- YOLO mode for aggressive autonomous development
- Validation checklists and safeguards
- Progress tracking in JSON format

---

### 3. **claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A**
**Last Updated:** 14 hours ago (Most Recent Active Development)  
**Status:** Active feature development  
**Purpose:** Timeline view implementation + deployment infrastructure

**Key Changes:**
- Sprint 2 timeline view complete implementation
- Comprehensive testing infrastructure (GitHub Actions workflows)
- Production deployment configuration
- Phase 5-7 implementation documentation
- Testing guide and audit documentation
- **Total Changes:** ~8,000+ lines added

**Key Files:**
- `.specify/plans/sprint-2-timeline-view-plan.md` (1,580 lines)
- `.specify/tasks/sprint-2-timeline-view-tasks.md` (1,428 lines)
- `AUDIT.md` (904 lines) - Comprehensive audit trail
- `TESTING.md` (728 lines) - Testing documentation
- `clinical-care-tools/` - Enhanced with CI/CD, env configs, coverage

**Notable Features:**
- GitHub Actions workflows for backend/frontend testing
- Environment configuration examples (.env files)
- Coverage configuration for Python backend

---

### 4. **claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK**
**Last Updated:** 6 minutes ago  
**Status:** Documentation branch  
**Purpose:** Branch comparison documentation (meta!)

**Key Changes:**
- Two comprehensive branch comparison documents
- **Total Changes:** ~2,200 lines documentation

**Files:**
- `BRANCH_COMPARISON.md` (947 lines)
- `BRANCH_COMPARISON_COMPLETE.md` (1,245 lines)

---

### 5. **claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL**
**Last Updated:** 5 days ago  
**Status:** Planning and roadmap definition  
**Purpose:** Complete sprint planning for Sprints 2-9.5

**Key Changes:**
- Comprehensive sprint plans for entire development roadmap
- Sprint 2: Timeline View (1,436 lines plan)
- Sprint 3: Full-Text Search (1,344 lines plan)
- Sprint 4: EHR Deidentification (944 lines plan)
- Sprint 5: Clinical Coding (644 lines plan)
- Sprint 5.5: Event Bus Architecture (522 lines plan)
- Sprints 6-9.5: Skeletal plans for advanced features
- **Total Changes:** ~10,000+ lines added

**Sprint Coverage:**
- Sprint 2: Timeline View ✓
- Sprint 3: Full-Text Search ✓
- Sprint 4: EHR Deidentification ✓
- Sprint 5: Clinical Coding ✓
- Sprint 5.5: Event Bus ✓
- Sprints 6-9.5: Advanced features (skeletal plans)

---

### 6. **claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18**
**Last Updated:** 24 hours ago  
**Status:** Active development with autonomous features  
**Purpose:** CCPM integration + autonomous workflows

**Key Changes:**
- CCPM framework integration
- Agent chaining and coordination system
- Autonomous loop design and testing
- Audit findings and agent status tracking
- Rate limiting for search endpoints
- **Total Changes:** ~15,000+ lines added

**Key Features:**
- Agent chaining framework (712 lines)
- Autonomous loop design (1,251 lines)
- CCPM autonomous integration
- Workflow test results documentation

**Similar to:** `autonomous/mvp-execution` but with more agent coordination

---

### 7. **claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat**
**Last Updated:** 4 hours ago (Recent Activity)  
**Status:** Active infrastructure development  
**Purpose:** Module registry + dynamic service loading

**Key Changes:**
- Pipeline and roadmap management system
- Todo tracking system (active/backlog/completed)
- Backend infrastructure setup
- Database migrations (Alembic)
- Module registry for dynamic loading
- Enhanced CONTEXT.md (1,063 lines added)
- **Total Changes:** ~3,000+ lines added

**Key Files:**
- `.claude/pipeline/PIPELINE_STATUS.md`
- `.claude/roadmap/ROADMAP.md`
- `.claude/todos/` - Todo management system
- `clinical-care-tools/backend/` - Database setup and migrations

**Notable Features:**
- Alembic migrations for documents, entities, patients tables
- Backend README with comprehensive setup guide
- Modular architecture with dynamic service loading

---

### 8. **fix/medcat-demo-model-config**
**Last Updated:** 6 days ago  
**Status:** Bug fix branch  
**Purpose:** Fix MedCAT demo model configuration

**Key Changes:**
- Removed many Claude skills (~7,000 lines removed)
- Removed git hooks infrastructure (~300 lines removed)
- Fixed MedCAT model path configuration
- Added missing dependencies
- **Total Changes:** Net deletion of ~7,000 lines

**Note:** This branch appears to be cleaning up and focusing the repository

---

## Branch Relationships and Merge Strategy

### Current State
```
main (base)
├── development (newest features + skills)
├── autonomous/mvp-execution (autonomous framework)
├── claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A (timeline + CI/CD)
├── claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL (planning docs)
├── claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18 (agent coordination)
├── claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat (infrastructure)
├── claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK (docs)
└── fix/medcat-demo-model-config (cleanup)
```

### Recommended Merge Order

1. **First:** `fix/medcat-demo-model-config` - Clean up base
2. **Second:** `claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL` - Establish planning docs
3. **Third:** `development` - Add new skills on top of clean base
4. **Fourth:** `claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat` - Infrastructure
5. **Fifth:** `claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A` - Feature implementation
6. **Sixth:** Consider merging autonomous features if needed

### Branch Overlap Analysis

**High Overlap:**
- `autonomous/mvp-execution` ↔ `claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18`
  - Both add CCPM framework
  - Both have autonomous execution features
  - **Recommendation:** Choose one or merge carefully

**Medium Overlap:**
- `development` ↔ `claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL`
  - Both have sprint planning docs
  - Development has additional skills
  - **Recommendation:** Easy merge, mostly complementary

**Low Overlap:**
- `claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A` - Mostly isolated feature work
- `claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat` - Backend infrastructure
- `fix/medcat-demo-model-config` - Cleanup only

---

## Feature Matrix

| Feature | main | dev | autonomous | ccweb-015 | roadmap | dev-ccweb-014 | setup-015 | fix |
|---------|------|-----|------------|-----------|---------|---------------|-----------|-----|
| Sprint Plans | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Claude Skills | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| CCPM Framework | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Autonomous Mode | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ |
| CI/CD Workflows | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Timeline Feature | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Backend DB Setup | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Module Registry | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Todo System | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Agent Chaining | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Cleanup | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Recommendations

### For Immediate Integration
1. **`development`** - Newest, clean feature additions (skills + plans)
2. **`claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat`** - Backend infrastructure needed
3. **`claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A`** - Complete feature with tests

### For Evaluation
- **Autonomous branches** - Decide between `autonomous/mvp-execution` vs `claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18`
- **Documentation branches** - Merge comparison docs if useful

### For Cleanup
- **`fix/medcat-demo-model-config`** - Evaluate if cleanup is still relevant after other merges

---

## Size Comparison (Lines Changed vs Main)

```
claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18: ~15,000+ lines
autonomous/mvp-execution:                            ~15,000+ lines
development:                                         ~10,000+ lines
claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL: ~10,000+ lines
claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A: ~8,000+ lines
claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat: ~3,000+ lines
claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK: ~2,200+ lines
fix/medcat-demo-model-config:                        -7,000 lines (net deletion)
```

---

## Last Updated Timeline

```
6 minutes ago:  claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK
4 hours ago:    claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat
14 hours ago:   claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A
24 hours ago:   claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18
2 days ago:     development (JUST PUSHED)
3 days ago:     autonomous/mvp-execution
5 days ago:     claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL
6 days ago:     fix/medcat-demo-model-config
```

---

## Conclusion

The repository has 8 active development branches with varying purposes:

- **Core Development:** `development` branch with new skills and planning
- **Feature Work:** Timeline view with full CI/CD in `claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A`
- **Infrastructure:** Backend setup in `claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat`
- **Autonomous Systems:** Two competing implementations of autonomous agent frameworks
- **Planning:** Comprehensive roadmap documentation
- **Cleanup:** Model configuration fixes

**Next Steps:**
1. Decide on autonomous framework approach (merge one or both)
2. Integrate feature branches in recommended order
3. Clean up completed/stale branches after merge
4. Consider creating a unified development strategy document
