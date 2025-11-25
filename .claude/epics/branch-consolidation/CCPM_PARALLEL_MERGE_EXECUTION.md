# CCPM Parallel Merge Execution Strategy

**Purpose**: Leverage Claude Code PM parallel execution system to expedite the 5-phase branch consolidation
**Estimated Time**: 2-3 hours (vs 8-10 hours sequential)
**Parallelization Factor**: 5x speedup with 5 concurrent agents

---

## Quick Start Commands

```bash
# 1. Verify worktrees ready
git worktree list

# 2. Launch parallel merge execution
/pm:epic-start branch-consolidation

# 3. Monitor progress
/pm:epic-status branch-consolidation

# 4. Merge all changes when complete
/pm:epic-merge branch-consolidation
```

---

## Phase-to-Worktree Mapping

| Phase | Source Branch | Worktree | GitHub Issue | Parallel Stream |
|-------|--------------|----------|--------------|-----------------|
| 1A | myfork/development | issue-3-medcat | #3 | MedCAT Core |
| 1B | myfork/development | issue-4-ui | #4 | Frontend Components |
| 1C | myfork/development | issue-5-search | #5 | Search & NLP |
| 1D | myfork/development | issue-6-infra | #6 | Infrastructure |
| 1E | myfork/development | issue-7-docs | #7 | Documentation |
| 2 | claude/sprint3-integration-* | issue-5-search | #5 | Advanced Search |
| 3 | claude/sprints-6-8-* | issue-3-medcat | #3 | CDS Features |
| 4 | autonomous/mvp-execution | issue-5-search | #5 | Task Execution |
| 5 | fix/medcat-demo-model-config | medcat-work | #3 | Config Fix |

---

## Parallel Execution Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CCPM Orchestrator (Main Thread)                   │
│  - Coordinates parallel agents                                       │
│  - Monitors progress via GitHub Issues                               │
│  - Handles conflict resolution                                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│   Agent 1     │      │   Agent 2     │      │   Agent 3     │
│ issue-3-medcat│      │  issue-4-ui   │      │ issue-5-search│
│               │      │               │      │               │
│ Phase 1A:     │      │ Phase 1B:     │      │ Phase 1C:     │
│ MedCAT Core   │      │ Frontend      │      │ Search/NLP    │
│ Phase 3:      │      │               │      │ Phase 2:      │
│ CDS Features  │      │               │      │ Advanced      │
│ Phase 5:      │      │               │      │ Phase 4:      │
│ Config Fix    │      │               │      │ Task Exec     │
└───────────────┘      └───────────────┘      └───────────────┘
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐
│   Agent 4     │      │   Agent 5     │
│ issue-6-infra │      │ issue-7-docs  │
│               │      │               │
│ Phase 1D:     │      │ Phase 1E:     │
│ Docker/CI     │      │ Specs/Docs    │
│               │      │               │
└───────────────┘      └───────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   ccpm-consolidated (Target Branch)                  │
│  All agents commit to same branch via worktrees                      │
│  No conflicts: each agent handles different file domains             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Parallel Development Merge (All Agents Simultaneously)

### Agent 1: MedCAT Core (issue-3-medcat)

**Source**: `myfork/development`
**Files to Cherry-Pick**:
```bash
cd .worktrees/issue-3-medcat

# Cherry-pick MedCAT-related commits
git cherry-pick --no-commit $(git log myfork/development --oneline --all | grep -i medcat | awk '{print $1}')

# Or merge specific paths
git checkout myfork/development -- \
  app/services/medcat_service.py \
  app/clients/medcat/ \
  tests/test_medcat*.py
```

**Expected Files**:
- `app/services/medcat_service.py`
- `app/clients/medcat/client.py`
- `app/clients/medcat/meta_annotations.py`
- `tests/test_medcat_service.py`

---

### Agent 2: Frontend Components (issue-4-ui)

**Source**: `myfork/development`
**Files to Cherry-Pick**:
```bash
cd .worktrees/issue-4-ui

git checkout myfork/development -- \
  frontend/src/components/ \
  frontend/src/views/ \
  frontend/src/composables/ \
  frontend/src/stores/
```

**Expected Files**:
- `frontend/src/components/clinical/PatientSearch.vue`
- `frontend/src/components/clinical/PatientTimeline.vue`
- `frontend/src/components/clinical/FilterPanel.vue`
- `frontend/src/stores/patientStore.ts`
- `frontend/src/composables/usePatientSearch.ts`

---

### Agent 3: Search & NLP (issue-5-search)

**Source**: `myfork/development` + `claude/sprint3-integration-*`
**Files to Cherry-Pick**:
```bash
cd .worktrees/issue-5-search

# Phase 1C: Base search from development
git checkout myfork/development -- \
  app/services/patient_search_service.py \
  app/services/elasticsearch_service.py \
  app/schemas/patient_search.py

# Phase 2: Advanced search from sprint3 branch
git checkout myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK -- \
  app/services/query_parser.py \
  app/services/advanced_search.py
```

