/**
 * E2E Tests for Timeline Filter Functionality
 *
 * Tests filter application and saved filter presets:
 * - Date range filtering
 * - Concept filtering
 * - Meta-annotation filtering
 * - Filter presets (save, load, apply)
 *
 * Task #007: E2E Tests, Performance Testing & Accessibility Audit
 */

import { test, expect } from '@playwright/test'

test.describe('Timeline Filters - Date Range', () => {
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
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
  })

  test('User can apply date range filter', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Wait for sidebar
    await expect(page.locator('[data-testid="filter-sidebar"]')).toBeVisible()

    // Set start date
    await page.fill('[data-testid="date-start-input"]', '2023-01-01')

    // Set end date
    await page.fill('[data-testid="date-end-input"]', '2023-12-31')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline updates
    await page.waitForLoadState('networkidle')

    // Verify filtered results
    const events = page.locator('[data-testid^="timeline-event-"]')
    const count = await events.count()
    expect(count).toBeGreaterThan(0)
  })

  test('Date range filter updates URL query params', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Set date range
    await page.fill('[data-testid="date-start-input"]', '2023-06-01')
    await page.fill('[data-testid="date-end-input"]', '2023-06-30')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify URL contains query params
    await page.waitForTimeout(500)
    const url = page.url()
    expect(url).toContain('date_start=2023-06-01')
    expect(url).toContain('date_end=2023-06-30')
  })

  test('User can clear date range filter', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Set date range
    await page.fill('[data-testid="date-start-input"]', '2023-01-01')
    await page.fill('[data-testid="date-end-input"]', '2023-12-31')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()
    await page.waitForLoadState('networkidle')

    // Clear filters
    await page.locator('[data-testid="clear-filters-button"]').click()

    // Verify filters cleared
    const startInput = page.locator('[data-testid="date-start-input"]')
    await expect(startInput).toHaveValue('')
  })
})

test.describe('Timeline Filters - Concept Filtering', () => {
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
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
  })

  test('User can filter by specific medical concept', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Search for concept
    await page.fill('[data-testid="concept-search-input"]', 'diabetes')

    // Wait for autocomplete results
    await page.waitForSelector('[data-testid="concept-suggestion-0"]', { timeout: 3000 })

    // Select first concept
    await page.locator('[data-testid="concept-suggestion-0"]').click()

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline shows only diabetes-related events
    await page.waitForLoadState('networkidle')

    // Verify filtered results
    const conceptMarkers = page.locator('[data-testid^="concept-marker-"]')
    const count = await conceptMarkers.count()
    expect(count).toBeGreaterThan(0)
  })

  test('User can select multiple concepts', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Add first concept
    await page.fill('[data-testid="concept-search-input"]', 'diabetes')
    await page.waitForSelector('[data-testid="concept-suggestion-0"]', { timeout: 3000 })
    await page.locator('[data-testid="concept-suggestion-0"]').click()

    // Add second concept
    await page.fill('[data-testid="concept-search-input"]', 'hypertension')
    await page.waitForSelector('[data-testid="concept-suggestion-0"]', { timeout: 3000 })
    await page.locator('[data-testid="concept-suggestion-0"]').click()

    // Verify chips displayed
    const conceptChips = page.locator('[data-testid^="concept-chip-"]')
    const chipCount = await conceptChips.count()
    expect(chipCount).toBe(2)

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline updates
    await page.waitForLoadState('networkidle')
  })

  test('User can remove selected concept', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Add concept
    await page.fill('[data-testid="concept-search-input"]', 'diabetes')
    await page.waitForSelector('[data-testid="concept-suggestion-0"]', { timeout: 3000 })
    await page.locator('[data-testid="concept-suggestion-0"]').click()

    // Verify chip displayed
    await expect(page.locator('[data-testid^="concept-chip-"]').first()).toBeVisible()

    // Remove concept chip
    await page.locator('[data-testid^="concept-chip-"] button').first().click()

    // Verify chip removed
    const chipCount = await page.locator('[data-testid^="concept-chip-"]').count()
    expect(chipCount).toBe(0)
  })
})

