/**
 * Timeline Filters Composable
 *
 * Manages timeline filter state, URL synchronization, and API integration.
 * Provides reactive filter management for concept, date, meta-annotation,
 * and document type filtering.
 */

import { ref, computed, watch, type Ref } from 'vue'
import { useRouter, useRoute, type LocationQuery } from 'vue-router'
import type { PatientTimeline } from '@/types/timeline'
import { timelineApi } from '@/api/timeline'

/**
 * Timeline filter configuration
 */
export interface TimelineFilters {
  /** List of SNOMED-CT CUIs to filter by */
  conceptCuis: string[]
  /** Start date for timeline (ISO 8601) */
  dateFrom: Date | null
  /** End date for timeline (ISO 8601) */
  dateTo: Date | null
  /** Meta-annotation filters (Negation, Experiencer, Temporality, Certainty) */
  metaAnnotations: Record<string, string | string[]>
  /** Document types to include */
  documentTypes: string[]
  /** Include document markers in timeline */
  includeDocuments: boolean
  /** Include concept markers in timeline */
  includeConcepts: boolean
}

/**
 * Default meta-annotation filters (safe for clinical use)
 * - Excludes negated conditions (e.g., "patient denies chest pain")
 * - Excludes family history (e.g., "family history of diabetes")
 * - Excludes historical conditions (e.g., "past history of asthma")
 */
const DEFAULT_META_ANNOTATIONS: Record<string, string | string[]> = {
  Negation: 'Affirmed',
  Experiencer: 'Patient',
  Temporality: ['Current', 'Recent']
}

/**
 * Composable for managing timeline filters
 *
 * @param patientId - Patient ID to filter timeline for
 * @returns Timeline filter state and methods
 */
