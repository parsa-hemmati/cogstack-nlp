# Next Wave: Spawn 5 Agents in Parallel

**Current Status**: 3 tasks completed, 7 pending delegated tasks ready
**Worktree**: epic-search-module
**Time to spawn**: Now!

---

## Quick Summary

**Wave 1** (completed):
- ✅ Developer (#019) - useSearch composable
- ✅ Developer (#020) - SearchBar component
- ✅ Documentation (#023) - comprehensive docs

**Wave 2** (ready to spawn):
- [ ] Auditor (#019-audit) - Review useSearch security/HIPAA
- [ ] Auditor (#020-audit) - Review SearchBar XSS/accessibility
- [ ] Tester (#019-test) - Validate useSearch test coverage
- [ ] Tester (#020-test) - Validate SearchBar test coverage
- [ ] Developer (#023-review) - Review documentation accuracy

---

## Spawn Command (Copy & Paste)

Use **5 Task tool calls in ONE message** to spawn all agents in parallel:

### Agent 1: Auditor for #019-audit

```yaml
Task:
  subagent_type: "auditor"
  description: "Review useSearch security/HIPAA"
  model: "sonnet"
  prompt: |
    You are reviewing code in worktree: ../epic-search-module

    **Task**: #019-audit - Review useSearch composable for security/HIPAA compliance
    **Files to Review**:
    - frontend/src/composables/useSearch.ts
    - frontend/src/api/search.ts
    - frontend/src/types/search.ts

    Your job:
    1. Review for HIPAA compliance:
       - PHI handling in search queries
       - Audit logging for search access
       - Session management security
       - Data encryption in transit
    2. Check for security vulnerabilities:
       - API authentication/authorization
       - Input sanitization in search queries
       - SQL injection risks (backend API)
       - Information disclosure in error messages
    3. Verify compliance with healthcare regulations:
       - § 164.308(a)(4) - Information Access Management
       - § 164.312(a)(1) - Access Control
       - § 164.312(e)(1) - Transmission Security

    Deliverables:
    - Create audit report: .claude/autonomous-worktrees/search-module/audits/019-audit-report.md
    - If issues found: Create developer task #019-fix with specific remediation steps
    - If clean: Mark #019-audit as complete, add note "No issues found ✅"

    Commit with: "audit(search): Task #019-audit - useSearch security review"

    Work directory: ../epic-search-module
```

### Agent 2: Auditor for #020-audit

```yaml
Task:
  subagent_type: "auditor"
  description: "Review SearchBar XSS/accessibility"
  model: "sonnet"
  prompt: |
    You are reviewing code in worktree: ../epic-search-module

    **Task**: #020-audit - Review SearchBar component for XSS/accessibility
    **Files to Review**:
    - frontend/src/components/search/SearchBar.vue
    - frontend/tests/unit/components/search/SearchBar.spec.ts

    Your job:
    1. Check for XSS vulnerabilities:
       - v-html usage (should not exist in search input)
       - Input sanitization before display
       - Event handler injection risks
       - Script tag injection via search query
    2. Verify accessibility (WCAG 2.1 AA):
       - Proper ARIA labels and roles
       - Keyboard navigation (Enter, Escape, Tab)
       - Focus indicators visible
       - Screen reader compatibility
       - Color contrast ratios
       - High contrast mode support
    3. Security best practices:
       - No credentials in component code
       - No sensitive data in console logs
       - Proper error handling (no stack traces to user)

    Deliverables:
    - Create audit report: .claude/autonomous-worktrees/search-module/audits/020-audit-report.md
    - If issues found: Create developer task #020-fix with specific fixes
    - If clean: Mark #020-audit as complete with "No issues found ✅"

    Commit with: "audit(search): Task #020-audit - SearchBar security/accessibility review"

    Work directory: ../epic-search-module
```

### Agent 3: Tester for #019-test

```yaml
Task:
  subagent_type: "tester"
  description: "Validate useSearch test coverage"
  model: "haiku"
  prompt: |
    You are testing code in worktree: ../epic-search-module

    **Task**: #019-test - Validate useSearch composable test coverage
    **Files to Test**:
    - frontend/src/composables/useSearch.ts (source)
    - frontend/tests/unit/composables/useSearch.spec.ts (tests - 27 tests, 21 passing)

    Your job:
    1. Fix failing tests (6 watcher-related tests):
       - Investigate async timing issues
       - Add proper waitFor() or flushPromises()
       - Ensure watchers trigger correctly in tests
    2. Increase coverage to >90%:
       - Add edge case tests (empty query, null results, network timeout)
       - Test error scenarios (API 500, API 404, invalid JSON)
       - Test cache expiration logic
    3. Validate test quality:
       - All assertions meaningful
       - No flaky tests (run 10 times, all pass)
       - Test isolation (no shared state between tests)
       - Mock API responses realistic

    Success Criteria:
    - All 27+ tests passing (100%)
    - Coverage ≥90% (statements, branches, functions)
    - No flaky tests (10 consecutive runs pass)
    - Performance: test suite runs in <5 seconds

    Deliverables:
    - Fix failing tests in useSearch.spec.ts
    - Add missing edge case tests
    - Run coverage report: npm run test:coverage
    - Create test report: .claude/autonomous-worktrees/search-module/test-reports/019-test-report.md

    Commit with: "test(search): Task #019-test - useSearch coverage validated"

    Work directory: ../epic-search-module
```

### Agent 4: Tester for #020-test

```yaml
Task:
  subagent_type: "tester"
  description: "Validate SearchBar test coverage"
  model: "haiku"
  prompt: |
    You are testing code in worktree: ../epic-search-module

    **Task**: #020-test - Validate SearchBar component test coverage
    **Files to Test**:
    - frontend/src/components/search/SearchBar.vue (source)
    - frontend/tests/unit/components/search/SearchBar.spec.ts (tests - 10 suites, currently blocked by CSS module issue)

    Your job:
    1. Fix CSS module loading issue:
       - Investigate worktree-specific vitest config
       - Add CSS module mock or transformer
       - Ensure tests can run without CSS errors
    2. Run all 10 test suites:
       - Rendering tests
       - Search triggering tests
       - Clear functionality tests
       - Loading states tests
       - Keyboard interaction tests
       - Accessibility tests
       - Props tests
       - Events tests
       - Edge cases tests
    3. Verify test coverage >90%:
       - All component methods tested
       - All user interactions tested
       - All props/events tested
       - Error states tested

    Success Criteria:
    - All tests passing (100%)
    - Coverage ≥90%
    - Accessibility tests validate WCAG 2.1 AA
    - Keyboard navigation fully tested

    Deliverables:
    - Fix vitest CSS module configuration
    - Run all tests successfully
    - Create test report: .claude/autonomous-worktrees/search-module/test-reports/020-test-report.md

    Commit with: "test(search): Task #020-test - SearchBar coverage validated"

    Work directory: ../epic-search-module
```

### Agent 5: Developer for #023-review

```yaml
Task:
  subagent_type: "developer"
  description: "Review documentation accuracy"
  model: "sonnet"
  prompt: |
    You are reviewing documentation in worktree: ../epic-search-module

    **Task**: #023-review - Review documentation for technical accuracy
    **Files to Review**:
    - docs/features/search/*.md (8 documentation files)
    - Inline JSDoc comments in source files

    Your job:
    1. Verify technical accuracy:
       - API references match actual implementation
       - Code examples are correct and tested
       - TypeScript types documented accurately
       - Props/events/slots match component code
       - No outdated information
    2. Test all code examples:
       - Copy examples from docs
       - Verify they compile without errors
       - Ensure examples follow best practices
       - Add "Tested ✅" comment to working examples
    3. Improve documentation where needed:
       - Add missing edge cases
       - Clarify ambiguous explanations
       - Fix typos and grammar
       - Ensure consistency across all docs

    Deliverables:
    - Fix any inaccurate documentation
    - Test and validate all 8 code examples
    - Add comments: "<!-- Tested 2025-11-21 ✅ -->" to working examples
    - Create review report: .claude/autonomous-worktrees/search-module/reviews/023-review-report.md

    Commit with: "docs(search): Task #023-review - documentation accuracy verified"

    Work directory: ../epic-search-module
```

---

## Expected Timeline

**All 5 agents spawn at**: ~16:35:00

**Estimated completion times**:
- Auditor #019-audit: ~10 min (16:45:00)
- Auditor #020-audit: ~10 min (16:45:00)
- Tester #019-test: ~20 min (16:55:00) - needs to fix 6 failing tests
- Tester #020-test: ~20 min (16:55:00) - needs to fix CSS module issue
- Developer #023-review: ~15 min (16:50:00) - review 8 docs + test examples

**Total parallel time**: ~20 minutes (vs 75 minutes sequential)
**Efficiency gain**: 3.75x faster!

---

## After Wave 2 Completes

### Expected Delegated Tasks

If issues found by auditors:
```
- [ ] #019-fix [developer] Fix HIPAA/security issues in useSearch
- [ ] #020-fix [developer] Fix XSS/accessibility issues in SearchBar
```

If testers need developer help:
```
- [ ] #019-test-help [developer] Help debug failing watcher tests
- [ ] #020-test-help [developer] Fix CSS module configuration
```

### Remaining Original Tasks
```
- [ ] #022 [tester] Integration Tests for Search Module
- [ ] #025 [auditor] Re-review XSS Fix Verification
```

### Wave 3 Ready

After Wave 2 completes, spawn:
- Integration tester for #022 (full E2E flow)
- Auditor for #025 (re-verify XSS fix from earlier work)
- Developers for any #019-fix, #020-fix tasks

---

## Monitoring Commands

### Watch Task Queue
```bash
watch -n 5 "cat .claude/autonomous-worktrees/search-module/TASK_QUEUE.md"
```

### View Worktree Commits
```bash
watch -n 10 "git -C ../epic-search-module log --oneline -10"
```

### Check Agent Activity
```bash
# View recent files modified
find ../epic-search-module -type f -mmin -5 -ls
```

---

## Summary

**Ready to spawn Wave 2!**

Copy the 5 Task tool prompts above into a **single message** to spawn all agents in parallel.

Expected result:
- 5 agents working simultaneously
- ~20 minutes total (vs 75 sequential)
- Delegated tasks created if issues found
- Never-ending loop continues!

**Go!** 🚀
