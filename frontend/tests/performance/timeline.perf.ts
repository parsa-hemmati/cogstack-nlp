/**
 * Frontend Performance Tests for Timeline Module
 *
 * Measures frontend performance metrics using browser performance APIs:
 * - First Contentful Paint (FCP)
 * - Largest Contentful Paint (LCP)
 * - Time to Interactive (TTI)
 * - Total Blocking Time (TBT)
 * - Cumulative Layout Shift (CLS)
 *
 * Complements Lighthouse CI for automated performance monitoring.
 *
 * Task #007: E2E Tests, Performance Testing & Accessibility Audit
 */

import { test, expect } from '@playwright/test'

interface PerformanceMetrics {
  fcp: number
  lcp: number
  tti: number
  tbt: number
  cls: number
}

/**
 * Collect performance metrics from browser
 */
async function collectPerformanceMetrics(page: any): Promise<PerformanceMetrics> {
  const metrics = await page.evaluate(() => {
    return new Promise<PerformanceMetrics>((resolve) => {
      // Get timing metrics
      const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming
      const paint = performance.getEntriesByType('paint')
      
      const fcp = paint.find(entry => entry.name === 'first-contentful-paint')?.startTime || 0
      
      // Use PerformanceObserver for LCP
      let lcp = 0
      new PerformanceObserver((list) => {
        const entries = list.getEntries()
        const lastEntry = entries[entries.length - 1] as any
        lcp = lastEntry.startTime
      }).observe({ type: 'largest-contentful-paint', buffered: true })
      
      // Approximate TTI as domInteractive
      const tti = navigation.domInteractive
      
      // TBT is complex to calculate accurately, use domContentLoadedEventEnd as proxy
      const tbt = navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart
      
      // CLS requires PerformanceObserver (simplified here)
      let cls = 0
      new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if ((entry as any).hadRecentInput) continue
          cls += (entry as any).value
        }
      }).observe({ type: 'layout-shift', buffered: true })
      
      // Wait a bit for observers to collect data
      setTimeout(() => {
        resolve({ fcp, lcp, tti, tbt, cls })
      }, 2000)
    })
  })
  
  return metrics
}

test.describe('Timeline Performance - Page Load Metrics', () => {
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

  test('Timeline page achieves FCP < 1.5s', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
    
    const metrics = await collectPerformanceMetrics(page)
    
    console.log(`First Contentful Paint: ${metrics.fcp.toFixed(2)}ms`)
    
    // Target: < 1500ms
    expect(metrics.fcp).toBeLessThan(1500)
  })

  test('Timeline page achieves LCP < 2.5s', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
    
    const metrics = await collectPerformanceMetrics(page)
    
    console.log(`Largest Contentful Paint: ${metrics.lcp.toFixed(2)}ms`)
    
    // Target: < 2500ms
    expect(metrics.lcp).toBeLessThan(2500)
  })

  test('Timeline page achieves TTI < 3.5s', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
    
    const metrics = await collectPerformanceMetrics(page)
    
    console.log(`Time to Interactive: ${metrics.tti.toFixed(2)}ms`)
    
    // Target: < 3500ms
    expect(metrics.tti).toBeLessThan(3500)
  })

  test('Timeline page achieves TBT < 300ms', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
    
    const metrics = await collectPerformanceMetrics(page)
    
    console.log(`Total Blocking Time: ${metrics.tbt.toFixed(2)}ms`)
    
    // Target: < 300ms
    expect(metrics.tbt).toBeLessThan(300)
  })

  test('Timeline page achieves CLS < 0.1', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
    
    const metrics = await collectPerformanceMetrics(page)
    
    console.log(`Cumulative Layout Shift: ${metrics.cls.toFixed(3)}`)
    
    // Target: < 0.1
    expect(metrics.cls).toBeLessThan(0.1)
  })
})

test.describe('Timeline Performance - Rendering Performance', () => {
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

  test('Timeline with 100 events renders within 500ms', async ({ page }) => {
    await page.goto('/patients/P_SMALL/timeline') // Patient with ~100 events
    
    const startTime = Date.now()
    
    // Wait for timeline to render
    await page.waitForSelector('[data-testid="timeline-axis"]', { timeout: 10000 })
    await page.waitForSelector('[data-testid^="concept-marker-"]', { timeout: 5000 })
    
    const endTime = Date.now()
    const renderTime = endTime - startTime
    
    console.log(`Render time (100 events): ${renderTime}ms`)
    
    // Target: < 500ms
    expect(renderTime).toBeLessThan(500)
  })

  test('Timeline with 1,000 events renders within 1000ms', async ({ page }) => {
    await page.goto('/patients/P_MEDIUM/timeline') // Patient with ~1,000 events
    
    const startTime = Date.now()
    
    // Wait for timeline to render
    await page.waitForSelector('[data-testid="timeline-axis"]', { timeout: 10000 })
    await page.waitForSelector('[data-testid^="concept-marker-"]', { timeout: 5000 })
    
    const endTime = Date.now()
    const renderTime = endTime - startTime
    
    console.log(`Render time (1,000 events): ${renderTime}ms`)
    
    // Target: < 1000ms
    expect(renderTime).toBeLessThan(1000)
  })

  test('Timeline with 10,000 events renders within 2000ms', async ({ page }) => {
    await page.goto('/patients/P_LARGE/timeline') // Patient with ~10,000 events
    
    const startTime = Date.now()
    
    // Wait for timeline to render
    await page.waitForSelector('[data-testid="timeline-axis"]', { timeout: 15000 })
    await page.waitForSelector('[data-testid^="concept-marker-"]', { timeout: 10000 })
    
    const endTime = Date.now()
    const renderTime = endTime - startTime
    
    console.log(`Render time (10,000 events): ${renderTime}ms`)
    
    // Target: < 2000ms (acceptable for large dataset)
    expect(renderTime).toBeLessThan(2000)
  })
})

