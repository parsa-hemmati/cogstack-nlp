/**
 * Timeline API client.
 *
 * Provides timeline data retrieval for patient clinical history visualization
 * and filter preset management.
 */
import api from './api'
import type { PatientTimeline, TimelineFilters } from '@/types/timeline'

/**
 * Filter preset response from API.
 */
export interface FilterPreset {
  id: string
  user_id: string
  name: string
  filters: Record<string, any>
  is_default: boolean
  created_at: string
  updated_at: string
}

/**
 * Filter preset list response from API.
 */
export interface FilterPresetListResponse {
  presets: FilterPreset[]
  total: number
}

/**
 * Create filter preset request.
 */
export interface CreateFilterPresetRequest {
  name: string
  filters: Record<string, any>
  is_default?: boolean
}

/**
 * Update filter preset request.
 */
export interface UpdateFilterPresetRequest {
  name?: string
  filters?: Record<string, any>
  is_default?: boolean
}

/**
 * Get patient timeline with documents and clinical concepts.
 *
 * Retrieves chronological timeline of patient documents and aggregated
 * clinical concepts with meta-annotation filtering.
 *
 * @param patientId - Patient UUID
 * @param filters - Optional timeline filters (concepts, date_range, meta_annotations, document_types)
 * @returns Complete patient timeline with documents and concepts
 *
 * @example
 * // Basic timeline (all data, safe defaults)
 * const timeline = await getPatientTimeline('patient-uuid-123')
 *
 * @example
 * // Timeline filtered by concept and date range
 * const timeline = await getPatientTimeline('patient-uuid-123', {
 *   concepts: ['C0011849'],  // Diabetes Mellitus
 *   dateRange: {
 *     start: new Date('2023-01-01'),
 *     end: new Date('2023-12-31')
 *   }
 * })
 *
 * @example
 * // Timeline including historical conditions
 * const timeline = await getPatientTimeline('patient-uuid-123', {
 *   metaAnnotations: {
 *     Temporality: ['Current', 'Recent', 'Historical']
 *   }
 * })
 */
export async function getPatientTimeline(
  patientId: string,
  filters?: TimelineFilters
): Promise<PatientTimeline> {
  const params = new URLSearchParams()

  if (filters) {
    // Concept filter (comma-separated CUIs)
    if (filters.concepts && filters.concepts.length > 0) {
      params.append('concepts', filters.concepts.join(','))
    }

    // Date range filter
    if (filters.dateRange) {
      params.append('date_start', filters.dateRange.start.toISOString())
      params.append('date_end', filters.dateRange.end.toISOString())
    }

    // Meta-annotation filters
    if (filters.metaAnnotations) {
      if (filters.metaAnnotations.Negation) {
        params.append('meta_negation', filters.metaAnnotations.Negation)
      }
      if (filters.metaAnnotations.Experiencer) {
        params.append('meta_experiencer', filters.metaAnnotations.Experiencer)
      }
      if (filters.metaAnnotations.Temporality) {
        // Handle both single value and array
        const temporality = Array.isArray(filters.metaAnnotations.Temporality)
          ? filters.metaAnnotations.Temporality
          : [filters.metaAnnotations.Temporality]
        params.append('meta_temporality', temporality.join(','))
      }
      if (filters.metaAnnotations.Certainty) {
        params.append('meta_certainty', filters.metaAnnotations.Certainty)
      }
    }

    // Document types filter (comma-separated)
    if (filters.documentTypes && filters.documentTypes.length > 0) {
      params.append('document_types', filters.documentTypes.join(','))
    }
  }

  const queryString = params.toString()
  const url = queryString
    ? `/api/v1/timeline/${patientId}?${queryString}`
    : `/api/v1/timeline/${patientId}`

  const response = await api.get<PatientTimeline>(url)

  return response.data
}

/**
 * Get all filter presets for the current user.
 *
 * Fetches user's saved filter configurations ordered by:
 * 1. Default presets first (is_default=True)
 * 2. Then by creation date (newest first)
 *
 * @returns List of user's filter presets
 *
 * @example
 * const { presets, total } = await getFilterPresets()
 * console.log(`Found ${total} saved presets`)
 */
export async function getFilterPresets(): Promise<FilterPresetListResponse> {
  const response = await api.get<FilterPresetListResponse>('/api/v1/timeline/filters')
  return response.data
}

/**
 * Create a new filter preset.
 *
 * Saves the current filter configuration with a user-provided name.
 * If is_default=true, automatically un-sets other default presets.
 *
 * @param data - Preset name, filters, and optional default flag
 * @returns Created preset with ID and timestamps
 *
 * @example
 * const preset = await createFilterPreset({
 *   name: 'Diabetes Management',
 *   filters: {
 *     concept_cuis: ['C0011849'],
 *     meta_annotations: { Negation: 'Affirmed' }
 *   },
 *   is_default: true
 * })
 */
export async function createFilterPreset(
  data: CreateFilterPresetRequest
): Promise<FilterPreset> {
  const response = await api.post<FilterPreset>('/api/v1/timeline/filters', data)
  return response.data
}

/**
 * Update an existing filter preset.
 *
 * Updates preset name, filters, or default status.
 * If is_default=true, automatically un-sets other default presets.
 *
 * @param id - Preset UUID
 * @param data - Fields to update (all optional)
 * @returns Updated preset
 *
 * @example
 * const updated = await updateFilterPreset('preset-uuid-123', {
 *   name: 'Diabetes & Hypertension'
 * })
 */
export async function updateFilterPreset(
  id: string,
  data: UpdateFilterPresetRequest
): Promise<FilterPreset> {
  const response = await api.put<FilterPreset>(`/api/v1/timeline/filters/${id}`, data)
  return response.data
}

/**
 * Delete a filter preset.
 *
 * Permanently removes a saved filter configuration.
 *
 * @param id - Preset UUID
 *
 * @example
 * await deleteFilterPreset('preset-uuid-123')
 */
export async function deleteFilterPreset(id: string): Promise<void> {
  await api.delete(`/api/v1/timeline/filters/${id}`)
}
