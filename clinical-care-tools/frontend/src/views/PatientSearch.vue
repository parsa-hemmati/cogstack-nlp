<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row>
      <v-col>
        <h1 class="text-h4 font-weight-bold mb-2">Patient Search</h1>
        <p class="text-subtitle-1 text-grey">
          Search for patients using medical concepts with advanced filtering
        </p>
      </v-col>
    </v-row>

    <!-- Search Form -->
    <v-row>
      <v-col>
        <SearchForm
          @search="handleSearch"
          @clear="handleClear"
          :loading="loading"
          :saved-searches="savedSearches"
          @load-saved="handleLoadSaved"
        />
      </v-col>
    </v-row>

    <!-- Meta-Annotation Filters -->
    <v-row v-if="showAdvancedFilters">
      <v-col>
        <MetaAnnotationFilters
          v-model="metaFilters"
          @update="handleFilterUpdate"
        />
      </v-col>
    </v-row>

    <!-- Results Summary -->
    <v-row v-if="searchPerformed">
      <v-col>
        <v-alert
          v-if="results.length === 0"
          type="info"
          variant="tonal"
        >
          No patients found matching your search criteria.
          Try adjusting your filters or search terms.
        </v-alert>

        <v-alert
          v-else
          type="success"
          variant="tonal"
          closable
        >
          Found {{ totalResults }} patient{{ totalResults !== 1 ? 's' : '' }}
          matching your criteria (showing {{ results.length }}).
          Query took {{ queryTime }}ms.
        </v-alert>
      </v-col>
    </v-row>

    <!-- Results Table -->
    <v-row v-if="results.length > 0">
      <v-col>
        <ResultsTable
          :results="results"
          :loading="loading"
          @view-patient="handleViewPatient"
          @export="handleExport"
          :total="totalResults"
          :page="currentPage"
          :items-per-page="itemsPerPage"
          @update:page="handlePageChange"
          @update:items-per-page="handleItemsPerPageChange"
        />
      </v-col>
    </v-row>

    <!-- Export Dialog -->
    <v-dialog v-model="exportDialog" max-width="500">
      <v-card>
        <v-card-title>Export Search Results</v-card-title>
        <v-card-text>
          <v-radio-group v-model="exportFormat" label="Select format:">
            <v-radio label="CSV (Spreadsheet)" value="csv" />
            <v-radio label="FHIR Bundle (Interoperability)" value="fhir" />
            <v-radio label="JSON (Raw Data)" value="json" />
          </v-radio-group>

          <v-checkbox
            v-model="exportOptions.includeContext"
            label="Include text context around matches"
          />
          <v-checkbox
            v-model="exportOptions.anonymize"
            label="Anonymize patient data"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="exportDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="confirmExport"
            :loading="exportLoading"
          >
            Export
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Save Search Dialog -->
    <v-dialog v-model="saveSearchDialog" max-width="500">
      <v-card>
        <v-card-title>Save Search</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="saveSearchName"
            label="Search Name"
            placeholder="e.g., Diabetes patients Q1 2024"
            required
          />
          <v-textarea
            v-model="saveSearchDescription"
            label="Description (optional)"
            rows="2"
          />
          <v-checkbox
            v-model="saveSearchPublic"
            label="Share with other users"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn @click="saveSearchDialog = false">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="confirmSaveSearch"
            :loading="saveLoading"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useNotification } from '@/composables/useNotification';
import { usePatientSearchStore } from '@/stores/patientSearch';
import SearchForm from '@/components/search/SearchForm.vue';
import ResultsTable from '@/components/search/ResultsTable.vue';
import MetaAnnotationFilters from '@/components/search/MetaAnnotationFilters.vue';
import type {
  PatientSearchRequest,
  PatientSearchResult,
  MetaAnnotationFilters as MetaFilters,
  SavedSearch,
} from '@/types/search';

const router = useRouter();
const { showSuccess, showError } = useNotification();
const searchStore = usePatientSearchStore();

// Search state
const loading = ref(false);
const searchPerformed = ref(false);
const results = ref<PatientSearchResult[]>([]);
const totalResults = ref(0);
const queryTime = ref(0);

// Pagination
const currentPage = ref(1);
const itemsPerPage = ref(20);

// Filters
const showAdvancedFilters = ref(false);
const metaFilters = ref<MetaFilters>({
  negation: 'Affirmed',
  temporality: ['Current', 'Recent'],
  experiencer: 'Patient',
  certainty: ['Confirmed'],
  confidence_min: 0.7,
});

// Saved searches
const savedSearches = ref<SavedSearch[]>([]);
const saveSearchDialog = ref(false);
const saveSearchName = ref('');
const saveSearchDescription = ref('');
const saveSearchPublic = ref(false);
const saveLoading = ref(false);

