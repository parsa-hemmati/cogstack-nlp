/**
 * Search Composable
 *
 * Provides reusable search functionality for document and content search.
 * Manages search state (query, results, pagination, loading/error states),
 * debounced input, caching of recent searches, and provides methods for
 * performing searches, navigating pages, and managing sort order.
 *
 * Features:
 * - Debounced search input (300ms default)
 * - Search result caching (last 10 searches)
 * - Pagination support
 * - Meta-annotation filtering
 * - Sorting options
 * - Error handling
 *
 * This is the central state manager for the search module and should be imported
 * in any component that needs search functionality.
 *
 * @example
 * ```typescript
 * import { useSearch } from '@/composables/useSearch'
 *
 * export default {
 *   setup() {
 *     const { query, results, search, isLoading } = useSearch()
 *
 *     const handleSearch = async () => {
 *       await search('diabetes')
 *     }
 *
 *     return { query, results, search, isLoading, handleSearch }
 *   }
 * }
 * ```
 *
 * @example
 * ```vue
 * <template>
 *   <div>
 *     <input v-model="query" placeholder="Search..." />
 *     <div v-if="isLoading">Loading...</div>
 *     <div v-else-if="error" class="error">{{ error }}</div>
 *     <div v-else>
 *       <p>Total results: {{ total }}</p>
 *       <div v-for="result in results" :key="result.id">
 *         <h3>{{ result.title }}</h3>
 *         <p>{{ result.content }}</p>
 *       </div>
 *     </div>
 *   </div>
 * </template>
 *
 * <script setup lang="ts">
 * import { useSearch } from '@/composables/useSearch'
 *
 * const {
 *   query,
 *   results,
 *   isLoading,
 *   error,
 *   total,
 *   page,
 *   pageSize,
 *   sort,
 *   search,
 *   nextPage,
 *   prevPage,
 *   setSort,
 *   clearSearch
 * } = useSearch()
 * </script>
 * ```
 *
 * @see {@link ../api/search.ts} for API client
 * @see {@link ../../../.specify/specifications/search-module.md} for detailed documentation
 */

import { ref, computed, watch, onMounted } from 'vue'
import { watchDebounced } from '@vueuse/core'
import { search as searchApi, type SearchResponse, type SearchResult, type SortOption, type SearchFilters } from '@/api/search'

/**
 * Cache entry for storing recent searches
 */
interface CacheEntry {
  query: string
  filters?: SearchFilters
  sort: SortOption
  response: SearchResponse
  timestamp: number
}

/**
 * Search cache with max 10 entries
 */
class SearchCache {
  private cache: Map<string, CacheEntry> = new Map()
  private readonly maxSize = 10

  /**
   * Generate cache key from query, filters, and sort
   */
  private getKey(query: string, filters?: SearchFilters, sort: SortOption = 'relevance'): string {
    const filterStr = filters ? JSON.stringify(filters) : ''
    return `${query}::${filterStr}::${sort}`
  }

  /**
   * Get cached result if available
   */
  get(query: string, filters?: SearchFilters, sort: SortOption = 'relevance'): SearchResponse | null {
    const key = this.getKey(query, filters, sort)
    const entry = this.cache.get(key)
    if (entry) {
      // Update timestamp to mark as recently used
      entry.timestamp = Date.now()
      return entry.response
    }
    return null
  }

  /**
   * Set cache entry
   */
  set(query: string, filters: SearchFilters | undefined, sort: SortOption, response: SearchResponse): void {
    const key = this.getKey(query, filters, sort)

    // If cache is full, remove oldest entry
    if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
      let oldestKey: string | null = null
      let oldestTime = Infinity

      for (const [k, entry] of this.cache.entries()) {
        if (entry.timestamp < oldestTime) {
          oldestTime = entry.timestamp
          oldestKey = k
        }
      }

      if (oldestKey) {
        this.cache.delete(oldestKey)
      }
    }

    this.cache.set(key, {
      query,
      filters,
      sort,
      response,
      timestamp: Date.now(),
    })
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.cache.clear()
  }

  /**
   * Get all cached queries
   */
  getAll(): CacheEntry[] {
    return Array.from(this.cache.values())
  }
}

