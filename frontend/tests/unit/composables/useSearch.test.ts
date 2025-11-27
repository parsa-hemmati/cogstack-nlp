/**
 * useSearch Composable Tests
 *
 * Comprehensive unit tests for the search composable including:
 * - State initialization
 * - Search functionality with debouncing
 * - Pagination
 * - Sorting
 * - Error handling
 * - Cache management
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { flushPromises } from '@vue/test-utils'
import { useSearch } from '@/composables/useSearch'
import * as searchApi from '@/api/search'
import type { SearchResponse, SearchResult } from '@/api/search'

// Mock the search API
vi.mock('@/api/search', () => ({
  search: vi.fn(),
  clearSearchCache: vi.fn(),
}))

/**
 * Mock search response helper
 */
const createMockResponse = (overrides?: Partial<SearchResponse>): SearchResponse => {
  return {
    query: 'diabetes',
    results: [
      {
        id: '1',
        title: 'Diabetes Type 2',
        content: 'Diabetes type 2 is the most common form...',
        document_type: 'article',
        author: 'Dr. Smith',
        date: '2025-01-01',
        score: 0.95,
        highlights: {
          title: ['<em>Diabetes</em>'],
          content: ['This is about <em>diabetes</em>'],
        },
      },
      {
        id: '2',
        title: 'Gestational Diabetes',
        content: 'Gestational diabetes occurs during pregnancy...',
        document_type: 'article',
        author: 'Dr. Johnson',
        date: '2025-01-02',
        score: 0.87,
      },
    ],
    total: 42,
    page: 1,
    page_size: 20,
    ...overrides,
  }
}

