/**
 * Search Store
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { SearchQuery, SearchResponse, SearchResult } from '@/types/search'
import { searchApi } from '@/api/search'

export const useSearchStore = defineStore('search', () => {
    // State
    const query = ref<string>('')
    const queryType = ref<string>('standard')
    const results = ref<SearchResult[]>([])
    const totalResults = ref(0)
    const page = ref(1)
    const pageSize = ref(20)
    const totalPages = ref(0)
    const facets = ref<SearchResponse['facets'] | null>(null)

    // Filters
    const filters = ref({
        documentType: null as string | null,
        dateFrom: null as string | null,
        dateTo: null as string | null,
        department: null as string | null,
        author: null as string | null,
    })

    // Status
    const loading = ref(false)
    const error = ref<string | null>(null)

    // Actions
    async function performSearch(resetPage = true) {
        if (!query.value.trim()) return

        if (resetPage) {
            page.value = 1
        }

        loading.value = true
        error.value = null

        try {
            const searchQuery: SearchQuery = {
                q: query.value,
                query_type: queryType.value as any,
                page: page.value,
                page_size: pageSize.value,
                document_type: filters.value.documentType || undefined,
                date_from: filters.value.dateFrom || undefined,
                date_to: filters.value.dateTo || undefined,
                department: filters.value.department || undefined,
                author: filters.value.author || undefined,
            }

            const response = await searchApi.search(searchQuery)

            results.value = response.results
            totalResults.value = response.total_results
            totalPages.value = response.total_pages
            facets.value = response.facets
        } catch (err: any) {
            console.error('Search failed:', err)
            error.value = err.response?.data?.detail || 'Search failed. Please try again.'
            results.value = []
        } finally {
            loading.value = false
        }
    }

    async function getSuggestions(partial: string) {
        if (!partial || partial.length < 2) return []
        try {
            return await searchApi.getSuggestions(partial)
        } catch (err) {
            console.error('Suggestions failed:', err)
            return []
        }
    }

    function setQuery(q: string) {
        query.value = q
    }

    function setPage(p: number) {
        page.value = p
        performSearch(false)
    }

    function clearFilters() {
        filters.value = {
            documentType: null,
            dateFrom: null,
            dateTo: null,
            department: null,
            author: null,
        }
        performSearch()
    }

    return {
        query,
        queryType,
        results,
        totalResults,
        page,
        pageSize,
        totalPages,
        facets,
        filters,
        loading,
        error,
        performSearch,
        getSuggestions,
        setQuery,
        setPage,
        clearFilters,
    }
})
