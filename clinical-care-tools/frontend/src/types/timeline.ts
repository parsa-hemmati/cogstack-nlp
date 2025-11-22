/**
 * Timeline Module TypeScript Types
 *
 * Corresponds to backend Pydantic models in app/modules/timeline/models.py
 */

// Meta-Annotations
export enum NegationValue {
  Affirmed = 'Affirmed',
  Negated = 'Negated',
  Possible = 'Possible',
}

export enum TemporalityValue {
  Current = 'Current',
  Recent = 'Recent',
  Historical = 'Historical',
  Future = 'Future',
}

export enum ExperiencerValue {
  Patient = 'Patient',
  Family = 'Family',
  Other = 'Other',
}

export enum CertaintyValue {
  Confirmed = 'Confirmed',
  Suspected = 'Suspected',
  Hypothetical = 'Hypothetical',
  Negative = 'Negative',
}

export interface MetaAnnotations {
  negation?: NegationValue
  experiencer?: ExperiencerValue
  temporality?: TemporalityValue[]
  certainty?: CertaintyValue[]
}

// Concept Mention
export interface ConceptMention {
  document_id: string
  document_date: string
  sentence: string
  start_char: number
  end_char: number
  meta_annotations: Record<string, string>
  confidence: number
}

// Timeline Concept
export interface TimelineConcept {
  concept_cui: string
  name: string
  type: string
  first_mention_date: string
  mention_count: number
  mentions: ConceptMention[]
}

// Timeline Document
export interface TimelineDocument {
  id: string
  title: string
  type: string
  document_date: string
  author?: string
  concept_count: number
}

// Timeline Request
export interface TimelineRequest {
  patient_id: string
  date_start?: string
  date_end?: string
  concept_cuis?: string[]
  document_types?: string[]
  meta_annotations?: MetaAnnotations
}

// Patient Timeline
export interface PatientTimeline {
  patient_id: string
  documents: TimelineDocument[]
  concepts: TimelineConcept[]
  date_range: [string, string]
  filters_applied: Record<string, any>
  statistics: Record<string, any>
}

// Export Types
export enum ExportFormat {
  PDF = 'pdf',
  FHIR = 'fhir',
  JSON = 'json',
}

export enum ExportStatus {
  Processing = 'processing',
  Completed = 'completed',
  Failed = 'failed',
}

export interface ExportRequest {
  format: ExportFormat
  filters?: Record<string, any>
  options?: Record<string, any>
}

export interface TimelineExportResponse {
  id: string
  patient_id: string
  status: ExportStatus
  format: ExportFormat
  download_url?: string
  expires_at: string
  audit_log_id?: string
  error_message?: string
}

// Filter Preset Types
export interface FilterPresetRequest {
  name: string
  description?: string
  filters: Record<string, any>
  is_default?: boolean
}

export interface FilterPresetResponse {
  id: string
  name: string
  description?: string
  filters: Record<string, any>
  is_default: boolean
  created_at: string
  updated_at: string
}

// Timeline Filters (for UI component v-model)
export interface TimelineFilters {
  date_start?: string
  date_end?: string
  concept_cuis?: string[]
  document_types?: string[]
  negation?: NegationValue
  experiencer?: ExperiencerValue
  temporality?: TemporalityValue
  certainty?: CertaintyValue
}