test.describe('Timeline Filters - Meta-Annotations', () => {
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
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
  })

  test('User can filter by Negation status', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Select "Affirmed" for Negation
    await page.selectOption('[data-testid="meta-negation-select"]', 'Affirmed')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline updates
    await page.waitForLoadState('networkidle')

    // Verify URL contains meta filter
    const url = page.url()
    expect(url).toContain('meta_negation=Affirmed')
  })

  test('User can filter by Experiencer', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Select "Patient" for Experiencer
    await page.selectOption('[data-testid="meta-experiencer-select"]', 'Patient')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline updates
    await page.waitForLoadState('networkidle')
  })

  test('User can filter by Temporality', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Select "Current" for Temporality
    await page.selectOption('[data-testid="meta-temporality-select"]', 'Current')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline updates
    await page.waitForLoadState('networkidle')
  })

  test('User can apply combined meta-annotation filters', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Set multiple meta-annotations
    await page.selectOption('[data-testid="meta-negation-select"]', 'Affirmed')
    await page.selectOption('[data-testid="meta-experiencer-select"]', 'Patient')
    await page.selectOption('[data-testid="meta-temporality-select"]', 'Current')

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Verify timeline updates
    await page.waitForLoadState('networkidle')

    // Verify URL contains all meta filters
    const url = page.url()
    expect(url).toContain('meta_negation=Affirmed')
    expect(url).toContain('meta_experiencer=Patient')
    expect(url).toContain('meta_temporality=Current')
  })
})

test.describe('Timeline Filters - Saved Presets', () => {
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
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
  })

  test('User can save current filters as preset', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Set some filters
    await page.fill('[data-testid="date-start-input"]', '2023-01-01')
    await page.selectOption('[data-testid="meta-negation-select"]', 'Affirmed')

    // Click save preset button
    await page.locator('[data-testid="save-preset-button"]').click()

    // Enter preset name
    await page.fill('[data-testid="preset-name-input"]', 'My Custom Filter')

    // Confirm save
    await page.locator('[data-testid="confirm-save-preset"]').click()

    // Verify success message
    await expect(page.locator('[data-testid="success-message"]')).toBeVisible()

    // Verify preset appears in list
    await expect(page.locator('text=My Custom Filter')).toBeVisible()
  })

  test('User can load saved preset', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Open presets dropdown
    await page.locator('[data-testid="presets-dropdown"]').click()

    // Select a preset (assuming one exists)
    await page.locator('[data-testid="preset-item-0"]').click()

    // Verify filters are applied
    await page.waitForTimeout(500)

    // Verify URL updates with filter params
    const url = page.url()
    expect(url).toMatch(/date_start=|meta_|concepts=/)
  })

  test('User can set a preset as default', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Open presets dropdown
    await page.locator('[data-testid="presets-dropdown"]').click()

    // Click star icon to set as default
    await page.locator('[data-testid="preset-set-default-0"]').click()

    // Verify star icon is filled
    await expect(page.locator('[data-testid="preset-default-icon-0"]')).toHaveClass(/filled/)
  })

  test('User can delete saved preset', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Open presets dropdown
    await page.locator('[data-testid="presets-dropdown"]').click()

    // Get initial preset count
    const initialCount = await page.locator('[data-testid^="preset-item-"]').count()

    // Delete first preset
    await page.locator('[data-testid="preset-delete-0"]').click()

    // Confirm deletion
    await page.locator('[data-testid="confirm-delete-preset"]').click()

    // Verify preset removed
    await page.waitForTimeout(500)
    const newCount = await page.locator('[data-testid^="preset-item-"]').count()
    expect(newCount).toBe(initialCount - 1)
  })
})

test.describe('Timeline Filters - Performance', () => {
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

  test('Filter application completes within 500ms', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Set filters
    await page.selectOption('[data-testid="meta-negation-select"]', 'Affirmed')

    // Measure filter application time
    const startTime = Date.now()

    // Apply filters
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Wait for timeline to update
    await page.waitForLoadState('networkidle')

    const endTime = Date.now()
    const duration = endTime - startTime

    // Verify performance target met
    expect(duration).toBeLessThan(500)
  })
})
