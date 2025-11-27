# Parallel Agent Spawning Instructions

**Worktree**: epic-search-module
**Module**: search-module
**Status**: Ready for parallel execution

---

## Current Task Queue

```
- [ ] #019 [developer] Create useSearch Composable
- [ ] #020 [developer] Create SearchBar Component
- [ ] #022 [tester] Integration Tests for Search Module
- [ ] #023 [documentation] Document Search Module
- [ ] #025 [developer] Re-review XSS Fix Verification (should be auditor)
```

---

## Spawn Agents in Parallel

Since tasks #019 and #020 have `parallel: true` in their epic files, they can be worked on simultaneously. Here's how to spawn multiple agents:

### Option 1: Use Task Tool (Recommended)

In a **single message**, spawn multiple agents using the Task tool:

```
I'm going to spawn 3 agents in parallel to work on the search module:
1. Developer agent for task #019 (useSearch composable)
2. Developer agent for task #020 (SearchBar component)
3. Documentation agent for task #023 (documentation)
```

Then use **3 Task tool calls in ONE message**:

#### Agent 1: Developer for Task #019

```yaml
Task:
  subagent_type: "developer"
  description: "Create useSearch composable"
  model: "sonnet"
  prompt: |
    You are working in the search-module worktree: ../epic-search-module

    **Task**: #019 - Create useSearch Composable
    **Epic**: .claude/ccpm/epics/search-module/019.md
    **Priority**: P0

    Read the full task specification:
    - File: /home/user/cogstack-nlp/.claude/ccpm/epics/search-module/019.md

    Your job:
    1. Read the task specification completely
    2. Create frontend/src/composables/useSearch.ts
    3. Implement all required functionality:
       - Search state management (query, results, loading, error)
       - API integration with POST /api/v1/search
       - Debounced search (300ms delay)
       - Pagination (nextPage, prevPage)
       - Sorting (setSort)
       - Cache (last 10 searches)
    4. Write comprehensive unit tests (>90% coverage)
    5. Ensure TypeScript types are complete

    When complete:
    - Commit changes with message: "feat(search): Task #019 - useSearch composable"
    - Update task queue: mark #019 as completed
    - Delegate to auditor (create task #019-audit)
    - Delegate to tester (create task #019-test)

    Work directory: ../epic-search-module
```

#### Agent 2: Developer for Task #020

```yaml
Task:
  subagent_type: "developer"
  description: "Create SearchBar component"
  model: "sonnet"
  prompt: |
    You are working in the search-module worktree: ../epic-search-module

    **Task**: #020 - Create SearchBar Component
    **Epic**: .claude/ccpm/epics/search-module/020.md
    **Priority**: P0
    **Depends on**: Task #019 (but can be developed in parallel with interface)

    Read the full task specification:
    - File: /home/user/cogstack-nlp/.claude/ccpm/epics/search-module/020.md

    Your job:
    1. Read the task specification completely
    2. Create frontend/src/components/search/SearchBar.vue
    3. Implement all required functionality:
       - Vuetify v-text-field with search icon
       - Integration with useSearch composable
       - Loading states
       - Keyboard support (Enter triggers search, Escape clears)
       - Responsive design
       - Accessibility (WCAG 2.1 AA)
    4. Write comprehensive unit tests (>90% coverage)
    5. Ensure TypeScript props/emits are typed

    When complete:
    - Commit changes with message: "feat(search): Task #020 - SearchBar component"
    - Update task queue: mark #020 as completed
    - Delegate to auditor (create task #020-audit)
    - Delegate to tester (create task #020-test)

    Work directory: ../epic-search-module
```

#### Agent 3: Documentation for Task #023

```yaml
Task:
  subagent_type: "documentation"
  description: "Document search module"
  model: "haiku"
  prompt: |
    You are working in the search-module worktree: ../epic-search-module

    **Task**: #023 - Document Search Module
    **Epic**: .claude/ccpm/epics/search-module/023.md
    **Priority**: P1

    Read the full task specification:
    - File: /home/user/cogstack-nlp/.claude/ccpm/epics/search-module/023.md

    Your job:
    1. Read the task specification completely
    2. Create documentation structure in docs/features/search/
    3. Write the following docs:
       - README.md (overview and quick start)
       - components/SearchBar.md (API docs)
       - components/SearchResults.md (API docs)
       - composables/useSearch.md (API docs)
       - security.md (XSS prevention details)
       - examples.md (8 usage examples)
       - troubleshooting.md (common issues)
    4. Add inline JSDoc comments to all exported functions
    5. Create architecture diagram (Mermaid)

    When complete:
    - Commit changes with message: "docs(search): Task #023 - comprehensive documentation"
    - Update task queue: mark #023 as completed
    - Request developer review (create task #023-review)

    Work directory: ../epic-search-module
```

### Option 2: Launch Agents via Terminal (Multiple Windows)

