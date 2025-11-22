<template>
  <v-container fluid>
    <v-row>
      <!-- Left Sidebar: Saved Searches -->
      <v-col cols="12" md="3">
        <SavedSearches
          :saved-searches="savedSearches"
          @execute="executeSavedSearch"
          @delete="deleteSavedSearch"
          @save="showSaveDialog = true"
        />
      </v-col>

      <!-- Main Content: Search and Results -->
      <v-col cols="12" md="9">
        <!-- Search Bar -->
        <v-card class="mb-4">
          <v-card-title>Full-Text Document Search</v-card-title>
          <v-card-text>
            <SearchBar
              v-model="searchQuery"
              :loading="searching"
              :error="searchError"
              @search="executeSearch"
              @clear="clearSearch"
            />
          </v-card-text>
        </v-card>

        <!-- Export Toolbar -->
        <v-card v-if="hasResults" class="mb-4">
          <v-card-title class="d-flex align-center justify-space-between">
            <span>
              <v-icon>mdi-file-document-outline</v-icon>
              Search Results ({{ searchResults.length }})
            </span>
            <div class="export-buttons">
              <v-btn
                variant="outlined"
                color="primary"
                size="small"
                prepend-icon="mdi-file-delimited"
                class="mr-2"
                :loading="exporting === 'csv'"
                :disabled="exporting !== null"
                @click="exportResults('csv')"
              >
                Export CSV
              </v-btn>
              <v-btn
                variant="outlined"
                color="primary"
                size="small"
                prepend-icon="mdi-code-json"
                class="mr-2"
                :loading="exporting === 'json'"
                :disabled="exporting !== null"
                @click="exportResults('json')"
              >
                Export JSON
              </v-btn>
              <v-btn
                variant="outlined"
                color="primary"
                size="small"
                prepend-icon="mdi-hospital-box"
                :loading="exporting === 'fhir'"
                :disabled="exporting !== null"
                @click="exportResults('fhir')"
              >
                Export FHIR
              </v-btn>
            </div>
          </v-card-title>
        </v-card>

        <!-- Search Results -->
        <SearchResults
          :results="searchResults"
          :loading="searching"
        />
      </v-col>
    </v-row>

    <!-- Save Search Dialog -->
    <SaveSearchDialog
      v-model="showSaveDialog"
      :query="searchQuery"
      :filters="searchFilters"
      @saved="handleSaveSearch"
    />

    <!-- Export Success Snackbar -->
    <v-snackbar
      v-model="showExportSuccess"
      color="success"
      :timeout="3000"
    >
      <v-icon start>mdi-check-circle</v-icon>
      Export successful! File downloaded.
    </v-snackbar>

    <!-- Export Error Snackbar -->
    <v-snackbar
      v-model="showExportError"
      color="error"
      :timeout="5000"
    >
      <v-icon start>mdi-alert-circle</v-icon>
      {{ exportError }}
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import SavedSearches from '@/components/search/SavedSearches.vue'
import SaveSearchDialog from '@/components/search/SaveSearchDialog.vue'
import SearchBar from '@/components/search/SearchBar.vue'
import SearchResults from '@/components/search/SearchResults.vue'
import { api } from '@/api/client'

/**
 * Interfaces
 */
interface SavedSearch {
  id: string
  name: string
  query: string
  filters?: Record<string, any>
}

interface SearchResult {
  document_id: string
  title: string
  document_type: string
  relevance_score: number
}

/**
 * State
 */
const savedSearches = ref<SavedSearch[]>([])
const searchQuery = ref('')
const searchFilters = ref<Record<string, any>>({})
const searchResults = ref<SearchResult[]>([])
const searching = ref(false)
const searchError = ref('')

const showSaveDialog = ref(false)
const exporting = ref<'csv' | 'json' | 'fhir' | null>(null)
const showExportSuccess = ref(false)
const showExportError = ref(false)
const exportError = ref('')

/**
 * Computed
 */
const hasResults = computed(() => searchResults.value.length > 0)

/**
 * Load saved searches on mount
 */
async function loadSavedSearches() {
  try {
    const response = await api.get('/api/v1/search/saved')
    savedSearches.value = response.data
  } catch (error: any) {
    console.error('Failed to load saved searches:', error)
  }
}

/**
 * Execute search
 */
async function executeSearch(query: string) {
  if (!query.trim()) return

  searching.value = true
  searchError.value = ''

  try {
    const response = await api.post('/api/v1/search', {
      query: query.trim(),
      filters: searchFilters.value,
      page: 1,
      page_size: 20,
      sort: 'relevance',
    })

    searchResults.value = response.data.documents || []
  } catch (error: any) {
    searchError.value = error.response?.data?.detail || 'Search failed'
    searchResults.value = []
  } finally {
    searching.value = false
  }
}

/**
 * Execute saved search
 */
function executeSavedSearch(savedSearch: SavedSearch) {
  searchQuery.value = savedSearch.query
  searchFilters.value = savedSearch.filters || {}
  executeSearch(savedSearch.query)
}

/**
 * Clear search
 */
function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
  searchError.value = ''
}

/**
 * Save current search
 */
async function handleSaveSearch(data: any) {
  try {
    await api.post('/api/v1/search/saved', data)
    showSaveDialog.value = false
    await loadSavedSearches() // Refresh list
  } catch (error: any) {
    console.error('Failed to save search:', error)
  }
}

/**
 * Delete saved search
 */
async function deleteSavedSearch(searchId: string) {
  try {
    await api.delete(`/api/v1/search/saved/${searchId}`)
    await loadSavedSearches() // Refresh list
  } catch (error: any) {
    console.error('Failed to delete search:', error)
  }
}

/**
 * Export search results
 */
async function exportResults(format: 'csv' | 'json' | 'fhir') {
  if (!hasResults.value) return

  exporting.value = format
  exportError.value = ''
  showExportError.value = false

  try {
    const response = await api.post(
      '/api/v1/search/export',
      {
        query: searchQuery.value,
        filters: searchFilters.value,
        format,
      },
      {
        responseType: 'blob',
      }
    )

    // Create download link
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url

    // Set filename
    const extension = format === 'fhir' ? 'json' : format
    link.download = `search_results_${Date.now()}.${extension}`

    // Trigger download
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    showExportSuccess.value = true
  } catch (error: any) {
    exportError.value = error.response?.data?.detail || 'Export failed'
    showExportError.value = true
  } finally {
    exporting.value = null
  }
}

// Load saved searches on component mount
loadSavedSearches()
</script>

<style scoped>
.export-buttons {
  display: flex;
  gap: 8px;
}
</style>
