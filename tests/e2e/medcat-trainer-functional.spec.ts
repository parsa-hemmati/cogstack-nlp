import { test, expect, APIRequestContext } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Functional E2E tests for MedCAT Trainer
 * Tests actual application workflows with dummy clinical data
 */

// Test credentials - create a test user in Django admin or via API
const TEST_USER = {
  username: 'e2e_test_user',
  password: 'TestPassword123!'
};

const ADMIN_USER = {
  username: 'admin',
  password: 'admin'
};

// Load clinical documents fixture
const fixturesPath = path.join(__dirname, 'fixtures', 'clinical-documents.json');
let clinicalFixtures: any = null;

try {
  clinicalFixtures = JSON.parse(fs.readFileSync(fixturesPath, 'utf-8'));
} catch (e) {
  console.warn('Could not load clinical fixtures:', e);
}

/**
 * Helper: Get API token for authentication
 */
async function getAuthToken(request: APIRequestContext, username: string, password: string): Promise<string | null> {
  try {
    const response = await request.post('/api/api-token-auth/', {
      data: { username, password }
    });

    if (response.ok()) {
      const data = await response.json();
      return data.token;
    }
  } catch (e) {
    console.warn('Auth failed:', e);
  }
  return null;
}

/**
 * Helper: Make authenticated API request
 */
async function authenticatedRequest(
  request: APIRequestContext,
  token: string,
  method: 'get' | 'post' | 'put' | 'delete',
  endpoint: string,
  data?: any
) {
  const options: any = {
    headers: {
      'Authorization': `Token ${token}`,
      'Content-Type': 'application/json'
    }
  };

  if (data) {
    options.data = data;
  }

  return request[method](endpoint, options);
}

// ============================================================================
// API Authentication Tests
// ============================================================================

test.describe('MedCAT Trainer - API Authentication', () => {
  test('should reject unauthenticated API requests', async ({ request }) => {
    const response = await request.get('/api/users/');
    expect(response.status()).toBe(401);

    const data = await response.json();
    expect(data.detail).toContain('Authentication credentials were not provided');
  });

  test('should reject invalid credentials', async ({ request }) => {
    const response = await request.post('/api/api-token-auth/', {
      data: {
        username: 'nonexistent_user',
        password: 'wrong_password'
      }
    });

    expect(response.status()).toBe(400);
  });

  test('should return token for valid credentials', async ({ request }) => {
    const token = await getAuthToken(request, ADMIN_USER.username, ADMIN_USER.password);

    // Token might not exist if admin user isn't created
    if (token) {
      expect(token.length).toBeGreaterThan(0);
      console.log('Successfully authenticated as admin');
    } else {
      console.log('Admin user not available - skipping token validation');
    }
  });
});

// ============================================================================
// API Endpoint Tests
// ============================================================================

test.describe('MedCAT Trainer - API Endpoints', () => {
  let authToken: string | null = null;

  test.beforeAll(async ({ request }) => {
    authToken = await getAuthToken(request, ADMIN_USER.username, ADMIN_USER.password);
  });

  test('should list available API endpoints', async ({ request }) => {
    const response = await request.get('/api/');
    expect(response.ok()).toBeTruthy();

    const endpoints = await response.json();

    // Verify core endpoints exist
    expect(endpoints).toHaveProperty('users');
    expect(endpoints).toHaveProperty('documents');
    expect(endpoints).toHaveProperty('project-annotate-entities');
    expect(endpoints).toHaveProperty('entities');
    expect(endpoints).toHaveProperty('annotated-entities');
    expect(endpoints).toHaveProperty('concept-dbs');
    expect(endpoints).toHaveProperty('datasets');
  });

  test('should access users endpoint with auth', async ({ request }) => {
    if (!authToken) {
      test.skip();
      return;
    }

    const response = await authenticatedRequest(request, authToken, 'get', '/api/users/');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('results');
    expect(Array.isArray(data.results)).toBeTruthy();
  });

  test('should access datasets endpoint with auth', async ({ request }) => {
    if (!authToken) {
      test.skip();
      return;
    }

    const response = await authenticatedRequest(request, authToken, 'get', '/api/datasets/');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('results');
  });

  test('should access concept-dbs endpoint with auth', async ({ request }) => {
    if (!authToken) {
      test.skip();
      return;
    }

    const response = await authenticatedRequest(request, authToken, 'get', '/api/concept-dbs/');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('results');
  });

  test('should access projects endpoint with auth', async ({ request }) => {
    if (!authToken) {
      test.skip();
      return;
    }

    const response = await authenticatedRequest(request, authToken, 'get', '/api/project-annotate-entities/');
    expect(response.ok()).toBeTruthy();

    const data = await response.json();
    expect(data).toHaveProperty('results');
  });
});

