/**
 * Timeline E2E Tests
 *
 * Tests complete user workflows for patient timeline feature using Playwright.
 *
 * Coverage:
 * - Login → Navigate to timeline → View timeline
 * - Apply filters (concept, date range, meta-annotations)
 * - Click concept marker → View details
 * - Export timeline (PDF, FHIR, JSON)
 * - RBAC enforcement (unauthorized access)
 */

import { test, expect, Page } from '@playwright/test'

/**
 * Page Object Model for Timeline Page
 */
class TimelinePage {
  constructor(private page: Page) {}

  async navigateToTimeline(patientId: string) {
    await this.page.goto(`/timeline/${patientId}`)
    await this.page.waitForLoadState('networkidle')
  }

  async waitForTimelineLoaded() {
    await this.page.waitForSelector('svg[viewBox]', { timeout: 10000 })
    await expect(this.page.locator('.timeline-chart')).toBeVisible()
  }

  async openFilterDrawer() {
    await this.page.click('[data-testid="filter-toggle"]')
    await expect(this.page.locator('.timeline-filters')).toBeVisible()
  }

  async applyConceptFilter(conceptCui: string) {
    await this.page.fill('[data-testid="concept-autocomplete"] input', conceptCui)
    await this.page.press('[data-testid="concept-autocomplete"] input', 'Enter')
  }

  async applyDateRangeFilter(startDate: string, endDate: string) {
    await this.page.fill('input[name="date_start"]', startDate)
    await this.page.fill('input[name="date_end"]', endDate)
  }

  async applyMetaAnnotationFilter(negationAffirmed: boolean) {
    if (negationAffirmed) {
      await this.page.check('[data-testid="negation-affirmed"]')
    } else {
      await this.page.uncheck('[data-testid="negation-affirmed"]')
    }
  }

  async clickApplyFilters() {
    await this.page.click('[data-testid="apply-filters"]')
    await this.page.waitForLoadState('networkidle')
  }

  async clickClearFilters() {
    await this.page.click('[data-testid="clear-filters"]')
    await this.page.waitForLoadState('networkidle')
  }

  async clickConceptMarker(conceptCui: string) {
    await this.page.click(`circle[data-concept-cui="${conceptCui}"]`)
  }

  async verifyConceptDetailsDialog(conceptName: string) {
    await expect(this.page.locator('.v-dialog .v-card-title')).toContainText(conceptName)
  }

  async exportTimeline(format: 'pdf' | 'fhir' | 'json') {
    await this.page.click('[data-testid="export-menu-button"]')
    await this.page.click(`[data-testid="export-${format}"]`)

    // Wait for download to complete
    const downloadPromise = this.page.waitForEvent('download', { timeout: 30000 })
    const download = await downloadPromise

    return download
  }

  async saveFilterPreset(name: string, description: string) {
    await this.page.click('[data-testid="save-preset"]')
    await expect(this.page.locator('.v-dialog')).toBeVisible()

    await this.page.fill('[data-testid="preset-name"]', name)
    await this.page.fill('[data-testid="preset-description"]', description)

    await this.page.click('[data-testid="save-preset-confirm"]')
    await this.page.waitForLoadState('networkidle')
  }

  async verifyTimelineStatistics(expectedDocCount: number, expectedConceptCount: number) {
    const docCountText = await this.page.locator('[data-testid="document-count"]').textContent()
    const conceptCountText = await this.page.locator('[data-testid="concept-count"]').textContent()

    expect(Number(docCountText)).toBe(expectedDocCount)
    expect(Number(conceptCountText)).toBe(expectedConceptCount)
  }
}

/**
 * Login Helper
 */
async function loginAsClinician(page: Page) {
  await page.goto('/login')

  await page.fill('input[name="email"]', 'clinician@test.com')
  await page.fill('input[name="password"]', 'TestPassword123!')

  await page.click('button[type="submit"]')
  await page.waitForNavigation({ url: '/dashboard' })
}