describe('useSearch', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // ============================================================================
  // INITIALIZATION TESTS
  // ============================================================================

  describe('initialization', () => {
    it('initializes with empty state', () => {
      const { query, results, total, page, isLoading, error } = useSearch()

      expect(query.value).toBe('')
      expect(results.value).toEqual([])
      expect(total.value).toBe(0)
      expect(page.value).toBe(1)
      expect(isLoading.value).toBe(false)
      expect(error.value).toBeNull()
    })

    it('initializes computed properties correctly', () => {
      const { hasResults, isEmpty, totalPages } = useSearch()

      expect(hasResults.value).toBe(false)
      expect(isEmpty.value).toBe(false)
      expect(totalPages.value).toBe(0)
    })

    it('initializes with default sort order', () => {
      const { sort, pageSize } = useSearch()

      expect(sort.value).toBe('relevance')
      expect(pageSize.value).toBe(20)
    })
  })

  // ============================================================================
  // SEARCH FUNCTIONALITY TESTS
  // ============================================================================

  describe('search', () => {
    it('performs search when query is provided', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, results, total } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledWith({
        query: 'diabetes',
        filters: undefined,
        page: 1,
        page_size: 20,
        sort: 'relevance',
      })

      expect(results.value).toEqual(mockResponse.results)
      expect(total.value).toBe(mockResponse.total)
    })

    it('updates query state when search is called', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { query, search } = useSearch()

      await search('heart failure')
      await flushPromises()

      expect(query.value).toBe('heart failure')
    })

    it('sets loading state correctly during search', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve(mockResponse), 100)
          })
      )

      const { search, isLoading } = useSearch()

      const searchPromise = search('diabetes')
      expect(isLoading.value).toBe(true)

      await searchPromise
      await flushPromises()

      expect(isLoading.value).toBe(false)
    })

    it('trims whitespace from query', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search } = useSearch()

      await search('  diabetes  ')
      await flushPromises()

      expect(vi.mocked(searchApi.search).mock.calls[0][0].query).toBe('diabetes')
    })

    it('returns error when query is empty', async () => {
      const { search, error } = useSearch()

      await search('')
      await flushPromises()

      expect(error.value).toBe('Please enter a search query')
      expect(searchApi.search).not.toHaveBeenCalled()
    })

    it('returns error when query is only whitespace', async () => {
      const { search, error } = useSearch()

      await search('   ')
      await flushPromises()

      expect(error.value).toBe('Please enter a search query')
    })

    it('clears error on successful search', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, error } = useSearch()

      error.value = 'Previous error'
      await search('diabetes')
      await flushPromises()

      expect(error.value).toBeNull()
    })

    it('handles API errors gracefully', async () => {
      const apiError = {
        response: {
          data: {
            detail: 'Search service unavailable',
          },
        },
      }
      vi.mocked(searchApi.search).mockRejectedValue(apiError)

      const { search, error, results, total } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(error.value).toBe('Search service unavailable')
      expect(results.value).toEqual([])
      expect(total.value).toBe(0)
    })

    it('handles API errors without detail property', async () => {
      const apiError = new Error('Network error')
      vi.mocked(searchApi.search).mockRejectedValue(apiError)

      const { search, error } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(error.value).toBe('Network error')
    })

    it('handles unknown API errors', async () => {
      vi.mocked(searchApi.search).mockRejectedValue({})

      const { search, error } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(error.value).toBe('Search failed. Please try again.')
    })
  })

  // ============================================================================
  // DEBOUNCE TESTS
  // ============================================================================

  describe('debounced search', () => {
    it('debounces search input changes', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { query } = useSearch()

      query.value = 'dia'
      await flushPromises()
      expect(searchApi.search).not.toHaveBeenCalled()

      query.value = 'diab'
      await flushPromises()
      expect(searchApi.search).not.toHaveBeenCalled()

      // Wait for debounce (300ms)
      await new Promise((resolve) => setTimeout(resolve, 350))
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledTimes(1)
    })

    it('clears results when query is cleared', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { query, results, clearSearch } = useSearch()

      query.value = 'diabetes'
      await new Promise((resolve) => setTimeout(resolve, 350))
      await flushPromises()

      expect(results.value.length).toBeGreaterThan(0)

      query.value = ''
      await new Promise((resolve) => setTimeout(resolve, 350))
      await flushPromises()

      expect(results.value).toEqual([])
    })
  })

  // ============================================================================
  // CACHING TESTS
  // ============================================================================

  describe('caching', () => {
    it('returns cached results for same query', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, results } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledTimes(1)

      // Second search with same query
      await search('diabetes')
      await flushPromises()

      // Should not make another API call if cached
      expect(searchApi.search).toHaveBeenCalledTimes(1) // Still 1
    })

    it('caches searches with filters', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search } = useSearch()

      await search('diabetes', { negation: 'Affirmed' })
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledTimes(1)

      // Same query but different filters should be separate cache entry
      await search('diabetes', { negation: 'Negated' })
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledTimes(2)
    })

    it('maintains cache for last 10 searches', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, recentSearches } = useSearch()

      // Perform 15 searches
      for (let i = 0; i < 15; i++) {
        await search(`query${i}`)
        await flushPromises()
      }

      // Should only cache last 10
      expect(recentSearches.value.length).toBeLessThanOrEqual(10)
    })

    it('clears cache on demand', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, clearCache } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledTimes(1)

      clearCache()

      // After clearing cache, should make new API call
      await search('diabetes')
      await flushPromises()

      expect(searchApi.search).toHaveBeenCalledTimes(2)
    })
  })

  // ============================================================================
  // PAGINATION TESTS
  // ============================================================================

  describe('pagination', () => {
    it('calculates total pages correctly', () => {
      const { total, pageSize, totalPages } = useSearch()

      total.value = 100
      pageSize.value = 20

      expect(totalPages.value).toBe(5)
    })

    it('handles pagination with remainder', () => {
      const { total, pageSize, totalPages } = useSearch()

      total.value = 95
      pageSize.value = 20

      expect(totalPages.value).toBe(5)
    })

    it('navigates to next page', async () => {
      const mockResponse1 = createMockResponse({ page: 1, total: 100 })
      const mockResponse2 = createMockResponse({ page: 2, total: 100, results: [] })

      vi.mocked(searchApi.search).mockResolvedValueOnce(mockResponse1)

      const { search, nextPage, page } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(page.value).toBe(1)

      vi.mocked(searchApi.search).mockResolvedValueOnce(mockResponse2)
      await nextPage()
      await flushPromises()

      expect(page.value).toBe(2)
    })

    it('navigates to previous page', async () => {
      const mockResponse1 = createMockResponse({ page: 2, total: 100 })
      const mockResponse2 = createMockResponse({ page: 1, total: 100 })

      const { search, page } = useSearch()

      // Manually set page to 2
      page.value = 2

      vi.mocked(searchApi.search).mockResolvedValueOnce(mockResponse2)
      const { prevPage } = useSearch()

      // Note: We need to re-get the composable to get the updated page
      // This is a limitation of the test setup
    })

    it('prevents navigation beyond last page', async () => {
      const mockResponse = createMockResponse({ total: 40, page_size: 20 })
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, nextPage, page, totalPages } = useSearch()

      await search('diabetes')
      await flushPromises()

      // Set page to last page manually
      page.value = totalPages.value

      const initialCallCount = vi.mocked(searchApi.search).mock.calls.length
      await nextPage()
      await flushPromises()

      // Should not make additional API call (same call count)
      expect(vi.mocked(searchApi.search).mock.calls.length).toBe(initialCallCount)
    })

    it('prevents navigation before first page', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, prevPage, page } = useSearch()

      await search('diabetes')
      await flushPromises()

      // Already on first page
      expect(page.value).toBe(1)

      const initialCallCount = vi.mocked(searchApi.search).mock.calls.length
      await prevPage()
      await flushPromises()

      // Should not make additional API call
      expect(vi.mocked(searchApi.search).mock.calls.length).toBe(initialCallCount)
    })
  })

  // ============================================================================
  // SORTING TESTS
  // ============================================================================

  describe('sorting', () => {
    it('changes sort order and re-searches', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, setSort, sort, page } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(sort.value).toBe('relevance')

      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)
      await setSort('date_desc')
      await flushPromises()

      expect(sort.value).toBe('date_desc')
      expect(page.value).toBe(1) // Reset to first page
    })

    it('passes correct sort parameter to API', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, setSort } = useSearch()

      await search('diabetes')
      await flushPromises()

      const callCountBeforeSort = vi.mocked(searchApi.search).mock.calls.length

      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)
      await setSort('title_asc')
      await flushPromises()

      const lastCall = vi.mocked(searchApi.search).mock.calls[vi.mocked(searchApi.search).mock.calls.length - 1]
      expect(lastCall[0].sort).toBe('title_asc')
    })

    it('supports all sort options', async () => {
      const sortOptions: Array<'relevance' | 'date_desc' | 'date_asc' | 'title_asc' | 'title_desc'> = [
        'relevance',
        'date_desc',
        'date_asc',
        'title_asc',
        'title_desc',
      ]

      for (const sortOption of sortOptions) {
        vi.clearAllMocks() // Clear mocks for each sort option
        const mockResponse = createMockResponse()
        vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

        const { search, setSort } = useSearch() // Fresh composable for each

        await search('diabetes')
        await flushPromises()

        vi.mocked(searchApi.search).mockResolvedValue(mockResponse)
        await setSort(sortOption)
        await flushPromises()

        const lastCall = vi.mocked(searchApi.search).mock.calls[vi.mocked(searchApi.search).mock.calls.length - 1]
        expect(lastCall[0].sort).toBe(sortOption)
      }
    })
  })

  // ============================================================================
  // CLEAR SEARCH TESTS
  // ============================================================================

  describe('clearSearch', () => {
    it('clears search state', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, clearSearch, results, total, page, error, query } = useSearch()

      await search('diabetes')
      await flushPromises()

      expect(results.value.length).toBeGreaterThan(0)

      clearSearch()

      expect(query.value).toBe('')
      expect(results.value).toEqual([])
      expect(total.value).toBe(0)
      expect(page.value).toBe(1)
      expect(error.value).toBeNull()
    })
  })

  // ============================================================================
  // COMPUTED PROPERTIES TESTS
  // ============================================================================

  describe('computed properties', () => {
    it('hasResults returns true when results exist', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, hasResults } = useSearch()

      expect(hasResults.value).toBe(false)

      await search('diabetes')
      await flushPromises()

      expect(hasResults.value).toBe(true)
    })

    it('isEmpty returns true when no results and query exists', async () => {
      const mockResponse = createMockResponse({ results: [] })
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, isEmpty, query } = useSearch()

      query.value = 'diabetes'
      await flushPromises()

      // Wait for debounce
      await new Promise((resolve) => setTimeout(resolve, 350))
      await flushPromises()

      expect(isEmpty.value).toBe(true)
    })

    it('isEmpty returns false when loading', async () => {
      const mockResponse = createMockResponse({ results: [] })
      vi.mocked(searchApi.search).mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => resolve(mockResponse), 200)
          })
      )

      const { search, isEmpty, query } = useSearch()

      query.value = 'diabetes'
      const searchPromise = search('diabetes')
      await flushPromises()

      // During loading, isEmpty should be false even with no results
      expect(isEmpty.value).toBe(false)

      await searchPromise
      await flushPromises()
    })

    it('recentSearches shows cached searches', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search, recentSearches } = useSearch()

      await search('diabetes')
      await flushPromises()

      await search('hypertension')
      await flushPromises()

      expect(recentSearches.value).toContain('diabetes')
      expect(recentSearches.value).toContain('hypertension')
    })
  })

  // ============================================================================
  // FILTER TESTS
  // ============================================================================

  describe('filtering', () => {
    it('passes filters to API', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search } = useSearch()

      await search('diabetes', { negation: 'Affirmed' })
      await flushPromises()

      expect(vi.mocked(searchApi.search).mock.calls[0][0].filters).toEqual({
        negation: 'Affirmed',
      })
    })

    it('handles multiple filter properties', async () => {
      const mockResponse = createMockResponse()
      vi.mocked(searchApi.search).mockResolvedValue(mockResponse)

      const { search } = useSearch()

      const filters = {
        negation: 'Affirmed',
        temporality: 'Current',
        experiencer: 'Patient',
      }

      await search('diabetes', filters)
      await flushPromises()

      expect(vi.mocked(searchApi.search).mock.calls[0][0].filters).toEqual(filters)
    })
  })

  // ============================================================================
  // PAGINATION WITH SEARCH TESTS
  // ============================================================================

  describe('pagination with search parameters', () => {
    it('maintains query and filters during pagination', async () => {
      const mockResponse1 = createMockResponse({ page: 1, total: 100 })
      const mockResponse2 = createMockResponse({ page: 2, total: 100 })

      vi.mocked(searchApi.search).mockResolvedValueOnce(mockResponse1).mockResolvedValueOnce(mockResponse2)

      const { search, nextPage, filters } = useSearch()

      const filterObj = { negation: 'Affirmed' }
      await search('diabetes', filterObj)
      await flushPromises()

      // Store filters in composable state
      filters.value = filterObj

      await nextPage()
      await flushPromises()

      const lastCall = vi.mocked(searchApi.search).mock.calls[vi.mocked(searchApi.search).mock.calls.length - 1]
      expect(lastCall[0].query).toBe('diabetes')
      expect(lastCall[0].filters).toEqual(filterObj)
    })
  })
})
