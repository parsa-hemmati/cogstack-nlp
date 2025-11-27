# Branch Topology Report

**Generated**: 2025-11-25
**Repository**: parsa-hemmati/cogstack-nlp (fork of CogStack/cogstack-nlp)

---

## Summary Statistics

| Category | Count |
|----------|-------|
| Local Branches | 10 |
| Remote (myfork) | 15 |
| Remote (origin/CogStack) | 67 |
| Active Worktrees | 7 |
| **Total Branches** | **92** |

---

## Visual Topology

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         UPSTREAM (origin/CogStack)                          │
│                                                                             │
│  origin/main ◄─────────────────────────────────────────────────────────────┐│
│       │                                                                    ││
│       ├── origin/medcat/v2.3 (latest stable)                               ││
│       ├── origin/medcat/v2.2                                               ││
│       ├── origin/medcat/v2.1                                               ││
│       ├── origin/medcat/v2.0                                               ││
│       ├── origin/medcat-v1/production                                      ││
│       ├── origin/medcat/v0.10-v0.13                                        ││
│       │                                                                    ││
│       ├── origin/build/medcat/CU-869awf45h-release-after-pre-release       ││
│       ├── origin/feat/medcat-demo-web-app/*                                ││
│       ├── origin/cogstack_es_ssl                                           ││
│       ├── origin/docs/add-pr-template                                      ││
│       └── origin/release/0.1-0.8                                           ││
│            + 50 more CU-* and version branches                             ││
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ fork
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YOUR FORK (myfork/parsa-hemmati)                    │
│                                                                             │
│  myfork/main ◄──────────── Synced with origin/main (5 days ago)            │
│       │                    Last: 53dddde9 "Merge branch 'CogStack:main'"   │
│       │                                                                    │
│       ├─────────────────────────────────────────────────────────────────── │
│       │                                                                    │
│       ▼                                                                    │
│  myfork/development ◄──── Main development branch                          │
│       │                    32 commits ahead of main                        │
│       │                    Last: a990f24e "feat(skills): add 4 skills"     │
│       │                    Contains: Sprints 2-5.5 complete                │
│       │                                                                    │
│       ├──► myfork/claude/develop-roadmap-phases-01AA61yz...                │
│       │         │  Merged into development                                 │
│       │         │  Content: Sprints 6-9.5 skeletal architecture            │
│       │         └  Last: 907be0db "feat(roadmap): Sprints 6-9.5"          │
│       │                                                                    │
│       ├──► myfork/claude/sprint3-integration-011M46D5...                   │
│       │         │  61 commits ahead of development                         │
│       │         │  Content: Sprint 3 Phase 2 Advanced Query Parsing        │
│       │         └  Last: 3eb51514 "docs(context): Sprint 3 Phase 2"       │
│       │                                                                    │
│       ├──► myfork/claude/sprints-6-8-implementation-011M46D5...            │
│       │         │  246 commits ahead of development                        │
│       │         │  Content: Sprint 6 CDS, Sprint 7-8 plans                 │
│       │         └  Last: e30747e9 "docs(cds): Sprint 6-8 status"          │
│       │                                                                    │
│       ├──► myfork/autonomous/mvp-execution                                 │
│       │         │  134 commits ahead of main                               │
│       │         │  Content: Autonomous task execution (search tasks)       │
│       │         └  Last: a624475d "feat(search): Task 2.8"                │
│       │                                                                    │
│       ├──► myfork/claude/create-ccweb-dev-branch-014Ne...                  │
│       ├──► myfork/claude/create-ccweb-dev-branch-015zp...                  │
│       ├──► myfork/claude/development-on-ccweb-014Ne...                     │
│       ├──► myfork/claude/create-comparison-doc-011M46D5...                 │
│       ├──► myfork/claude/setup-ai-agent-onboarding-015LJ...                │
│       └──► myfork/claude/understand-codebase-01Snf...                      │
│                                                                            │
│       │                                                                    │
│       ▼                                                                    │
│  myfork/ccpm-consolidated ◄── ACTIVE CONSOLIDATION BRANCH                  │
│       │                       36 commits ahead of main                     │
│       │                       Last: c7e95ae0 "feat(ccpm): complete"        │
│       │                       Contains: All sprint specs consolidated       │
│       │                                                                    │
│       └──► myfork/fix/medcat-demo-model-config                             │
│                 Content: MedCAT demo configuration fix                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ local checkout
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           LOCAL BRANCHES                                    │
│                                                                             │
│  * ccpm-consolidated (CURRENT) ◄── Tracking myfork/ccpm-consolidated       │
│        │                                                                    │
│        ├── consolidation-medcat ◄── Worktree: .worktrees/issue-3-medcat    │
│        ├── consolidation-ui ◄────── Worktree: .worktrees/issue-4-ui        │
│        ├── consolidation-search ◄── Worktree: .worktrees/issue-5-search    │
│        ├── consolidation-infra ◄─── Worktree: .worktrees/issue-6-infra     │
│        ├── consolidation-docs ◄──── Worktree: .worktrees/issue-7-docs      │
│        └── medcat-consolidation ◄── Worktree: .worktrees/medcat-work       │
│                                                                             │
│    development ◄───────────────── Tracking myfork/development              │
│    main ◄──────────────────────── Tracking origin/main                     │
│    fix/medcat-demo-model-config                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Branch Details by Category

### 🔵 Primary Development Branches

| Branch | Base | Ahead | Content |
|--------|------|-------|---------|
| `myfork/development` | main | +32 | Sprints 2-5.5, Skills, CCPM framework |
| `myfork/ccpm-consolidated` | main | +36 | Complete consolidation with specs |
| `myfork/autonomous/mvp-execution` | main | +134 | Autonomous task execution |

### 🟢 Claude AI-Generated Branches

| Branch | Parent | Commits | Sprint Content |
|--------|--------|---------|----------------|
| `claude/develop-roadmap-phases-*` | development | Merged | Sprints 6-9.5 skeletal |
| `claude/sprint3-integration-*` | development | +61 | Sprint 3 Phase 2 |
| `claude/sprints-6-8-implementation-*` | development | +246 | Sprint 6 CDS, 7-8 plans |
| `claude/create-ccweb-dev-branch-*` | main | - | CCWEB development |
| `claude/development-on-ccweb-*` | main | - | CCWEB features |
| `claude/setup-ai-agent-onboarding-*` | main | - | AI agent setup |
| `claude/understand-codebase-*` | main | - | Codebase analysis |
| `claude/create-comparison-doc-*` | main | - | Documentation comparison |

### 🟡 Active Worktrees

| Worktree | Branch | Path |
|----------|--------|------|
| Main | ccpm-consolidated | `/cogstack-nlp` |
| Issue 3 | consolidation-medcat | `.worktrees/issue-3-medcat` |
| Issue 4 | consolidation-ui | `.worktrees/issue-4-ui` |
| Issue 5 | consolidation-search | `.worktrees/issue-5-search` |
| Issue 6 | consolidation-infra | `.worktrees/issue-6-infra` |
| Issue 7 | consolidation-docs | `.worktrees/issue-7-docs` |
| MedCAT | medcat-consolidation | `.worktrees/medcat-work` |

### 🔴 Upstream Origin Branches (CogStack)

| Category | Count | Key Branches |
|----------|-------|--------------|
| MedCAT versions | 8 | v2.0-v2.3, v1.x, v0.10-v0.13 |
| Release branches | 8 | release/0.1 - release/0.8 |
| Feature branches | 15+ | CU-* task branches |
| Build/CI | 3 | build/medcat/*, docs/* |
| Legacy | 20+ | v1.x.post versions |

---

## All Branches List

### Local Branches (10)

1. `* ccpm-consolidated` - Current branch, consolidation complete
2. `+ consolidation-docs` - Worktree branch
3. `+ consolidation-infra` - Worktree branch
4. `+ consolidation-medcat` - Worktree branch
5. `+ consolidation-search` - Worktree branch
6. `+ consolidation-ui` - Worktree branch
7. `development` - Main dev, tracking myfork/development
8. `fix/medcat-demo-model-config` - MedCAT config fix
9. `main` - Tracking origin/main
10. `+ medcat-consolidation` - Worktree branch

### Remote myfork Branches (15)

1. `myfork/HEAD -> myfork/main`
2. `myfork/autonomous/mvp-execution`
3. `myfork/ccpm-consolidated`
4. `myfork/claude/create-ccweb-dev-branch-014NeWxCVzNfcbd6R6RFpo18`
5. `myfork/claude/create-ccweb-dev-branch-015zpMnefWaNr28fLqHR9E1A`
6. `myfork/claude/create-comparison-doc-011M46D5vbdi9FbGxSzThebK`
7. `myfork/claude/develop-roadmap-phases-01AA61yzporwCFfD6BQpAerL`
8. `myfork/claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18`
9. `myfork/claude/setup-ai-agent-onboarding-015LJGj2rWtJvBbL6GBaXGat`
10. `myfork/claude/sprint3-integration-011M46D5vbdi9FbGxSzThebK`
11. `myfork/claude/sprints-6-8-implementation-011M46D5vbdi9FbGxSzThebK`
12. `myfork/claude/understand-codebase-01Snfj6ziqMUNHxa6sBuv9eB`
13. `myfork/development`
14. `myfork/fix/medcat-demo-model-config`
15. `myfork/main`

### Remote origin Branches (67)

See full list with: `git branch -r | grep origin`

Key categories:
- MedCAT v2.x: `origin/medcat/v2.0`, `v2.1`, `v2.2`, `v2.3`
- MedCAT v1.x: `origin/medcat-v1/production`, `v1.16.post`
- MedCAT v0.x: `origin/medcat/v0.10` - `v0.13`
- Releases: `origin/release/0.1` - `origin/release/0.8`
- Features: `origin/feat/medcat-demo-web-app/*`
- Tasks: `origin/CU-*` (ClickUp task branches)

---

## Sprint Implementation Locations

| Sprint | Primary Branch | Status |
|--------|---------------|--------|
| Sprint 1 | `myfork/development` | ✅ Complete |
| Sprint 2 | `myfork/development` | ✅ Complete |
| Sprint 3 | `myfork/claude/sprint3-integration-*` | ✅ Complete |
| Sprint 4 | `myfork/development` | ✅ Complete |
| Sprint 5 | `myfork/development` | ✅ Complete |
| Sprint 5.5 | `myfork/development` | ✅ Complete |
| Sprint 6 | `myfork/claude/sprints-6-8-*` | ⚠️ Skeletal |
| Sprint 7 | `myfork/claude/sprints-6-8-*` | ⚠️ Planned |
| Sprint 8 | `myfork/claude/sprints-6-8-*` | ⚠️ Planned |
| Sprint 9 | `myfork/development` | ⚠️ Skeletal |
| Sprint 9.5 | (not started) | 📋 Planned |

---

## Branch Relationships

```
origin/main
    │
    └──► myfork/main (fork sync)
              │
              ├──► myfork/development (+32 commits)
              │         │
              │         ├──► myfork/claude/develop-roadmap-phases-* (merged)
              │         ├──► myfork/claude/sprint3-integration-* (+61)
              │         ├──► myfork/claude/sprints-6-8-implementation-* (+246)
              │         └──► myfork/autonomous/mvp-execution (+134)
              │
              ├──► myfork/ccpm-consolidated (+36 commits)
              │
              ├──► myfork/claude/create-ccweb-dev-branch-* (feature)
              ├──► myfork/claude/development-on-ccweb-* (feature)
              ├──► myfork/claude/setup-ai-agent-onboarding-* (feature)
              ├──► myfork/claude/understand-codebase-* (research)
              ├──► myfork/claude/create-comparison-doc-* (docs)
              │
              └──► myfork/fix/medcat-demo-model-config (bugfix)
```

---

## Notes

- **Worktrees**: 6 worktrees are active for parallel CCPM consolidation work
- **Claude branches**: AI-generated branches contain significant sprint implementations
- **Consolidation target**: `ccpm-consolidated` is the target branch for all consolidation
- **Upstream sync**: `myfork/main` should be kept in sync with `origin/main`
