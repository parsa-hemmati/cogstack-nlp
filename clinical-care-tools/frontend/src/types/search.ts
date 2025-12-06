/**
 * Search API Types
 */

export interface SearchQuery {
    q: string
    query_type?: 'standard' | 'boolean' | 'wildcard' | 'fuzzy' | 'proximity' | 'range' | 'regex'
    document_type?: string
    date_from?: string
    date_to?: string
    department?: string
    author?: string
    page?: number
    page_size?: number
}

export interface SearchFacet {
    value: string
    count: number
}

export interface SearchFacets {
    document_types: SearchFacet[]
    departments: SearchFacet[]
    authors: SearchFacet[]
    years: SearchFacet[]
}

export interface Highlight {
    field: string
    snippet: string
}

export interface SearchResult {
    id: string
    score: number
    index: string
    source: {
        id: string
        title: string
        document_type: string
        date: string
        author?: string
        snippet?: string
        [key: string]: any
    }
    highlights: Highlight[]
}

export interface SearchResponse {
    results: SearchResult[]
    total_results: number
    page: number
    page_size: number
    total_pages: number
    execution_time_ms: number
    facets: SearchFacets
    query_suggestions?: string[]
}
