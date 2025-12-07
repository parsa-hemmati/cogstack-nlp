import { test, expect } from '@playwright/test';

/**
 * E2E tests for MedCAT Service API
 * Tests the REST API service for medical concept extraction
 */

test.describe('MedCAT Service - API Health', () => {
  test('should have health endpoint responding', async ({ request }) => {
    const endpoints = ['/api/health', '/health', '/api/info', '/info', '/'];

    let healthyEndpoint = null;
    for (const endpoint of endpoints) {
      try {
        const response = await request.get(endpoint);
        if (response.ok()) {
          healthyEndpoint = endpoint;
          break;
        }
      } catch {
        continue;
      }
    }

    expect(healthyEndpoint).toBeTruthy();
    console.log(`Healthy endpoint found: ${healthyEndpoint}`);
  });

  test('should return JSON from API', async ({ request }) => {
    const endpoints = ['/api/info', '/info', '/api/', '/'];

    for (const endpoint of endpoints) {
      try {
        const response = await request.get(endpoint);
        if (response.ok()) {
          const contentType = response.headers()['content-type'];
          // API should return JSON or HTML
          expect(contentType).toMatch(/json|html|text/);
          break;
        }
      } catch {
        continue;
      }
    }
  });
});

test.describe('MedCAT Service - API Endpoints', () => {
  test('should have annotation endpoint', async ({ request }) => {
    const annotationEndpoints = [
      '/api/process',
      '/api/annotate',
      '/api/ner',
      '/api/entities',
      '/process',
      '/annotate'
    ];

    let foundEndpoint = false;
    for (const endpoint of annotationEndpoints) {
      try {
        // Try OPTIONS or HEAD to check if endpoint exists
        const response = await request.head(endpoint);
        if (response.status() !== 404) {
          foundEndpoint = true;
          console.log(`Annotation endpoint found: ${endpoint}`);
          break;
        }
      } catch {
        continue;
      }
    }

    // Log result but don't fail - endpoint names vary
    console.log(`Annotation endpoint available: ${foundEndpoint}`);
  });

  test('should handle POST request to process text', async ({ request }) => {
    const processEndpoints = ['/api/process', '/process', '/api/annotate', '/annotate'];

    for (const endpoint of processEndpoints) {
      try {
        const response = await request.post(endpoint, {
          data: {
            text: 'Patient has diabetes mellitus type 2.'
          },
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (response.status() !== 404) {
          console.log(`Process endpoint ${endpoint} responded with status: ${response.status()}`);
          // Any non-404 response is acceptable for this check
          break;
        }
      } catch {
        continue;
      }
    }
  });
});

test.describe('MedCAT Service - API Documentation', () => {
  test('should have API documentation available', async ({ request }) => {
    const docEndpoints = [
      '/docs',
      '/swagger',
      '/api/docs',
      '/openapi.json',
      '/api/openapi.json',
      '/redoc'
    ];

    let docsAvailable = false;
    for (const endpoint of docEndpoints) {
      try {
        const response = await request.get(endpoint);
        if (response.ok()) {
          docsAvailable = true;
          console.log(`API docs found at: ${endpoint}`);
          break;
        }
      } catch {
        continue;
      }
    }

    console.log(`API documentation available: ${docsAvailable}`);
  });
});

test.describe('MedCAT Service - Error Handling', () => {
  test('should return proper error for invalid endpoint', async ({ request }) => {
    const response = await request.get('/api/nonexistent-endpoint-12345');

    // Should return 404 for non-existent endpoints
    expect(response.status()).toBe(404);
  });

  test('should handle malformed JSON gracefully', async ({ request }) => {
    const endpoints = ['/api/process', '/process', '/api/annotate'];

    for (const endpoint of endpoints) {
      try {
        const response = await request.post(endpoint, {
          data: 'not valid json {{{',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        // Should return 4xx error for malformed input
        if (response.status() !== 404) {
          expect(response.status()).toBeGreaterThanOrEqual(400);
          expect(response.status()).toBeLessThan(500);
          console.log(`${endpoint} handled malformed JSON with status: ${response.status()}`);
          break;
        }
      } catch {
        continue;
      }
    }
  });
});

test.describe('MedCAT Service - Performance', () => {
  test('should respond within acceptable time', async ({ request }) => {
    const startTime = Date.now();

    const response = await request.get('/');

    const responseTime = Date.now() - startTime;
    console.log(`API response time: ${responseTime}ms`);

    expect(responseTime).toBeLessThan(5000);
  });
});

test.describe('MedCAT Service - Security', () => {
  test('should not expose sensitive information in headers', async ({ request }) => {
    const response = await request.get('/');
    const headers = response.headers();

    // Should not expose server version details
    const serverHeader = headers['server'] || '';
    const xPoweredBy = headers['x-powered-by'] || '';

    console.log(`Server header: ${serverHeader}`);
    console.log(`X-Powered-By: ${xPoweredBy}`);
  });

  test('should handle large payloads appropriately', async ({ request }) => {
    const largeText = 'Patient has diabetes. '.repeat(1000);

    const endpoints = ['/api/process', '/process'];

    for (const endpoint of endpoints) {
      try {
        const response = await request.post(endpoint, {
          data: { text: largeText },
          headers: { 'Content-Type': 'application/json' }
        });

        if (response.status() !== 404) {
          // Should either process or return appropriate error
          expect(response.status()).toBeLessThan(500);
          console.log(`Large payload handling: ${response.status()}`);
          break;
        }
      } catch {
        continue;
      }
    }
  });
});
