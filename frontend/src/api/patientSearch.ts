/**
 * Patient Search API client.
 *
 * Provides search functionality for patients by clinical concepts
 * with meta-annotation filtering.
 */
import api from './api'

// ============================================================================
// Request/Response Types (matching current backend implementation)
// ============================================================================

/**
 * Temporal filter options for search
 */
export type TemporalFilter = 'current' | 'historical' | 'future' | 'any'

/**
 * Sort options for search results
 */
export type SortOption = 'relevance' | 'name' | 'lastUpdated'

/**
 * Date range filter
 */
export interface DateRangeFilter {
  start?: string  // ISO 8601 date
  end?: string    // ISO 8601 date
}

/**
 * Search filters for patient search
 */
export interface SearchFilters {
  temporal?: TemporalFilter
  includeNegated?: boolean
  includeFamily?: boolean
  dateRange?: DateRangeFilter
}

/**
 * Pagination parameters
 */
export interface Pagination {
  page: number
  pageSize: number
}

/**
 * Patient search request
 */
export interface PatientSearchRequest {
  concept: string
  filters?: SearchFilters
  pagination?: Pagination
  sort?: SortOption
}

/**
 * Meta-annotations for concept mention
 */
export interface MetaAnnotations {
  temporality?: string
  negated?: boolean
  experiencer?: string
  certainty?: string
}

/**
 * Patient demographics
 */
export interface Demographics {
  age: number
  gender?: string
  department?: string
}

/**
 * Single annotation with full details
 */
export interface Annotation {
  cui: string
  conceptName: string
  sourceValue: string
  documentId: string
  documentType: string
  documentDate: string
  startChar: number
  endChar: number
  confidence: number
  metaAnnotations: MetaAnnotations
  snomedCT?: string[]
  icd10?: string[]
}

/**
 * Patient search result
 */
export interface PatientSearchResult {
  mrn: string              // Masked MRN (XXX-XXX-1234)
  demographics: Demographics
  annotations: Annotation[]
  lastUpdated: string      // ISO 8601 timestamp
}

/**
 * Pagination information (PRD-compliant nested object).
 */
export interface PaginationInfo {
  page: number
  pageSize: number
  totalResults: number
  totalPages: number
}

/**
 * Performance metrics (PRD-compliant nested object).
 */
export interface PerformanceInfo {
  searchTime: number
  source: 'cache' | 'live'
}

/**
 * Patient search response (PRD-compliant with nested objects).
 */
export interface PatientSearchResponse {
  results: PatientSearchResult[]
  pagination: PaginationInfo
  performance: PerformanceInfo
}

/**
 * Meta-annotation display for highlights
 */
export interface MetaAnnotationDisplay {
  Negation: string
  Temporality: string
  Experiencer: string
  Certainty: string
}

/**
 * Document highlight with snippet
 */
export interface DocumentHighlight {
  documentId: string
  title: string
  date: string            // ISO 8601 date
  snippet: string         // Text with concept bolded
  metaAnnotations: MetaAnnotationDisplay
  startChar: number
  endChar: number
}

/**
 * Concept highlights response
 */
export interface ConceptHighlightResponse {
  documents: DocumentHighlight[]
  totalCount: number
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Search for patients by clinical concept.
 *
 * @param request - Search parameters
 * @returns Search results with matching patients
 *
 * @example
 * const response = await searchPatients({
 *   concept: 'atrial flutter',
 *   filters: { includeNegated: false },
 *   pagination: { page: 1, pageSize: 20 }
 * })
 * // response.pagination.totalResults contains count
 */
export async function searchPatients(request: PatientSearchRequest): Promise<PatientSearchResponse> {
  const response = await api.post<PatientSearchResponse>('/patients/search', request)
  return response.data
}

/**
 * Get concept highlights for a specific patient.
 *
 * Retrieves all documents containing the specified concept for a patient,
 * with document snippets showing context (100 chars before/after concept).
 *
 * @param patientId - Patient UUID
 * @param cui - SNOMED-CT CUI or concept name
 * @param filters - Optional meta-annotation filters
 * @returns Document highlights with snippets
 *
 * @example
 * const response = await getConceptHighlights(
 *   'patient-uuid',
 *   'C0004238',
 *   { temporal: 'current', includeNegated: false }
 * )
 * // response.totalCount contains document count
 */
export async function getConceptHighlights(
  patientId: string,
  cui: string,
  filters?: SearchFilters
): Promise<ConceptHighlightResponse> {
  const params: Record<string, string> = { cui }

  if (filters) {
    if (filters.temporal) params.temporal = filters.temporal
    if (filters.includeNegated !== undefined) params.include_negated = String(filters.includeNegated)
    if (filters.includeFamily !== undefined) params.include_family = String(filters.includeFamily)
  }

  const response = await api.get<ConceptHighlightResponse>(
    `/patients/${patientId}/concept-highlights`,
    { params }
  )

  return response.data
}