If you prefer terminal-based execution:

**Terminal 1** (Developer for #019):
```bash
cd ../epic-search-module

# Claim task #019
echo "[🔄]" > .claude/locks/task-019.lock

# Work on task #019
# ... implement useSearch.ts ...

# Commit when done
git add frontend/src/composables/useSearch.ts
git commit -m "feat(search): Task #019 - useSearch composable"

# Remove lock
rm .claude/locks/task-019.lock
```

**Terminal 2** (Developer for #020):
```bash
cd ../epic-search-module

# Claim task #020
echo "[🔄]" > .claude/locks/task-020.lock

# Work on task #020
# ... implement SearchBar.vue ...

# Commit when done
git add frontend/src/components/search/SearchBar.vue
git commit -m "feat(search): Task #020 - SearchBar component"

# Remove lock
rm .claude/locks/task-020.lock
```

**Terminal 3** (Documentation for #023):
```bash
cd ../epic-search-module

# Claim task #023
echo "[🔄]" > .claude/locks/task-023.lock

# Work on task #023
# ... write documentation ...

# Commit when done
git add docs/features/search/
git commit -m "docs(search): Task #023 - comprehensive documentation"

# Remove lock
rm .claude/locks/task-023.lock
```

---

## Monitoring Parallel Execution

### Check Active Agents

```bash
# From main repo
.claude/scripts/monitor-loops.sh --status
```

Expected output:
```
📦 search-module (../epic-search-module)
   Branch: epic/search-module
   Status: ✅ RUNNING
   Agents: 3 active (developer, developer, documentation)
   Tasks: 0/5 complete (0%)
   Last commit: just now
```

### Watch Task Queue Updates

```bash
# Watch task queue for status changes
watch -n 5 "cat .claude/autonomous-worktrees/search-module/TASK_QUEUE.md"
```

As agents complete work, you'll see:
```
- [🔄] #019 [developer] Create useSearch Composable (Agent working...)
- [🔄] #020 [developer] Create SearchBar Component (Agent working...)
- [ ] #022 [tester] Integration Tests for Search Module
- [🔄] #023 [documentation] Document Search Module (Agent working...)
- [ ] #025 [developer] Re-review XSS Fix Verification
```

Then after commits:
```
- [✅] #019 [developer] Create useSearch Composable (Completed!)
- [✅] #020 [developer] Create SearchBar Component (Completed!)
- [ ] #022 [tester] Integration Tests for Search Module
- [✅] #023 [documentation] Document Search Module (Completed!)
- [ ] #025 [developer] Re-review XSS Fix Verification
```

### View Recent Commits

```bash
cd ../epic-search-module
git log --oneline -10
```

Expected:
```
abc123 docs(search): Task #023 - comprehensive documentation
def456 feat(search): Task #020 - SearchBar component
ghi789 feat(search): Task #019 - useSearch composable
```

---

## Task Delegation After Completion

When developer agents complete tasks #019 and #020, they should automatically create follow-up tasks:

### Expected Delegated Tasks

After Task #019 completes:
```
- [ ] #019-audit [auditor] Review useSearch composable for HIPAA/security
- [ ] #019-test [tester] Validate useSearch test coverage and edge cases
```

After Task #020 completes:
```
- [ ] #020-audit [auditor] Review SearchBar for XSS/accessibility
- [ ] #020-test [tester] Validate SearchBar test coverage and interactions
```

This creates the "never-ending loop":
```
Developer completes #019
    ↓
Creates tasks for auditor + tester
    ↓
Auditor/tester work on their tasks
    ↓
If issues found → create new developer task
    ↓
Developer fixes issues
    ↓
Loop continues...
```

---

## Next Steps After Parallel Work Completes

1. **Merge completed work back to main**:
   ```bash
   cd /home/user/cogstack-nlp
   git checkout claude/development-on-ccweb-014NeWxCVzNfcbd6R6RFpo18
   git merge epic/search-module
   ```

2. **Create more parallel worktrees** for other modules:
   ```bash
   # Timeline module
   git worktree add ../epic-timeline-module -b epic/timeline-module
   .claude/scripts/spawn-worktree-loop.sh timeline-module ../epic-timeline-module

   # De-identification module
   git worktree add ../epic-deidentification-module -b epic/deidentification-module
   .claude/scripts/spawn-worktree-loop.sh deidentification-module ../epic-deidentification-module
   ```

3. **Monitor all worktrees**:
   ```bash
   .claude/scripts/monitor-loops.sh --report
   ```

---

## Summary

**Ready to spawn agents!** Choose Option 1 (Task tool - 3 agents in one message) for maximum efficiency.

Each agent will:
- ✅ Work in isolated worktree (no conflicts)
- ✅ Complete their assigned task
- ✅ Commit changes
- ✅ Delegate to other agents
- ✅ Continue loop indefinitely

**The worktree is initialized and waiting for agents to start!**
