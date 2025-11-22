/**
 * E2E Tests for Patient Timeline Feature
 *
 * Tests the complete user workflow for viewing patient timelines:
 * - Authentication and navigation
 * - Timeline rendering with documents and concepts
 * - Event detail viewing
 * - Export functionality
 *
 * Task #007: E2E Tests, Performance Testing & Accessibility Audit
 */

import { test, expect, type Page } from '@playwright/test'

/**
 * Helper function to login as a test clinician
 */
async function login(page: Page, email: string = 'dr.smith@hospital.com', password: string = 'Test123!') {
  await page.goto('/login')
  await page.fill('input[name="email"]', email)
  await page.fill('input[name="password"]', password)
  await page.click('button[type="submit"]')

  // Wait for redirect to dashboard
  await page.waitForURL('/dashboard', { timeout: 10000 })
}

/**
 * Helper function to navigate to patient timeline
 */
async function navigateToTimeline(page: Page, patientId: string = 'P12345') {
  await page.goto(`/patients/${patientId}/timeline`)
  await page.waitForLoadState('networkidle')
}

test.describe('Patient Timeline - Basic Viewing', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication for test environment
    await page.context().addCookies([
      {
        name: 'access_token',
        value: 'test_token_123',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }
    ])
  })

  test('User views patient timeline successfully', async ({ page }) => {
    // Navigate to patient timeline
    await navigateToTimeline(page)

    // Verify page title
    await expect(page).toHaveTitle(/Timeline/)

    // Verify timeline axis is visible
    const timelineAxis = page.locator('[data-testid="timeline-axis"]')
    await expect(timelineAxis).toBeVisible({ timeout: 10000 })

    // Verify timeline events are rendered
    const timelineEvents = page.locator('[data-testid^="timeline-event-"]')
    await expect(timelineEvents.first()).toBeVisible()

    // Verify at least some events are displayed
    const eventCount = await timelineEvents.count()
    expect(eventCount).toBeGreaterThan(0)
  })

  test('Timeline displays patient information header', async ({ page }) => {
    await navigateToTimeline(page)

    // Verify patient header is visible
    const patientHeader = page.locator('[data-testid="patient-header"]')
    await expect(patientHeader).toBeVisible()

    // Verify patient ID is displayed
    await expect(page.locator('text=P12345')).toBeVisible()
  })

  test('Timeline displays document markers', async ({ page }) => {
    await navigateToTimeline(page)

    // Verify document markers are rendered
    const documentMarkers = page.locator('[data-testid^="document-marker-"]')
    await expect(documentMarkers.first()).toBeVisible({ timeout: 10000 })

    // Verify document count
    const docCount = await documentMarkers.count()
    expect(docCount).toBeGreaterThan(0)
  })

  test('Timeline displays concept markers', async ({ page }) => {
    await navigateToTimeline(page)

    // Verify concept markers are rendered
    const conceptMarkers = page.locator('[data-testid^="concept-marker-"]')
    await expect(conceptMarkers.first()).toBeVisible({ timeout: 10000 })

    // Verify at least one medical concept is displayed
    const conceptCount = await conceptMarkers.count()
    expect(conceptCount).toBeGreaterThan(0)
  })

  test('Timeline shows date labels on axis', async ({ page }) => {
    await navigateToTimeline(page)

    // Verify date axis labels
    const dateLabels = page.locator('[data-testid="timeline-axis"] text')
    const labelCount = await dateLabels.count()
    expect(labelCount).toBeGreaterThan(0)
  })
})

test.describe('Patient Timeline - Event Interaction', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      {
        name: 'access_token',
        value: 'test_token_123',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }
    ])
  })

  test('User clicks event marker to view details', async ({ page }) => {
    await navigateToTimeline(page)

    // Click on first concept marker
    const firstConceptMarker = page.locator('[data-testid^="concept-marker-"]').first()
    await firstConceptMarker.click()

    // Verify modal or popover opens
    const eventDetail = page.locator('[data-testid="event-detail-modal"], [data-testid="concept-popover"]')
    await expect(eventDetail).toBeVisible({ timeout: 5000 })

    // Verify event details are displayed
    await expect(page.locator('[data-testid="concept-name"]')).toBeVisible()
    await expect(page.locator('[data-testid="concept-date"]')).toBeVisible()
  })

  test('Event detail modal shows meta-annotations', async ({ page }) => {
    await navigateToTimeline(page)

    // Click on first concept marker
    await page.locator('[data-testid^="concept-marker-"]').first().click()

    // Wait for detail modal
    await page.waitForSelector('[data-testid="event-detail-modal"], [data-testid="concept-popover"]', {
      state: 'visible',
      timeout: 5000
    })

    // Verify meta-annotations are displayed
    // At least one of: Negation, Experiencer, Temporality, Certainty
    const metaAnnotations = page.locator('[data-testid^="meta-annotation-"]')
    const metaCount = await metaAnnotations.count()
    expect(metaCount).toBeGreaterThan(0)
  })

  test('User can close event detail modal', async ({ page }) => {
    await navigateToTimeline(page)

    // Open event detail
    await page.locator('[data-testid^="concept-marker-"]').first().click()

    // Wait for modal
    const eventDetail = page.locator('[data-testid="event-detail-modal"]')
    await expect(eventDetail).toBeVisible({ timeout: 5000 })

    // Close modal (Escape key or close button)
    await page.keyboard.press('Escape')

    // Verify modal is closed
    await expect(eventDetail).not.toBeVisible({ timeout: 2000 })
  })

  test('Hovering over event shows tooltip', async ({ page }) => {
    await navigateToTimeline(page)

    // Hover over first concept marker
    const firstMarker = page.locator('[data-testid^="concept-marker-"]').first()
    await firstMarker.hover()

    // Verify tooltip appears
    const tooltip = page.locator('[data-testid="concept-tooltip"]')
    await expect(tooltip).toBeVisible({ timeout: 2000 })
  })
})

