---
name: browser-testing
description: Browser automation patterns for E2E testing. Use when writing Playwright tests, browser-use AI tests, or Docker orchestration for test environments. Provides patterns for healthcare UI testing, accessibility validation, and AI-driven exploration.
---

# Browser Testing Skill

Expert knowledge for E2E browser testing in the Clinical Care Tools platform.

## Docker Orchestration

### Start All Services
```bash
# Using orchestration script
./scripts/docker-test-runner.sh start

# Manual start
docker-compose up -d
```

### Health Check Polling
```bash
# Check all services
./scripts/docker-test-runner.sh status

# Individual service checks
docker-compose exec -T postgres pg_isready -U clinicaltools
docker-compose exec -T redis redis-cli ping
curl -f http://localhost:9200/_cluster/health
curl -f http://localhost:8001/api/info
curl -f http://localhost:8000/api/health
curl -f http://localhost:8080
```

### Service Startup Times
| Service | Expected Time | Health Check |
|---------|---------------|--------------|
| postgres | 10-15s | pg_isready |
| redis | 3-5s | redis-cli ping |
| elasticsearch | 45-60s | _cluster/health |
| medcat-service | 60-90s | /api/info |
| backend | 15-20s | /api/health |
| frontend | 10-15s | HTTP 200 |

### Stop Services
```bash
./scripts/docker-test-runner.sh stop
# or
docker-compose down
```

---

## Playwright Best Practices

### Selector Strategy
```typescript
// PREFERRED: data-testid attributes
await page.getByTestId('timeline-view');
await page.getByTestId('search-input');
await page.getByTestId('export-button');

// GOOD: Role-based (accessible)
await page.getByRole('button', { name: 'Export' });
await page.getByRole('searchbox');
await page.getByRole('navigation');

// ACCEPTABLE: Text content
await page.getByText('Patient Timeline');
await page.getByLabel('Search patients');

// AVOID: CSS selectors (fragile)
// await page.locator('.btn-primary'); // Bad
```

### Waiting Strategies
```typescript
// Wait for element to be visible
await page.waitForSelector('[data-testid="timeline-loaded"]');

// Wait for network idle (all API calls complete)
await page.waitForLoadState('networkidle');

// Wait for specific response
await page.waitForResponse(resp =>
  resp.url().includes('/api/v1/timeline') && resp.status() === 200
);

// Explicit timeout for slow operations
await expect(page.getByTestId('results')).toBeVisible({ timeout: 30000 });
```

### Page Object Pattern
```typescript
// pages/TimelinePage.ts
export class TimelinePage {
  constructor(private page: Page) {}

  async navigate(patientId: string) {
    await this.page.goto(`/timeline/${patientId}`);
    await this.page.waitForSelector('[data-testid="timeline-loaded"]');
  }

  async zoomIn() {
    await this.page.getByTestId('zoom-in-btn').click();
  }

  async getConceptCount(): Promise<number> {
    return await this.page.getByTestId('concept-marker').count();
  }
}
```

### Assertions
```typescript
// Visibility
await expect(page.getByTestId('timeline')).toBeVisible();

// Text content
await expect(page.getByTestId('patient-name')).toHaveText('John Doe');

// Count
await expect(page.getByTestId('concept-marker')).toHaveCount(15);

// Attribute
await expect(page.getByTestId('export-btn')).toBeEnabled();
```

---

## browser-use AI Testing

### Basic Setup
```python
from browser_use import Agent
from langchain_anthropic import ChatAnthropic

llm = ChatAnthropic(model="claude-sonnet-4-20250514")

agent = Agent(
    task="Your exploration task here",
    llm=llm
)

result = await agent.run()
```

### Healthcare UI Exploration Prompts

#### Timeline Exploration
```python
task = """
Navigate to the patient timeline view at http://localhost:8080/timeline/patient-123.

Perform these explorations:
1. Test all zoom controls (zoom in, zoom out, reset)
2. Test panning (drag left, drag right)
3. Click on different concept markers and verify popover appears
4. Test keyboard navigation (arrow keys, Tab, Enter)
5. Verify the date range is displayed correctly

Report any UI issues, accessibility problems, or unexpected behaviors.
"""
```

