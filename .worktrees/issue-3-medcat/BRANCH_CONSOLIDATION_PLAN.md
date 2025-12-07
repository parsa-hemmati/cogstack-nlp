# Branch Consolidation Plan
**Generated:** November 23, 2025  
**Repository:** parsa-hemmati/cogstack-nlp  
**Status:** DETAILED ANALYSIS & RECOMMENDATIONS

---

## Executive Summary

### Current State
- **8 active branches** diverged from main
- **673 maximum files changed** in a single branch
- **67 common files** modified across multiple branches (highest overlap)
- **0 direct merge conflicts** with main (clean base)
- **Significant overlap** in `clinical-care-tools/` across 3 branches

### Complexity Assessment
🟢 **Low Risk:** `fix/medcat-demo-model-config`, `claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK`  
🟡 **Medium Risk:** `development`, `claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL`  
🟠 **High Risk:** `claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat`, `claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A`  
🔴 **Very High Risk:** `autonomous/mvp-execution`, `claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18`

---

## Detailed Branch Analysis

### 1. **development** (CURRENT)
```
Files Changed: 193
Top Directories: clinical-care-tools (159), .specify (20), .claude (5)
Conflict Risk: MEDIUM
Status: JUST PUSHED TO REMOTE
```

**Content:**
- 4 new Claude skills (Elasticsearch, Redis, Search Optimization, Test Coverage)
- Sprint planning documents (2-9.5)
- Backend: 123 files
- Frontend: 27 files
- CONTEXT.md: 2,896 lines (+790 from main)

**Overlap Analysis:**
- 35 files overlap with `setup-015`
- 47 files overlap with `ccweb-015`
- Primarily in `clinical-care-tools/backend/` infrastructure

**Commits (Last 5):**
1. `a990f24e` - feat(skills): add 4 new skills from Sprint 3
2. `4a2ff444` - docs: add comprehensive project status report
3. `70f759cf` - feat(search): complete Sprint 3 Phase 2
4. `8f59ef62` - test(search): comprehensive e2e tests
5. `3231e1ad` - docs(search): comprehensive documentation

**Recommendation:** ⭐ **KEEP AS PRIMARY - Use as base for consolidation**

---

### 2. **claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat**
```
Files Changed: 145
Top Directories: clinical-care-tools (139), .claude (5)
Conflict Risk: HIGH (67 common files with ccweb-015)
Status: Updated 4 hours ago
```

**Content:**
- Module registry for dynamic service loading
- Pipeline and roadmap management (`.claude/pipeline/`, `.claude/roadmap/`)
- Todo tracking system (`.claude/todos/`)
- Database migrations (Alembic): documents, entities, patients tables
- Backend infrastructure: 101 files
- Frontend: 38 files
- CONTEXT.md: 2,970 lines (+864 from main)

**Unique Features:**
- Module registry system
- Alembic migrations for core tables
- Enhanced patient aggregation with fuzzy matching
- Document upload component with progress
- PHI de-identification tests

**Overlap Analysis:**
- 35 files with `development`
- 67 files with `ccweb-015` ⚠️ **HIGHEST OVERLAP**
- Common areas: backend config, models, database setup

**Commits (Last 5):**
1. `36f49f4c` - feat(services): module registry for dynamic loading
2. `46249561` - feat(models): Module model
3. `d34b38b6` - feat(security): PHI de-identification tests
4. `f564c602` - feat(frontend): document upload component
5. `709a096c` - feat(services): enhanced patient aggregation

**Recommendation:** ⭐ **MERGE AFTER CCWEB-015 - Contains critical infrastructure**

---

### 3. **claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A**
```
Files Changed: 270
Top Directories: clinical-care-tools (266)
Conflict Risk: HIGH (67 common files with setup-015)
Status: Updated 14 hours ago
```

**Content:**
- **Timeline view feature** (complete implementation)
- Sprint 2 implementation (1,580 lines plan, 1,428 lines tasks)
- Comprehensive testing infrastructure
- GitHub Actions CI/CD workflows
- Phase 5-7 implementation reports
- Backend: 154 files
- Frontend: 79 files
- CONTEXT.md: 2,350 lines (+244 from main)