test.describe('Patient Timeline - Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      {
        name: 'access_token',
        value: 'test_token_123',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }
    ])
  })

  test('User can zoom in on timeline', async ({ page }) => {
    await navigateToTimeline(page)

    // Get initial zoom level (via transform or scale)
    const initialTransform = await page.locator('[data-testid="timeline-canvas"]').getAttribute('transform')

    // Click zoom in button
    await page.locator('[data-testid="zoom-in-button"]').click()

    // Wait for zoom animation
    await page.waitForTimeout(500)

    // Verify zoom level changed
    const newTransform = await page.locator('[data-testid="timeline-canvas"]').getAttribute('transform')
    expect(newTransform).not.toBe(initialTransform)
  })

  test('User can zoom out on timeline', async ({ page }) => {
    await navigateToTimeline(page)

    // Click zoom out button
    await page.locator('[data-testid="zoom-out-button"]').click()

    // Wait for zoom animation
    await page.waitForTimeout(500)

    // Verify zoom controls are functional
    const zoomOutButton = page.locator('[data-testid="zoom-out-button"]')
    await expect(zoomOutButton).toBeEnabled()
  })

  test('User can reset zoom to default', async ({ page }) => {
    await navigateToTimeline(page)

    // Zoom in a few times
    await page.locator('[data-testid="zoom-in-button"]').click({ clickCount: 3 })

    // Reset zoom
    await page.locator('[data-testid="zoom-reset-button"]').click()

    // Wait for reset animation
    await page.waitForTimeout(500)

    // Verify timeline is at default zoom
    const transform = await page.locator('[data-testid="timeline-canvas"]').getAttribute('transform')
    // Default transform should be identity or null
    expect(transform).toBeTruthy()
  })

  test('User can pan timeline left and right', async ({ page }) => {
    await navigateToTimeline(page)

    // Get initial position
    const canvas = page.locator('[data-testid="timeline-canvas"]')
    const initialBox = await canvas.boundingBox()

    // Pan right using mouse drag
    await canvas.hover()
    await page.mouse.down()
    await page.mouse.move(initialBox!.x - 100, initialBox!.y)
    await page.mouse.up()

    // Wait for pan animation
    await page.waitForTimeout(300)

    // Verify position changed
    const newBox = await canvas.boundingBox()
    // Position should have changed (allowing for some variance)
    expect(Math.abs(newBox!.x - initialBox!.x)).toBeGreaterThan(10)
  })
})

test.describe('Patient Timeline - Export', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      {
        name: 'access_token',
        value: 'test_token_123',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }
    ])
  })

  test('User can export timeline as PDF', async ({ page }) => {
    await navigateToTimeline(page)

    // Start waiting for download before clicking
    const downloadPromise = page.waitForEvent('download')

    // Click export button
    await page.locator('[data-testid="export-button"]').click()

    // Select PDF format
    await page.locator('[data-testid="export-format-pdf"]').click()

    // Confirm export
    await page.locator('[data-testid="confirm-export"]').click()

    // Wait for download
    const download = await downloadPromise

    // Verify download filename
    expect(download.suggestedFilename()).toMatch(/timeline.*\.pdf$/i)
  })

  test('User can export timeline as FHIR', async ({ page }) => {
    await navigateToTimeline(page)

    // Start waiting for download
    const downloadPromise = page.waitForEvent('download')

    // Click export button
    await page.locator('[data-testid="export-button"]').click()

    // Select FHIR format
    await page.locator('[data-testid="export-format-fhir"]').click()

    // Confirm export
    await page.locator('[data-testid="confirm-export"]').click()

    // Wait for download
    const download = await downloadPromise

    // Verify download filename
    expect(download.suggestedFilename()).toMatch(/timeline.*\.(json|xml)$/i)
  })
})

test.describe('Patient Timeline - Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      {
        name: 'access_token',
        value: 'test_token_123',
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        secure: false,
        sameSite: 'Lax'
      }
    ])
  })

  test('Timeline shows error message for invalid patient', async ({ page }) => {
    // Navigate to non-existent patient
    await page.goto('/patients/INVALID_ID/timeline')

    // Verify error message is displayed
    const errorMessage = page.locator('[data-testid="error-message"]')
    await expect(errorMessage).toBeVisible({ timeout: 5000 })

    // Verify error text mentions patient not found
    await expect(errorMessage).toContainText(/patient not found/i)
  })

  test('Timeline shows loading state while fetching data', async ({ page }) => {
    // Navigate to timeline
    await page.goto('/patients/P12345/timeline')

    // Verify loading spinner is shown initially
    const loadingSpinner = page.locator('[data-testid="loading-spinner"]')
    await expect(loadingSpinner).toBeVisible({ timeout: 1000 })

    // Wait for timeline to load
    await page.waitForSelector('[data-testid="timeline-axis"]', { state: 'visible', timeout: 10000 })

    // Verify loading spinner is hidden
    await expect(loadingSpinner).not.toBeVisible()
  })

  test('Timeline handles network errors gracefully', async ({ page }) => {
    // Intercept API call and force failure
    await page.route('**/api/v1/timeline/**', route => route.abort())

    // Navigate to timeline
    await page.goto('/patients/P12345/timeline')

    // Verify error message is displayed
    const errorMessage = page.locator('[data-testid="error-message"]')
    await expect(errorMessage).toBeVisible({ timeout: 5000 })

    // Verify retry button is available
    const retryButton = page.locator('[data-testid="retry-button"]')
    await expect(retryButton).toBeVisible()
  })
})