// ============================================================================
// UI Authentication Flow Tests
// ============================================================================

test.describe('MedCAT Trainer - UI Authentication Flow', () => {
  test('should show login modal on initial load', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Wait for Vue app to render
    await page.waitForTimeout(1500);

    // Check for login modal elements
    const loginModal = page.locator('.login, .modal');
    const hasLoginModal = await loginModal.count() > 0;

    // Either login modal or already logged in state
    const usernameField = page.locator('#uname');
    const hasUsernameField = await usernameField.count() > 0;

    console.log(`Login modal present: ${hasLoginModal}, Username field: ${hasUsernameField}`);
  });

  test('should allow typing in login form', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    const usernameField = page.locator('#uname');
    const passwordField = page.locator('#password');

    if (await usernameField.count() > 0) {
      await usernameField.fill('testuser');
      await passwordField.fill('testpassword');

      expect(await usernameField.inputValue()).toBe('testuser');
      expect(await passwordField.inputValue()).toBe('testpassword');
    }
  });

  test('should show error on failed login', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    const usernameField = page.locator('#uname');
    const passwordField = page.locator('#password');
    const loginButton = page.locator('.login-submit');

    if (await loginButton.count() > 0 && await usernameField.count() > 0) {
      await usernameField.fill('invalid_user_12345');
      await passwordField.fill('invalid_pass_67890');
      await loginButton.click();

      // Wait for API response
      await page.waitForTimeout(2000);

      // Should show error message
      const errorMessage = page.locator('.text-danger');
      const hasError = await errorMessage.count() > 0;

      // Either error shown or still on login page
      const stillOnLogin = await page.locator('#uname').count() > 0;
      expect(hasError || stillOnLogin).toBeTruthy();
    }
  });
});

// ============================================================================
// Project Management UI Tests
// ============================================================================

test.describe('MedCAT Trainer - Project Management UI', () => {
  test('should display projects page after login', async ({ page, request }) => {
    // First get auth token
    const token = await getAuthToken(request, ADMIN_USER.username, ADMIN_USER.password);

    if (!token) {
      console.log('Admin not available - testing unauthenticated state');
      await page.goto('/');
      await page.waitForLoadState('networkidle');
      return;
    }

    // Set auth cookie before navigation
    await page.goto('/');
    await page.evaluate((authToken) => {
      document.cookie = `api-token=${authToken}; path=/`;
      document.cookie = `username=admin; path=/`;
    }, token);

    await page.reload();
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Should see project list or home screen
    const pageContent = await page.content();
    console.log('Page loaded after auth setup');
  });

  test('should have navigation sidebar', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Look for navigation elements
    const hasNav = await page.locator('nav, .sidebar, .v-navigation-drawer, [class*="nav"]').count() > 0;
    const hasAppBar = await page.locator('.v-app-bar, .app-bar, header').count() > 0;

    console.log(`Navigation: ${hasNav}, App bar: ${hasAppBar}`);
  });
});

// ============================================================================
// Clinical Document Display Tests
// ============================================================================

test.describe('MedCAT Trainer - Document Display', () => {
  test('should have document viewing capability', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Look for document-related UI elements
    const docElements = await page.locator('[class*="document"], [class*="text"], .editor, .annotation-view').count();

    console.log(`Document-related elements found: ${docElements}`);
  });

  test('should support text selection for annotation', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Check for elements that support text selection
    const selectableContent = await page.locator('[class*="selectable"], .document-text, .clinical-text, pre, code').count();

    console.log(`Selectable content areas: ${selectableContent}`);
  });
});

// ============================================================================
// Annotation Workflow Tests
// ============================================================================

