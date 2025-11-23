# End-to-End Tests

E2E tests for Clinical Care Tools using Playwright.

## Setup

### Install Playwright

```bash
cd clinical-care-tools/frontend
npm install -D @playwright/test
npx playwright install
```

### Install Browsers

```bash
npx playwright install chromium firefox webkit
```

## Running Tests

### Run All E2E Tests

```bash
npx playwright test
```

### Run Specific Test File

```bash
npx playwright test tests/e2e/user-management.spec.ts
```

### Run in UI Mode (Interactive)

```bash
npx playwright test --ui
```

### Run in Headed Mode (See Browser)

```bash
npx playwright test --headed
```

### Run Specific Browser

```bash
npx playwright test --project=chromium
npx playwright test --project=firefox
npx playwright test --project=webkit
```

## Test Reports

### View HTML Report

```bash
npx playwright show-report
```

Reports are generated in `playwright-report/` directory after test runs.

## Test Coverage

### User Management (user-management.spec.ts)

Tests complete user lifecycle workflow:

1. **Admin Login**: Admin authenticates to the system
2. **Navigate to User Management**: Access user management page
3. **Create User**: Admin creates new user with credentials
4. **Admin Logout**: Admin logs out of the system
5. **New User Login**: Newly created user logs in
6. **Change Password**: New user changes password on first login
7. **Verify Access**: New user can access appropriate pages based on role
8. **Edit User**: Admin can edit existing user details
9. **Filter Users**: Admin can filter users by role (when implemented)
10. **Access Control**: Non-admin users cannot access user management

## Prerequisites

Before running E2E tests:

1. **Backend API Running**: Ensure backend is running at `http://localhost:8000`
2. **Frontend Dev Server Running**: Ensure frontend is running at `http://localhost:3000`
3. **Database Populated**: Ensure default admin user exists in database
4. **Services Healthy**: All dependencies (PostgreSQL, Redis) are running

## Configuration

E2E test configuration is in `playwright.config.ts`:

- **Test Directory**: `tests/e2e/`
- **Base URL**: `http://localhost:3000`
- **API Base URL**: `http://localhost:8000`
- **Browsers**: Chromium, Firefox, WebKit, Mobile Chrome, Mobile Safari
- **Screenshots**: Captured on failure
- **Videos**: Retained on failure
- **Traces**: Captured on first retry

## Debugging Tests

### Debug Mode

```bash
npx playwright test --debug
```

### Show Trace Viewer

```bash
npx playwright show-trace trace.zip
```

### Console Logs

Playwright captures console logs from the browser. View them in the HTML report.

## Writing New E2E Tests

### Test Structure

```typescript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup before each test
    await page.goto('http://localhost:3000')
  })

  test('should do something', async ({ page }) => {
    // Test implementation
    await page.click('button')
    await expect(page.locator('text=Success')).toBeVisible()
  })
})
```

### Best Practices

1. **Use Test Steps**: Group related actions with `test.step()`
2. **Wait for Elements**: Use `await expect(...).toBeVisible()` instead of hardcoded waits
3. **Screenshot on Failure**: Configured automatically
4. **Isolate Tests**: Each test should be independent
5. **Clean Up**: Delete test data created during tests
6. **Descriptive Names**: Use clear, descriptive test names
7. **Page Object Pattern**: Consider using page objects for complex pages

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Start services
        run: docker-compose up -d

      - name: Run E2E tests
        run: npx playwright test

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

## Troubleshooting

### Tests Timing Out

- Increase timeout in `playwright.config.ts`: `timeout: 60000`
- Check if backend/frontend servers are running
- Verify database is accessible

### Element Not Found

- Use `page.waitForSelector()` before interacting
- Check if element selector is correct
- Verify page has loaded completely

### Authentication Failures

- Ensure default admin user exists in database
- Verify credentials in test file match database
- Check if login endpoint is working

### Browser Not Launching

- Run `npx playwright install` to install browsers
- Check system dependencies: `npx playwright install-deps`

## Additional Resources

- [Playwright Documentation](https://playwright.dev/)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Playwright API Reference](https://playwright.dev/docs/api/class-playwright)