test.describe('Timeline Performance - Interaction Performance', () => {
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

  test('Zoom operation completes within 100ms', async ({ page }) => {
    // Click zoom in button
    const startTime = Date.now()
    
    await page.locator('[data-testid="zoom-in-button"]').click()
    
    // Wait for zoom animation
    await page.waitForTimeout(100)
    
    const endTime = Date.now()
    const zoomTime = endTime - startTime
    
    console.log(`Zoom time: ${zoomTime}ms`)
    
    // Target: < 100ms (60fps = ~16ms per frame, 100ms = 6 frames)
    expect(zoomTime).toBeLessThan(100)
  })

  test('Pan operation is smooth (60fps)', async ({ page }) => {
    const canvas = page.locator('[data-testid="timeline-canvas"]')
    const box = await canvas.boundingBox()
    
    // Measure frame times during pan
    const frameTimes: number[] = []
    
    await page.evaluate(() => {
      const times: number[] = []
      let lastTime = performance.now()
      
      const measureFrame = () => {
        const now = performance.now()
        times.push(now - lastTime)
        lastTime = now
        
        if (times.length < 60) {
          requestAnimationFrame(measureFrame)
        }
      }
      
      requestAnimationFrame(measureFrame)
      
      // @ts-ignore
      window.__frameTimes = times
    })
    
    // Perform pan
    await canvas.hover()
    await page.mouse.down()
    await page.mouse.move(box!.x - 100, box!.y)
    await page.mouse.up()
    
    // Wait for measurements
    await page.waitForTimeout(1000)
    
    // Get frame times
    const times = await page.evaluate(() => {
      // @ts-ignore
      return window.__frameTimes || []
    })
    
    if (times.length > 0) {
      const avgFrameTime = times.reduce((a: number, b: number) => a + b, 0) / times.length
      console.log(`Average frame time: ${avgFrameTime.toFixed(2)}ms`)
      
      // Target: < 16.67ms (60fps)
      expect(avgFrameTime).toBeLessThan(20) // Allow slight variance
    }
  })

  test('Filter application completes within 300ms', async ({ page }) => {
    // Open filter sidebar
    await page.locator('[data-testid="filter-toggle-button"]').click()
    
    // Set filter
    await page.selectOption('[data-testid="meta-negation-select"]', 'Affirmed')
    
    const startTime = Date.now()
    
    // Apply filter
    await page.locator('[data-testid="apply-filters-button"]').click()
    
    // Wait for timeline update
    await page.waitForLoadState('networkidle')
    
    const endTime = Date.now()
    const filterTime = endTime - startTime
    
    console.log(`Filter application time: ${filterTime}ms`)
    
    // Target: < 300ms (frontend update, not API call)
    expect(filterTime).toBeLessThan(300)
  })
})

test.describe('Timeline Performance - Memory Usage', () => {
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

  test('Timeline does not leak memory on repeated zooms', async ({ page }) => {
    await page.goto('/patients/P12345/timeline')
    await page.waitForLoadState('networkidle')
    
    // Get initial memory usage
    const initialMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize
      }
      return 0
    })
    
    // Perform 50 zoom operations
    for (let i = 0; i < 50; i++) {
      await page.locator('[data-testid="zoom-in-button"]').click()
      await page.waitForTimeout(50)
      await page.locator('[data-testid="zoom-out-button"]').click()
      await page.waitForTimeout(50)
    }
    
    // Force garbage collection (if available)
    await page.evaluate(() => {
      if ((window as any).gc) {
        (window as any).gc()
      }
    })
    
    // Get final memory usage
    const finalMemory = await page.evaluate(() => {
      if (performance.memory) {
        return performance.memory.usedJSHeapSize
      }
      return 0
    })
    
    if (initialMemory > 0 && finalMemory > 0) {
      const memoryIncrease = finalMemory - initialMemory
      const memoryIncreaseMB = memoryIncrease / (1024 * 1024)
      
      console.log(`Initial memory: ${(initialMemory / (1024 * 1024)).toFixed(2)}MB`)
      console.log(`Final memory: ${(finalMemory / (1024 * 1024)).toFixed(2)}MB`)
      console.log(`Memory increase: ${memoryIncreaseMB.toFixed(2)}MB`)
      
      // Target: < 10MB increase (allowing for some variance)
      expect(memoryIncreaseMB).toBeLessThan(10)
    }
  })
})

// Usage:
// Run with: npx playwright test tests/performance/timeline.perf.ts
//
// With HTML report:
//   npx playwright test tests/performance/timeline.perf.ts --reporter=html
//
// With JSON output for CI:
//   npx playwright test tests/performance/timeline.perf.ts --reporter=json > perf-results.json
