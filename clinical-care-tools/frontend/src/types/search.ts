/**
 * Search Types
 *
 * TypeScript interfaces for patient search functionality.
 */

// Meta-annotation values
export type NegationValue = 'Affirmed' | 'Negated' | 'Possible';
export type TemporalityValue = 'Current' | 'Recent' | 'Historical' | 'Future';
export type ExperiencerValue = 'Patient' | 'Family' | 'Other';
export type CertaintyValue = 'Confirmed' | 'Suspected' | 'Hypothetical' | 'Negative';

// Boolean operators for complex queries
export type BooleanOperator = 'AND' | 'OR' | 'NOT';

// Export format options
export type ExportFormat = 'csv' | 'fhir' | 'json';

/**
 * Meta-annotation filters for high-precision filtering.
 *
 * These filters are critical for achieving 95% precision by excluding:
 * - Negated mentions (patient denies chest pain)
 * - Historical conditions (history of diabetes)
 * - Family history (mother had breast cancer)
 * - Hypothetical scenarios (risk of developing)
 */
export interface MetaAnnotationFilters {
  negation?: NegationValue;
  temporality?: TemporalityValue[];
  experiencer?: ExperiencerValue;
  certainty?: CertaintyValue[];
  confidence_min: number;
}

/**
 * Individual search query with concept and operator.
 */
export interface SearchQuery {
  concept: string;
  operator?: BooleanOperator;
  cui?: string;
}

/**
 * Patient search request with query and filters.
 */
export interface PatientSearchRequest {
  query: string;
  queries?: SearchQuery[];
  filters: MetaAnnotationFilters;
  date_from?: string;
  date_to?: string;
  department_ids?: string[];
  document_types?: string[];
  limit: number;
  offset: number;
}

/**
 * Matched medical concept with metadata.
 */
export interface ConceptMatch {
  text: string;
  cui: string;
  pretty_name: string;
  confidence: number;

  // Meta-annotations
  negation: string;
  temporality: string;
  experiencer: string;
  certainty: string;

  // Context
  start_idx: number;
  end_idx: number;
  context: string;
}

/**
 * Individual patient search result.
 */
export interface PatientSearchResult {
  patient_id: string;
  patient_mrn: string;

  // Basic demographics (limited for privacy)
  age?: number;
  gender?: string;

  // Match information
  matched_concepts: ConceptMatch[];
  relevance_score: number;

  // Document information
  document_count: number;
  latest_match_date: string;

  // Summary
  summary?: string;
}

/**
 * Patient search response with results and metadata.
 */
export interface PatientSearchResponse {
  results: PatientSearchResult[];
  total: number;
  query_time_ms: number;
  filters_applied: MetaAnnotationFilters;
  stats?: Record<string, any>;
}

/**
 * Saved search request.
 */
export interface SavedSearchRequest {
  name: string;
  description?: string;
  search_request: PatientSearchRequest;
  is_public: boolean;
}

/**
 * Saved search information.
 */
export interface SavedSearch {
  id: string;
  name: string;
  description?: string;
  search_request: PatientSearchRequest;
  is_public: boolean;
  created_by: string;
  created_at: string;
  last_used?: string;
  use_count: number;
}

/**
 * Concept suggestion for autocomplete.
 */
export interface ConceptSuggestion {
  cui: string;
  pretty_name: string;
  semantic_type: string;
  synonyms: string[];
  popularity: number;
}

/**
 * Export request.
 */
export interface ExportRequest {
  format: ExportFormat;
  patient_ids: string[];
  include_concepts: boolean;
  include_context: boolean;
  anonymize: boolean;
}