**Unique Features:**
- D3.js Timeline Visualization
- Timeline Pinia Store
- Timeline filters and view components
- Comprehensive test suite (Tasks 5.1-5.3)
- Deployment infrastructure (Tasks 6.1-6.3)
- `.coveragerc` for Python testing
- GitHub workflows: test-all, test-backend, test-frontend

**Overlap Analysis:**
- 47 files with `development`
- 67 files with `setup-015` ⚠️ **HIGHEST OVERLAP**
- Heavy overlap in backend/frontend infrastructure

**Commits (Last 5):**
1. `e22661d0` - feat(timeline): deployment infrastructure
2. `f9279eb6` - feat(timeline): comprehensive test suite
3. `ae89f534` - feat(timeline): filters and view page
4. `96b9fb30` - feat(timeline): D3.js visualization
5. `2b6d1e61` - feat(timeline): Pinia store

**Recommendation:** ⭐ **MERGE SECOND - Complete feature with tests**

---

### 4. **claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL**
```
Files Changed: 172
Top Directories: clinical-care-tools (145), .specify (20)
Conflict Risk: MEDIUM
Status: Updated 5 days ago
```

**Content:**
- Comprehensive sprint planning (Sprints 2-9.5)
- Sprint 3: Full-Text Search (1,344 lines)
- Sprint 4: EHR Deidentification (944 lines)
- Sprint 5: Clinical Coding (644 lines)
- Sprint 5.5: Event Bus (522 lines)
- Skeletal plans for Sprints 6-9.5

**Commits (Last 5):**
1. `907be0db` - feat(roadmap): Sprints 6-9.5 skeletal complete
2. `c1a766e7` - feat(events): Sprint 5.5 complete
3. `6c1a04bc` - feat(coding): Sprint 5 core complete
4. `8748ce23` - feat(deidentification): Sprint 4 core
5. `5b9e6215` - feat(search): Sprint 3 backend complete

**Overlap with development:**
- Both have sprint planning, but `roadmap` has more comprehensive Sprint 3-5 plans
- `development` has newer Sprint 2 details

**Recommendation:** 🔄 **CHERRY-PICK Sprint 3-5.5 plans into development**

---

### 5. **autonomous/mvp-execution**
```
Files Changed: 366
Top Directories: backend (140), models (82), frontend (60), .claude (24)
Conflict Risk: VERY HIGH
Status: Updated 3 days ago
```

**Content:**
- CCPM framework (~547 lines config)
- Autonomous execution framework
- Git hook orchestration
- Mission queue system
- Blocker tracking (Docker, MedCAT models)
- Agent configuration and validators

**Comparison with development-on-ccweb-014:**
- **365 common files** between the two autonomous branches
- Only 1 unique file in mvp-execution
- development-on-ccweb-014 has 308 unique files

**Recommendation:** ❌ **DO NOT MERGE - Superseded by development-on-ccweb-014**

---

### 6. **claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18**
```
Files Changed: 673 (LARGEST)
Top Directories: .claude (188), backend (186), frontend (124), models (83)
Conflict Risk: VERY HIGH
Status: Updated 24 hours ago
```

**Content:**
- CCPM framework (advanced version)
- Agent chaining framework (712 lines)
- Autonomous loop design (1,251 lines)
- Agent coordination and status tracking
- Comprehensive autonomous workflow testing
- Rate limiting for search/export endpoints

**Unique Features (vs mvp-execution):**
- AGENT_CHAINING.md (712 lines)
- AUTONOMOUS_LOOP_DESIGN.md (1,251 lines)
- CCPM_AUTONOMOUS_INTEGRATION.md
- COORDINATION.md
- PARALLEL_EXECUTION_DEMO.md
- More mature autonomous framework

**Recommendation:** 🤔 **EVALUATE - If autonomous features needed, use this over mvp-execution**

---

### 7. **fix/medcat-demo-model-config**
```
Files Changed: 65 (NET DELETIONS)
Top Directories: .specify (17), docs (14), .claude (13)
Conflict Risk: LOW
Status: Updated 6 days ago
```

