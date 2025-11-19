/**
 * Timeline types for API requests/responses.
 *
 * Matches backend schemas in backend/app/schemas/timeline.py
 */

/**
 * Meta-annotations for clinical concept mentions
 */
export interface MetaAnnotations {
  Negation: string        // "Affirmed" | "Negated"
  Temporality: string     // "Current" | "Recent" | "Historical"
  Experiencer: string     // "Patient" | "Family" | "Other"
  Certainty: string       // "High" | "Medium" | "Low"
}

/**
 * Single mention of a concept in a document
 */
export interface ConceptMention {
  conceptCui: string
  conceptName: string
  conceptType: string
  documentId: string
  date: string            // ISO 8601 timestamp
  sentence: string
  metaAnnotations: MetaAnnotations
  confidence: number
  isFirstMention: boolean  // True for earliest mention, false for recurring
}

/**
 * Aggregated concept with all mentions
 */
export interface TimelineConcept {
  conceptCui: string
  conceptName: string
  conceptType: string
  firstMentionDate: string  // ISO 8601 timestamp
  mentionCount: number
  mentions: ConceptMention[]
}

/**
 * Document in the timeline
 */
export interface TimelineDocument {
  documentId: string
  title: string
  documentType: string
  date: string            // ISO 8601 timestamp
  author: string | null
  concepts: string[]      // CUI list
}

/**
 * Date range filter
 */
export interface DateRange {
  start: Date
  end: Date
}

/**
 * Timeline filters for API query
 */
export interface TimelineFilters {
  concepts?: string[]
  dateRange?: DateRange
  metaAnnotations?: {
    Negation?: string
    Temporality?: string | string[]  // Can be single value or list for OR logic
    Experiencer?: string
    Certainty?: string
  }
  documentTypes?: string[]
}

/**
 * Complete patient timeline response
 */
export interface PatientTimeline {
  patientId: string
  documents: TimelineDocument[]
  concepts: TimelineConcept[]
  dateRange: {
    start: string         // ISO 8601 timestamp
    end: string           // ISO 8601 timestamp
  }
  filtersApplied: TimelineFilters
}

/**
 * Timeline filter preset (for saved filters)
 */
export interface TimelineFilterPreset {
  id: string
  name: string
  description: string
  filters: TimelineFilters
  userId: string
  createdAt: string       // ISO 8601 timestamp
}

/**
 * Timeline export request
 */
export interface TimelineExportRequest {
  patientId: string
  filters: TimelineFilters
  format: 'pdf' | 'json' | 'csv'
  includeDocuments: boolean
  includeConcepts: boolean
}

/**
 * Timeline export response
 */
export interface TimelineExportResponse {
  exportId: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  downloadUrl: string | null
  createdAt: string       // ISO 8601 timestamp
  completedAt: string | null
  error: string | null
}