export function useTimelineFilters(patientId: Ref<string | null>) {
  const router = useRouter()
  const route = useRoute()

  // Filter state
  const filters = ref<TimelineFilters>({
    conceptCuis: [],
    dateFrom: null,
    dateTo: null,
    metaAnnotations: { ...DEFAULT_META_ANNOTATIONS },
    documentTypes: [],
    includeDocuments: true,
    includeConcepts: true
  })

  // API state
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const timeline = ref<PatientTimeline | null>(null)

  /**
   * Check if any filters are active (non-default)
   */
  const hasActiveFilters = computed(() => {
    return (
      filters.value.conceptCuis.length > 0 ||
      filters.value.dateFrom !== null ||
      filters.value.dateTo !== null ||
      filters.value.documentTypes.length > 0 ||
      // Check if meta-annotations differ from defaults
      JSON.stringify(filters.value.metaAnnotations) !== JSON.stringify(DEFAULT_META_ANNOTATIONS)
    )
  })

  /**
   * Count of active filters
   */
  const activeFilterCount = computed(() => {
    let count = 0
    if (filters.value.conceptCuis.length > 0) count++
    if (filters.value.dateFrom || filters.value.dateTo) count++
    if (filters.value.documentTypes.length > 0) count++
    if (JSON.stringify(filters.value.metaAnnotations) !== JSON.stringify(DEFAULT_META_ANNOTATIONS)) {
      count++
    }
    return count
  })

  /**
   * Set concept filter (add or remove concepts)
   */
  function setConceptFilter(cuis: string[]) {
    filters.value.conceptCuis = [...cuis]
  }

  /**
   * Add a concept to the filter
   */
  function addConcept(cui: string) {
    if (!filters.value.conceptCuis.includes(cui)) {
      filters.value.conceptCuis.push(cui)
    }
  }

  /**
   * Remove a concept from the filter
   */
  function removeConcept(cui: string) {
    filters.value.conceptCuis = filters.value.conceptCuis.filter(c => c !== cui)
  }

  /**
   * Set date range filter
   */
  function setDateRange(from: Date | null, to: Date | null) {
    filters.value.dateFrom = from
    filters.value.dateTo = to
  }

  /**
   * Set meta-annotation filter
   * @param key - Meta-annotation key (Negation, Experiencer, Temporality, Certainty)
   * @param value - Single value or array of values (for OR logic)
   */
  function setMetaAnnotationFilter(key: string, value: string | string[]) {
    filters.value.metaAnnotations[key] = value
  }

  /**
   * Set document type filter
   */
  function setDocumentTypeFilter(types: string[]) {
    filters.value.documentTypes = [...types]
  }

  /**
   * Clear all filters (reset to defaults)
   */
  function clearFilters() {
    filters.value = {
      conceptCuis: [],
      dateFrom: null,
      dateTo: null,
      metaAnnotations: { ...DEFAULT_META_ANNOTATIONS },
      documentTypes: [],
      includeDocuments: true,
      includeConcepts: true
    }
    syncFiltersToURL()
  }

  /**
   * Apply filters and fetch timeline
   */
  async function applyFilters() {
    if (!patientId.value) {
      error.value = 'Patient ID is required'
      return
    }

    isLoading.value = true
    error.value = null

    try {
      // Sync filters to URL (shareable link)
      syncFiltersToURL()

      // Fetch timeline with filters
      const result = await timelineApi.getPatientTimeline(patientId.value, filters.value)
      timeline.value = result
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch timeline'
      console.error('Timeline filter error:', err)
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Serialize filters to URL query params
   */
  function serializeFilters(): LocationQuery {
    const query: LocationQuery = {}

    if (filters.value.conceptCuis.length > 0) {
      query.concepts = filters.value.conceptCuis.join(',')
    }

    if (filters.value.dateFrom) {
      query.from = filters.value.dateFrom.toISOString().split('T')[0] // YYYY-MM-DD
    }

    if (filters.value.dateTo) {
      query.to = filters.value.dateTo.toISOString().split('T')[0] // YYYY-MM-DD
    }

    // Serialize meta-annotations
    for (const [key, value] of Object.entries(filters.value.metaAnnotations)) {
      const paramKey = `meta_${key.toLowerCase()}`
      if (Array.isArray(value)) {
        query[paramKey] = value.join(',')
      } else {
        query[paramKey] = value
      }
    }

    if (filters.value.documentTypes.length > 0) {
      query.types = filters.value.documentTypes.join(',')
    }

    return query
  }

  /**
   * Deserialize URL query params to filters
   */
  function deserializeFilters(query: LocationQuery) {
    const newFilters: TimelineFilters = {
      conceptCuis: [],
      dateFrom: null,
      dateTo: null,
      metaAnnotations: { ...DEFAULT_META_ANNOTATIONS },
      documentTypes: [],
      includeDocuments: true,
      includeConcepts: true
    }

    // Parse concepts
    if (query.concepts && typeof query.concepts === 'string') {
      newFilters.conceptCuis = query.concepts.split(',').filter(Boolean)
    }

    // Parse date range
    if (query.from && typeof query.from === 'string') {
      try {
        newFilters.dateFrom = new Date(query.from)
      } catch {
        console.warn('Invalid date_from in URL:', query.from)
      }
    }

    if (query.to && typeof query.to === 'string') {
      try {
        newFilters.dateTo = new Date(query.to)
      } catch {
        console.warn('Invalid date_to in URL:', query.to)
      }
    }

    // Parse meta-annotations
    const metaKeys = ['negation', 'experiencer', 'temporality', 'certainty']
    for (const metaKey of metaKeys) {
      const paramKey = `meta_${metaKey}`
      const capitalizedKey = metaKey.charAt(0).toUpperCase() + metaKey.slice(1)

      if (query[paramKey] && typeof query[paramKey] === 'string') {
        const value = query[paramKey] as string
        if (value.includes(',')) {
          // Array value
          newFilters.metaAnnotations[capitalizedKey] = value.split(',').filter(Boolean)
        } else {
          // Single value
          newFilters.metaAnnotations[capitalizedKey] = value
        }
      }
    }

    // Parse document types
    if (query.types && typeof query.types === 'string') {
      newFilters.documentTypes = query.types.split(',').filter(Boolean)
    }

    filters.value = newFilters
  }

  /**
   * Sync filters to URL query params
   */
  function syncFiltersToURL() {
    const query = serializeFilters()
    router.push({ query }).catch(() => {
      // Ignore navigation duplicated errors
    })
  }

  /**
   * Load filters from URL on mount
   */
  function loadFiltersFromURL() {
    if (route.query && Object.keys(route.query).length > 0) {
      deserializeFilters(route.query)
    }
  }

  // Watch for patient ID changes and reload
  watch(patientId, (newId) => {
    if (newId) {
      loadFiltersFromURL()
      applyFilters()
    }
  })

  // Initialize filters from URL on mount
  loadFiltersFromURL()

  return {
    // State
    filters,
    isLoading,
    error,
    timeline,

    // Computed
    hasActiveFilters,
    activeFilterCount,

    // Methods
    setConceptFilter,
    addConcept,
    removeConcept,
    setDateRange,
    setMetaAnnotationFilter,
    setDocumentTypeFilter,
    clearFilters,
    applyFilters,
    syncFiltersToURL,
    loadFiltersFromURL
  }
}