**Content:**
- Removes ~7,000 lines of Claude skills
- Removes git hooks infrastructure
- Fixes MedCAT model path configuration
- Cleanup-focused branch

**Recommendation:** ❌ **DO NOT MERGE - Conflicts with development's additions**

---

### 8. **claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK**
```
Files Changed: 2
Conflict Risk: NONE
Status: Updated 6 minutes ago
```

**Content:**
- BRANCH_COMPARISON.md (947 lines)
- BRANCH_COMPARISON_COMPLETE.md (1,245 lines)

**Recommendation:** ✅ **MERGE ANYTIME - Documentation only, no conflicts**

---

## Critical Overlap Analysis

### Highest Risk: setup-015 ↔ ccweb-015 (67 common files)

**Common Modified Files:**
```
CONTEXT.md
clinical-care-tools/backend/.env.example
clinical-care-tools/backend/README.md
clinical-care-tools/backend/alembic.ini
clinical-care-tools/backend/alembic/env.py
clinical-care-tools/backend/app/core/config.py
clinical-care-tools/backend/app/core/database.py
clinical-care-tools/backend/app/main.py
clinical-care-tools/backend/app/models/__init__.py
clinical-care-tools/backend/app/models/audit_log.py
clinical-care-tools/backend/app/models/document.py
clinical-care-tools/backend/app/models/extracted_entity.py
... and 55 more
```

**Analysis:**
- Both branches evolved `clinical-care-tools/` infrastructure
- `ccweb-015` focused on timeline feature + testing
- `setup-015` focused on module registry + migrations
- **Both modified core backend architecture**

**Merge Strategy:**
1. Merge `ccweb-015` first (complete feature)
2. Then merge `setup-015` (resolve conflicts manually)
3. Test integration thoroughly

---

### Medium Risk: development ↔ setup-015 (35 common files)

**Common Areas:**
- `CONTEXT.md` (different additions)
- `clinical-care-tools/backend/` (infrastructure overlap)
- Database configuration files

**Merge Strategy:**
- Use `development` as base
- Cherry-pick module registry from `setup-015`
- Merge CONTEXT.md manually (combine insights)

---

### Autonomous Branches: 365/366 files overlap

**Analysis:**
- `autonomous/mvp-execution` has only 1 unique file
- `claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18` is significantly more advanced
- Both contain CCPM framework

**Decision Required:**
- If autonomous features needed → use `development-on-ccweb-014`
- If not needed → skip both branches

---

## CONTEXT.md Growth Analysis

```
main:        2,106 lines (base)
ccweb-015:   2,350 lines (+244, +11.6%)
development: 2,896 lines (+790, +37.5%)
setup-015:   2,970 lines (+864, +41.0%)
```

**Observations:**
- `setup-015` has most comprehensive CONTEXT.md
- `development` has significant additions
- `ccweb-015` has focused timeline documentation

**Merge Strategy for CONTEXT.md:**
1. Use `setup-015` version as base (most complete)
2. Add skills documentation from `development`
3. Add timeline specifics from `ccweb-015`
4. Create unified comprehensive version

---

## Recommended Consolidation Strategy

### 🎯 Strategy: Progressive Feature Integration

---

## Phase 1: Foundation (Days 1-2)

### Step 1.1: Create Integration Branch
```bash
git checkout myfork/main
git checkout -b consolidation/sprint-integration
git push -u myfork consolidation/sprint-integration
```

### Step 1.2: Merge Documentation
```bash
# Low risk, immediate value
git merge --no-ff myfork/claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK
git push
```

### Step 1.3: Cherry-pick Sprint Plans from Roadmap Branch
```bash
# Get comprehensive Sprint 3-5.5 plans that development doesn't have
git cherry-pick c1a766e7  # Sprint 5.5 Event Bus
git cherry-pick 6c1a04bc  # Sprint 5 Clinical Coding
git cherry-pick 8748ce23  # Sprint 4 Deidentification
git cherry-pick 5b9e6215  # Sprint 3 Full-Text Search
git push
```

---

## Phase 2: Core Development (Days 3-5)

