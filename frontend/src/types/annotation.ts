/**
 * Manual Annotation Types
 *
 * Type definitions for manual PHI annotation and job tracking
 */

import type { PHIEntityType } from './deidentification'

/**
 * Manual annotation created by human reviewer
 */
export interface ManualAnnotation {
  annotation_id: string
  note_id: string
  user_id: string
  text: string
  start_offset: number
  end_offset: number
  entity_type: PHIEntityType
  confidence: number
  created_at: string
  manually_reviewed: boolean
}

/**
 * Request to create manual annotation
 */
export interface CreateAnnotationRequest {
  note_id: string
  text: string
  start_offset: number
  end_offset: number
  entity_type: PHIEntityType
  confidence: number
}

/**
 * Selected text range for annotation
 */
export interface TextSelection {
  selectedText: string
  startOffset: number
  endOffset: number
  rect?: DOMRect
}

/**
 * Job summary for dashboard
 */
export interface JobSummary {
  job_id: string
  user_id: string
  user_email: string
  status: string
  method: string
  total_notes: number
  processed_notes: number
  progress_percentage: number
  error_count: number
  created_at: string
  updated_at: string
  completed_at?: string
}

/**
 * Job analytics data
 */
export interface JobAnalytics {
  total_jobs: number
  completed_jobs: number
  failed_jobs: number
  success_rate: number
  avg_processing_time: string
  total_notes: number
  total_phi_entities: number
  jobs_over_time: TimeSeriesData[]
  phi_distribution: CategoryData[]
  confidence_by_type: CategoryData[]
}

/**
 * Time series data point
 */
export interface TimeSeriesData {
  date: string
  count: number
}

/**
 * Category data for charts
 */
export interface CategoryData {
  label: string
  value: number
  percentage?: number
}

/**
 * Job filter options
 */
export interface JobFilters {
  status?: string
  user_id?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

/**
 * Re-run de-identification request
 */
export interface ReRunRequest {
  job_id: string
  include_manual_annotations: boolean
}
