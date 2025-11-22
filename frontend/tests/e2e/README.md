# Timeline E2E Tests

End-to-end tests for the Timeline module using Playwright.

## Overview

This directory contains comprehensive E2E tests for the patient timeline feature:

- **timeline.spec.ts**: Core timeline viewing workflows
- **timelineFilters.spec.ts**: Filter application and saved presets
- **timelineAccessibility.spec.ts**: WCAG 2.1 AA compliance tests

## Running Tests

### Prerequisites

```bash
# Install dependencies
npm install

# Install Playwright browsers
npx playwright install
```

### Run All E2E Tests

```bash
npm run test:e2e
```

### Run Specific Test File

```bash
npx playwright test tests/e2e/timeline.spec.ts
```

### Run Tests with UI

```bash
npm run test:e2e:ui
```

### Run Tests in Headed Mode (see browser)

```bash
npm run test:e2e:headed
```

### Run Accessibility Tests Only

```bash
npm run test:accessibility
```

### Debug Mode

```bash
npm run test:e2e:debug
```

## Test Reports

After running tests, view the HTML report:

```bash
npx playwright show-report
```

## Test Data

Tests expect the following test patients to exist:

- **P12345**: 50 events (light load)
- **P_MEDIUM**: 500 events (medium load)
- **P_LARGE**: 5000 events (heavy load)

### Seed Test Data

```bash
# Backend test data seeding
python backend/scripts/seed_timeline_test_data.py
```

## Test Coverage

### timeline.spec.ts (10 tests)

- User views patient timeline
- Timeline loads with performance <500ms
- Timeline displays correct event count
- Timeline handles empty state
- Timeline handles API errors gracefully
- User can retry failed timeline load
- Timeline displays loading state
- Timeline respects RBAC - unauthorized access blocked
- Timeline audit logging - verifies request headers

### timelineFilters.spec.ts (10 tests)

- User filters timeline by date range
- User filters timeline by event type
- User filters timeline by multiple event types
- User filters by specialty
- User clears filters
- Filters update URL parameters
- Filters persist on page reload
- Filter panel can be toggled open/closed
- Debounced filter updates - prevents excessive API calls

### timelineAccessibility.spec.ts (15+ tests)

- Timeline passes automated accessibility audit
- Timeline has proper ARIA labels
- Timeline supports keyboard navigation
- Event markers have descriptive accessible names
- Filter controls announce changes to screen readers
- Event detail modal announces when opened
- Color contrast meets WCAG AA (4.5:1 minimum)
- Focus indicators are visible
- Form inputs have associated labels
- Interactive elements are keyboard accessible
- Screen reader landmarks are properly defined
- Images have alt text
- Error messages are announced to screen readers
- Loading states are announced to screen readers
- Modal traps focus when open

## Performance Targets

All tests verify the following performance targets:

- **Timeline load**: <500ms for 1,000 events
- **Filter application**: <300ms (debounced)
- **Event detail modal**: <100ms to open
- **Accessibility audit**: 0 violations
- **WCAG 2.1 AA compliance**: All checks passing

## CI/CD Integration

Tests run automatically in CI/CD pipeline:

```yaml
# .github/workflows/e2e.yml
- name: Run E2E tests
  run: npm run test:e2e
```

## Troubleshooting

### Tests Failing Locally

1. **Check test data**: Ensure test patients exist
2. **Check services**: Ensure backend API is running
3. **Check ports**: Ensure port 5173 (frontend) and 8000 (backend) are available
4. **Clear cache**: `rm -rf node_modules/.cache`
5. **Reinstall browsers**: `npx playwright install --force`

### Debugging Failing Tests

```bash
# Run with trace
npx playwright test --trace on

# View trace
npx playwright show-trace trace.zip
```

### Slow Tests

```bash
# Run with timeout
npx playwright test --timeout 60000

# Run in parallel
npx playwright test --workers 4
```

## Writing New Tests

### Best Practices

1. **Use data-testid attributes**: Prefer `[data-testid="..."]` over CSS classes
2. **Wait for network idle**: Use `await page.waitForLoadState('networkidle')`
3. **Use explicit waits**: `await expect(element).toBeVisible({ timeout: 5000 })`
4. **Mock API responses**: For deterministic tests
5. **Test user workflows**: Not implementation details

### Example Test

```typescript
test('User can filter timeline by date', async ({ page }) => {
  // Navigate to timeline
  await page.goto('/patients/P12345/timeline')
  await page.waitForLoadState('networkidle')

  // Open filters
  await page.click('[data-testid="filter-toggle"]')

  // Set date range
  await page.fill('[data-testid="start-date"]', '2024-01-01')
  await page.fill('[data-testid="end-date"]', '2024-12-31')

  // Apply filters
  await page.click('[data-testid="apply-filters"]')

  // Verify results
  await expect(page.locator('[data-testid="event-count"]')).toContainText('50')
})
```

## Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [axe-core Accessibility Testing](https://github.com/dequelabs/axe-core)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