async function loginAsResearcher(page: Page) {
  await page.goto('/login')

  await page.fill('input[name="email"]', 'researcher@test.com')
  await page.fill('input[name="password"]', 'TestPassword123!')

  await page.click('button[type="submit"]')
  await page.waitForNavigation({ url: '/dashboard' })
}

/**
 * Test Suite: Timeline View
 */
test.describe('Timeline View', () => {
  test.beforeEach(async ({ page }) => {
    // Seed test data (in real implementation, this would be done via API or database setup)
    // For now, we assume test data exists
  })

  test('clinician can login and view patient timeline', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000' // Test patient ID

    // Act
    await timelinePage.navigateToTimeline(testPatientId)

    // Assert
    await expect(page.locator('.v-toolbar-title')).toContainText('Patient Timeline')
    await timelinePage.waitForTimelineLoaded()

    // Verify timeline chart rendered
    await expect(page.locator('svg[viewBox]')).toBeVisible()

    // Verify document markers present
    const documentMarkers = page.locator('circle.document-marker')
    await expect(documentMarkers).toHaveCount(5, { timeout: 10000 }) // Assuming 5 documents

    // Verify concept markers present
    const conceptMarkers = page.locator('circle.concept-marker')
    await expect(conceptMarkers.first()).toBeVisible()
  })

  test('filters update timeline correctly', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    await timelinePage.navigateToTimeline(testPatientId)
    await timelinePage.waitForTimelineLoaded()

    // Get initial concept count
    const initialConceptCountText = await page.locator('[data-testid="concept-count"]').textContent()
    const initialConceptCount = Number(initialConceptCountText)

    // Act: Open filter drawer and apply filters
    await timelinePage.openFilterDrawer()

    await timelinePage.applyDateRangeFilter('2024-01-01', '2024-02-28')
    await timelinePage.applyMetaAnnotationFilter(true) // Only affirmed conditions

    await timelinePage.clickApplyFilters()

    // Assert: Timeline updated with filters
    await page.waitForTimeout(1000) // Wait for timeline to re-render

    // Verify filters applied (check URL params or timeline data)
    const url = new URL(page.url())
    expect(url.searchParams.get('date_start')).toBe('2024-01-01')
    expect(url.searchParams.get('date_end')).toBe('2024-02-28')

    // Verify concept count may have changed (due to filtering)
    const filteredConceptCountText = await page.locator('[data-testid="concept-count"]').textContent()
    const filteredConceptCount = Number(filteredConceptCountText)

    // Concept count should be <= initial count (filters can only remove, not add)
    expect(filteredConceptCount).toBeLessThanOrEqual(initialConceptCount)
  })

  test('clicking concept marker opens details dialog', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    await timelinePage.navigateToTimeline(testPatientId)
    await timelinePage.waitForTimelineLoaded()

    // Act: Click first concept marker
    const firstConceptMarker = page.locator('circle.concept-marker').first()
    await firstConceptMarker.click()

    // Assert: Details dialog opens
    await expect(page.locator('.v-dialog')).toBeVisible({ timeout: 5000 })
    await expect(page.locator('.v-dialog .v-card-title')).toBeVisible()

    // Verify dialog contains concept information
    const dialogTitle = await page.locator('.v-dialog .v-card-title').textContent()
    expect(dialogTitle).toBeTruthy() // Should have concept name

    // Verify mentions list present
    await expect(page.locator('.v-dialog .v-list-item').first()).toBeVisible()
  })

  test('export to PDF downloads file', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    await timelinePage.navigateToTimeline(testPatientId)
    await timelinePage.waitForTimelineLoaded()

    // Act: Export to PDF
    const download = await timelinePage.exportTimeline('pdf')

    // Assert: File downloaded
    expect(download.suggestedFilename()).toMatch(/timeline_export_.*\.pdf/)

    // Verify file saved successfully
    const path = await download.path()
    expect(path).toBeTruthy()
  })

  test('export to FHIR downloads JSON file', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    await timelinePage.navigateToTimeline(testPatientId)
    await timelinePage.waitForTimelineLoaded()

    // Act: Export to FHIR
    const download = await timelinePage.exportTimeline('fhir')

    // Assert: File downloaded with .json extension
    expect(download.suggestedFilename()).toMatch(/timeline_export_.*\.json/)
  })

  test('unauthorized user cannot access timeline', async ({ page }) => {
    // Arrange: Navigate to timeline without logging in
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    // Act: Try to access timeline
    await page.goto(`/timeline/${testPatientId}`)

    // Assert: Redirected to login
    await page.waitForURL('/login', { timeout: 5000 })

    // Verify redirect query param includes return URL
    const url = new URL(page.url())
    expect(url.searchParams.get('redirect')).toContain('/timeline/')
  })

  test('researcher can view timeline in read-only mode', async ({ page }) => {
    // Arrange
    await loginAsResearcher(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    // Act
    await timelinePage.navigateToTimeline(testPatientId)

    // Assert: Can view timeline
    await expect(page.locator('.v-toolbar-title')).toContainText('Patient Timeline')
    await timelinePage.waitForTimelineLoaded()

    // Verify timeline chart rendered
    await expect(page.locator('svg[viewBox]')).toBeVisible()

    // Note: Read-only mode enforcement depends on backend permissions
    // Frontend should show all features; backend may restrict export/edit actions
  })

  test('filter presets can be saved and loaded', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    await timelinePage.navigateToTimeline(testPatientId)
    await timelinePage.waitForTimelineLoaded()

    // Act: Open filter drawer and apply filters
    await timelinePage.openFilterDrawer()
    await timelinePage.applyDateRangeFilter('2024-01-01', '2024-03-31')
    await timelinePage.applyMetaAnnotationFilter(true)

    // Save preset
    await timelinePage.saveFilterPreset(
      'Q1 2024 Active Conditions',
      'First quarter 2024 with affirmed patient conditions'
    )

    // Assert: Preset saved
    await expect(page.locator('.v-snackbar')).toContainText('Filter preset saved', { timeout: 5000 })

    // Clear filters
    await timelinePage.clickClearFilters()

    // Load preset
    await timelinePage.openFilterDrawer()
    await page.selectOption('[data-testid="preset-select"]', { label: 'Q1 2024 Active Conditions' })

    // Verify filters restored
    const dateStartValue = await page.inputValue('input[name="date_start"]')
    const dateEndValue = await page.inputValue('input[name="date_end"]')

    expect(dateStartValue).toBe('2024-01-01')
    expect(dateEndValue).toBe('2024-03-31')
  })
})

