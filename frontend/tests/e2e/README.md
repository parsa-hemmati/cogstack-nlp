# E2E, Performance, and Accessibility Testing

This directory contains comprehensive end-to-end, performance, and accessibility tests for the Timeline Module.

## Overview

### Test Coverage

1. **E2E Tests (Playwright)**:
   - `timeline.spec.ts` - Core timeline functionality
   - `timelineFilters.spec.ts` - Filter application and presets
   - `timelineAccessibility.spec.ts` - WCAG 2.1 AA compliance

2. **Performance Tests**:
   - Backend: `backend/tests/performance/test_timeline_load.py` (Locust)
   - Frontend: `tests/performance/timeline.perf.ts` (Playwright + Performance API)

3. **Accessibility Tests**:
   - Automated audits with axe-core
   - Keyboard navigation testing
   - Screen reader support validation
   - Color contrast verification

## Prerequisites

### Dependencies

```bash
# Frontend dependencies (already installed)
npm install

# Backend dependencies
pip install locust

# Playwright browsers
npx playwright install chromium firefox webkit
```

### Test Data

Create test patients with varying event counts:

```bash
# Run test data seeding script
python backend/scripts/seed_test_data.py
```

This creates:
- **P_SMALL**: 50 events (low complexity)
- **P_MEDIUM**: 1,000 events (medium complexity)
- **P_LARGE**: 10,000 events (high complexity)

## Running Tests

### E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run with UI (interactive mode)
npm run test:e2e:ui

# Run in headed mode (see browser)
npm run test:e2e:headed

# Run specific test file
npx playwright test tests/e2e/timeline.spec.ts

# Debug mode
npm run test:e2e:debug
```

### Performance Tests

#### Backend Load Testing (Locust)

```bash
# Web UI mode (recommended for interactive testing)
locust -f backend/tests/performance/test_timeline_load.py --host=http://localhost:8000

# Then open http://localhost:8089 and configure:
# - Number of users: 100
# - Spawn rate: 10 users/second
# - Run time: 5 minutes

# Headless mode (CI/CD)
locust -f backend/tests/performance/test_timeline_load.py \
  --host=http://localhost:8000 \
  --headless \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --html=timeline_load_test_report.html
```

#### Frontend Performance (Playwright)

```bash
# Run performance tests
npx playwright test tests/performance/timeline.perf.ts

# Generate HTML report
npx playwright test tests/performance/timeline.perf.ts --reporter=html
```

#### Frontend Performance (Lighthouse CI)

```bash
# Run Lighthouse CI
npm run test:perf

# This will:
# 1. Build production bundle
# 2. Start preview server
# 3. Run Lighthouse on 3 URLs
# 4. Generate performance report
```

### Accessibility Tests

```bash
# Run accessibility tests only
npm run test:accessibility

# Or run all accessibility tests in timelineAccessibility.spec.ts
npx playwright test tests/e2e/timelineAccessibility.spec.ts
```

## Performance Targets

### Backend (Locust)

- **P50 response time**: < 200ms
- **P95 response time**: < 500ms
- **P99 response time**: < 1000ms
- **Success rate**: > 99%

### Frontend (Lighthouse CI)

- **Performance score**: > 90
- **Accessibility score**: > 95
- **First Contentful Paint**: < 1.5s
- **Largest Contentful Paint**: < 2.5s
- **Time to Interactive**: < 3.5s
- **Total Blocking Time**: < 300ms
- **Cumulative Layout Shift**: < 0.1

### Rendering Performance

- **100 events**: < 500ms
- **1,000 events**: < 1000ms
- **10,000 events**: < 2000ms

## Accessibility Requirements

### WCAG 2.1 AA Compliance

- ✅ No automated accessibility violations (axe-core)
- ✅ Keyboard navigation for all interactions
- ✅ Screen reader support (ARIA labels)
- ✅ Color contrast ratio ≥ 4.5:1
- ✅ Focus indicators visible
- ✅ Semantic HTML structure

### Keyboard Shortcuts

- **Tab**: Navigate between elements
- **Arrow keys**: Navigate timeline events
- **Enter**: Open event detail
- **Escape**: Close modal
- **+**: Zoom in
- **-**: Zoom out
- **0**: Reset zoom

## Test Reports

### Playwright HTML Report

```bash
# Generate HTML report after test run
npx playwright show-report
```

### Lighthouse CI Report

Results saved to `.lighthouseci/` directory after running `npm run test:perf`.

### Locust HTML Report

Generated with `--html` flag. Example:

```bash
locust -f backend/tests/performance/test_timeline_load.py \
  --host=http://localhost:8000 \
  --headless \
  --users=100 \
  --spawn-rate=10 \
  --run-time=5m \
  --html=reports/timeline_load_test_$(date +%Y%m%d_%H%M%S).html
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E and Performance Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: |
          npm ci
          npx playwright install --with-deps
      - name: Run E2E tests
        run: npm run test:e2e
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: playwright-report
          path: playwright-report/

  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm ci
      - name: Run Lighthouse CI
        run: npm run test:perf
      - name: Upload Lighthouse results
        uses: actions/upload-artifact@v3
        with:
          name: lighthouse-results
          path: .lighthouseci/
```

## Troubleshooting

### Common Issues

1. **Playwright browsers not installed**:
   ```bash
   npx playwright install chromium
   ```

2. **Test data not seeded**:
   ```bash
   python backend/scripts/seed_test_data.py
   ```

3. **Backend not running**:
   ```bash
   # Start backend server
   cd backend && uvicorn app.main:app --reload
   ```

4. **Frontend not running**:
   ```bash
   # Start frontend dev server
   npm run dev
   ```

5. **Locust not installed**:
   ```bash
   pip install locust
   ```

## Test Maintenance

### Adding New Tests

1. **E2E test**: Add to appropriate `*.spec.ts` file
2. **Performance test**: Add task to `test_timeline_load.py` or new test case to `timeline.perf.ts`
3. **Accessibility test**: Add to `timelineAccessibility.spec.ts`

### Updating Test Data

Modify `backend/scripts/seed_test_data.py` to adjust test patient data.

## References

- [Playwright Documentation](https://playwright.dev/)
- [Locust Documentation](https://docs.locust.io/)
- [Lighthouse CI Documentation](https://github.com/GoogleChrome/lighthouse-ci)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Task Reference

**Task #007**: E2E Tests, Performance Testing & Accessibility Audit
**Status**: Complete
**Date**: 2025-11-22
