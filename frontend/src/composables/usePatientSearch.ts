/**
 * Patient Search Composable
 *
 * Provides reusable search logic for patient search functionality.
 * Manages search state (query, results, pagination, loading/error states) and provides
 * methods for performing searches, navigating pages, and clearing results.
 *
 * This is the central state manager for the search module and should be imported
 * in any component that needs search functionality.
 *
 * @example
 * ```typescript
 * const { results, search, isLoading, error } = usePatientSearch()
 * await search('diabetes', { Negation: 'Affirmed' }, 1, 20)
 * ```
 *
 * @example
 * ```vue
 * <template>
 *   <SearchResults :results="results" :loading="isLoading" />
 * </template>
 *
 * <script setup lang="ts">
 * import { usePatientSearch } from '@/composables/usePatientSearch'
 * const { results, search, isLoading } = usePatientSearch()
 * </script>
 * ```
 *
 * @see {@link ../../../docs/features/search/composables/useSearch.md} for detailed documentation
 */
import { ref, computed } from 'vue'
import { searchPatients, type PatientSearchRequest, type PatientSearchResult, type SearchFilters } from '@/api/patientSearch'

/**
 * Patient search state and methods
 *
 * @returns {Object} Search state, computed properties, and methods
 *   - results: Ref<PatientSearchResult[]> - Array of search results
 *   - total: Ref<number> - Total matching results (may be >results.length)
 *   - page: Ref<number> - Current page (1-indexed)
 *   - pageSize: Ref<number> - Results per page (default 20)
 *   - totalPages: ComputedRef<number> - Calculated pages needed
 *   - queryTimeMs: Ref<number> - Search response time in milliseconds
 *   - isLoading: Ref<boolean> - Search in progress
 *   - error: Ref<string | null> - Error message if any
 *   - hasResults: ComputedRef<boolean> - true if results.length > 0
 *   - isEmpty: ComputedRef<boolean> - true if no results and query was entered
 *   - lastSearchConcept: Ref<string> - Last searched concept (for tracking)
 *   - search: Function - Perform search with optional filters/pagination
 *   - nextPage: Function - Navigate to next page
 *   - previousPage: Function - Navigate to previous page
 *   - goToPage: Function - Navigate to specific page
 *   - clearResults: Function - Clear all results and reset state
 *   - clearError: Function - Clear error message
 */
