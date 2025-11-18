/**
 * Patient Search Composable.
 *
 * Provides reusable search logic for patient search component.
 * Manages search state, API calls, loading/error states.
 *
 * @example
 * ```typescript
 * const { results, total, isLoading, error, search, clearResults } = usePatientSearch()
 *
 * await search('diabetes', { includeNegated: false }, 1, 20)
 * // total.value contains patient count
 * ```
 */
import { ref, computed } from 'vue'
import { searchPatients, type PatientSearchRequest, type PatientSearchResult, type SearchFilters } from '@/api/patientSearch'

export function usePatientSearch() {
  // State
  const results = ref<PatientSearchResult[]>([])
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)
  const queryTimeMs = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const lastSearchConcept = ref<string>('')

  // Computed
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))
  const hasResults = computed(() => results.value.length > 0)
  const isEmpty = computed(() => !isLoading.value && results.value.length === 0 && lastSearchConcept.value !== '')

  /**
   * Perform patient search.
   *
   * @param concept - Medical concept to search for
   * @param filters - Meta-annotation filters
   * @param pageNum - Page number (default: 1)
   * @param size - Results per page (default: 20)
   */
  const search = async (
    concept: string,
    filters?: SearchFilters,
    pageNum: number = 1,
    size: number = 20
  ) => {
    if (!concept || concept.trim() === '') {
      error.value = 'Please enter a concept to search'
      return
    }

    isLoading.value = true
    error.value = null
    lastSearchConcept.value = concept

    try {
      const request: PatientSearchRequest = {
        concept: concept.trim(),
        filters: filters || {},
        pagination: {
          page: pageNum,
          pageSize: size,
        },
        sort: 'relevance',
      }

      const response = await searchPatients(request)

      results.value = response.results
      total.value = response.pagination.totalResults
      page.value = pageNum
      pageSize.value = size
      queryTimeMs.value = response.performance.searchTime

    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Search failed. Please try again.'
      results.value = []
      total.value = 0
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Search next page (pagination).
   */
  const nextPage = async (concept: string, filters?: SearchFilters) => {
    if (page.value < totalPages.value) {
      await search(concept, filters, page.value + 1, pageSize.value)
    }
  }

  /**
   * Search previous page (pagination).
   */
  const previousPage = async (concept: string, filters?: SearchFilters) => {
    if (page.value > 1) {
      await search(concept, filters, page.value - 1, pageSize.value)
    }
  }

  /**
   * Go to specific page (pagination).
   */
  const goToPage = async (concept: string, filters: SearchFilters | undefined, targetPage: number) => {
    if (targetPage >= 1 && targetPage <= totalPages.value) {
      await search(concept, filters, targetPage, pageSize.value)
    }
  }

  /**
   * Clear search results.
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
   * Reset error state.
   */
  const clearError = () => {
    error.value = null
  }

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