### Step 2.1: Merge Development Branch
```bash
# Current branch with skills and Sprint 2 implementation
git merge --no-ff myfork/development -m "Merge development: Add 4 new skills + Sprint 2 implementation"

# Test after merge
cd clinical-care-tools
# Run tests to verify nothing broke
git push
```

**Expected Conflicts:** Minimal (mostly in CONTEXT.md)

**Resolution:**
- Keep development's skill additions
- Preserve sprint documentation from both sources

---

## Phase 3: Timeline Feature (Days 6-8)

### Step 3.1: Merge Timeline Implementation
```bash
git merge --no-ff myfork/claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A \
  -m "Merge ccweb-015: Add Timeline feature with D3.js visualization + CI/CD"
```

**Expected Conflicts:** 
- CONTEXT.md (low risk)
- Backend configuration files (medium risk)
- Some model definitions (medium risk)

**Resolution Strategy:**
```bash
# For conflicts in backend/app/core/config.py:
# - Keep timeline's additions
# - Preserve database config from development

# For conflicts in CONTEXT.md:
# - Combine both documentation sections
# - Keep timeline feature description
# - Keep skills documentation from development

# Test thoroughly
cd clinical-care-tools/backend
# Run test suite
cd ../frontend
# Run frontend tests
```

### Step 3.2: Verify Timeline Feature
- [ ] Timeline visualization renders
- [ ] D3.js integration works
- [ ] Pinia store functions correctly
- [ ] Filters work as expected
- [ ] Backend API endpoints respond
- [ ] All tests pass

---

## Phase 4: Infrastructure Enhancement (Days 9-12)

### Step 4.1: Merge Module Registry & Migrations
```bash
git merge --no-ff myfork/claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat \
  -m "Merge setup-015: Add module registry + database migrations"
```

**Expected Conflicts:** HIGH RISK (67 common files with ccweb-015)

**Critical Conflict Areas:**
1. `clinical-care-tools/backend/app/core/config.py`
2. `clinical-care-tools/backend/app/core/database.py`
3. `clinical-care-tools/backend/app/main.py`
4. Model definitions in `app/models/`
5. `CONTEXT.md`

**Resolution Strategy:**

```bash
# For app/main.py:
# - Integrate module registry initialization from setup-015
# - Preserve timeline routes from ccweb-015
# - Keep both sets of middleware

# For models/:
# - Merge model definitions (should be additive)
# - Keep both timeline models and module models
# - Verify relationships don't conflict

# For database.py:
# - Combine session management approaches
# - Keep both connection pool configurations
# - Test database connectivity

# For Alembic migrations:
# - Keep all migrations from both branches
# - Renumber if needed to maintain sequence
# - Test migration chain: alembic upgrade head
```

### Step 4.2: Test Integration
```bash
# Backend testing
cd clinical-care-tools/backend
alembic upgrade head  # Test migrations
# Run full test suite

# Frontend testing  
cd ../frontend
# Run component tests
# Test timeline with new backend

# Integration testing
# Test module registry loading
# Test document upload with timeline
# Test patient aggregation
```

---

## Phase 5: (Optional) Autonomous Features (Days 13-15)

### Decision Point: Do you need autonomous agent features?

**If YES:**
```bash
git merge --no-ff myfork/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18 \
  -m "Merge development-on-ccweb: Add CCPM + autonomous agent framework"
```

**If NO:**
```bash
# Skip autonomous branches entirely
# Mark branches for eventual deletion
```

**If YES - Expected Conflicts:** VERY HIGH (673 files)

**Resolution Strategy:**
- This is a major integration effort
- Consider doing in a separate experimental branch first
- Test autonomous features independently
- Only merge if they provide clear value

---

## Phase 6: Finalization (Days 16-18)

### Step 6.1: Unified CONTEXT.md
```bash
# Manually create comprehensive CONTEXT.md by combining:
# 1. setup-015's structure (most complete)
# 2. development's skills documentation
# 3. ccweb-015's timeline documentation
# 4. Module registry documentation from setup-015
```

