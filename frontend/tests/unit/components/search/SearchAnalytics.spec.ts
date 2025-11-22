/**
 * SearchAnalytics Component Unit Tests
 *
 * Tests the admin analytics dashboard component for displaying search analytics.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import SearchAnalytics from '@/components/search/SearchAnalytics.vue'
import type { AnalyticsResponse } from '@/api/search'

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
})

// Mock analytics data
const mockAnalyticsData: AnalyticsResponse = {
  top_queries: [
    { query: 'diabetes', count: 42 },
    { query: 'hypertension', count: 35 },
    { query: 'asthma', count: 28 },
  ],
  zero_result_queries: [
    { query: 'rare disease xyz', count: 5 },
    { query: 'unknown condition', count: 3 },
  ],
  slow_queries: [
    {
      query: 'complex boolean query',
      execution_time_ms: 2500,
      avg_execution_time_ms: 2200,
      count: 5,
    },
    {
      query: 'another slow query',
      execution_time_ms: 3000,
      avg_execution_time_ms: 2800,
      count: 3,
    },
  ],
  trends: [
    { date: '2025-11-18', count: 42 },
    { date: '2025-11-19', count: 38 },
    { date: '2025-11-20', count: 45 },
  ],
}

describe('SearchAnalytics', () => {
  let wrapper: VueWrapper

  const createWrapper = (props = {}) => {
    return mount(SearchAnalytics, {
      props,
      global: {
        plugins: [vuetify],
        stubs: {
          // Stub D3 charts to avoid DOM rendering in tests
          'v-chart': true,
        },
      },
    })
  }

  beforeEach(() => {
    // Reset mocks before each test
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('renders analytics dashboard', () => {
      wrapper = createWrapper()

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('[data-testid="analytics-dashboard"]').exists()).toBe(true)
    })

    it('displays loading state', async () => {
      wrapper = createWrapper()

      // Set loading state
      await wrapper.vm.loadAnalytics()

      expect(wrapper.find('[data-testid="loading-spinner"]').exists()).toBe(true)
    })

    it('displays error message when fetch fails', async () => {
      wrapper = createWrapper()

      // Simulate error
      wrapper.vm.error = 'Access denied. Admin role required.'

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="error-alert"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('Access denied')
    })

    it('displays empty state when no data', async () => {
      wrapper = createWrapper()

      // Ensure no data
      wrapper.vm.analytics = null
      wrapper.vm.isLoading = false

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    })
  })

  describe('Top Queries Display', () => {
    it('displays top queries chart', async () => {
      wrapper = createWrapper()

      // Set analytics data
      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="top-queries-chart"]').exists()).toBe(true)
    })

    it('shows top query count', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('diabetes')
      expect(wrapper.text()).toContain('42')
    })

    it('displays top 10 queries only', async () => {
      wrapper = createWrapper()

      // Create data with more than 10 queries
      const largeDataset: AnalyticsResponse = {
        ...mockAnalyticsData,
        top_queries: Array.from({ length: 15 }, (_, i) => ({
          query: `query${i}`,
          count: 100 - i,
        })),
      }

      wrapper.vm.analytics = largeDataset

      await wrapper.vm.$nextTick()

      // Should only display 10 queries
      const queryElements = wrapper.findAll('[data-testid^="top-query-"]')
      expect(queryElements.length).toBeLessThanOrEqual(10)
    })
  })

  describe('Search Trends Chart', () => {
    it('displays search trends line chart', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="trends-chart"]').exists()).toBe(true)
    })

    it('shows trend data points', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      // Check for dates in trend
      expect(wrapper.text()).toContain('2025-11-18')
    })

    it('displays only when date range is set', async () => {
      wrapper = createWrapper()

      // Set analytics with empty trends
      wrapper.vm.analytics = {
        ...mockAnalyticsData,
        trends: [],
      }

      await wrapper.vm.$nextTick()

      // Trends chart should show empty state or message
      const trendsChart = wrapper.find('[data-testid="trends-chart"]')
      expect(trendsChart.exists() || wrapper.text().toContain('No trends data')).toBe(true)
    })
  })

  describe('Zero Result Queries Table', () => {
    it('displays zero result queries table', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="zero-result-table"]').exists()).toBe(true)
    })

    it('shows query and count columns', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('rare disease xyz')
      expect(wrapper.text()).toContain('5')
    })

    it('displays message when no zero-result queries', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = {
        ...mockAnalyticsData,
        zero_result_queries: [],
      }

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('No zero-result queries')
    })
  })

  describe('Slow Queries Table', () => {
    it('displays slow queries table', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="slow-queries-table"]').exists()).toBe(true)
    })

    it('shows execution time columns', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('2500') // Max execution time
      expect(wrapper.text()).toContain('2200') // Avg execution time
    })

    it('displays message when no slow queries', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = {
        ...mockAnalyticsData,
        slow_queries: [],
      }

      await wrapper.vm.$nextTick()

      expect(wrapper.text()).toContain('No slow queries')
    })
  })

  describe('Date Range Picker', () => {
    it('displays date range picker', () => {
      wrapper = createWrapper()

      expect(wrapper.find('[data-testid="date-range-picker"]').exists()).toBe(true)
    })

    it('fetches analytics when date range changes', async () => {
      wrapper = createWrapper()

      const fetchSpy = vi.spyOn(wrapper.vm, 'fetchAnalytics')

      // Change date range
      await wrapper.vm.setDateRange('2025-11-01', '2025-11-22')

      expect(fetchSpy).toHaveBeenCalled()
    })

    it('validates date range (start <= end)', async () => {
      wrapper = createWrapper()

      // Set invalid range (start > end)
      wrapper.vm.startDate = '2025-11-22'
      wrapper.vm.endDate = '2025-11-01'

      await wrapper.vm.$nextTick()

      // Should show validation error
      expect(wrapper.text()).toContain('Start date must be before end date')
    })

    it('clears date range when clear button clicked', async () => {
      wrapper = createWrapper()

      // Set date range
      wrapper.vm.startDate = '2025-11-01'
      wrapper.vm.endDate = '2025-11-22'

      await wrapper.vm.$nextTick()

      // Click clear button
      const clearButton = wrapper.find('[data-testid="clear-date-range"]')
      await clearButton.trigger('click')

      expect(wrapper.vm.startDate).toBe(null)
      expect(wrapper.vm.endDate).toBe(null)
    })
  })

  describe('Export Functionality', () => {
    it('displays export to CSV button', () => {
      wrapper = createWrapper()

      expect(wrapper.find('[data-testid="export-csv-button"]').exists()).toBe(true)
    })

    it('exports analytics data to CSV when clicked', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      const exportSpy = vi.spyOn(wrapper.vm, 'exportToCSV')

      const exportButton = wrapper.find('[data-testid="export-csv-button"]')
      await exportButton.trigger('click')

      expect(exportSpy).toHaveBeenCalled()
    })

    it('includes all analytics data in CSV export', async () => {
      wrapper = createWrapper()

      wrapper.vm.analytics = mockAnalyticsData

      const csvData = wrapper.vm.exportToCSV()

      expect(csvData).toContain('Top Queries')
      expect(csvData).toContain('diabetes')
      expect(csvData).toContain('Zero Result Queries')
      expect(csvData).toContain('Slow Queries')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA labels on tables', () => {
      wrapper = createWrapper()

      const topQueriesTable = wrapper.find('[data-testid="top-queries-chart"]')
      expect(topQueriesTable.attributes('aria-label')).toBeTruthy()
    })

    it('has keyboard navigation support', async () => {
      wrapper = createWrapper()

      const dateRangePicker = wrapper.find('[data-testid="date-range-picker"]')
      expect(dateRangePicker.attributes('tabindex')).toBe('0')
    })

    it('displays loading state with aria-live', () => {
      wrapper = createWrapper()

      wrapper.vm.isLoading = true

      const loadingSpinner = wrapper.find('[data-testid="loading-spinner"]')
      expect(loadingSpinner.attributes('aria-live')).toBe('polite')
    })
  })

  describe('Refresh Functionality', () => {
    it('displays refresh button', () => {
      wrapper = createWrapper()

      expect(wrapper.find('[data-testid="refresh-button"]').exists()).toBe(true)
    })

    it('refreshes analytics when refresh button clicked', async () => {
      wrapper = createWrapper()

      const refreshSpy = vi.spyOn(wrapper.vm, 'refresh')

      const refreshButton = wrapper.find('[data-testid="refresh-button"]')
      await refreshButton.trigger('click')

      expect(refreshSpy).toHaveBeenCalled()
    })
  })
})
