# CCPM Execution Plan: Branch Consolidation

## Overview

This plan uses CCPM's parallel execution system to consolidate 82+ branches into `ccpm-consolidated` on your fork, achieving the PRD specifications.

## Branch-to-Task Mapping

### Issue #2: Environment Setup (Sequential - Must Complete First)
**No branches to analyze** - Sets up worktrees for other agents

### Issue #3: MedCAT Core Consolidation (Parallel)
**Branches to analyze:**
- `origin/medcat/v2.3` - Latest stable MedCAT
- `origin/medcat/v2.2`
- `origin/medcat/v2.1`
- `origin/medcat/v2.0`
- `origin/medcat-v1/production`
- `origin/medcat-v1/v1.16.post`
- `origin/medcat-stats-import`
- `origin/medcat/v0.10` through `v0.13`
- `myfork/fix/medcat-demo-model-config`
- `origin/feat/medcat-demo-web-app/*`

**PRD Requirements Addressed:**
- NLP pipeline integration
- Meta-annotation handling
- Model loading optimization

### Issue #4: UI/Frontend Consolidation (Parallel)
**Branches to analyze:**
- `myfork/claude/create-ccweb-dev-branch-*`
- `myfork/claude/development-on-ccweb-*`
- `myfork/development` (Vue components)
- `origin/trainer-remove-medcat-utils` (deleted but may have commits)

**PRD Requirements Addressed:**
- Patient timeline view
- Search interface
- Annotation UI

### Issue #5: Search & NLP Features (Parallel)
**Branches to analyze:**
- `myfork/development` (Sprint 3 search features)
- `myfork/claude/sprint3-integration-*`
- `myfork/claude/sprints-6-8-implementation-*`

**PRD Requirements Addressed:**
- Advanced query parsing (Boolean, fuzzy, proximity)
- Elasticsearch integration
- Query caching and optimization

### Issue #6: Infrastructure Updates (Parallel)
**Branches to analyze:**
- `myfork/autonomous/mvp-execution`
- `origin/build/medcat/*`
- `origin/cogstack_es_ssl`
- `myfork/claude/setup-ai-agent-onboarding-*`

**PRD Requirements Addressed:**
- Docker configuration
- CI/CD pipelines
- Deployment scripts

### Issue #7: Documentation Sync (Parallel)
**Branches to analyze:**
- `myfork/claude/create-comparison-doc-*`
- `myfork/claude/understand-codebase-*`
- `myfork/development` (docs)
- `origin/docs/add-pr-template`

**PRD Requirements Addressed:**
- API documentation
- User guides
- Architecture docs

### Issue #8: Test Suite Integration (Sequential - After #3-7)
**Branches to analyze:**
- All branches from #3-7 for their test files
- `myfork/development` (comprehensive tests)

**PRD Requirements Addressed:**
- 85% backend coverage
- 80% frontend coverage
- E2E tests

### Issue #9: Clinical Features (Sequential - After #3, #5)
**Branches to analyze:**
- `myfork/claude/develop-roadmap-phases-*` (FHIR, ICD-10)
- `myfork/development` (Sprint 4-6 clinical features)
- `myfork/claude/sprints-6-8-implementation-*`

**PRD Requirements Addressed:**
- FHIR R4 integration
- ICD-10 coding
- Patient safety features
- Clinical decision support

### Issue #10: API & Backend Services (Sequential - After #3, #5)
**Branches to analyze:**
- `myfork/development` (FastAPI services)
- `myfork/claude/develop-roadmap-phases-*`

**PRD Requirements Addressed:**
- API endpoints
- Service layer
- Performance optimization

### Issue #11: Final Validation (Last)
**No branches to analyze** - Validates the consolidated result

## Execution Commands

### Phase 1: Setup (Issue #2)
```bash
/pm:issue-start 2
# Creates worktrees for all parallel agents
```

### Phase 2: Launch 5 Parallel Agents (Issues #3-7)
```bash
# Launch all simultaneously - each gets its own worktree
/pm:issue-start 3  # MedCAT agent
/pm:issue-start 4  # UI agent
/pm:issue-start 5  # Search agent
/pm:issue-start 6  # Infrastructure agent
/pm:issue-start 7  # Documentation agent
```

### Phase 3: Integration (Issues #8-10)
```bash
# After Phase 2 completes
/pm:issue-start 8   # Test integration
/pm:issue-start 9   # Clinical features
/pm:issue-start 10  # API services
```

### Phase 4: Validation (Issue #11)
```bash
/pm:issue-start 11  # Final validation
```

## Agent Instructions Template

Each agent follows this workflow:

```markdown
## Agent Workflow for Issue #X

1. **Setup Worktree**
   ```bash
   git worktree add .worktrees/issue-X -b consolidation-issue-X
   cd .worktrees/issue-X
   ```

2. **Analyze Assigned Branches**
   ```bash
   # For each branch in assignment:
   git log --oneline [branch] --not ccpm-consolidated | head -20
   ```

3. **Identify Valuable Commits**
   - Look for: feat, fix, perf, test commits
   - Check if already in ccpm-consolidated
   - Prioritize by: recency, test coverage, relevance to PRD

4. **Cherry-Pick Best Implementations**
   ```bash
   git cherry-pick [commit-sha]
   # Resolve conflicts if any
   ```

5. **Update Issue Progress**
   ```bash
   gh issue comment X --repo parsa-hemmati/cogstack-nlp --body "Progress: Cherry-picked [commits]"
   ```

6. **Merge to Main Branch**
   ```bash
   git checkout ccpm-consolidated
   git merge consolidation-issue-X
   ```

7. **Close Issue**
   ```bash
   gh issue close X --repo parsa-hemmati/cogstack-nlp
   ```
```

## PRD Traceability

| PRD Requirement | Implementing Issue | Source Branches |
|-----------------|-------------------|-----------------|
| Patient Search | #5 | myfork/development (Sprint 3) |
| Timeline View | #4, #9 | myfork/claude/develop-roadmap-* |
| NLP Integration | #3 | origin/medcat/v2.3 |
| FHIR Export | #9 | myfork/development (Sprint 6) |
| Meta-annotations | #3, #5 | origin/medcat/*, myfork/development |
| De-identification | #9 | myfork/development (Sprint 4) |
| Clinical Coding | #9 | myfork/development (Sprint 5) |
| API Endpoints | #10 | myfork/development |
| Docker Deploy | #6 | origin/build/*, myfork/autonomous/* |
| Test Coverage | #8 | All branches |

## Success Criteria

- [ ] All 82+ branches analyzed
- [ ] Best implementations cherry-picked
- [ ] No regression (tests pass)
- [ ] PRD requirements met
- [ ] Pushed to myfork/ccpm-consolidated
