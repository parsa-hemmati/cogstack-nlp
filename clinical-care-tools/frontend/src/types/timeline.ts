/**
 * Timeline types for patient medical history visualization
 */

export interface TimelineFilters {
  startDate?: string
  endDate?: string
  documentTypes?: string[]
  conceptTypes?: string[]
  includeNegated?: boolean
  includeFamily?: boolean
}

export type ViewMode = 'documents' | 'concepts' | 'combined'

export interface TimelineDocument {
  id: string
  title: string
  documentType: string
  date: string
  annotationCount: number
}

export interface MetaAnnotations {
  negation?: string
  temporality?: string
  experiencer?: string
  certainty?: string
}

export interface ConceptOccurrence {
  documentId: string
  documentTitle: string
  date: string
  context: string
}

export interface TimelineConcept {
  cui: string
  preferredName: string
  conceptType: string
  firstMentioned: string
  lastMentioned: string
  occurrenceCount: number
  metaAnnotations: MetaAnnotations
  occurrences: ConceptOccurrence[]
}

export interface TimelineMetadata {
  documentCount: number
  conceptCount: number
  generatedAt: string
}

export interface TimelineResponse {
  patientId: string
  documents: TimelineDocument[]
  concepts: TimelineConcept[]
  dateRange: {
    start: string
    end: string
  }
  metadata: TimelineMetadata
}

export interface Annotation {
  id: string
  cui: string
  preferredName: string
  conceptType: string
  startChar: number
  endChar: number
  text: string
  metaAnnotations: MetaAnnotations
}

export interface DocumentDetail {
  id: string
  title: string
  documentType: string
  date: string
  author?: string
  content: string
  annotations: Annotation[]
}