export function usePatientSearch() {
  // ============================================================================
  // STATE
  // ============================================================================

  /**
   * Array of search results for current page
   * @type {Ref<PatientSearchResult[]>}
   */
  const results = ref<PatientSearchResult[]>([])

  /**
   * Total number of results matching query (may be > results.length)
   * @type {Ref<number>}
   */
  const total = ref(0)

  /**
   * Current page number (1-indexed, not 0-indexed)
   * @type {Ref<number>}
   */
  const page = ref(1)

  /**
   * Number of results per page (default 20, max typically 100)
   * @type {Ref<number>}
   */
  const pageSize = ref(20)

  /**
   * Time taken for search API to respond in milliseconds
   * Used for performance monitoring
   * @type {Ref<number>}
   */
  const queryTimeMs = ref(0)

  /**
   * Whether a search is currently in progress
   * @type {Ref<boolean>}
   */
  const isLoading = ref(false)

  /**
   * Error message from last search, or null if no error
   * Set on API failures, validation errors, network issues
   * @type {Ref<string | null>}
   */
  const error = ref<string | null>(null)

  /**
   * The last concept that was searched for
   * Used for tracking and analytics
   * @type {Ref<string>}
   */
  const lastSearchConcept = ref<string>('')

  // ============================================================================
  // COMPUTED PROPERTIES
  // ============================================================================

  /**
   * Number of pages based on total results and page size
   * Formula: Math.ceil(total / pageSize)
   * @type {ComputedRef<number>}
   */
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

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
  const isEmpty = computed(() => !isLoading.value && results.value.length === 0 && lastSearchConcept.value !== '')

  // ============================================================================
  // METHODS
  // ============================================================================

  /**
   * Perform a search with optional filters and pagination
   *
   * Side effects:
   * - Sets isLoading = true while fetching
   * - Updates results, total, page, pageSize, queryTimeMs
   * - Clears error on success, sets error on failure
   * - Sets lastSearchConcept for tracking
   *
   * @param {string} concept - Medical concept to search (required)
   *   Examples: "diabetes", "heart failure", "hypertension"
   *
   * @param {SearchFilters} [filters] - Meta-annotation filters (optional)
   *   Filters results by clinical context:
   *   - Negation: 'Affirmed' | 'Negated' - Patient has condition or not
   *   - Experiencer: 'Patient' | 'Family' | 'Other' - Who has the condition
   *   - Temporality: 'Current' | 'Recent' | 'Historical' | 'Future' - When
   *   - Certainty: 'Certain' | 'Possible' | 'Hypothetical' - How certain
   *
   * @param {number} [pageNum=1] - Page number to fetch (1-indexed)
   *
   * @param {number} [size=20] - Results per page
   *   Typical values: 10, 20, 50, 100
   *   Higher values = slower response but fewer page requests
   *
   * @returns {Promise<void>} Resolves when search completes
   *
   * @throws {Error} If concept is empty string or contains invalid characters
   *
   * @example
   * // Simple search
   * await search('diabetes')
   *
   * @example
   * // Search with filters
   * await search('diabetes', {
   *   Negation: 'Affirmed',           // Patient has it
   *   Experiencer: 'Patient',         // Not family history
   *   Temporality: 'Current'          // Active condition
   * })
   *
   * @example
   * // Search with pagination
   * await search('diabetes', {}, 2, 50)
   * // Page 2, 50 results per page
   */
  const search = async (
    concept: string,
    filters?: SearchFilters,
    pageNum: number = 1,
    size: number = 20
  ) => {
    // Validation
    if (!concept || concept.trim() === '') {
      error.value = 'Please enter a concept to search'
      return
    }

    // State setup
    isLoading.value = true
    error.value = null
    lastSearchConcept.value = concept

    try {
      // Build request
      const request: PatientSearchRequest = {
        concept: concept.trim(),
        filters: filters || {},
        pagination: {
          page: pageNum,
          pageSize: size,
        },
        sort: 'relevance',
      }

      // Perform search
      const response = await searchPatients(request)

      // Update state
      results.value = response.results
      total.value = response.pagination.totalResults
      page.value = pageNum
      pageSize.value = size
      queryTimeMs.value = response.performance.searchTime

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
   * Navigate to the next page of results
   *
   * Only works if current page < total pages
   * Automatically refetches with same query and filters
   *
   * @param {string} concept - The search concept (required)
   * @param {SearchFilters} [filters] - Meta-annotation filters (optional)
   *
   * @returns {Promise<void>} Resolves when next page loaded
   *
   * @example
   * if (page.value < totalPages.value) {
   *   await nextPage('diabetes')
   * }
   *
   * @see search - For detailed parameter documentation
   */
  const nextPage = async (concept: string, filters?: SearchFilters) => {
    if (page.value < totalPages.value) {
      await search(concept, filters, page.value + 1, pageSize.value)
    }
  }

  /**
   * Navigate to the previous page of results
   *
   * Only works if current page > 1
   * Automatically refetches with same query and filters
   *
   * @param {string} concept - The search concept (required)
   * @param {SearchFilters} [filters] - Meta-annotation filters (optional)
   *
   * @returns {Promise<void>} Resolves when previous page loaded
   *
   * @example
   * if (page.value > 1) {
   *   await previousPage('diabetes')
   * }
   *
   * @see search - For detailed parameter documentation
   */
  const previousPage = async (concept: string, filters?: SearchFilters) => {
    if (page.value > 1) {
      await search(concept, filters, page.value - 1, pageSize.value)
    }
  }

  /**
   * Navigate to a specific page number
   *
   * Only works if targetPage is between 1 and totalPages
   * Automatically refetches with same query and filters
   *
   * @param {string} concept - The search concept (required)
   * @param {SearchFilters | undefined} filters - Meta-annotation filters (required but can be undefined)
   * @param {number} targetPage - The page to navigate to (1-indexed)
   *
   * @returns {Promise<void>} Resolves when page loaded
   *
   * @example
   * await goToPage('diabetes', undefined, 5)
   * // Jump to page 5
   *
   * @example
   * await goToPage('diabetes', { Negation: 'Affirmed' }, 3)
   * // Jump to page 3 with filters applied
   *
   * @see search - For detailed parameter documentation
   */
  const goToPage = async (concept: string, filters: SearchFilters | undefined, targetPage: number) => {
    if (targetPage >= 1 && targetPage <= totalPages.value) {
      await search(concept, filters, targetPage, pageSize.value)
    }
  }

  /**
   * Clear all search results and reset state
   *
   * Resets:
   * - results = []
   * - total = 0
   * - page = 1
   * - queryTimeMs = 0
   * - error = null
   * - lastSearchConcept = ''
   *
   * Use when:
   * - User navigates away from search page
   * - Clearing search on component unmount
   * - Resetting search form
   *
   * @returns {void}
   *
   * @example
   * onUnmounted(() => {
   *   clearResults()
   * })
   *
   * @example
   * const handleClearSearch = () => {
   *   clearResults()
   * }
   */
  const clearResults = () => {
    results.value = []
    total.value = 0
    page.value = 1
    queryTimeMs.value = 0
    error.value = null
    lastSearchConcept.value = ''
  }

  /**
   * Clear the error message
   *
   * Use when:
   * - User dismisses error alert
   * - Attempting search retry after error
   * - Clearing error state on new search
   *
   * Note: Errors are automatically cleared on successful search
   * Only call this when user explicitly dismisses error UI
   *
   * @returns {void}
   *
   * @example
   * const handleDismissError = () => {
   *   clearError()
   * }
   */
  const clearError = () => {
    error.value = null
  }

  // ============================================================================
  // RETURN PUBLIC API
  // ============================================================================

  return {
    // State
    results,
    total,
    page,
    pageSize,
    totalPages,
    queryTimeMs,
    isLoading,
    error,
    hasResults,
    isEmpty,
    lastSearchConcept,

    // Actions
    search,
    nextPage,
    previousPage,
    goToPage,
    clearResults,
    clearError,
  }
}