/**
 * Search state and methods
 *
 * @returns {Object} Search composable with state, computed properties, and methods
 *   - query: Ref<string> - Current search query
 *   - results: Ref<SearchResult[]> - Array of search results for current page
 *   - total: Ref<number> - Total matching results (may be > results.length)
 *   - page: Ref<number> - Current page (1-indexed)
 *   - pageSize: Ref<number> - Results per page (default 20)
 *   - sort: Ref<SortOption> - Current sort order (default 'relevance')
 *   - totalPages: ComputedRef<number> - Calculated pages needed
 *   - isLoading: Ref<boolean> - Search in progress
 *   - error: Ref<string | null> - Error message if any
 *   - hasResults: ComputedRef<boolean> - true if results.length > 0
 *   - isEmpty: ComputedRef<boolean> - true if no results and query was entered
 *   - recentSearches: ComputedRef<string[]> - Last 10 searched queries
 *   - search: Function - Perform search (debounced)
 *   - nextPage: Function - Navigate to next page
 *   - prevPage: Function - Navigate to previous page
 *   - setSort: Function - Change sort order
 *   - clearSearch: Function - Clear all results and reset state
 */
export function useSearch() {
  // ============================================================================
  // STATE
  // ============================================================================

  /**
   * Current search query input
   * @type {Ref<string>}
   */
  const query = ref<string>('')

  /**
   * Array of search results for current page
   * @type {Ref<SearchResult[]>}
   */
  const results = ref<SearchResult[]>([])

  /**
   * Total number of results matching query (may be > results.length)
   * @type {Ref<number>}
   */
  const total = ref(0)

  /**
   * Current page number (1-indexed)
   * @type {Ref<number>}
   */
  const page = ref(1)

  /**
   * Number of results per page
   * @type {Ref<number>}
   */
  const pageSize = ref(20)

  /**
   * Current sort order for results
   * @type {Ref<SortOption>}
   */
  const sort = ref<SortOption>('relevance')

  /**
   * Meta-annotation filters
   * @type {Ref<SearchFilters | undefined>}
   */
  const filters = ref<SearchFilters | undefined>()

  /**
   * Whether a search is currently in progress
   * @type {Ref<boolean>}
   */
  const isLoading = ref(false)

  /**
   * Error message from last search, or null if no error
   * @type {Ref<string | null>}
   */
  const error = ref<string | null>(null)

  /**
   * Search cache for storing recent results
   * @type {SearchCache}
   */
  const cache = new SearchCache()

  // ============================================================================
  // COMPUTED PROPERTIES
  // ============================================================================

  /**
   * Number of pages based on total results and page size
   * Formula: Math.ceil(total / pageSize)
   * @type {ComputedRef<number>}
   */
  const totalPages = computed(() => {
    if (total.value === 0) return 0
    return Math.ceil(total.value / pageSize.value)
  })

  /**
   * Whether current search has any results
   * @type {ComputedRef<boolean>}
   */
  const hasResults = computed(() => results.value.length > 0)

  /**
   * Whether search is empty (no results and a query was entered)
   * Used for displaying "no results" empty state
   * @type {ComputedRef<boolean>}
   */
  const isEmpty = computed(() => !isLoading.value && results.value.length === 0 && query.value.trim() !== '')

  /**
   * Get recent searches from cache
   * @type {ComputedRef<string[]>}
   */
  const recentSearches = computed(() => {
    return cache.getAll().map((entry) => entry.query)
  })

  // ============================================================================
  // METHODS
  // ============================================================================

  /**
   * Perform a search with optional filters and pagination
   *
   * Side effects:
   * - Sets isLoading = true while fetching
   * - Updates results, total, page
   * - Clears error on success, sets error on failure
   * - Caches results for later retrieval
   *
   * @param {string} [searchQuery] - Query to search for (uses ref if not provided)
   * @param {SearchFilters} [searchFilters] - Meta-annotation filters (optional)
   * @param {number} [pageNum=1] - Page number to fetch (1-indexed)
   *
   * @returns {Promise<void>} Resolves when search completes
   *
   * @example
   * // Search with default params
   * await search()
   *
   * @example
   * // Search specific query
   * await search('diabetes', { negation: 'Affirmed' })
   *
   * @example
   * // Search with pagination
   * await search('diabetes', undefined, 2)
   */
  const performSearch = async (
    searchQuery?: string,
    searchFilters?: SearchFilters,
    pageNum: number = 1
  ): Promise<void> => {
    // Use provided query or ref value
    const q = searchQuery || query.value
    const f = searchFilters || filters.value

    // Validation
    if (!q || q.trim() === '') {
      error.value = 'Please enter a search query'
      return
    }

    // Check cache first
    const cached = cache.get(q, f, sort.value)
    if (cached && cached.page === pageNum) {
      results.value = cached.results
      total.value = cached.total
      page.value = pageNum
      error.value = null
      // Store filters for later pagination
      if (searchFilters !== undefined) {
        filters.value = searchFilters
      }
      return
    }

    // State setup
    isLoading.value = true
    error.value = null

    try {
      // Call API
      const response = await searchApi({
        query: q.trim(),
        filters: f,
        page: pageNum,
        page_size: pageSize.value,
        sort: sort.value,
      })

      // Update state
      results.value = response.results
      total.value = response.total
      page.value = pageNum
      query.value = q
      // Store filters for pagination
      if (searchFilters !== undefined) {
        filters.value = searchFilters
      }

      // Cache result
      cache.set(q, f, sort.value, response)

    } catch (err: any) {
      // Error handling
      error.value = err.response?.data?.detail || err.message || 'Search failed. Please try again.'
      results.value = []
      total.value = 0
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Debounced version of performSearch
   * Waits 300ms after user stops typing before searching
   */
  const search = async (
    searchQuery?: string,
    searchFilters?: SearchFilters,
    pageNum: number = 1
  ): Promise<void> => {
    return performSearch(searchQuery, searchFilters, pageNum)
  }

  /**
   * Navigate to the next page of results
   *
   * Only works if current page < total pages
   * Automatically refetches with same query and filters
   *
   * @returns {Promise<void>} Resolves when next page loaded
   */
  const nextPage = async (): Promise<void> => {
    if (page.value < totalPages.value) {
      await performSearch(query.value, filters.value, page.value + 1)
    }
  }

  /**
   * Navigate to the previous page of results
   *
   * Only works if current page > 1
   * Automatically refetches with same query and filters
   *
   * @returns {Promise<void>} Resolves when previous page loaded
   */
  const prevPage = async (): Promise<void> => {
    if (page.value > 1) {
      await performSearch(query.value, filters.value, page.value - 1)
    }
  }

  /**
   * Change sort order and re-search
   *
   * @param {SortOption} newSort - New sort order
   * @returns {Promise<void>}
   */
  const setSort = async (newSort: SortOption): Promise<void> => {
    sort.value = newSort
    page.value = 1 // Reset to first page on sort change
    await performSearch(query.value, filters.value, 1)
  }

  /**
   * Clear all search results and reset state
   *
   * Resets:
   * - query = ''
   * - results = []
   * - total = 0
   * - page = 1
   * - error = null
   *
   * @returns {void}
   */
  const clearSearch = (): void => {
    query.value = ''
    results.value = []
    total.value = 0
    page.value = 1
    error.value = null
  }

  /**
   * Clear the search cache
   *
   * @returns {void}
   */
  const clearCache = (): void => {
    cache.clear()
  }

  // ============================================================================
  // WATCHERS - Setup debounced search
  // ============================================================================

  /**
   * Watch for query changes with debounce
   * Performs search 300ms after user stops typing
   */
  watchDebounced(
    query,
    async (newQuery) => {
      if (newQuery.trim() === '') {
        clearSearch()
      } else {
        page.value = 1 // Reset to first page on new query
        await performSearch(newQuery, filters.value, 1)
      }
    },
    { debounce: 300 }
  )

  // ============================================================================
  // LIFECYCLE HOOKS
  // ============================================================================

  /**
   * Initialize on mount
   * Could be used for restoring previous search state
   */
  onMounted(() => {
    // Can add initialization logic here if needed
  })

  // ============================================================================
  // RETURN PUBLIC API
  // ============================================================================

  return {
    // State
    query,
    results,
    total,
    page,
    pageSize,
    sort,
    filters,
    isLoading,
    error,

    // Computed
    totalPages,
    hasResults,
    isEmpty,
    recentSearches,

    // Methods
    search,
    nextPage,
    prevPage,
    setSort,
    clearSearch,
    clearCache,
  }
}
