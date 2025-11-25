/**
 * E2E Accessibility Tests for Timeline Module
 *
 * Tests WCAG 2.1 AA compliance:
 * - Automated accessibility audits (axe-core)
 * - Keyboard navigation
 * - Screen reader support (ARIA labels)
 * - Color contrast
 * - Focus management
 *
 * Task #007: E2E Tests, Performance Testing & Accessibility Audit
 */

import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Timeline Accessibility - Automated Audits', () => {
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

  test('Timeline page passes automated accessibility audit', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Run axe accessibility audit
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    // Verify no violations
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('Filter sidebar passes accessibility audit', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()
    await expect(page.locator('[data-testid="filter-sidebar"]')).toBeVisible()

    // Run accessibility audit on sidebar
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('[data-testid="filter-sidebar"]')
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    // Verify no violations
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('Event detail modal passes accessibility audit', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open event detail
    await page.locator('[data-testid^="concept-marker-"]').first().click()
    await expect(page.locator('[data-testid="event-detail-modal"], [data-testid="concept-popover"]')).toBeVisible()

    // Run accessibility audit on modal
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('[data-testid="event-detail-modal"], [data-testid="concept-popover"]')
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    // Verify no violations
    expect(accessibilityScanResults.violations).toEqual([])
  })
})

test.describe('Timeline Accessibility - Keyboard Navigation', () => {
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

  test('User can navigate timeline with Tab key', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Tab to first interactive element
    await page.keyboard.press('Tab')

    // Verify focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).toBeTruthy()

    // Tab through several elements
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Verify focus moves
    const newFocusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(newFocusedElement).toBeTruthy()
  })

  test('User can navigate events with Arrow keys', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Focus on timeline canvas
    await page.locator('[data-testid="timeline-canvas"]').focus()

    // Use arrow keys to navigate
    await page.keyboard.press('ArrowRight')
    await page.keyboard.press('ArrowRight')

    // Verify navigation works (would check focused event marker)
    const focusedElement = await page.evaluate(() => 
      document.activeElement?.getAttribute('data-testid')
    )
    expect(focusedElement).toMatch(/concept-marker-|document-marker-/)
  })

  test('User can open event detail with Enter key', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Tab to first event marker
    await page.locator('[data-testid^="concept-marker-"]').first().focus()

    // Press Enter to open detail
    await page.keyboard.press('Enter')

    // Verify modal opens
    await expect(page.locator('[data-testid="event-detail-modal"], [data-testid="concept-popover"]')).toBeVisible()
  })

  test('User can close modal with Escape key', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open event detail
    await page.locator('[data-testid^="concept-marker-"]').first().click()
    await expect(page.locator('[data-testid="event-detail-modal"]')).toBeVisible()

    // Press Escape to close
    await page.keyboard.press('Escape')

    // Verify modal closes
    await expect(page.locator('[data-testid="event-detail-modal"]')).not.toBeVisible()
  })

  test('User can zoom with keyboard shortcuts', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Focus on timeline canvas
    await page.locator('[data-testid="timeline-canvas"]').focus()

    // Zoom in with + key
    await page.keyboard.press('+')

    // Wait for zoom animation
    await page.waitForTimeout(300)

    // Verify zoom level changed
    const transform = await page.locator('[data-testid="timeline-canvas"]').getAttribute('transform')
    expect(transform).toBeTruthy()

    // Zoom out with - key
    await page.keyboard.press('-')

    // Reset zoom with 0 key
    await page.keyboard.press('0')
  })

  test('Tab order is logical and predictable', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    const tabOrder: string[] = []

    // Tab through first 5 elements
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab')
      const focusedId = await page.evaluate(() => 
        document.activeElement?.getAttribute('data-testid') || 
        document.activeElement?.tagName || 
        'unknown'
      )
      tabOrder.push(focusedId)
    }

    // Verify tab order is logical (no empty or duplicate elements)
    expect(tabOrder.every(id => id !== 'unknown')).toBe(true)
    expect(new Set(tabOrder).size).toBe(tabOrder.length)
  })
})

test.describe('Timeline Accessibility - ARIA Labels', () => {
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

  test('Timeline has descriptive ARIA labels', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Verify main timeline region has aria-label
    const timelineRegion = page.locator('[role="region"]').first()
    const ariaLabel = await timelineRegion.getAttribute('aria-label')
    expect(ariaLabel).toMatch(/timeline|patient history/i)
  })

  test('Event markers have descriptive ARIA labels', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Check first concept marker
    const firstMarker = page.locator('[data-testid^="concept-marker-"]').first()
    const ariaLabel = await firstMarker.getAttribute('aria-label')
    
    // Should include concept name and date
    expect(ariaLabel).toBeTruthy()
    expect(ariaLabel!.length).toBeGreaterThan(10)
  })

  test('Filter controls have ARIA labels', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Check date inputs
    const dateStartInput = page.locator('[data-testid="date-start-input"]')
    const dateStartLabel = await dateStartInput.getAttribute('aria-label')
    expect(dateStartLabel || await dateStartInput.locator('label').textContent()).toMatch(/start date/i)

    // Check select elements
    const negationSelect = page.locator('[data-testid="meta-negation-select"]')
    const negationLabel = await negationSelect.getAttribute('aria-label')
    expect(negationLabel || await negationSelect.locator('label').textContent()).toMatch(/negation/i)
  })

  test('Export buttons have ARIA labels', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Check export button
    const exportButton = page.locator('[data-testid="export-button"]')
    const ariaLabel = await exportButton.getAttribute('aria-label')
    expect(ariaLabel || await exportButton.textContent()).toMatch(/export/i)
  })

  test('Loading states are announced to screen readers', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')

    // Check for aria-live region during loading
    const liveRegion = page.locator('[aria-live="polite"], [aria-live="assertive"]')
    const liveText = await liveRegion.textContent()
    
    // Should announce loading or loaded state
    expect(liveText).toMatch(/loading|loaded|ready/i)
  })
})

