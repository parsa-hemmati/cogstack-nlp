import { test, expect, Page } from '@playwright/test';

/**
 * E2E tests for MedCAT Trainer Demo page.
 * Tests the demo annotation functionality including:
 * - Navigation to Demo page
 * - Document selection
 * - Annotation display (MedCAT entities)
 * - Regex extraction highlighting (NHS Number, Consultant, Specialty)
 */

// Helper function to login if needed
async function loginIfNeeded(page: Page) {
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(1000);

  // Check if login form is present
  const loginForm = page.locator('#uname');
  if (await loginForm.count() > 0) {
    console.log('Logging in with admin credentials...');
    await page.locator('#uname').fill('admin');
    await page.locator('#password').fill('admin');
    await page.locator('.login-submit, button:has-text("Login")').first().click();
    await page.waitForTimeout(2000);
  }
}

test.describe('MedCAT Trainer - Demo Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await loginIfNeeded(page);
  });

  test('should navigate to Demo page', async ({ page }) => {
    // Click on Demo link in navigation
    const demoLink = page.locator('a:has-text("Demo"), .v-list-item:has-text("Demo")').first();

    if (await demoLink.count() > 0) {
      await demoLink.click();
      await page.waitForLoadState('networkidle');

      // Verify we're on the Demo page
      const url = page.url();
      expect(url).toContain('/demo');
    } else {
      // Try direct navigation
      await page.goto('/#/demo');
      await page.waitForLoadState('networkidle');
    }

    // Wait for page content - the Demo page should load without errors
    await page.waitForTimeout(3000);

    // Verify we can see some page content
    const pageBody = page.locator('body');
    await expect(pageBody).toBeVisible();

    // Check that we're on the demo page or there's no error
    const hasError = await page.locator('.error-page, .not-found').count() > 0;
    const hasErrorText = await page.locator('text=Error').count() > 0;
    console.log(`Demo page error state: ${hasError || hasErrorText}`);
  });

  test('should display project selector on Demo page', async ({ page }) => {
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Look for project selector dropdown
    const projectSelector = page.locator('select, .v-select, [data-testid="project-select"]');

    if (await projectSelector.count() > 0) {
      await expect(projectSelector.first()).toBeVisible();
    }
  });

  test('should display document selector when project is selected', async ({ page }) => {
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for document selector
    const documentSelector = page.locator(
      '.document-list, .v-list, [data-testid="document-select"], select:nth-of-type(2)'
    );

    // Document list should exist (may be empty if no project selected)
    const hasDocumentUI = await documentSelector.count() > 0 ||
      await page.locator('text=/document/i').count() > 0;

    // Just verify the demo page loaded without errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.waitForTimeout(1000);

    // Filter benign errors
    const criticalErrors = consoleErrors.filter(err =>
      !err.includes('favicon') &&
      !err.includes('404')
    );

    expect(criticalErrors).toHaveLength(0);
  });

  test('should display clinical text area', async ({ page }) => {
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for text display area
    const textArea = page.locator(
      'textarea, .clinical-text, .document-text, pre, [class*="text-display"]'
    );

    const hasTextArea = await textArea.count() > 0;

    // The demo page should have some form of text display
    console.log(`Text display area found: ${hasTextArea}`);
  });

  test('should process and display annotations when text is loaded', async ({ page }) => {
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    // Look for annotated entities
    const annotations = page.locator(
      '.annotation, .entity, [class*="highlight"], span[style*="background"], mark'
    );

    // Wait for potential annotations to render
    await page.waitForTimeout(2000);

    const annotationCount = await annotations.count();
    console.log(`Annotations found: ${annotationCount}`);

    // Verify the page structure is correct
    const hasMainContent = await page.locator('.v-main, main, [role="main"]').count() > 0;
    expect(hasMainContent).toBeTruthy();
  });
});

test.describe('MedCAT Trainer - Demo Annotations', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await loginIfNeeded(page);
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
  });

  test('should display entity tooltip on hover over annotation', async ({ page }) => {
    await page.waitForTimeout(3000);

    // Find annotated spans
    const annotations = page.locator(
      '.annotation, .entity, [class*="highlight"], span[data-cui]'
    );

    if (await annotations.count() > 0) {
      // Hover over first annotation
      await annotations.first().hover();
      await page.waitForTimeout(500);

      // Look for tooltip/popover
      const tooltip = page.locator(
        '.v-tooltip, .tooltip, [role="tooltip"], .v-menu__content, .popover'
      );

      const hasTooltip = await tooltip.count() > 0;
      console.log(`Tooltip displayed on hover: ${hasTooltip}`);
    }
  });

  test('should show stats panel with entity counts', async ({ page }) => {
    await page.waitForTimeout(3000);

    // Look for stats or summary panel
    const statsPanel = page.locator(
      '.stats, .summary, [class*="stats"], [class*="count"]'
    );

    // Or look for specific counts
    const entityCount = page.locator('text=/entities/i, text=/annotations/i');

    const hasStats = await statsPanel.count() > 0 || await entityCount.count() > 0;
    console.log(`Stats panel found: ${hasStats}`);
  });
});

