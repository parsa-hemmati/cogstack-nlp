/**
 * Timeline API client.
 *
 * Provides timeline data retrieval for patient clinical history visualization.
 */
import api from './api'
import type { PatientTimeline, TimelineFilters } from '@/types/timeline'

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