**Expected Files**:
- `app/services/patient_search_service.py`
- `app/services/elasticsearch_service.py`
- `app/services/query_parser.py`
- `app/schemas/patient_search.py`

---

### Agent 4: Infrastructure (issue-6-infra)

**Source**: `myfork/development`
**Files to Cherry-Pick**:
```bash
cd .worktrees/issue-6-infra

git checkout myfork/development -- \
  docker/ \
  docker-compose*.yml \
  .github/workflows/ \
  scripts/
```

**Expected Files**:
- `docker/Dockerfile`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.github/workflows/ci.yml`
- `scripts/deploy.sh`

---

### Agent 5: Documentation (issue-7-docs)

**Source**: `myfork/development`
**Files to Cherry-Pick**:
```bash
cd .worktrees/issue-7-docs

git checkout myfork/development -- \
  docs/ \
  .specify/ \
  README.md \
  CONTEXT.md
```

**Expected Files**:
- `docs/api/`
- `docs/guides/`
- `.specify/specifications/`
- `CONTEXT.md`

---

## Phase 2-5: Sequential Cherry-Picks (After Phase 1)

After Phase 1 completes, agents continue with sequential phases in their worktrees:

### Agent 3 continues: Sprint 3 Advanced Search
```bash
cd .worktrees/issue-5-search
git cherry-pick myfork/claude/sprint3-integration-* --no-commit
# Resolve any conflicts with Phase 1C files
```

### Agent 1 continues: Sprint 6-8 CDS Features
```bash
cd .worktrees/issue-3-medcat
git checkout myfork/claude/sprints-6-8-implementation-* -- \
  app/services/cds/ \
  app/api/v1/cds.py
```

### Agent 1 continues: Config Fix
```bash
cd .worktrees/issue-3-medcat
git cherry-pick myfork/fix/medcat-demo-model-config
```

---

## Execution Commands

### Step 1: Verify Worktrees
```bash
# Check all worktrees exist
git worktree list

# Expected output:
# C:/Users/.../cogstack-nlp                   f4009602 [ccpm-consolidated]
# C:/Users/.../cogstack-nlp/.worktrees/issue-3-medcat
# C:/Users/.../cogstack-nlp/.worktrees/issue-4-ui
# C:/Users/.../cogstack-nlp/.worktrees/issue-5-search
# C:/Users/.../cogstack-nlp/.worktrees/issue-6-infra
# C:/Users/.../cogstack-nlp/.worktrees/issue-7-docs
```

### Step 2: Launch Parallel Agents
```
/pm:epic-start branch-consolidation
```

This will:
1. Read `.claude/epics/branch-consolidation/epic.md`
2. Identify ready issues (#3, #4, #5, #6, #7)
3. Launch 5 parallel Task agents
4. Each agent works in its assigned worktree

### Step 3: Monitor Progress
```
/pm:epic-status branch-consolidation
/pm:standup
```

### Step 4: Resolve Conflicts (If Any)
```
# Check conflict status in each worktree
cd .worktrees/issue-3-medcat && git status
cd .worktrees/issue-4-ui && git status
# ...
```

### Step 5: Merge All Worktrees
```
/pm:epic-merge branch-consolidation
```

This will:
1. Collect all commits from worktrees
2. Create merge commits on ccpm-consolidated
3. Push to myfork/ccpm-consolidated
4. Update GitHub Issues

---

## Agent Task Prompts

### Agent 1 Task Prompt (MedCAT Core)
```markdown
Working in worktree: .worktrees/issue-3-medcat
Issue: #3 - MedCAT Core Consolidation
Branch: consolidation-medcat

