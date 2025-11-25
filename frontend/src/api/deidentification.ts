/**
 * De-identification API Client
 *
 * Provides functions to interact with de-identification endpoints
 */
import api from './api'
import type {
  DeidentifyRequest,
  DeidentifyResponse,
  BatchDeidentifyRequest,
  BatchDeidentifyResponse,
  DeidentificationJobStatus,
  DeidentifiedNoteResult,
  DownloadFormat
} from '@/types/deidentification'

/**
 * De-identify a single clinical note
 *
 * @param request - De-identification request
 * @returns De-identified text and detected entities
 *
 * @example
 * ```typescript
 * const result = await deidentifySingleNote({
 *   text: "Patient John Doe was admitted on 01/15/2024",
 *   method: DeidentificationMethod.REPLACEMENT,
 *   return_entities: true
 * })
 * console.log(result.deidentified_text) // "Patient [NAME] was admitted on [DATE]"
 * ```
 */
export async function deidentifySingleNote(
  request: DeidentifyRequest
): Promise<DeidentifyResponse> {
  const response = await api.post<DeidentifyResponse>(
    '/deidentify',
    request
  )
  return response.data
}

/**
 * Submit batch of notes for de-identification
 *
 * Creates a background job and returns job ID for tracking
 *
 * @param request - Batch de-identification request
 * @returns Job information including job_id and status
 *
 * @example
 * ```typescript
 * const job = await deidentifyBatch({
 *   notes: [
 *     { id: 'note1', text: 'Clinical text...' },
 *     { id: 'note2', text: 'More clinical text...' }
 *   ],
 *   method: DeidentificationMethod.REMOVAL,
 *   notify_email: 'researcher@example.com'
 * })
 * console.log(`Job created: ${job.job_id}`)
 * ```
 */
export async function deidentifyBatch(
  request: BatchDeidentifyRequest
): Promise<BatchDeidentifyResponse> {
  const response = await api.post<BatchDeidentifyResponse>(
    '/deidentify/batch',
    request
  )
  return response.data
}

/**
 * Upload CSV file for batch de-identification
 *
 * @param file - CSV file containing notes
 * @param method - De-identification method
 * @param notifyEmail - Optional email for completion notification
 * @returns Job information
 *
 * @example
 * ```typescript
 * const file = fileInput.files[0]
 * const job = await uploadCSVForDeidentification(
 *   file,
 *   DeidentificationMethod.REPLACEMENT,
 *   'researcher@example.com'
 * )
 * ```
 */
export async function uploadCSVForDeidentification(
  file: File,
  method: string,
  notifyEmail?: string
): Promise<BatchDeidentifyResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('method', method)
  if (notifyEmail) {
    formData.append('notify_email', notifyEmail)
  }

  const response = await api.post<BatchDeidentifyResponse>(
    '/deidentify/batch',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    }
  )
  return response.data
}

/**
 * Get job status
 *
 * Polls job status to track progress
 *
 * @param jobId - Job UUID
 * @returns Job status including progress and errors
 *
 * @example
 * ```typescript
 * const status = await getJobStatus(jobId)
 * console.log(`Progress: ${status.progress_percentage}%`)
 * console.log(`Processed: ${status.processed_notes}/${status.total_notes}`)
 * ```
 */
export async function getJobStatus(
  jobId: string
): Promise<DeidentificationJobStatus> {
  const response = await api.get<DeidentificationJobStatus>(
    `/deidentify/job/${jobId}`
  )
  return response.data
}

/**
 * Cancel a running job
 *
 * @param jobId - Job UUID
 * @returns Cancellation confirmation
 *
 * @example
 * ```typescript
 * await cancelJob(jobId)
 * console.log('Job cancelled')
 * ```
 */
export async function cancelJob(jobId: string): Promise<void> {
  await api.post(`/deidentify/job/${jobId}/cancel`)
}

/**
 * Download de-identified results
 *
 * @param jobId - Job UUID
 * @param format - Download format (csv, json, txt)
 * @returns Blob for file download
 *
 * @example
 * ```typescript
 * const blob = await downloadResults(jobId, 'csv')
 * const url = window.URL.createObjectURL(blob)
 * const a = document.createElement('a')
 * a.href = url
 * a.download = `deidentified_${jobId}.csv`
 * a.click()
 * ```
 */
export async function downloadResults(
  jobId: string,
  format: DownloadFormat
): Promise<Blob> {
  const response = await api.get(
    `/deidentify/job/${jobId}/download`,
    {
      params: { format },
      responseType: 'blob'
    }
  )
  return response.data
}

/**
 * Get de-identified note results for review
 *
 * @param jobId - Job UUID
 * @param limit - Maximum results to return
 * @param offset - Results offset for pagination
 * @returns List of de-identified notes
 *
 * @example
 * ```typescript
 * const results = await getJobResults(jobId, 20, 0)
 * results.forEach(result => {
 *   console.log(`Note ${result.note_id}: ${result.confidence_score}`)
 * })
 * ```
 */
export async function getJobResults(
  jobId: string,
  limit: number = 20,
  offset: number = 0
): Promise<DeidentifiedNoteResult[]> {
  const response = await api.get<DeidentifiedNoteResult[]>(
    `/deidentify/job/${jobId}/results`,
    {
      params: { limit, offset }
    }
  )
  return response.data
}

/**
 * Download audit report (PDF)
 *
 * @param jobId - Job UUID
 * @returns PDF blob
 */
export async function downloadAuditReport(jobId: string): Promise<Blob> {
  const response = await api.get(
    `/deidentify/job/${jobId}/audit-report`,
    {
      responseType: 'blob'
    }
  )
  return response.data
}
