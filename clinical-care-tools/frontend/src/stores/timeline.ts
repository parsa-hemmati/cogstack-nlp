/**
 * Timeline store using Pinia
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TimelineResponse, TimelineFilters } from '@/types/timeline'
import { timelineApi } from '@/api/timeline'

interface Patient {
  id: string
  mrn?: string
  firstName?: string
  lastName?: string
  dateOfBirth?: string
  gender?: string
}

export const useTimelineStore = defineStore('timeline', () => {
  // State
  const timelineData = ref<TimelineResponse | null>(null)
  const patient = ref<Patient | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const currentFilters = ref<TimelineFilters>({})

  // Getters
  const hasData = computed(() => !!timelineData.value)

  const documentCount = computed(
    () => timelineData.value?.documents?.length || 0
  )

  const conceptCount = computed(
    () => timelineData.value?.concepts?.length || 0
  )

  const dateRange = computed(() => {
    if (!timelineData.value?.dateRange) return null
    return {
      start: new Date(timelineData.value.dateRange.start),
      end: new Date(timelineData.value.dateRange.end),
    }
  })

  const filteredDocuments = computed(() => {
    if (!timelineData.value?.documents) return []
    return timelineData.value.documents
  })

  const filteredConcepts = computed(() => {
    if (!timelineData.value?.concepts) return []
    return timelineData.value.concepts
  })

  // Actions
  async function fetchTimeline(
    patientId: string,
    filters?: TimelineFilters
  ): Promise<void> {
    loading.value = true
    error.value = null

    try {
      const data = await timelineApi.getTimeline(patientId, filters)
      timelineData.value = data
      currentFilters.value = filters || {}

      // Set patient data if available
      patient.value = {
        id: data.patientId,
        // Additional patient data would come from the API response
        // For now, just set the ID
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to load timeline'
      timelineData.value = null
      console.error('Error fetching timeline:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function applyFilters(
    patientId: string,
    filters: TimelineFilters
  ): Promise<void> {
    currentFilters.value = filters
    await fetchTimeline(patientId, filters)
  }

  function clearFilters() {
    currentFilters.value = {}
  }

  function clearData() {
    timelineData.value = null
    patient.value = null
    error.value = null
    currentFilters.value = {}
  }

  return {
    // State
    timelineData,
    patient,
    loading,
    error,
    currentFilters,

    // Getters
    hasData,
    documentCount,
    conceptCount,
    dateRange,
    filteredDocuments,
    filteredConcepts,

    // Actions
    fetchTimeline,
    applyFilters,
    clearFilters,
    clearData,
  }
})
