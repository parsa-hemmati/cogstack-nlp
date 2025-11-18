/**
 * Timeline API endpoints
 */

import type { TimelineResponse, TimelineFilters } from '@/types/timeline'
import apiClient from './client'

export const timelineApi = {
  /**
   * Fetch patient timeline data
   */
  async getTimeline(
    patientId: string,
    filters?: TimelineFilters
  ): Promise<TimelineResponse> {
    const params: Record<string, any> = {}

    if (filters) {
      if (filters.startDate) params.start_date = filters.startDate
      if (filters.endDate) params.end_date = filters.endDate
      if (filters.documentTypes && filters.documentTypes.length > 0) {
        params.document_types = filters.documentTypes.join(',')
      }
      if (filters.conceptTypes && filters.conceptTypes.length > 0) {
        params.concept_types = filters.conceptTypes.join(',')
      }
      if (filters.includeNegated !== undefined) {
        params.include_negated = filters.includeNegated
      }
      if (filters.includeFamily !== undefined) {
        params.include_family = filters.includeFamily
      }
    }

    const response = await apiClient.get<TimelineResponse>(
      `/v1/timeline/${patientId}`,
      { params }
    )
    return response.data
  },

  /**
   * Get concept occurrences for detailed view
   */
  async getConceptOccurrences(
    patientId: string,
    conceptCui: string
  ): Promise<any> {
    const response = await apiClient.get(
      `/v1/timeline/${patientId}/concepts/${conceptCui}`
    )
    return response.data
  },

  /**
   * Export timeline to specified format
   */
  async exportTimeline(
    patientId: string,
    format: 'pdf' | 'json' | 'fhir',
    filters?: TimelineFilters
  ): Promise<Blob> {
    const params: Record<string, any> = { format }

    if (filters) {
      if (filters.startDate) params.start_date = filters.startDate
      if (filters.endDate) params.end_date = filters.endDate
      if (filters.documentTypes && filters.documentTypes.length > 0) {
        params.document_types = filters.documentTypes.join(',')
      }
      if (filters.conceptTypes && filters.conceptTypes.length > 0) {
        params.concept_types = filters.conceptTypes.join(',')
      }
      if (filters.includeNegated !== undefined) {
        params.include_negated = filters.includeNegated
      }
      if (filters.includeFamily !== undefined) {
        params.include_family = filters.includeFamily
      }
    }

    const response = await apiClient.post(
      `/v1/timeline/${patientId}/export`,
      {},
      {
        params,
        responseType: 'blob',
      }
    )
    return response.data
  },
}
