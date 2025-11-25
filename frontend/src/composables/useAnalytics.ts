/**
 * Analytics Composable
 *
 * Provides reusable analytics functionality for search performance monitoring.
 * Manages analytics state (data, loading/error states), date range filtering,
 * and provides methods for fetching analytics data.
 *
 * Features:
 * - Date range filtering
 * - Top queries tracking
 * - Zero-result query detection
 * - Slow query identification
 * - Search volume trends
 * - Error handling
 * - Admin-only access (403 handling)
 *
 * @example
 * ```typescript
 * import { useAnalytics } from '@/composables/useAnalytics'
 *
 * export default {
 *   setup() {
 *     const { analytics, isLoading, error, fetchAnalytics } = useAnalytics()
 *
 *     onMounted(() => {
 *       fetchAnalytics()
 *     })
 *
 *     return { analytics, isLoading, error }
 *   }
 * }
 * ```
 */

import { ref, computed } from 'vue'
import { getAnalytics, type AnalyticsResponse, type AnalyticsParams } from '@/api/search'

/**
 * Analytics state and methods
 *
 * @returns {Object} Analytics composable with state and methods
 *   - analytics: Ref<AnalyticsResponse | null> - Analytics data
 *   - isLoading: Ref<boolean> - Fetch in progress
 *   - error: Ref<string | null> - Error message if any
 *   - startDate: Ref<string | null> - Filter start date (ISO format)
 *   - endDate: Ref<string | null> - Filter end date (ISO format)
 *   - hasData: ComputedRef<boolean> - true if analytics data exists
 *   - fetchAnalytics: Function - Fetch analytics data
 *   - setDateRange: Function - Set date range filter
 *   - clearDateRange: Function - Clear date filters
 */
export function useAnalytics() {
  // ============================================================================
  // STATE
  // ============================================================================

  /**
   * Analytics data
   * @type {Ref<AnalyticsResponse | null>}
   */
  const analytics = ref<AnalyticsResponse | null>(null)

  /**
   * Whether a fetch is currently in progress
   * @type {Ref<boolean>}
   */
  const isLoading = ref(false)

  /**
   * Error message from last fetch, or null if no error
   * @type {Ref<string | null>}
   */
  const error = ref<string | null>(null)

  /**
   * Start date for filtering (ISO format YYYY-MM-DD)
   * @type {Ref<string | null>}
   */
  const startDate = ref<string | null>(null)

  /**
   * End date for filtering (ISO format YYYY-MM-DD)
   * @type {Ref<string | null>}
   */
  const endDate = ref<string | null>(null)

  // ============================================================================
  // COMPUTED PROPERTIES
  // ============================================================================

  /**
   * Whether analytics data exists
   * @type {ComputedRef<boolean>}
   */
  const hasData = computed(() => analytics.value !== null)

  /**
   * Whether date range is set
   * @type {ComputedRef<boolean>}
   */
  const hasDateRange = computed(() => startDate.value !== null && endDate.value !== null)

  /**
   * Number of top queries
   * @type {ComputedRef<number>}
   */
  const topQueriesCount = computed(() => analytics.value?.top_queries.length || 0)

  /**
   * Number of zero-result queries
   * @type {ComputedRef<number>}
   */
  const zeroResultCount = computed(() => analytics.value?.zero_result_queries.length || 0)

  /**
   * Number of slow queries
   * @type {ComputedRef<number>}
   */
  const slowQueriesCount = computed(() => analytics.value?.slow_queries.length || 0)

  /**
   * Number of trend data points
   * @type {ComputedRef<number>}
   */
  const trendsCount = computed(() => analytics.value?.trends.length || 0)

  // ============================================================================
  // METHODS
  // ============================================================================

  /**
   * Fetch analytics data with optional parameters
   *
   * Side effects:
   * - Sets isLoading = true while fetching
   * - Updates analytics data
   * - Clears error on success, sets error on failure
   *
   * @param {AnalyticsParams} [params] - Optional query parameters
   * @returns {Promise<void>} Resolves when fetch completes
   *
   * @example
   * // Fetch all analytics
   * await fetchAnalytics()
   *
   * @example
   * // Fetch with date range
   * await fetchAnalytics({
   *   start_date: '2025-11-01',
   *   end_date: '2025-11-22'
   * })
   */
  const fetchAnalytics = async (params?: AnalyticsParams): Promise<void> => {
    isLoading.value = true
    error.value = null

    try {
      // Use provided params or build from state
      const queryParams: AnalyticsParams = params || {}
      if (!params) {
        if (startDate.value) queryParams.start_date = startDate.value
        if (endDate.value) queryParams.end_date = endDate.value
      }

      // Call API
      const response = await getAnalytics(queryParams)

      // Update state
      analytics.value = response
    } catch (err: any) {
      // Error handling
      if (err.response?.status === 403) {
        error.value = 'Access denied. Admin role required to view analytics.'
      } else if (err.response?.status === 400) {
        error.value = err.response?.data?.detail || 'Invalid date format. Use YYYY-MM-DD.'
      } else {
        error.value = err.response?.data?.detail || err.message || 'Failed to fetch analytics. Please try again.'
      }
      analytics.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Set date range filter and refresh analytics
   *
   * @param {string} start - Start date (ISO format YYYY-MM-DD)
   * @param {string} end - End date (ISO format YYYY-MM-DD)
   * @returns {Promise<void>}
   */
  const setDateRange = async (start: string, end: string): Promise<void> => {
    startDate.value = start
    endDate.value = end
    await fetchAnalytics()
  }

  /**
   * Clear date range filter and refresh analytics
   *
   * @returns {Promise<void>}
   */
  const clearDateRange = async (): Promise<void> => {
    startDate.value = null
    endDate.value = null
    await fetchAnalytics()
  }

  /**
   * Refresh analytics with current filters
   *
   * @returns {Promise<void>}
   */
  const refresh = async (): Promise<void> => {
    await fetchAnalytics()
  }

  // ============================================================================
  // RETURN PUBLIC API
  // ============================================================================

  return {
    // State
    analytics,
    isLoading,
    error,
    startDate,
    endDate,

    // Computed
    hasData,
    hasDateRange,
    topQueriesCount,
    zeroResultCount,
    slowQueriesCount,
    trendsCount,

    // Methods
    fetchAnalytics,
    setDateRange,
    clearDateRange,
    refresh,
  }
}