### Step 6.2: Update Documentation
- [ ] Update README.md with consolidated features
- [ ] Update QUICK_START.md if needed
- [ ] Create CHANGELOG.md entry
- [ ] Update deployment guides

### Step 6.3: Final Testing
```bash
# Run complete test suite
cd clinical-care-tools/backend
pytest --cov=app --cov-report=html

cd ../frontend
npm test
npm run test:e2e

# Manual testing checklist
# - Timeline feature works end-to-end
# - Search functionality intact
# - Module registry loads correctly
# - Database migrations apply cleanly
# - Document upload works
# - Patient aggregation works
```

---

## Phase 7: Cleanup (Days 19-20)

### Step 7.1: Merge to Main
```bash
git checkout myfork/main
git merge --no-ff consolidation/sprint-integration \
  -m "Major consolidation: Timeline + Skills + Infrastructure"
git push myfork main
```

### Step 7.2: Branch Cleanup
```bash
# Archive merged branches
git branch -d development
git push myfork --delete development

git push myfork --delete claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A
git push myfork --delete claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat
git push myfork --delete claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL
git push myfork --delete claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK

# Keep or delete autonomous branches based on Phase 5 decision
# Keep or delete fix/medcat-demo-model-config for future reference
```

---

## Alternative Strategy: Selective Feature Integration

If the full consolidation seems too risky, consider this approach:

### Option A: Keep Branches Separate Longer
```bash
# Just merge the cleanest wins
git checkout myfork/main
git merge development  # Skills + Sprint 2
git merge claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK  # Docs

# Work on other branches independently
# Merge when more stable
```

### Option B: Create Feature-Specific Branches
```bash
# Extract specific features into new clean branches
git checkout myfork/main
git checkout -b feature/timeline-visualization
# Cherry-pick only timeline commits from ccweb-015

git checkout -b feature/module-registry
# Cherry-pick only module registry from setup-015
```

---

## Risk Mitigation Strategies

### Before Each Merge

1. **Create backup branch:**
   ```bash
   git branch backup/pre-merge-$(date +%Y%m%d)
   ```

2. **Review changes:**
   ```bash
   git diff myfork/main..BRANCH_TO_MERGE --stat
   git diff myfork/main..BRANCH_TO_MERGE -- CRITICAL_FILE
   ```

3. **Test in isolation:**
   ```bash
   git checkout -b test/BRANCH_NAME-integration
   git merge BRANCH_TO_MERGE
   # Run full test suite
   # If successful, apply to main integration branch
   ```

### Conflict Resolution Best Practices

1. **For code conflicts:**
   - Favor the more recent, feature-complete version
   - Test immediately after resolution
   - Use `git diff` to verify you didn't lose functionality

2. **For CONTEXT.md:**
   - Combine both versions manually
   - Keep all unique information
   - Organize by topic, not by source branch

3. **For database migrations:**
   - Never delete migrations
   - Renumber if sequence is broken
   - Test full migration path: `alembic downgrade base && alembic upgrade head`

4. **For configuration files:**
   - Combine all unique settings
   - Comment the source of each section
   - Verify all environment variables are documented

---

## Testing Checklist

### After Each Phase

#### Backend
- [ ] All pytest tests pass
- [ ] Database migrations apply cleanly
- [ ] API endpoints respond correctly
- [ ] No import errors
- [ ] Configuration loads properly

#### Frontend
- [ ] All component tests pass
- [ ] No console errors
- [ ] Pages render correctly
- [ ] API calls succeed
- [ ] No TypeScript errors

#### Integration
- [ ] End-to-end user flows work
- [ ] No performance degradation
- [ ] Docker containers build successfully
- [ ] Documentation matches implementation

---

## Success Criteria

### Consolidated Main Branch Should Have:

✅ **Features:**
- 4 new Claude skills (Elasticsearch, Redis, Search, Test Coverage)
- Timeline visualization with D3.js
- Comprehensive sprint planning (Sprints 2-9.5)
- Module registry for dynamic loading
- Database migrations for core entities
- Document upload functionality
- Enhanced patient aggregation

✅ **Infrastructure:**
- GitHub Actions CI/CD workflows
- Comprehensive test coverage
- Alembic migrations
- Environment configuration examples
- Docker deployment setup