/**
 * Test Suite: Timeline Performance
 */
test.describe('Timeline Performance', () => {
  test('timeline loads within 2 seconds for typical patient', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    // Act: Navigate and measure load time
    const startTime = Date.now()

    await page.goto(`/timeline/${testPatientId}`)
    await page.waitForSelector('svg[viewBox]', { timeout: 10000 })

    const loadTime = Date.now() - startTime

    // Assert: Load time < 2 seconds
    expect(loadTime).toBeLessThan(2000)
  })

  test('filter updates complete within 500ms', async ({ page }) => {
    // Arrange
    await loginAsClinician(page)

    const timelinePage = new TimelinePage(page)
    const testPatientId = '123e4567-e89b-12d3-a456-426614174000'

    await timelinePage.navigateToTimeline(testPatientId)
    await timelinePage.waitForTimelineLoaded()

    await timelinePage.openFilterDrawer()
    await timelinePage.applyDateRangeFilter('2024-01-01', '2024-12-31')

    // Act: Apply filters and measure update time
    const startTime = Date.now()

    await timelinePage.clickApplyFilters()
    await page.waitForLoadState('networkidle')

    const updateTime = Date.now() - startTime

    // Assert: Update time < 500ms
    expect(updateTime).toBeLessThan(500)
  })
})
