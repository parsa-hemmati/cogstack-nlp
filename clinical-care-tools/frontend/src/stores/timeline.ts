/**
 * Timeline Store
 *
 * Pinia store for patient timeline functionality.
 * Manages timeline data, concept details, exports, and filter presets.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import type {
  PatientTimeline,
  TimelineConcept,
  TimelineFilters,
  ExportRequest,
  TimelineExportResponse,
  FilterPresetRequest,
  FilterPresetResponse,
} from '@/types/timeline'

export const useTimelineStore = defineStore('timeline', () => {
  // State
  const timeline = ref<PatientTimeline | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const filterPresets = ref<FilterPresetResponse[]>([])

  // Getters
  const hasTimeline = computed(() => timeline.value !== null)
  const documentCount = computed(() => timeline.value?.documents.length || 0)
  const conceptCount = computed(() => timeline.value?.concepts.length || 0)

  // Actions

  /**
   * Fetch patient timeline with optional filters
   */
  async function fetchTimeline(
    patientId: string,
    filters?: TimelineFilters
  ): Promise<PatientTimeline> {
    loading.value = true
    error.value = null

    try {
      const params: Record<string, any> = {}

      if (filters) {
        if (filters.date_start) params.date_start = filters.date_start
        if (filters.date_end) params.date_end = filters.date_end
        if (filters.concept_cuis && filters.concept_cuis.length > 0) {
          params.concept_cuis = filters.concept_cuis
        }
        if (filters.document_types && filters.document_types.length > 0) {
          params.document_types = filters.document_types
        }
        if (filters.negation) params.negation = filters.negation
        if (filters.experiencer) params.experiencer = filters.experiencer
        if (filters.temporality) params.temporality = filters.temporality
        if (filters.certainty) params.certainty = filters.certainty
      }

      const response = await axios.get<PatientTimeline>(
        `/api/v1/timeline/${patientId}`,
        { params }
      )

      timeline.value = response.data
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch timeline'
      error.value = errorMessage
      timeline.value = null
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch detailed information about a specific concept
   */
  async function fetchConceptDetails(
    patientId: string,
    conceptCui: string,
    filters?: TimelineFilters
  ): Promise<TimelineConcept> {
    loading.value = true
    error.value = null

    try {
      const params: Record<string, any> = {}

      if (filters) {
        if (filters.date_start) params.date_start = filters.date_start
        if (filters.date_end) params.date_end = filters.date_end
      }

      const response = await axios.get<TimelineConcept>(
        `/api/v1/timeline/${patientId}/concepts/${conceptCui}`,
        { params }
      )

      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to fetch concept details'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create timeline export (PDF, FHIR, or JSON)
   */
  async function exportTimeline(
    patientId: string,
    request: ExportRequest
  ): Promise<TimelineExportResponse> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post<TimelineExportResponse>(
        `/api/v1/timeline/${patientId}/export`,
        request
      )

      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create export'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Get export status
   */
  async function getExportStatus(exportId: string): Promise<TimelineExportResponse> {
    try {
      const response = await axios.get<TimelineExportResponse>(
        `/api/v1/timeline/exports/${exportId}`
      )

      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to get export status'
      error.value = errorMessage
      throw err
    }
  }

  /**
   * Download completed export file
   */
  async function downloadExport(exportId: string, format: string): Promise<void> {
    try {
      const response = await axios.get(
        `/api/v1/timeline/exports/${exportId}/download`,
        {
          responseType: 'blob',
        }
      )

      // Create download link
      const url = window.URL.createObjectURL(response.data)
      const link = document.createElement('a')
      link.href = url

      // Set filename based on format
      const extension = format === 'fhir' ? 'json' : format
      link.download = `timeline_export_${exportId}.${extension}`

      // Trigger download
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to download export'
      error.value = errorMessage
      throw err
    }
  }

  /**
   * Save a filter preset
   */
  async function saveFilterPreset(
    request: FilterPresetRequest
  ): Promise<FilterPresetResponse> {
    loading.value = true
    error.value = null

    try {
      const response = await axios.post<FilterPresetResponse>(
        '/api/v1/timeline/filters',
        request
      )

      // Add to filter presets
      filterPresets.value.push(response.data)

      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to save filter preset'
      error.value = errorMessage
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load filter presets
   */
  async function loadFilterPresets(): Promise<FilterPresetResponse[]> {
    try {
      const response = await axios.get<FilterPresetResponse[]>(
        '/api/v1/timeline/filters'
      )

      filterPresets.value = response.data
      return response.data
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to load filter presets'
      error.value = errorMessage
      throw err
    }
  }

  /**
   * Clear timeline data
   */
  function clearTimeline() {
    timeline.value = null
    error.value = null
  }

  return {
    // State
    timeline,
    loading,
    error,
    filterPresets,

    // Getters
    hasTimeline,
    documentCount,
    conceptCount,

    // Actions
    fetchTimeline,
    fetchConceptDetails,
    exportTimeline,
    getExportStatus,
    downloadExport,
    saveFilterPreset,
    loadFilterPresets,
    clearTimeline,
  }
})