// Export
const exportDialog = ref(false);
const exportFormat = ref('csv');
const exportOptions = ref({
  includeContext: false,
  anonymize: false,
});
const exportLoading = ref(false);

// Current search parameters (for saving/exporting)
const currentSearchParams = ref<PatientSearchRequest | null>(null);

/**
 * Handle search submission
 */
async function handleSearch(searchParams: PatientSearchRequest) {
  loading.value = true;
  searchPerformed.value = true;

  try {
    // Store current search parameters
    currentSearchParams.value = {
      ...searchParams,
      filters: metaFilters.value,
      limit: itemsPerPage.value,
      offset: (currentPage.value - 1) * itemsPerPage.value,
    };

    // Execute search
    const response = await searchStore.searchPatients(currentSearchParams.value);

    // Update results
    results.value = response.results;
    totalResults.value = response.total;
    queryTime.value = response.query_time_ms;

    // Show filters if we have results
    if (response.total > 0) {
      showAdvancedFilters.value = true;
    }

    showSuccess(`Found ${response.total} patients in ${response.query_time_ms}ms`);
  } catch (error: any) {
    showError(error.message || 'Search failed. Please try again.');
    results.value = [];
    totalResults.value = 0;
  } finally {
    loading.value = false;
  }
}

/**
 * Handle clear search
 */
function handleClear() {
  results.value = [];
  totalResults.value = 0;
  searchPerformed.value = false;
  showAdvancedFilters.value = false;
  currentPage.value = 1;
  currentSearchParams.value = null;
}

/**
 * Handle filter update
 */
async function handleFilterUpdate() {
  if (currentSearchParams.value) {
    await handleSearch(currentSearchParams.value);
  }
}

/**
 * Handle page change
 */
async function handlePageChange(page: number) {
  currentPage.value = page;
  if (currentSearchParams.value) {
    await handleSearch(currentSearchParams.value);
  }
}

/**
 * Handle items per page change
 */
async function handleItemsPerPageChange(items: number) {
  itemsPerPage.value = items;
  currentPage.value = 1; // Reset to first page
  if (currentSearchParams.value) {
    await handleSearch(currentSearchParams.value);
  }
}

/**
 * Handle view patient
 */
function handleViewPatient(patient: PatientSearchResult) {
  router.push({
    name: 'PatientTimeline',
    params: { id: patient.patient_id },
  });
}

/**
 * Handle export
 */
function handleExport() {
  if (results.value.length === 0) {
    showError('No results to export');
    return;
  }
  exportDialog.value = true;
}

/**
 * Confirm export
 */
async function confirmExport() {
  exportLoading.value = true;

  try {
    const patientIds = results.value.map(r => r.patient_id);

    await searchStore.exportResults({
      format: exportFormat.value as 'csv' | 'fhir' | 'json',
      patient_ids: patientIds,
      include_concepts: true,
      include_context: exportOptions.value.includeContext,
      anonymize: exportOptions.value.anonymize,
    });

    showSuccess(`Export completed successfully`);
    exportDialog.value = false;
  } catch (error: any) {
    showError(error.message || 'Export failed');
  } finally {
    exportLoading.value = false;
  }
}

/**
 * Handle load saved search
 */
async function handleLoadSaved(savedSearch: SavedSearch) {
  // Load the saved search parameters
  const searchParams = savedSearch.search_request;
  metaFilters.value = searchParams.filters;
  await handleSearch(searchParams);
}

/**
 * Confirm save search
 */
async function confirmSaveSearch() {
  if (!saveSearchName.value || !currentSearchParams.value) {
    showError('Please provide a name for the saved search');
    return;
  }

  saveLoading.value = true;

  try {
    await searchStore.saveSearch({
      name: saveSearchName.value,
      description: saveSearchDescription.value || undefined,
      search_request: currentSearchParams.value,
      is_public: saveSearchPublic.value,
    });

    showSuccess('Search saved successfully');
    saveSearchDialog.value = false;

    // Refresh saved searches
    await loadSavedSearches();

    // Reset form
    saveSearchName.value = '';
    saveSearchDescription.value = '';
    saveSearchPublic.value = false;
  } catch (error: any) {
    showError(error.message || 'Failed to save search');
  } finally {
    saveLoading.value = false;
  }
}

/**
 * Load saved searches
 */
async function loadSavedSearches() {
  try {
    savedSearches.value = await searchStore.getSavedSearches();
  } catch (error) {
  }
}

// Load saved searches on mount
onMounted(() => {
  loadSavedSearches();
});
</script>

<style scoped>
/* Add any custom styles here */
</style>