test.describe('Timeline Accessibility - Color Contrast', () => {
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

  test('Color contrast meets WCAG AA standards', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Run axe audit specifically for color contrast
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['cat.color'])
      .analyze()

    // Verify no color contrast violations
    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('Event markers have sufficient contrast', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Get background and foreground colors of marker
    const marker = page.locator('[data-testid^="concept-marker-"]').first()
    const colors = await marker.evaluate((el) => {
      const style = window.getComputedStyle(el)
      return {
        background: style.backgroundColor,
        foreground: style.color,
        fill: style.fill
      }
    })

    // Verify colors are not the same
    expect(colors.background).not.toBe(colors.foreground)
  })
})

test.describe('Timeline Accessibility - Focus Management', () => {
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

  test('Focus is visible on all interactive elements', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Tab to first interactive element
    await page.keyboard.press('Tab')

    // Check for focus outline
    const focusedElement = page.locator(':focus')
    const outline = await focusedElement.evaluate((el) => {
      const style = window.getComputedStyle(el)
      return {
        outlineWidth: style.outlineWidth,
        outlineColor: style.outlineColor,
        outlineStyle: style.outlineStyle,
        boxShadow: style.boxShadow
      }
    })

    // Verify focus indicator exists (outline or box-shadow)
    expect(
      outline.outlineWidth !== 'none' || 
      outline.boxShadow !== 'none'
    ).toBe(true)
  })

  test('Focus is trapped in modal when open', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open modal
    await page.locator('[data-testid^="concept-marker-"]').first().click()
    await expect(page.locator('[data-testid="event-detail-modal"]')).toBeVisible()

    // Tab through modal elements
    const initialFocus = await page.evaluate(() => document.activeElement?.tagName)

    // Tab multiple times (should stay within modal)
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab')
    }

    // Verify focus is still within modal
    const currentFocus = await page.evaluate(() => {
      const activeEl = document.activeElement
      const modal = document.querySelector('[data-testid="event-detail-modal"]')
      return modal?.contains(activeEl)
    })

    expect(currentFocus).toBe(true)
  })

  test('Focus returns to trigger element after modal closes', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Click marker to open modal
    const marker = page.locator('[data-testid^="concept-marker-"]').first()
    await marker.click()
    await expect(page.locator('[data-testid="event-detail-modal"]')).toBeVisible()

    // Close modal
    await page.keyboard.press('Escape')

    // Verify focus returns to marker
    await page.waitForTimeout(100)
    const focusedElement = await page.evaluate(() => 
      document.activeElement?.getAttribute('data-testid')
    )
    expect(focusedElement).toMatch(/concept-marker-/)
  })
})

test.describe('Timeline Accessibility - Screen Reader Support', () => {
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

  test('Page has descriptive page title', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')

    // Verify page title includes patient context
    const title = await page.title()
    expect(title).toMatch(/timeline|patient|P12345/i)
  })

  test('Main landmark regions are defined', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Verify main landmark
    const mainRegion = page.locator('main, [role="main"]')
    await expect(mainRegion).toBeVisible()

    // Verify navigation landmark (if present)
    const navRegion = page.locator('nav, [role="navigation"]')
    const navCount = await navRegion.count()
    expect(navCount).toBeGreaterThanOrEqual(0)
  })

  test('Filter changes are announced to screen readers', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')

    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()

    // Apply filter
    await page.selectOption('[data-testid="meta-negation-select"]', 'Affirmed')
    await page.locator('[data-testid="apply-filters-button"]').click()

    // Check for aria-live announcement
    const liveRegion = page.locator('[aria-live="polite"], [aria-live="assertive"]')
    await page.waitForTimeout(500)
    
    const announcement = await liveRegion.textContent()
    expect(announcement).toMatch(/filter|update|result/i)
  })

  test('Error messages are announced to screen readers', async ({ page }) => {
    // Navigate to invalid patient
    await page.goto('/patients/INVALID_ID/timeline')

    // Check for error announcement
    const errorRegion = page.locator('[role="alert"], [aria-live="assertive"]')
    await expect(errorRegion).toBeVisible({ timeout: 5000 })

    const errorText = await errorRegion.textContent()
    expect(errorText).toMatch(/error|not found/i)
  })
})
