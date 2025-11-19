/**
 * Timeline Composable.
 *
 * Provides reusable timeline logic for patient timeline visualization.
 * Manages timeline state, API calls, loading/error states, and filters.
 *
 * @example
 * ```typescript
 * const { timeline, isLoading, error, fetchTimeline, clearTimeline } = useTimeline()
 *
 * await fetchTimeline('patient-uuid', { concepts: ['C0011849'] })
 * // timeline.value contains documents and concepts
 * ```
 */
import { ref, computed, type Ref } from 'vue'
import { getPatientTimeline } from '@/api/timeline'
import type { PatientTimeline, TimelineFilters } from '@/types/timeline'

export function useTimeline() {
  // State
  const timeline: Ref<PatientTimeline | null> = ref(null)
  const isLoading = ref(false)
  const error: Ref<string | null> = ref(null)
  const lastPatientId = ref<string>('')

  // Computed
  const hasTimeline = computed(() => timeline.value !== null)
  const isEmpty = computed(() =>
    !isLoading.value &&
    timeline.value !== null &&
    timeline.value.documents.length === 0 &&
    timeline.value.concepts.length === 0
  )
  const documentCount = computed(() => timeline.value?.documents.length || 0)
  const conceptCount = computed(() => timeline.value?.concepts.length || 0)

  /**
   * Fetch patient timeline.
   *
   * @param patientId - Patient UUID
   * @param filters - Optional timeline filters (concepts, date_range, meta_annotations, document_types)
   *
   * @example
   * // Basic timeline (all data, safe defaults)
   * await fetchTimeline('patient-uuid-123')
   *
   * @example
   * // Timeline filtered by concept
   * await fetchTimeline('patient-uuid-123', { concepts: ['C0011849'] })
   *
   * @example
   * // Timeline with date range
   * await fetchTimeline('patient-uuid-123', {
   *   dateRange: {
   *     start: new Date('2023-01-01'),
   *     end: new Date('2023-12-31')
   *   }
   * })
   */
  const fetchTimeline = async (
    patientId: string,
    filters?: TimelineFilters
  ) => {
    if (!patientId || patientId.trim() === '') {
      error.value = 'Patient ID is required'
      return
    }

    isLoading.value = true
    error.value = null
    lastPatientId.value = patientId

    try {
      timeline.value = await getPatientTimeline(patientId, filters)
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to load timeline. Please try again.'
      timeline.value = null
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Refresh timeline (refetch with same filters).
   */
  const refreshTimeline = async () => {
    if (!lastPatientId.value) {
      error.value = 'No patient ID available for refresh'
      return
    }

    if (timeline.value) {
      // Refetch with same filters
      await fetchTimeline(lastPatientId.value, timeline.value.filtersApplied)
    } else {
      // Fetch without filters
      await fetchTimeline(lastPatientId.value)
    }
  }

  /**
   * Clear timeline data.
   */
  const clearTimeline = () => {
    timeline.value = null
    error.value = null
    lastPatientId.value = ''
  }

  /**
   * Clear error state.
   */
  const clearError = () => {
    error.value = null
  }

  return {
    // State
    timeline,
    isLoading,
    error,
    lastPatientId,

    // Computed
    hasTimeline,
    isEmpty,
    documentCount,
    conceptCount,

    // Actions
    fetchTimeline,
    refreshTimeline,
    clearTimeline,
    clearError,
  }
}