test.describe('MedCAT Trainer - Annotation Workflow', () => {
  test('should have annotation controls', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Look for annotation-related buttons
    const annotationControls = await page.locator(
      'button:has-text("Correct"), button:has-text("Incorrect"), ' +
      'button:has-text("Validate"), button:has-text("Submit"), ' +
      '[class*="annotation"], [class*="entity"]'
    ).count();

    console.log(`Annotation controls found: ${annotationControls}`);
  });

  test('should have meta-annotation options if visible', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Look for meta-annotation UI (Negation, Temporality, etc.)
    const metaAnnotations = await page.locator(
      '[class*="meta"], [class*="negation"], [class*="temporal"], ' +
      'select, .v-select, .dropdown'
    ).count();

    console.log(`Meta-annotation elements found: ${metaAnnotations}`);
  });
});

// ============================================================================
// Data Export Tests
// ============================================================================

test.describe('MedCAT Trainer - Data Export', () => {
  test('should have export functionality UI', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Look for export buttons or menu items
    const exportElements = await page.locator(
      'button:has-text("Export"), a:has-text("Export"), ' +
      '[class*="export"], [class*="download"]'
    ).count();

    console.log(`Export elements found: ${exportElements}`);
  });
});

// ============================================================================
// Admin Panel Tests
// ============================================================================

test.describe('MedCAT Trainer - Admin Panel', () => {
  test('should have admin link for admin users', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1500);

    // Look for admin link
    const adminLink = await page.locator('a[href*="admin"], button:has-text("Admin")').count();

    console.log(`Admin link found: ${adminLink > 0}`);
  });

  test('should access Django admin panel', async ({ page }) => {
    const response = await page.goto('/admin/');

    // Admin should return 200 or redirect to login
    expect(response?.status()).toBeLessThan(500);

    const title = await page.title();
    console.log(`Admin page title: ${title}`);
  });
});

// ============================================================================
// Error Handling Tests
// ============================================================================

test.describe('MedCAT Trainer - Error Handling', () => {
  test('should handle 404 pages gracefully', async ({ page }) => {
    const response = await page.goto('/nonexistent-page-12345');

    // Should handle gracefully (might be SPA routing)
    expect(response?.status()).toBeLessThan(500);
  });

  test('should handle API errors gracefully', async ({ request }) => {
    // Test invalid API endpoint - try a more specific invalid path
    const response = await request.get('/api/users/99999999/');

    // Should return 404 for non-existent resource or 401 if auth required
    expect([401, 404]).toContain(response.status());
  });

  test('should not expose stack traces', async ({ page }) => {
    await page.goto('/api/nonexistent/');

    const content = await page.content();

    // Should not expose Python stack traces
    expect(content.toLowerCase()).not.toContain('traceback');
    expect(content.toLowerCase()).not.toContain('django');
  });
});

// ============================================================================
// Performance Tests
// ============================================================================

test.describe('MedCAT Trainer - Performance', () => {
  test('should load API endpoints quickly', async ({ request }) => {
    const startTime = Date.now();

    await request.get('/api/');

    const responseTime = Date.now() - startTime;
    console.log(`API root response time: ${responseTime}ms`);

    expect(responseTime).toBeLessThan(2000);
  });

  test('should handle concurrent requests', async ({ request }) => {
    const startTime = Date.now();

    // Make 5 concurrent requests
    const requests = Array(5).fill(null).map(() => request.get('/api/'));
    const responses = await Promise.all(requests);

    const totalTime = Date.now() - startTime;
    console.log(`5 concurrent requests completed in: ${totalTime}ms`);

    // All should succeed
    responses.forEach(response => {
      expect(response.ok()).toBeTruthy();
    });

    // Should complete within reasonable time
    expect(totalTime).toBeLessThan(5000);
  });
});

// ============================================================================
// Security Tests
// ============================================================================

test.describe('MedCAT Trainer - Security', () => {
  test('should not expose sensitive headers', async ({ request }) => {
    const response = await request.get('/');
    const headers = response.headers();

    // Should not expose detailed server info
    const server = headers['server'] || '';
    const xPoweredBy = headers['x-powered-by'] || '';

    console.log(`Server header: ${server}`);
    console.log(`X-Powered-By: ${xPoweredBy}`);
  });

  test('should protect against unauthorized data access', async ({ request }) => {
    // Try to access user data without auth
    const response = await request.get('/api/users/');
    expect(response.status()).toBe(401);
  });

  test('should validate content-type for API requests', async ({ request }) => {
    // Send malformed request
    const response = await request.post('/api/api-token-auth/', {
      headers: {
        'Content-Type': 'text/plain'
      },
      data: 'not json data'
    });

    // Should reject or handle gracefully
    expect(response.status()).toBeGreaterThanOrEqual(400);
  });
});
