/**
 * Search API endpoints
 */

import type { SearchQuery, SearchResponse } from '@/types/search'
import apiClient from './client'

export const searchApi = {
    /**
     * Search documents
     */
    async search(query: SearchQuery): Promise<SearchResponse> {
        const params: Record<string, any> = {
            q: query.q,
            page: query.page || 1,
            page_size: query.page_size || 20,
        }

        if (query.query_type) params.query_type = query.query_type
        if (query.document_type) params.document_type = query.document_type
        if (query.date_from) params.date_from = query.date_from
        if (query.date_to) params.date_to = query.date_to
        if (query.department) params.department = query.department
        if (query.author) params.author = query.author

        const response = await apiClient.get<SearchResponse>('/v1/search', { params })
        return response.data
    },

    /**
     * Get search suggestions
     */
    async getSuggestions(q: string, size: number = 5): Promise<string[]> {
        const response = await apiClient.get<{ suggestions: string[] }>('/v1/search/suggest', {
            params: { q, size },
        })
        return response.data.suggestions
    },

    /**
     * Validate query syntax
     */
    async validateQuery(q: string, queryType: string): Promise<{ valid: boolean; message?: string; error?: string }> {
        const response = await apiClient.post('/v1/search/validate', null, {
            params: {
                q,
                query_type: queryType,
            },
        })
        return response.data
    },
}
