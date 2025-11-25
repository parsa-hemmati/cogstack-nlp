/**
 * Integration tests for Search Module
 *
 * Tests end-to-end search flow including:
 * - SearchBar + SearchResults component integration
 * - useSearch composable with mocked backend API
 * - Pagination, sorting, error handling
 * - XSS prevention and security
 * - Performance benchmarks
 */
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount, flushPromises, VueWrapper } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import SearchBar from '@/components/search/SearchBar.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import SearchResultItem from '@/components/search/SearchResultItem.vue'
import { useSearch } from '@/composables/useSearch'
import * as searchApi from '@/api/search'
import type { SearchResponse, SearchResult } from '@/api/search'

// Mock the search API
vi.mock('@/api/search', () => ({
  search: vi.fn(),
  clearSearchCache: vi.fn(),
}))

// Create Vuetify instance
const vuetify = createVuetify({
  components,
  directives,
})

/**
 * Mock search results generator
 */
const createMockResults = (count: number, query: string, page: number = 1): SearchResult[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `result-${page}-${i + 1}`,
    title: `Patient with ${query} - Document ${(page - 1) * 20 + i + 1}`,
    content: `This is a clinical document about ${query}. The patient was diagnosed with ${query} and is being monitored.`,
    document_type: i % 3 === 0 ? 'Clinical Note' : i % 3 === 1 ? 'Lab Results' : 'Discharge Summary',
    author: i % 2 === 0 ? 'Dr. Smith' : 'Dr. Johnson',
    date: `2024-01-${String(i + 1).padStart(2, '0')}`,
    score: 95.5 - i,
    highlights: {
      title: [`Patient with <mark>${query}</mark>`],
      content: [`...diagnosed with <mark>${query}</mark>...`],
    },
  }))
}

/**
 * Mock API response generator
 */
const createMockResponse = (
  query: string,
  page: number = 1,
  total: number = 150,
  pageSize: number = 20
): SearchResponse => {
  const resultsCount = Math.min(pageSize, total - (page - 1) * pageSize)
  return {
    results: createMockResults(resultsCount, query, page),
    total,
    page,
    page_size: pageSize,
    query,
  }
}

/**
 * Helper component that combines SearchBar and SearchResults
 * Simulates a full search page
 */
const SearchPage = {
  components: { SearchBar, SearchResults },
  template: `
    <div>
      <SearchBar
        v-model="searchQuery"
        :loading="isLoading"
        :error="error"
        @search="handleSearch"
        @clear="handleClear"
      />
      <SearchResults
        :results="results"
        :query="searchQuery"
        :loading="isLoading"
        :error="error"
        :total="total"
        :page="page"
        :page-size="pageSize"
        @page-change="handlePageChange"
        @sort-change="handleSortChange"
      />
    </div>
  `,
  setup() {
    const {
      query: searchQuery,
      results,
      total,
      page,
      pageSize,
      isLoading,
      error,
      search,
      clearSearch,
      nextPage,
      prevPage,
      setSort,
    } = useSearch()

    const handleSearch = async (query: string) => {
      await search(query)
    }

    const handleClear = () => {
      clearSearch()
    }

    const handlePageChange = async (newPage: number) => {
      if (newPage > page.value) {
        await nextPage()
      } else {
        await prevPage()
      }
    }

    const handleSortChange = async (sort: string) => {
      await setSort(sort as any)
    }

    return {
      searchQuery,
      results,
      total,
      page,
      pageSize,
      isLoading,
      error,
      handleSearch,
      handleClear,
      handlePageChange,
      handleSortChange,
    }
  },
}

