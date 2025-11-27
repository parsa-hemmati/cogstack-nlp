<template>
  <v-container>
    <!-- Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-account-search</v-icon>
          Patient Search
        </h1>
      </v-col>
    </v-row>

    <!-- Search Box -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-magnify</v-icon>
            Search by Clinical Concept
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" md="8">
                <v-text-field
                  v-model="searchConcept"
                  label="Enter medical concept"
                  placeholder="e.g., atrial flutter, diabetes, hypertension"
                  prepend-inner-icon="mdi-stethoscope"
                  :loading="isLoading"
                  :disabled="isLoading"
                  :error-messages="error || undefined"
                  clearable
                  @keydown.enter="handleSearch"
                  @click:clear="clearResults"
                />
              </v-col>
              <v-col cols="12" md="4">
                <v-btn
                  color="primary"
                  size="large"
                  :loading="isLoading"
                  :disabled="!searchConcept || isLoading"
                  block
                  @click="handleSearch"
                >
                  <v-icon class="mr-2">mdi-magnify</v-icon>
                  Search
                </v-btn>
              </v-col>
            </v-row>

            <!-- Filters -->
            <v-row class="mt-2">
              <v-col cols="12">
                <v-expansion-panels>
                  <v-expansion-panel>
                    <v-expansion-panel-title>
                      <v-icon class="mr-2">mdi-filter</v-icon>
                      Advanced Filters
                    </v-expansion-panel-title>
                    <v-expansion-panel-text>
                      <v-row>
                        <v-col cols="12" md="3">
                          <v-select
                            v-model="filters.temporal"
                            label="Temporal Context"
                            :items="temporalOptions"
                            density="comfortable"
                          />
                        </v-col>
                        <v-col cols="12" md="3">
                          <v-checkbox
                            v-model="filters.includeNegated"
                            label="Include negated mentions"
                            hint="e.g., 'no chest pain'"
                            persistent-hint
                            density="comfortable"
                          />
                        </v-col>
                        <v-col cols="12" md="3">
                          <v-checkbox
                            v-model="filters.includeFamily"
                            label="Include family history"
                            hint="e.g., 'family history of diabetes'"
                            persistent-hint
                            density="comfortable"
                          />
                        </v-col>
                        <v-col cols="12" md="3">
                          <v-select
                            v-model="sortOption"
                            label="Sort By"
                            :items="sortOptions"
                            density="comfortable"
                          />
                        </v-col>
                      </v-row>
                    </v-expansion-panel-text>
                  </v-expansion-panel>
                </v-expansion-panels>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Search Results -->
    <v-row v-if="hasResults || isLoading" class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-table</v-icon>
            Search Results
            <v-spacer />
            <v-chip color="primary" variant="tonal" class="mr-2">
              {{ total }} patients found
            </v-chip>
            <v-chip color="secondary" variant="tonal">
              {{ queryTimeMs }}ms
            </v-chip>
          </v-card-title>

          <v-card-text>
            <v-data-table
              :headers="headers"
              :items="results"
              :loading="isLoading"
              :items-per-page="pageSize"
              hide-default-footer
              show-expand
              class="elevation-1"
            >
              <!-- MRN Column -->
              <template #item.mrn="{ item }">
                <v-chip size="small" variant="outlined">
                  {{ item.mrn }}
                </v-chip>
              </template>

              <!-- Age Column -->
              <template #item.demographics.age="{ item }">
                {{ item.demographics.age }} years
              </template>

              <!-- Annotations Count Column -->
              <template #item.annotations="{ item }">
                <v-chip color="primary" size="small">
                  {{ item.annotations.length }} mentions
                </v-chip>
              </template>

              <!-- Last Updated Column -->
              <template #item.lastUpdated="{ item }">
                {{ formatDate(item.lastUpdated) }}
              </template>

              <!-- Actions Column -->
              <template #item.actions="{ item }">
                <v-btn
                  size="small"
                  color="primary"
                  variant="text"
                  @click="viewPatientDetails(item)"
                >
                  <v-icon class="mr-1">mdi-eye</v-icon>
                  View
                </v-btn>
              </template>

              <!-- Expandable Row: Document Highlights -->
              <template #expanded-row="{ item }">
                <tr>
                  <td :colspan="headers.length + 1" class="pa-0">
                    <DocumentHighlights
                      :patient-id="item.patientId"
                      :concept="searchConcept"
                      :filters="filters"
                    />
                  </td>
                </tr>
              </template>
            </v-data-table>
          </v-card-text>

          <!-- Pagination -->
          <v-card-actions>
            <v-spacer />
            <v-pagination
              v-model="page"
              :length="totalPages"
              :disabled="isLoading"
              @update:model-value="handlePageChange"
            />
            <v-spacer />
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- Empty State -->
    <v-row v-if="isEmpty" class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-text class="text-center pa-8">
            <v-icon size="64" color="grey-lighten-1">mdi-account-search-outline</v-icon>
            <h3 class="text-h6 mt-4 mb-2">No patients found</h3>
            <p class="text-body-2 text-grey">
              No patients found matching "<strong>{{ lastSearchConcept }}</strong>".
              Try adjusting your search or filters.
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Error Alert -->
    <v-row v-if="error && !isLoading" class="mt-4">
      <v-col cols="12">
        <v-alert
          type="error"
          variant="tonal"
          closable
          @click:close="clearError"
        >
          <v-alert-title>Search Error</v-alert-title>
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { usePatientSearch } from '@/composables/usePatientSearch'
import DocumentHighlights from '@/components/DocumentHighlights.vue'
import type { SearchFilters, TemporalFilter, SortOption, PatientSearchResult } from '@/api/patientSearch'

