/**
 * Patient Search Store
 *
 * Pinia store for patient search functionality.
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import axios from 'axios';
import type {
  PatientSearchRequest,
  PatientSearchResponse,
  ConceptSuggestion,
  SavedSearch,
  SavedSearchRequest,
  ExportRequest,
} from '@/types/search';

export const usePatientSearchStore = defineStore('patientSearch', () => {
  // State
  const searchHistory = ref<PatientSearchRequest[]>([]);
  const savedSearches = ref<SavedSearch[]>([]);
  const recentConcepts = ref<ConceptSuggestion[]>([]);
  const lastSearchResponse = ref<PatientSearchResponse | null>(null);
  const isSearching = ref(false);

  // Getters
  const hasSearchHistory = computed(() => searchHistory.value.length > 0);
  const lastSearch = computed(() =>
    searchHistory.value.length > 0
      ? searchHistory.value[searchHistory.value.length - 1]
      : null
  );

  // Actions
  /**
   * Execute patient search
   */
  async function searchPatients(
    request: PatientSearchRequest
  ): Promise<PatientSearchResponse> {
    isSearching.value = true;

    try {
      const response = await axios.post<PatientSearchResponse>(
        '/api/v1/modules/patient-search/search',
        request
      );

      // Store in history
      searchHistory.value.push(request);
      if (searchHistory.value.length > 10) {
        searchHistory.value.shift(); // Keep only last 10 searches
      }

      // Store response
      lastSearchResponse.value = response.data;

      return response.data;
    } finally {
      isSearching.value = false;
    }
  }

  /**
   * Get concept suggestions for autocomplete
   */
  async function getConceptSuggestions(
    query: string
  ): Promise<ConceptSuggestion[]> {
    try {
      const response = await axios.get<ConceptSuggestion[]>(
        '/api/v1/modules/patient-search/concepts',
        {
          params: { q: query, limit: 10 },
        }
      );

      // Update recent concepts
      const newConcepts = response.data;
      newConcepts.forEach((concept) => {
        if (!recentConcepts.value.find((c) => c.cui === concept.cui)) {
          recentConcepts.value.unshift(concept);
        }
      });

      // Keep only last 20 recent concepts
      if (recentConcepts.value.length > 20) {
        recentConcepts.value = recentConcepts.value.slice(0, 20);
      }

      return response.data;
    } catch (error) {
      return [];
    }
  }

  /**
   * Save a search query
   */
  async function saveSearch(
    request: SavedSearchRequest
  ): Promise<SavedSearch> {
    const response = await axios.post<SavedSearch>(
      '/api/v1/modules/patient-search/saved-searches',
      request
    );

    // Add to saved searches
    savedSearches.value.push(response.data);

    return response.data;
  }

  /**
   * Get saved searches
   */
  async function getSavedSearches(
    includePublic: boolean = true
  ): Promise<SavedSearch[]> {
    try {
      const response = await axios.get<SavedSearch[]>(
        '/api/v1/modules/patient-search/saved-searches',
        {
          params: { include_public: includePublic },
        }
      );

      savedSearches.value = response.data;
      return response.data;
    } catch (error) {
      return [];
    }
  }

  /**
   * Delete a saved search
   */
  async function deleteSavedSearch(searchId: string): Promise<void> {
    await axios.delete(
      `/api/v1/modules/patient-search/saved-searches/${searchId}`
    );

    // Remove from local state
    const index = savedSearches.value.findIndex((s) => s.id === searchId);
    if (index >= 0) {
      savedSearches.value.splice(index, 1);
    }
  }

  /**
   * Export search results
   */
  async function exportResults(request: ExportRequest): Promise<Blob> {
    const response = await axios.post(
      '/api/v1/modules/patient-search/export',
      request,
      {
        responseType: 'blob',
      }
    );

    // Create download link
    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;

    // Set filename based on format
    const extension = request.format === 'fhir' ? 'json' : request.format;
    link.download = `patient_search_export.${extension}`;

    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    return response.data;
  }

  /**
   * Clear search history
   */
  function clearSearchHistory() {
    searchHistory.value = [];
    lastSearchResponse.value = null;
  }

  return {
    // State
    searchHistory,
    savedSearches,
    recentConcepts,
    lastSearchResponse,
    isSearching,

    // Getters
    hasSearchHistory,
    lastSearch,

    // Actions
    searchPatients,
    getConceptSuggestions,
    saveSearch,
    getSavedSearches,
    deleteSavedSearch,
    exportResults,
    clearSearchHistory,
  };
});