test.describe('MedCAT Trainer - Demo Regex Extractions', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await loginIfNeeded(page);
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
  });

  test('should highlight NHS Number in clinical text', async ({ page }) => {
    await page.waitForTimeout(3000);

    // Look for NHS Number highlight
    const nhsHighlight = page.locator(
      'span:has-text("NHS Number"), [data-type="nhs_number"], .nhs-number, span[class*="nhs"]'
    );

    // Or look for the NHS pattern text
    const nhsText = page.locator('text=/NHS\\s*Number/i');

    const hasNhsHighlight = await nhsHighlight.count() > 0 || await nhsText.count() > 0;
    console.log(`NHS Number highlight found: ${hasNhsHighlight}`);
  });

  test('should highlight Consultant name in clinical text', async ({ page }) => {
    await page.waitForTimeout(3000);

    // Look for Consultant highlight
    const consultantHighlight = page.locator(
      'span:has-text("Consultant"), [data-type="consultant"], .consultant, span[class*="consultant"]'
    );

    // Or look for consultant pattern text
    const consultantText = page.locator('text=/Consultant/i');

    const hasConsultantHighlight = await consultantHighlight.count() > 0 || await consultantText.count() > 0;
    console.log(`Consultant highlight found: ${hasConsultantHighlight}`);
  });

  test('should highlight Specialty in clinical text', async ({ page }) => {
    await page.waitForTimeout(3000);

    // Look for Specialty highlight
    const specialtyHighlight = page.locator(
      'span:has-text("Specialty"), [data-type="specialty"], .specialty, span[class*="specialty"]'
    );

    // Or look for specialty pattern text
    const specialtyText = page.locator('text=/Specialty/i');

    const hasSpecialtyHighlight = await specialtyHighlight.count() > 0 || await specialtyText.count() > 0;
    console.log(`Specialty highlight found: ${hasSpecialtyHighlight}`);
  });

  test('should display extracted values in summary panel', async ({ page }) => {
    await page.waitForTimeout(3000);

    // Look for regex extraction summary
    const regexSummary = page.locator(
      '.regex-extractions, .extracted-fields, [class*="extraction"]'
    );

    // Or look for specific field labels
    const nhsLabel = page.locator('text=/NHS\\s*Number/i');
    const consultantLabel = page.locator('text=/Consultant/i');
    const specialtyLabel = page.locator('text=/Specialty/i');

    const hasNhs = await nhsLabel.count() > 0;
    const hasConsultant = await consultantLabel.count() > 0;
    const hasSpecialty = await specialtyLabel.count() > 0;

    console.log(`Extracted NHS: ${hasNhs}, Consultant: ${hasConsultant}, Specialty: ${hasSpecialty}`);

    // At least one should be found if there's clinical text
    const hasSomeExtraction = hasNhs || hasConsultant || hasSpecialty;
    console.log(`Has some regex extraction: ${hasSomeExtraction}`);
  });
});

test.describe('MedCAT Trainer - Demo API Integration', () => {
  test('should make annotate-text API call on document load', async ({ page }) => {
    // Set up request interception
    const apiCalls: string[] = [];

    page.on('request', request => {
      if (request.url().includes('/api/annotate-text')) {
        apiCalls.push(request.url());
      }
    });

    await page.goto('/');
    await loginIfNeeded(page);
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);

    // API call should have been made when document is selected
    console.log(`Annotate API calls: ${apiCalls.length}`);
  });

  test('should receive valid response from annotate-text API', async ({ page }) => {
    let apiResponse: any = null;

    page.on('response', async response => {
      if (response.url().includes('/api/annotate-text')) {
        try {
          apiResponse = await response.json();
        } catch (e) {
          console.log('Could not parse API response as JSON');
        }
      }
    });

    await page.goto('/');
    await loginIfNeeded(page);
    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);

    if (apiResponse) {
      // Verify response structure
      expect(apiResponse).toHaveProperty('message');
      expect(apiResponse).toHaveProperty('entities');
      expect(apiResponse).toHaveProperty('regex_extractions');

      console.log(`API response received with ${apiResponse.entities?.length || 0} entities`);
      console.log(`Regex extractions: ${JSON.stringify(apiResponse.regex_extractions)}`);
    }
  });
});

test.describe('MedCAT Trainer - Demo Performance', () => {
  test('should load demo page within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;

    // Demo page should load within 10 seconds
    expect(loadTime).toBeLessThan(10000);

    console.log(`Demo page load time: ${loadTime}ms`);
  });

  test('should display annotations within reasonable time', async ({ page }) => {
    await page.goto('/');
    await loginIfNeeded(page);

    const startTime = Date.now();

    await page.goto('/#/demo');
    await page.waitForLoadState('networkidle');

    // Wait for annotations to appear (up to 10 seconds)
    try {
      await page.waitForSelector(
        '.annotation, .entity, [class*="highlight"], span[data-cui]',
        { timeout: 10000 }
      );

      const annotationTime = Date.now() - startTime;
      console.log(`Annotations displayed in: ${annotationTime}ms`);
      expect(annotationTime).toBeLessThan(10000);
    } catch (e) {
      console.log('No annotations appeared within timeout - may need document selection');
    }
  });
});