// Composable
const {
  results,
  total,
  page,
  pageSize,
  totalPages,
  queryTimeMs,
  isLoading,
  error,
  hasResults,
  isEmpty,
  lastSearchConcept,
  search,
  clearResults,
  clearError,
} = usePatientSearch()

// Search state
const searchConcept = ref('')
const filters = ref<SearchFilters>({
  temporal: 'current',
  includeNegated: false,
  includeFamily: false,
})
const sortOption = ref<SortOption>('relevance')

// Filter options
const temporalOptions = [
  { title: 'Current', value: 'current' },
  { title: 'Historical', value: 'historical' },
  { title: 'Future', value: 'future' },
  { title: 'Any', value: 'any' },
]

const sortOptions = [
  { title: 'Relevance', value: 'relevance' },
  { title: 'Name', value: 'name' },
  { title: 'Last Updated', value: 'lastUpdated' },
]

// Table headers
const headers = [
  { title: 'MRN', key: 'mrn', sortable: false },
  { title: 'Age', key: 'demographics.age', sortable: false },
  { title: 'Gender', key: 'demographics.gender', sortable: false },
  { title: 'Department', key: 'demographics.department', sortable: false },
  { title: 'Mentions', key: 'annotations', sortable: false },
  { title: 'Last Updated', key: 'lastUpdated', sortable: false },
  { title: 'Actions', key: 'actions', sortable: false, align: 'end' },
]

// Event handlers
const handleSearch = async () => {
  if (!searchConcept.value) return

  await search(
    searchConcept.value,
    filters.value,
    1,
    20
  )
}

const handlePageChange = async (newPage: number) => {
  await search(
    searchConcept.value,
    filters.value,
    newPage,
    pageSize.value
  )
}

const viewPatientDetails = (patient: PatientSearchResult) => {
  // Future: Navigate to patient details page with highlights (tracked in technical debt)
  alert(`Patient details view coming soon!\n\nMRN: ${patient.mrn}\nMentions: ${patient.annotations.length}`)
}

// Utility functions
const formatDate = (isoDate: string): string => {
  return new Date(isoDate).toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}
</script>