#### Search Flow Exploration
```python
task = """
Navigate to http://localhost:8080/search.

Test the patient search functionality:
1. Enter a medical concept (e.g., "diabetes")
2. Apply meta-annotation filters (negation, temporality)
3. Execute the search
4. Verify results appear with patient information
5. Click on a patient to view their timeline

Report any search bugs, missing features, or usability issues.
"""
```

#### Export Workflow
```python
task = """
Navigate to a patient timeline at http://localhost:8080/timeline/patient-123.

Test the export functionality:
1. Locate the export toolbar
2. Test CSV export - verify file downloads
3. Test JSON export - verify file downloads
4. Test FHIR export - verify file downloads
5. Check if exported files contain expected data

Report any export failures or data issues.
"""
```

### AI Test Structure
```python
import pytest
from browser_use import Agent
from langchain_anthropic import ChatAnthropic

@pytest.fixture
def llm():
    return ChatAnthropic(model="claude-sonnet-4-20250514")

@pytest.mark.asyncio
async def test_timeline_exploration(llm):
    agent = Agent(
        task="Navigate to timeline and test zoom controls",
        llm=llm
    )
    result = await agent.run()

    # Check for critical errors
    assert "error" not in result.lower()
    assert "crash" not in result.lower()

    # AI should report findings
    print(f"AI Findings: {result}")
```

---

## TESTING.md Report Format

### Section Header
```markdown
## Browser Test Runner Results [2025-01-15 14:30:00]
```

### Docker Status Table
```markdown
### Docker Services
| Service | Status | Startup Time |
|---------|--------|--------------|
| postgres | healthy | 12s |
| redis | healthy | 5s |
| elasticsearch | healthy | 45s |
| medcat-service | healthy | 90s |
| backend | healthy | 20s |
| frontend | healthy | 15s |
```

### Playwright Results
```markdown
### Playwright Tests
- **Total**: 25 tests
- **Passed**: 24
- **Failed**: 1
- **Skipped**: 0
- **Duration**: 2m 45s

#### Failed Tests
1. `timeline.spec.ts > should export PDF`
   - Error: Timeout waiting for download
   - Screenshot: [link]
```

### AI Test Results
```markdown
### AI Exploratory Tests (browser-use)
| Test | Status | Duration | Findings |
|------|--------|----------|----------|
| Timeline Exploration | PASS | 45s | Zoom controls work |
| Search Flow | PASS | 60s | None |
| Export Workflow | FAIL | 30s | PDF export timeout |

#### AI Findings
- Keyboard navigation missing for concept markers
- Color contrast low on disabled buttons
- Mobile viewport not tested
```

### Summary
```markdown
### Summary
- **Overall Status**: FAIL (1 Playwright + 1 AI test failed)
- **Total Execution Time**: 8m 30s
- **Recommendations**:
  1. Fix PDF export timeout issue
  2. Add aria-labels to concept markers
  3. Improve button contrast ratio
```

---

## Accessibility Testing

### axe-core Integration
```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('timeline accessibility', async ({ page }) => {
  await page.goto('/timeline/patient-123');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

### Manual Checks
- Keyboard navigation (Tab, Shift+Tab, Enter, Escape)
- Screen reader announcements (aria-live regions)
- Focus indicators visible
- Color contrast (4.5:1 minimum)
- Alternative text for images

---

## Troubleshooting

### Docker Issues
```bash
# Check Docker is running
docker info

# View service logs
docker-compose logs backend
docker-compose logs frontend

# Check port conflicts
netstat -tulpn | grep -E '8000|8080|5432'

# Restart specific service
docker-compose restart backend
```

### Playwright Issues
```bash
# Install browsers
npx playwright install chromium

# Run with headed browser (visible)
npm run test:e2e -- --headed

# Debug mode
npm run test:e2e -- --debug

# Generate report
npx playwright show-report
```

### browser-use Issues
```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check API key
import os
assert os.getenv("ANTHROPIC_API_KEY"), "Missing API key"

# Test with simple task first
agent = Agent(task="Go to google.com", llm=llm)
```
