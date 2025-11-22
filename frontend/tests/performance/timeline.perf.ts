/**
 * Frontend Performance Tests for Timeline using Lighthouse
 *
 * Tests Core Web Vitals and performance metrics:
 * - First Contentful Paint (FCP) <1.5s
 * - Time to Interactive (TTI) <3.5s
 * - Total Blocking Time (TBT) <300ms
 * - Largest Contentful Paint (LCP) <2.5s
 * - Cumulative Layout Shift (CLS) <0.1
 *
 * Run with:
 *   node frontend/tests/performance/timeline.perf.ts
 */

import lighthouse from 'lighthouse'
import * as chromeLauncher from 'chrome-launcher'
import { writeFileSync } from 'fs'
import { resolve } from 'path'

interface PerformanceResult {
  url: string
  score: number
  fcp: number
  tti: number
  tbt: number
  lcp: number
  cls: number
  speedIndex: number
  passed: boolean
  violations: string[]
}

/**
 * Run Lighthouse audit on a URL
 */
async function runLighthouseAudit(url: string): Promise<PerformanceResult> {
  const chrome = await chromeLauncher.launch({
    chromeFlags: ['--headless', '--disable-gpu', '--no-sandbox']
  })

  const options = {
    logLevel: 'info' as const,
    output: 'json' as const,
    onlyCategories: ['performance'],
    port: chrome.port,
    disableStorageReset: false
  }

  const runnerResult = await lighthouse(url, options)

  if (!runnerResult || !runnerResult.lhr) {
    throw new Error('Lighthouse audit failed')
  }

  const lhr = runnerResult.lhr
  const performanceCategory = lhr.categories.performance
  const audits = lhr.audits

  // Extract Core Web Vitals
  const fcp = audits['first-contentful-paint'].numericValue || 0
  const tti = audits['interactive'].numericValue || 0
  const tbt = audits['total-blocking-time'].numericValue || 0
  const lcp = audits['largest-contentful-paint'].numericValue || 0
  const cls = audits['cumulative-layout-shift'].numericValue || 0
  const speedIndex = audits['speed-index'].numericValue || 0

  const violations: string[] = []

  // Check against targets
  if (fcp > 1500) {
    violations.push(`FCP ${Math.round(fcp)}ms exceeds 1500ms target`)
  }

  if (tti > 3500) {
    violations.push(`TTI ${Math.round(tti)}ms exceeds 3500ms target`)
  }

  if (tbt > 300) {
    violations.push(`TBT ${Math.round(tbt)}ms exceeds 300ms target`)
  }

  if (lcp > 2500) {
    violations.push(`LCP ${Math.round(lcp)}ms exceeds 2500ms target`)
  }

  if (cls > 0.1) {
    violations.push(`CLS ${cls.toFixed(3)} exceeds 0.1 target`)
  }

  if (performanceCategory.score < 0.9) {
    violations.push(
      `Performance score ${Math.round(performanceCategory.score * 100)} is below 90 target`
    )
  }

  await chrome.kill()

  return {
    url,
    score: performanceCategory.score * 100,
    fcp,
    tti,
    tbt,
    lcp,
    cls,
    speedIndex,
    passed: violations.length === 0,
    violations
  }
}

/**
 * Main performance test suite
 */
async function runPerformanceTests() {
  console.log('🚀 Starting Timeline Performance Tests...\n')

  const baseUrl = process.env.VITE_APP_URL || 'http://localhost:5173'

  const tests = [
    {
      name: 'Timeline View - Light Load (50 events)',
      url: `${baseUrl}/patients/P12345/timeline`
    },
    {
      name: 'Timeline View - Medium Load (500 events)',
      url: `${baseUrl}/patients/P_MEDIUM/timeline`
    },
    {
      name: 'Timeline View - Heavy Load (5000 events)',
      url: `${baseUrl}/patients/P_LARGE/timeline`
    }
  ]

  const results: PerformanceResult[] = []

  for (const test of tests) {
    console.log(`\n📊 Testing: ${test.name}`)
    console.log(`   URL: ${test.url}`)

    try {
      const result = await runLighthouseAudit(test.url)
      results.push(result)

      console.log(`   ✅ Performance Score: ${Math.round(result.score)}`)
      console.log(`   📈 Metrics:`)
      console.log(`      FCP: ${Math.round(result.fcp)}ms`)
      console.log(`      LCP: ${Math.round(result.lcp)}ms`)
      console.log(`      TTI: ${Math.round(result.tti)}ms`)
      console.log(`      TBT: ${Math.round(result.tbt)}ms`)
      console.log(`      CLS: ${result.cls.toFixed(3)}`)
      console.log(`      Speed Index: ${Math.round(result.speedIndex)}ms`)

      if (result.violations.length > 0) {
        console.log(`   ⚠️  Violations:`)
        result.violations.forEach((v) => console.log(`      - ${v}`))
      } else {
        console.log(`   ✅ All targets met!`)
      }
    } catch (error) {
      console.error(`   ❌ Test failed: ${error}`)
    }
  }

  // Generate report
  const reportPath = resolve(__dirname, '../../test-results/performance-report.json')
  writeFileSync(reportPath, JSON.stringify(results, null, 2))

  console.log(`\n📝 Performance report saved to: ${reportPath}`)

  // Summary
  console.log(`\n\n📊 Performance Test Summary`)
  console.log(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`)

  const passedTests = results.filter((r) => r.passed).length
  const totalTests = results.length

  console.log(`   Tests Passed: ${passedTests}/${totalTests}`)
  console.log(
    `   Average Performance Score: ${Math.round(
      results.reduce((sum, r) => sum + r.score, 0) / results.length
    )}`
  )
  console.log(
    `   Average FCP: ${Math.round(results.reduce((sum, r) => sum + r.fcp, 0) / results.length)}ms`
  )
  console.log(
    `   Average LCP: ${Math.round(results.reduce((sum, r) => sum + r.lcp, 0) / results.length)}ms`
  )
  console.log(
    `   Average TTI: ${Math.round(results.reduce((sum, r) => sum + r.tti, 0) / results.length)}ms`
  )

  // Exit with error if any test failed
  if (passedTests < totalTests) {
    console.log(`\n❌ Performance tests FAILED (${totalTests - passedTests} failures)`)
    process.exit(1)
  } else {
    console.log(`\n✅ All performance tests PASSED`)
    process.exit(0)
  }
}

// Run tests
runPerformanceTests().catch((error) => {
  console.error('❌ Performance test suite failed:', error)
  process.exit(1)
})
