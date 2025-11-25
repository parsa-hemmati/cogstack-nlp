/**
 * Annotations API Client
 *
 * Functions to interact with manual annotation endpoints
 */
import api from './api'
import type {
  ManualAnnotation,
  CreateAnnotationRequest,
  JobSummary,
  JobAnalytics,
  JobFilters,
  ReRunRequest
} from '@/types/annotation'

/**
 * Create manual annotation
 *
 * @param request - Annotation details
 * @returns Created annotation
 */
export async function createAnnotation(
  request: CreateAnnotationRequest
): Promise<ManualAnnotation> {
  const response = await api.post<ManualAnnotation>(
    '/deidentify/annotations',
    request
  )
  return response.data
}

/**
 * Get annotations for a note
 *
 * @param noteId - Note UUID
 * @returns List of annotations
 */
export async function getAnnotations(
  noteId: string
): Promise<ManualAnnotation[]> {
  const response = await api.get<ManualAnnotation[]>(
    `/deidentify/annotations/${noteId}`
  )
  return response.data
}

/**
 * Delete annotation
 *
 * @param annotationId - Annotation UUID
 */
export async function deleteAnnotation(annotationId: string): Promise<void> {
  await api.delete(`/deidentify/annotations/${annotationId}`)
}

/**
 * Re-run de-identification with manual annotations
 *
 * @param request - Re-run request
 * @returns Job ID for reprocessing
 */
export async function reRunDeidentification(
  request: ReRunRequest
): Promise<{ job_id: string }> {
  const response = await api.post<{ job_id: string }>(
    '/deidentify/review',
    request
  )
  return response.data
}

/**
 * Get all jobs (with filters)
 *
 * @param filters - Filter options
 * @returns List of jobs
 */
export async function getAllJobs(
  filters?: JobFilters
): Promise<JobSummary[]> {
  const response = await api.get<JobSummary[]>(
    '/deidentify/jobs',
    { params: filters }
  )
  return response.data
}

/**
 * Delete job
 *
 * @param jobId - Job UUID
 */
export async function deleteJob(jobId: string): Promise<void> {
  await api.delete(`/deidentify/job/${jobId}`)
}

/**
 * Get job analytics
 *
 * @param dateFrom - Start date filter
 * @param dateTo - End date filter
 * @returns Analytics data
 */
export async function getJobAnalytics(
  dateFrom?: string,
  dateTo?: string
): Promise<JobAnalytics> {
  const response = await api.get<JobAnalytics>(
    '/deidentify/analytics',
    {
      params: {
        date_from: dateFrom,
        date_to: dateTo
      }
    }
  )
  return response.data
}

/**
 * Export analytics
 *
 * @param format - Export format (csv or pdf)
 * @param dateFrom - Start date filter
 * @param dateTo - End date filter
 * @returns Blob for download
 */
export async function exportAnalytics(
  format: 'csv' | 'pdf',
  dateFrom?: string,
  dateTo?: string
): Promise<Blob> {
  const response = await api.get(
    '/deidentify/analytics/export',
    {
      params: {
        format,
        date_from: dateFrom,
        date_to: dateTo
      },
      responseType: 'blob'
    }
  )
  return response.data
}
