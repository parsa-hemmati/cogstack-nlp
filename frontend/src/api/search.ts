/**
 * Search API Client
 *
 * Provides methods for searching documents and results with meta-annotation filtering,
 * pagination, and sorting.
 *
 * @example
 * ```typescript
 * const response = await search({
 *   query: 'diabetes',
 *   page: 1,
 *   page_size: 20,
 *   sort: 'relevance'
 * })
 * ```
 */

import apiClient from '@/services/api'

/**
 * Sort order options for search results
 */
export type SortOption = 'relevance' | 'date_desc' | 'date_asc' | 'title_asc' | 'title_desc'

/**
 * Meta-annotation filters for search
 */
export interface SearchFilters {
  negation?: string
  temporality?: string
  experiencer?: string
}

/**
 * Search request payload
 */
export interface SearchRequest {
  query: string
  filters?: SearchFilters
  page: number
  page_size: number
  sort: SortOption
}

/**
 * Individual search result with highlights
 */
export interface SearchResult {
  id: string
  title: string
  content: string
  document_type: string
  author: string
  date: string
  score: number
  highlights?: {
    title?: string[]
    content?: string[]
  }
}

/**
 * Search API response
 */
export interface SearchResponse {
  results: SearchResult[]
  total: number
  page: number
  page_size: number
  query: string
}

/**
 * Perform a search request
 *
 * Sends a POST request to `/api/v1/search` with the search parameters.
 * Handles pagination, filtering by meta-annotations, and result sorting.
 *
 * @param {SearchRequest} request - The search request parameters
 * @returns {Promise<SearchResponse>} The search results with pagination info
 *
 * @throws {Error} If the API request fails
 *
 * @example
 * ```typescript
 * const response = await search({
 *   query: 'diabetes',
 *   filters: { negation: 'Affirmed' },
 *   page: 1,
 *   page_size: 20,
 *   sort: 'relevance'
 * })
 *
 * console.log(response.total) // Total matching results
 * console.log(response.results) // Current page results
 * ```
 */
export async function search(request: SearchRequest): Promise<SearchResponse> {
  const response = await apiClient.post<SearchResponse>('/api/v1/search', request)
  return response.data
}

/**
 * Clear search cache on the server
 *
 * Clears cached search results for better freshness in subsequent searches.
 * Useful when underlying data has changed significantly.
 *
 * @returns {Promise<void>}
 *
 * @throws {Error} If the API request fails
 */
export async function clearSearchCache(): Promise<void> {
  await apiClient.post('/api/v1/search/cache/clear')
}

// ============================================================================
// Analytics API
// ============================================================================

/**
 * Single query analytics entry
 */
export interface QueryAnalytics {
  query: string
  count: number
}

/**
 * Slow query analytics entry
 */
export interface SlowQueryAnalytics {
  query: string
  execution_time_ms: number
  avg_execution_time_ms: number
  count: number
}

/**
 * Trend data point for search volume
 */
export interface TrendDataPoint {
  date: string
  count: number
}

/**
 * Aggregated analytics response
 */
export interface AnalyticsResponse {
  top_queries: QueryAnalytics[]
  zero_result_queries: QueryAnalytics[]
  slow_queries: SlowQueryAnalytics[]
  trends: TrendDataPoint[]
}

/**
 * Analytics query parameters
 */
export interface AnalyticsParams {
  start_date?: string  // ISO format YYYY-MM-DD
  end_date?: string    // ISO format YYYY-MM-DD
  user_id?: string     // UUID
}

/**
 * Get aggregated search analytics (admin only)
 *
 * Retrieves analytics data including:
 * - Top 10 most frequently searched queries
 * - Queries with zero results
 * - Slow queries (>2000ms threshold)
 * - Daily search volume trends
 *
 * @param {AnalyticsParams} params - Optional date range and user filter
 * @returns {Promise<AnalyticsResponse>} Aggregated analytics data
 *
 * @throws {Error} If the API request fails or user is not admin (403)
 *
 * @example
 * ```typescript
 * const analytics = await getAnalytics({
 *   start_date: '2025-11-01',
 *   end_date: '2025-11-22'
 * })
 *
 * console.log(analytics.top_queries) // Top 10 queries
 * console.log(analytics.trends) // Daily search volume
 * ```
 */
export async function getAnalytics(params?: AnalyticsParams): Promise<AnalyticsResponse> {
  const response = await apiClient.get<AnalyticsResponse>('/api/v1/search/analytics', { params })
  return response.data
}