Your scope:
- Files: app/services/medcat*.py, app/clients/medcat/*, tests/test_medcat*

Work:
1. Phase 1A: Cherry-pick MedCAT files from myfork/development
2. Phase 3: Cherry-pick CDS files from myfork/claude/sprints-6-8-*
3. Phase 5: Cherry-pick config fix from myfork/fix/medcat-demo-model-config

Commit format: "Issue #3: {specific change}"
Update progress: .claude/epics/branch-consolidation/updates/3/
```

### Agent 2 Task Prompt (Frontend)
```markdown
Working in worktree: .worktrees/issue-4-ui
Issue: #4 - UI/Frontend Consolidation
Branch: consolidation-ui

Your scope:
- Files: frontend/src/components/**, frontend/src/views/**, frontend/src/stores/**

Work:
1. Phase 1B: Cherry-pick all frontend files from myfork/development
2. Ensure Vue 3 Composition API patterns
3. Verify TypeScript types

Commit format: "Issue #4: {specific change}"
Update progress: .claude/epics/branch-consolidation/updates/4/
```

### Agent 3 Task Prompt (Search & NLP)
```markdown
Working in worktree: .worktrees/issue-5-search
Issue: #5 - Search & NLP Features
Branch: consolidation-search

Your scope:
- Files: app/services/*search*.py, app/services/*query*.py, app/schemas/patient_search.py

Work:
1. Phase 1C: Cherry-pick base search from myfork/development
2. Phase 2: Cherry-pick advanced search from myfork/claude/sprint3-integration-*
3. Phase 4: Cherry-pick task execution from myfork/autonomous/mvp-execution (selective)

Commit format: "Issue #5: {specific change}"
Update progress: .claude/epics/branch-consolidation/updates/5/
```

### Agent 4 Task Prompt (Infrastructure)
```markdown
Working in worktree: .worktrees/issue-6-infra
Issue: #6 - Infrastructure Updates
Branch: consolidation-infra

Your scope:
- Files: docker/**, docker-compose*.yml, .github/workflows/**, scripts/**

Work:
1. Phase 1D: Cherry-pick all infrastructure files from myfork/development
2. Ensure Docker configs are compatible
3. Validate CI/CD workflows

Commit format: "Issue #6: {specific change}"
Update progress: .claude/epics/branch-consolidation/updates/6/
```

### Agent 5 Task Prompt (Documentation)
```markdown
Working in worktree: .worktrees/issue-7-docs
Issue: #7 - Documentation Sync
Branch: consolidation-docs

Your scope:
- Files: docs/**, .specify/**, README.md, CONTEXT.md, CLAUDE.md

Work:
1. Phase 1E: Cherry-pick all documentation from myfork/development
2. Ensure specs are complete for Sprints 1-9.5
3. Update CONTEXT.md with consolidation status

Commit format: "Issue #7: {specific change}"
Update progress: .claude/epics/branch-consolidation/updates/7/
```

---

## Conflict Resolution Strategy

### Low Risk Files (No Conflicts Expected)
- Different agents work on completely separate directories
- Frontend (Agent 2) never touches backend files
- Infrastructure (Agent 4) never touches application code

### Medium Risk Files (Coordinate)
- `package.json` / `requirements.txt` - Merge dependencies
- `pyproject.toml` - Combine configurations
- Schema files - Ensure compatibility

### High Risk Files (Manual Review)
- `app/__init__.py` - May have import changes
- `frontend/src/main.ts` - Entry point changes
- Configuration files with overlapping settings

### Resolution Process
```bash
# If conflict detected in worktree:
cd .worktrees/issue-X
git status  # See conflicting files

# Option 1: Take ours (current worktree)
git checkout --ours <file>

# Option 2: Take theirs (source branch)
git checkout --theirs <file>

# Option 3: Manual merge
# Edit file, then:
git add <file>
```

---

## Expected Results

| Metric | Sequential | Parallel (CCPM) | Improvement |
|--------|-----------|-----------------|-------------|
| Total Time | 8-10 hours | 2-3 hours | **4-5x faster** |
| Agents | 1 | 5 concurrent | 5 workers |
| Commits | ~50 | ~50 | Same quality |
| Conflicts | ~10 | ~10 | Same |
| Context Loss | High | None | Full traceability |

---

## Post-Merge Validation

After `/pm:epic-merge`:

```bash
# 1. Verify all files present
ls -la app/services/
ls -la frontend/src/components/

# 2. Run tests
pytest tests/ -v

# 3. Check build
docker-compose build

# 4. Validate compliance
# (Use healthcare-compliance-checker skill)

# 5. Push to remote
git push myfork ccpm-consolidated
```

---

## Troubleshooting

### Worktree Not Found
```bash
git worktree add .worktrees/issue-X -b consolidation-X
```

### Agent Failed Mid-Execution
```bash
# Check progress file
cat .claude/epics/branch-consolidation/updates/X/stream-A.md

# Resume from checkpoint
/pm:issue-start X
```

### Merge Conflicts Blocking
```bash
# Abort and retry with different strategy
git merge --abort
git cherry-pick --abort

# Try selective file checkout instead
git checkout <branch> -- <specific-file>
```

---

## Summary

The CCPM parallel execution system transforms the 5-phase merge from:

**Sequential** (8-10 hours):
```
Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
```

**To Parallel** (2-3 hours):
```
┌─ Agent 1: Phase 1A + 3 + 5
├─ Agent 2: Phase 1B
├─ Agent 3: Phase 1C + 2 + 4
├─ Agent 4: Phase 1D
└─ Agent 5: Phase 1E
```

**Key Benefits**:
1. **5x faster** - All Phase 1 streams run simultaneously
2. **No context loss** - Each agent has focused scope
3. **Full traceability** - GitHub Issues track all progress
4. **Isolated execution** - Worktrees prevent conflicts
5. **Easy rollback** - Each worktree is independent
