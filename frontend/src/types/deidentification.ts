/**
 * De-identification Types
 *
 * Type definitions for de-identification API and UI components
 * Matches backend schemas from backend/app/schemas/deidentification_api.py
 */

/**
 * De-identification methods
 */
export enum DeidentificationMethod {
  REMOVAL = 'removal',
  REPLACEMENT = 'replacement',
  GENERALIZATION = 'generalization'
}

/**
 * Job status values
 */
export enum JobStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

/**
 * PHI entity types (18 HIPAA identifiers)
 */
export type PHIEntityType =
  | 'NAME'
  | 'LOCATION'
  | 'DATE'
  | 'AGE'
  | 'PHONE'
  | 'FAX'
  | 'EMAIL'
  | 'SSN'
  | 'MRN'
  | 'ACCOUNT'
  | 'LICENSE'
  | 'VEHICLE'
  | 'DEVICE'
  | 'URL'
  | 'IP'
  | 'BIOMETRIC'
  | 'PHOTO'
  | 'OTHER'

/**
 * PHI entity detected in text
 */
export interface PHIEntity {
  type: PHIEntityType
  text: string
  start: number
  end: number
  confidence: number
}

/**
 * Single note for batch upload
 */
export interface BatchNote {
  id: string
  text: string
}

/**
 * Request to de-identify a single note
 */
export interface DeidentifyRequest {
  text: string
  method: DeidentificationMethod
  return_entities?: boolean
}

/**
 * Response from single note de-identification
 */
export interface DeidentifyResponse {
  deidentified_text: string
  entities_removed: PHIEntity[]
  method_used: DeidentificationMethod
  confidence_score: number
  review_required: boolean
  processing_time_ms: number
}

/**
 * Request to de-identify a batch of notes
 */
export interface BatchDeidentifyRequest {
  notes: BatchNote[]
  method: DeidentificationMethod
  notify_email?: string
}

/**
 * Response from batch de-identification (job created)
 */
export interface BatchDeidentifyResponse {
  job_id: string
  status: JobStatus
  total_notes: number
  created_at: string
  estimated_completion: string
}

/**
 * Job status response
 */
export interface DeidentificationJobStatus {
  job_id: string
  status: JobStatus
  total_notes: number
  processed_notes: number
  progress_percentage: number
  created_at: string
  updated_at: string
  estimated_completion: string
  errors: Array<{
    note_id: string
    error: string
  }>
  error_count?: number
}

/**
 * De-identified note result
 */
export interface DeidentifiedNoteResult {
  job_id: string
  note_id: string
  deidentified_text: string
  entities_removed: PHIEntity[]
  method_used: DeidentificationMethod
  confidence_score: number
  review_required: boolean
  created_at: string
}

/**
 * Upload method types
 */
export type UploadMethod = 'csv' | 'database'

/**
 * Download format types
 */
export type DownloadFormat = 'csv' | 'json' | 'txt'

/**
 * CSV upload validation result
 */
export interface CSVValidationResult {
  valid: boolean
  errors: string[]
  row_count?: number
  preview?: string[]
}

/**
 * Database query validation result
 */
export interface QueryValidationResult {
  valid: boolean
  errors: string[]
  estimated_rows?: number
}

/**
 * Confidence color mapping
 */
export type ConfidenceColor = 'success' | 'warning' | 'error'

/**
 * Get color based on confidence score
 */
export function getConfidenceColor(confidence: number): ConfidenceColor {
  if (confidence >= 0.9) return 'success'
  if (confidence >= 0.8) return 'warning'
  return 'error'
}

/**
 * Get display label for de-identification method
 */
export function getMethodLabel(method: DeidentificationMethod): string {
  const labels: Record<DeidentificationMethod, string> = {
    [DeidentificationMethod.REMOVAL]: 'Remove PHI',
    [DeidentificationMethod.REPLACEMENT]: 'Replace with Placeholders',
    [DeidentificationMethod.GENERALIZATION]: 'Generalize Dates/Ages'
  }
  return labels[method]
}

/**
 * Get display label for job status
 */
export function getStatusLabel(status: JobStatus): string {
  const labels: Record<JobStatus, string> = {
    [JobStatus.PENDING]: 'Pending',
    [JobStatus.PROCESSING]: 'Processing',
    [JobStatus.COMPLETED]: 'Completed',
    [JobStatus.FAILED]: 'Failed',
    [JobStatus.CANCELLED]: 'Cancelled'
  }
  return labels[status]
}

/**
 * Get color for job status
 */
export function getStatusColor(status: JobStatus): string {
  const colors: Record<JobStatus, string> = {
    [JobStatus.PENDING]: 'info',
    [JobStatus.PROCESSING]: 'primary',
    [JobStatus.COMPLETED]: 'success',
    [JobStatus.FAILED]: 'error',
    [JobStatus.CANCELLED]: 'warning'
  }
  return colors[status]
}