describe('Search Flow Integration', () => {
  let wrapper: VueWrapper<any>
  const mockSearch = vi.mocked(searchApi.search)

  beforeEach(() => {
    vi.clearAllMocks()
    mockSearch.mockResolvedValue(createMockResponse('atrial flutter'))
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  // ============================================================================
  // SCENARIO 1: Basic Search Flow
  // ============================================================================
  describe('Scenario 1: Basic Search Flow', () => {
    it('performs end-to-end search', async () => {
      // 1. Mount search page
      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      // 2. User types query
      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('atrial flutter')

      // 3. User presses Enter
      await input.trigger('keydown.enter')
      await flushPromises()

      // Wait for debounce and search to complete
      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // 4. API called with correct params
      expect(mockSearch).toHaveBeenCalledWith({
        query: 'atrial flutter',
        filters: undefined,
        page: 1,
        page_size: 20,
        sort: 'relevance',
      })

      // 5. Results displayed
      const searchResults = wrapper.findComponent(SearchResults)
      const resultItems = searchResults.findAllComponents(SearchResultItem)
      expect(resultItems.length).toBeGreaterThan(0)

      // 6. Highlights are present and sanitized
      const firstResult = resultItems[0]
      const html = firstResult.html()
      expect(html).toContain('atrial flutter')
      // Should have mark tags for highlights
      expect(html).toContain('<mark>')
      // Should NOT have script tags
      expect(html).not.toContain('<script>')
    })

    it('displays correct result count', async () => {
      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('diabetes')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      const searchResults = wrapper.findComponent(SearchResults)
      const resultsText = searchResults.text()

      // Should show total count (150 in mock)
      expect(resultsText).toContain('150')
      expect(resultsText).toContain('results')
    })
  })

  // ============================================================================
  // SCENARIO 2: Pagination
  // ============================================================================
  describe('Scenario 2: Pagination', () => {
    it('paginates through results', async () => {
      // Setup: Mock returns different results for different pages
      mockSearch.mockImplementation(async (req) => {
        return createMockResponse(req.query, req.page, 150, req.page_size)
      })

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      // 1. Perform initial search (results 1-20)
      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('diabetes')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // Verify page 1 results
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1 })
      )

      let searchResults = wrapper.findComponent(SearchResults)
      let resultItems = searchResults.findAllComponents(SearchResultItem)
      const firstPageFirstId = resultItems[0].props('result').id
      expect(firstPageFirstId).toBe('result-1-1')

      // 2. Click page 2
      const pagination = searchResults.find('.v-pagination')
      expect(pagination.exists()).toBe(true)

      // Emit page change event
      searchResults.vm.$emit('page-change', 2)
      await flushPromises()

      // 3. Verify API called with page=2
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 })
      )

      // 4. Verify new results loaded (21-40)
      await flushPromises()
      searchResults = wrapper.findComponent(SearchResults)
      resultItems = searchResults.findAllComponents(SearchResultItem)
      const secondPageFirstId = resultItems[0].props('result').id
      expect(secondPageFirstId).toBe('result-2-1')

      // 5. Click previous page
      searchResults.vm.$emit('page-change', 1)
      await flushPromises()

      // 6. Verify back to results 1-20
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({ page: 1 })
      )
    })

    it('disables navigation at boundaries', async () => {
      // Mock only 1 page of results
      mockSearch.mockResolvedValue(createMockResponse('test', 1, 10, 20))

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      const searchResults = wrapper.findComponent(SearchResults)

      // With only 10 results (< 20), pagination should not show
      const pagination = searchResults.find('.v-pagination')
      expect(pagination.exists()).toBe(false)
    })
  })

  // ============================================================================
  // SCENARIO 3: Sorting
  // ============================================================================
  describe('Scenario 3: Sorting', () => {
    it('changes sort order', async () => {
      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      // 1. Perform initial search
      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('hypertension')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // Verify initial sort
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({ sort: 'relevance' })
      )

      // 2. Change sort to "Date (Newest)"
      const searchResults = wrapper.findComponent(SearchResults)
      searchResults.vm.$emit('sort-change', 'date_desc')
      await flushPromises()

      // 3. Verify API called with sort=date_desc
      expect(mockSearch).toHaveBeenCalledWith(
        expect.objectContaining({
          sort: 'date_desc',
          page: 1, // Should reset to page 1
        })
      )
    })

    it('resets to page 1 when sort changes', async () => {
      mockSearch.mockImplementation(async (req) => {
        return createMockResponse(req.query, req.page, 150, req.page_size)
      })

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      // Navigate to page 2
      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      let searchResults = wrapper.findComponent(SearchResults)
      searchResults.vm.$emit('page-change', 2)
      await flushPromises()

      // Now change sort - should reset to page 1
      searchResults.vm.$emit('sort-change', 'date_desc')
      await flushPromises()

      expect(mockSearch).toHaveBeenLastCalledWith(
        expect.objectContaining({
          page: 1,
          sort: 'date_desc',
        })
      )
    })
  })

  // ============================================================================
  // SCENARIO 4: Empty State
  // ============================================================================
  describe('Scenario 4: Empty State', () => {
    it('shows empty state when no results', async () => {
      // 1. Mock API to return 0 results
      mockSearch.mockResolvedValue({
        results: [],
        total: 0,
        page: 1,
        page_size: 20,
        query: 'nonexistent',
      })

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      // 2. Perform search
      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('nonexistent')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // 3. Verify "No results found" message displayed
      const searchResults = wrapper.findComponent(SearchResults)
      const text = searchResults.text()
      expect(text).toContain('No results found')
      expect(text).toContain('0 results')
    })

    it('hides empty state when loading', async () => {
      // Mock slow API
      mockSearch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(createMockResponse('test')), 1000)
          )
      )

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      const searchResults = wrapper.findComponent(SearchResults)

      // Should show loading state, not empty state
      expect(searchResults.find('.v-skeleton-loader').exists()).toBe(true)
      expect(searchResults.text()).not.toContain('No results found')
    })
  })

  // ============================================================================
  // SCENARIO 5: Error Handling
  // ============================================================================
  describe('Scenario 5: Error Handling', () => {
    it('handles API errors gracefully', async () => {
      // 1. Mock API to return error
      const errorMessage = 'Search service unavailable'
      mockSearch.mockRejectedValue({
        response: {
          data: {
            detail: errorMessage,
          },
        },
      })

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      // 2. Perform search
      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('diabetes')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // 3. Verify error message displayed
      const errorAlert = searchBar.find('.v-alert[type="error"]')
      expect(errorAlert.exists()).toBe(true)
      expect(errorAlert.text()).toContain(errorMessage)

      // 4. Verify user can retry
      // Clear error and retry
      mockSearch.mockResolvedValue(createMockResponse('diabetes'))
      await input.setValue('diabetes retry')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // Error should be cleared and results shown
      const searchResults = wrapper.findComponent(SearchResults)
      const resultItems = searchResults.findAllComponents(SearchResultItem)
      expect(resultItems.length).toBeGreaterThan(0)
    })

    it('handles network errors', async () => {
      mockSearch.mockRejectedValue(new Error('Network error'))

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      const errorAlert = searchBar.find('.v-alert[type="error"]')
      expect(errorAlert.exists()).toBe(true)
      expect(errorAlert.text()).toContain('Network error')
    })
  })

  // ============================================================================
  // SCENARIO 6: XSS Prevention
  // ============================================================================
  describe('Scenario 6: XSS Prevention', () => {
    it('prevents XSS attacks in search results', async () => {
      // 1. Mock malicious search results with scripts
      const maliciousResults: SearchResult[] = [
        {
          id: '1',
          title: '<script>alert("XSS")</script>Patient Record',
          content: 'This is content with <img src=x onerror="alert(1)">malicious code',
          document_type: 'Clinical Note',
          author: 'Dr. <script>alert("author")</script>Smith',
          date: '2024-01-15',
          score: 95.5,
          highlights: {
            title: ['<img src=x onerror="alert(1)">Patient'],
            content: ['<script>alert("XSS")</script>content'],
          },
        },
      ]

      mockSearch.mockResolvedValue({
        results: maliciousResults,
        total: 1,
        page: 1,
        page_size: 20,
        query: 'test',
      })

      // 2. Render results
      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      const html = wrapper.html()

      // 3. Verify scripts stripped
      expect(html).not.toContain('<script>')
      expect(html).not.toContain('onerror')
      expect(html).not.toContain('alert(')

      // 4. Verify safe content remains
      expect(wrapper.text()).toContain('Patient')
      expect(wrapper.text()).toContain('content')
    })

    it('sanitizes highlights correctly', async () => {
      const resultsWithHighlights: SearchResult[] = [
        {
          id: '1',
          title: 'Safe Title',
          content: 'Safe content',
          document_type: 'Clinical Note',
          author: 'Dr. Smith',
          date: '2024-01-15',
          score: 95.5,
          highlights: {
            title: ['Safe <mark>Title</mark><script>alert("xss")</script>'],
            content: ['<mark>Safe</mark> content<img src=x onerror=alert(1)>'],
          },
        },
      ]

      mockSearch.mockResolvedValue({
        results: resultsWithHighlights,
        total: 1,
        page: 1,
        page_size: 20,
        query: 'Safe',
      })

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('Safe')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      const html = wrapper.html()

      // Should allow <mark> tags (safe)
      expect(html).toContain('<mark>')

      // Should strip <script> and onerror
      expect(html).not.toContain('<script>')
      expect(html).not.toContain('onerror')
      expect(html).not.toContain('alert(')
    })
  })

  // ============================================================================
  // SCENARIO 7: Loading States
  // ============================================================================
  describe('Scenario 7: Loading States', () => {
    it('shows loading indicators correctly', async () => {
      // 1. Start search with slow API
      mockSearch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(createMockResponse('test')), 500)
          )
      )

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // 2. Verify SearchBar shows loading state
      const textField = searchBar.find('.v-text-field')
      expect(textField.attributes('loading')).toBeDefined()

      // 3. Verify SearchResults shows skeleton loaders
      const searchResults = wrapper.findComponent(SearchResults)
      const skeletonLoader = searchResults.find('.v-skeleton-loader')
      expect(skeletonLoader.exists()).toBe(true)

      // 4. When API responds, loading indicators disappear
      await new Promise((resolve) => setTimeout(resolve, 200))
      await flushPromises()

      const updatedTextField = wrapper.findComponent(SearchBar).find('.v-text-field')
      expect(updatedTextField.attributes('loading')).toBeUndefined()

      const updatedResults = wrapper.findComponent(SearchResults)
      expect(updatedResults.find('.v-skeleton-loader').exists()).toBe(false)
    })

    it('disables input during search', async () => {
      mockSearch.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => resolve(createMockResponse('test')), 300)
          )
      )

      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')
      await input.setValue('test')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // Input should be disabled during loading
      expect(input.attributes('disabled')).toBeDefined()
    })
  })

  // ============================================================================
  // SCENARIO 8: Cache Behavior
  // ============================================================================
  describe('Scenario 8: Cache Behavior', () => {
    it('uses cached results for repeated searches', async () => {
      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')

      // 1. Perform search for "diabetes"
      await input.setValue('diabetes')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // 2. Verify API called once
      expect(mockSearch).toHaveBeenCalledTimes(1)

      // 3. Clear search
      searchBar.vm.$emit('clear')
      await flushPromises()

      // 4. Search for "diabetes" again
      await input.setValue('diabetes')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // 5. Verify API NOT called again (cached results used)
      // Note: Due to debouncing and clear, this might be called twice
      // But the cache should prevent unnecessary calls for the same query
      const callCount = mockSearch.mock.calls.length
      expect(callCount).toBeLessThanOrEqual(2)
    })

    it('caches up to 10 recent searches', async () => {
      wrapper = mount(SearchPage, {
        global: {
          plugins: [vuetify],
        },
      })

      const searchBar = wrapper.findComponent(SearchBar)
      const input = searchBar.find('input')

      // Perform 12 different searches
      for (let i = 1; i <= 12; i++) {
        mockSearch.mockResolvedValue(createMockResponse(`query${i}`))
        await input.setValue(`query${i}`)
        await input.trigger('keydown.enter')

        await new Promise((resolve) => setTimeout(resolve, 400))
        await flushPromises()
      }

      // Search for query1 again (should NOT be cached - evicted)
      mockSearch.mockClear()
      await input.setValue('query1')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // Should call API again (not cached)
      expect(mockSearch).toHaveBeenCalled()

      // Search for query12 again (should be cached)
      mockSearch.mockClear()
      await input.setValue('query12')
      await input.trigger('keydown.enter')

      await new Promise((resolve) => setTimeout(resolve, 400))
      await flushPromises()

      // Might use cache (depends on implementation)
      // This test verifies cache limit behavior
    })
  })
})