✅ **Documentation:**
- Unified CONTEXT.md (3000+ lines)
- Sprint plans and tasks
- Branch comparison documentation
- Testing guide
- Deployment guide

✅ **Code Quality:**
- All tests passing
- No merge artifacts
- Consistent code style
- Up-to-date dependencies
- Clean git history

---

## Timeline Summary

| Phase | Duration | Risk | Effort |
|-------|----------|------|--------|
| Phase 1: Foundation | 2 days | Low | Low |
| Phase 2: Core Development | 3 days | Medium | Medium |
| Phase 3: Timeline Feature | 3 days | High | High |
| Phase 4: Infrastructure | 4 days | Very High | Very High |
| Phase 5: Autonomous (Optional) | 3 days | Very High | Very High |
| Phase 6: Finalization | 3 days | Medium | Medium |
| Phase 7: Cleanup | 2 days | Low | Low |
| **Total (without Phase 5)** | **17 days** | - | - |
| **Total (with Phase 5)** | **20 days** | - | - |

---

## Recommended Approach: PROGRESSIVE

Start with Phase 1-2, validate the results, then proceed to Phase 3-4. Evaluate Phase 5 based on actual needs.

**Key Decision Points:**
1. **After Phase 2:** Is development merge successful? → Proceed to Phase 3
2. **After Phase 3:** Is timeline feature working? → Proceed to Phase 4  
3. **After Phase 4:** Do we need autonomous features? → Decide on Phase 5
4. **After successful phase:** Merge to main and cleanup

---

## Branch Priority Matrix

### Immediate Value (Merge Soon):
1. ✅ `development` - New skills + Sprint 2
2. ✅ `claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK` - Documentation
3. ✅ `claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A` - Timeline feature

### High Value (Merge After Testing):
4. ⚠️ `claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat` - Infrastructure
5. 🔄 `claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL` - Cherry-pick plans

### Evaluate Need:
6. 🤔 `claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18` - Autonomous (if needed)

### Skip:
7. ❌ `autonomous/mvp-execution` - Superseded by #6
8. ❌ `fix/medcat-demo-model-config` - Conflicts with additions

---

## Final Recommendations

### ⭐ Recommended Path (Moderate Risk, High Reward)

```bash
# Week 1: Foundation
1. Merge documentation branch (no risk)
2. Merge development branch (low risk)
3. Cherry-pick roadmap plans (low risk)

# Week 2-3: Features
4. Merge timeline feature (high risk, high value)
5. Merge infrastructure (very high risk, very high value)

# Week 4: Optional
6. Evaluate autonomous features
7. Final testing and merge to main
8. Branch cleanup
```

### 🎯 Quick Win Path (Low Risk, Medium Reward)

```bash
# If you want faster, safer progress:
1. Merge documentation
2. Merge development  
3. Stop and stabilize
4. Tackle other branches later one-by-one
```

### 🚀 Aggressive Path (High Risk, Maximum Reward)

```bash
# If you're confident and have good testing:
1. Merge all non-autonomous branches in one sprint
2. Resolve conflicts as they come
3. Extensive testing phase
4. Deploy consolidated version
```

---

## Next Steps

1. **Review this plan** and choose a strategy
2. **Create consolidation/sprint-integration branch**
3. **Start with Phase 1** (low risk)
4. **Test thoroughly** after each phase
5. **Adjust plan** based on results

**Estimated Total Effort:** 15-20 days of focused work  
**Recommended Team Size:** 1-2 developers  
**Testing Requirements:** Comprehensive after each phase

---

## Questions to Answer Before Starting

1. Do you need autonomous agent features? (Phase 5 decision)
2. What's your risk tolerance? (Choose strategy)
3. Do you have comprehensive test coverage? (Needed for validation)
4. Can you dedicate 2-3 weeks to this? (Timeline commitment)
5. Do you have a rollback plan? (Safety net)

---

**Document Status:** Ready for execution  
**Last Updated:** November 23, 2025  
**Author:** GitHub Copilot (Claude Sonnet 4.5)