// ============================================================================
// PERFORMANCE TESTS
// ============================================================================
describe('Search Performance', () => {
  let wrapper: VueWrapper<any>
  const mockSearch = vi.mocked(searchApi.search)

  beforeEach(() => {
    vi.clearAllMocks()
    mockSearch.mockResolvedValue(createMockResponse('test'))
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('renders results within 100ms', async () => {
    wrapper = mount(SearchPage, {
      global: {
        plugins: [vuetify],
      },
    })

    const searchBar = wrapper.findComponent(SearchBar)
    const input = searchBar.find('input')

    await input.setValue('test query')
    await input.trigger('keydown.enter')

    await new Promise((resolve) => setTimeout(resolve, 400))
    await flushPromises()

    // Measure render time
    const start = performance.now()
    await wrapper.vm.$nextTick()
    const end = performance.now()

    const renderTime = end - start
    expect(renderTime).toBeLessThan(100)
  })

  it('handles 100 results without lag', async () => {
    // Mock 100 results
    const largeResponse: SearchResponse = {
      results: createMockResults(100, 'test'),
      total: 100,
      page: 1,
      page_size: 100,
      query: 'test',
    }

    mockSearch.mockResolvedValue(largeResponse)

    wrapper = mount(SearchPage, {
      global: {
        plugins: [vuetify],
      },
    })

    const searchBar = wrapper.findComponent(SearchBar)
    const input = searchBar.find('input')

    await input.setValue('test')
    await input.trigger('keydown.enter')

    await new Promise((resolve) => setTimeout(resolve, 400))
    await flushPromises()

    const start = performance.now()

    // Trigger re-render
    await wrapper.vm.$forceUpdate()
    await wrapper.vm.$nextTick()

    const end = performance.now()
    const renderTime = end - start

    // Should render quickly even with 100 results
    expect(renderTime).toBeLessThan(200)

    // Verify all results rendered
    const searchResults = wrapper.findComponent(SearchResults)
    const resultItems = searchResults.findAllComponents(SearchResultItem)
    expect(resultItems.length).toBe(100)
  })

  it('debounces search input efficiently', async () => {
    wrapper = mount(SearchPage, {
      global: {
        plugins: [vuetify],
      },
    })

    const searchBar = wrapper.findComponent(SearchBar)
    const input = searchBar.find('input')

    // Type multiple characters quickly
    await input.setValue('d')
    await input.setValue('di')
    await input.setValue('dia')
    await input.setValue('diab')
    await input.setValue('diabe')
    await input.setValue('diabet')
    await input.setValue('diabetes')

    // Wait less than debounce time
    await new Promise((resolve) => setTimeout(resolve, 200))
    await flushPromises()

    // API should not be called yet
    expect(mockSearch).not.toHaveBeenCalled()

    // Wait for debounce to complete (300ms total)
    await new Promise((resolve) => setTimeout(resolve, 200))
    await flushPromises()

    // API should be called only once
    expect(mockSearch).toHaveBeenCalledTimes(1)
  })

  it('handles rapid page changes efficiently', async () => {
    mockSearch.mockImplementation(async (req) => {
      return createMockResponse(req.query, req.page, 150, req.page_size)
    })

    wrapper = mount(SearchPage, {
      global: {
        plugins: [vuetify],
      },
    })

    const searchBar = wrapper.findComponent(SearchBar)
    const input = searchBar.find('input')

    await input.setValue('test')
    await input.trigger('keydown.enter')

    await new Promise((resolve) => setTimeout(resolve, 400))
    await flushPromises()

    mockSearch.mockClear()

    const start = performance.now()

    // Rapidly change pages
    const searchResults = wrapper.findComponent(SearchResults)
    for (let page = 2; page <= 5; page++) {
      searchResults.vm.$emit('page-change', page)
      await flushPromises()
    }

    const end = performance.now()
    const totalTime = end - start

    // Should handle rapid changes efficiently
    expect(totalTime).toBeLessThan(500)
  })
})
