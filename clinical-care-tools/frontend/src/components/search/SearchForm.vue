<template>
  <v-card elevation="2">
    <v-card-text>
      <v-form @submit.prevent="handleSubmit">
        <!-- Main Search Input with Autocomplete -->
        <v-row>
          <v-col cols="12" md="8">
            <v-autocomplete
              v-model="searchQuery"
              v-model:search="searchInput"
              :items="suggestions"
              :loading="suggestionsLoading"
              item-title="pretty_name"
              item-value="cui"
              label="Search for medical concepts"
              placeholder="e.g., diabetes, atrial fibrillation, hypertension"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details="auto"
              variant="outlined"
              density="comfortable"
              :custom-filter="() => true"
              @update:search="fetchSuggestions"
            >
              <template v-slot:item="{ props, item }">
                <v-list-item
                  v-bind="props"
                  :title="item.raw.pretty_name"
                  :subtitle="`${item.raw.cui} - ${item.raw.semantic_type}`"
                >
                  <template v-slot:prepend>
                    <v-icon :color="getSemanticTypeColor(item.raw.semantic_type)">
                      {{ getSemanticTypeIcon(item.raw.semantic_type) }}
                    </v-icon>
                  </template>
                </v-list-item>
              </template>

              <template v-slot:no-data>
                <v-list-item>
                  <v-list-item-title>
                    Type to search for medical concepts...
                  </v-list-item-title>
                </v-list-item>
              </template>
            </v-autocomplete>
          </v-col>

          <v-col cols="12" md="4">
            <v-btn-toggle
              v-model="searchMode"
              mandatory
              divided
              variant="outlined"
              density="comfortable"
            >
              <v-btn value="simple" size="small">
                <v-icon start>mdi-magnify</v-icon>
                Simple
              </v-btn>
              <v-btn value="advanced" size="small">
                <v-icon start>mdi-filter</v-icon>
                Advanced
              </v-btn>
              <v-btn value="boolean" size="small">
                <v-icon start>mdi-code-brackets</v-icon>
                Boolean
              </v-btn>
            </v-btn-toggle>
          </v-col>
        </v-row>

        <!-- Advanced Search Options -->
        <v-expand-transition>
          <div v-if="searchMode === 'advanced'">
            <v-divider class="my-4" />

            <v-row>
              <!-- Date Range -->
              <v-col cols="12" md="6">
                <v-row>
                  <v-col cols="6">
                    <v-text-field
                      v-model="dateFrom"
                      label="From Date"
                      type="date"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                  <v-col cols="6">
                    <v-text-field
                      v-model="dateTo"
                      label="To Date"
                      type="date"
                      variant="outlined"
                      density="compact"
                      hide-details
                    />
                  </v-col>
                </v-row>
              </v-col>

              <!-- Document Types -->
              <v-col cols="12" md="6">
                <v-select
                  v-model="documentTypes"
                  :items="availableDocumentTypes"
                  label="Document Types"
                  multiple
                  chips
                  closable-chips
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>

            <v-row class="mt-2">
              <!-- Departments -->
              <v-col cols="12" md="6">
                <v-select
                  v-model="departments"
                  :items="availableDepartments"
                  label="Departments"
                  multiple
                  chips
                  closable-chips
                  variant="outlined"
                  density="compact"
                  hide-details
                />
              </v-col>

              <!-- Confidence Threshold -->
              <v-col cols="12" md="6">
                <v-slider
                  v-model="confidenceThreshold"
                  label="Min Confidence"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  thumb-label
                  hide-details
                >
                  <template v-slot:thumb-label="{ modelValue }">
                    {{ (modelValue * 100).toFixed(0) }}%
                  </template>
                </v-slider>
              </v-col>
            </v-row>
          </div>
        </v-expand-transition>

        <!-- Boolean Search Builder -->
        <v-expand-transition>
          <div v-if="searchMode === 'boolean'">
            <v-divider class="my-4" />

            <div v-for="(query, index) in booleanQueries" :key="index">
              <v-row align="center">
                <v-col cols="12" md="3" v-if="index > 0">
                  <v-select
                    v-model="query.operator"
                    :items="['AND', 'OR', 'NOT']"
                    label="Operator"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>

                <v-col :cols="index > 0 ? 7 : 10">
                  <v-text-field
                    v-model="query.concept"
                    label="Medical Concept"
                    variant="outlined"
                    density="compact"
                    hide-details
                  />
                </v-col>

                <v-col cols="2">
                  <v-btn
                    icon
                    variant="text"
                    color="error"
                    @click="removeBooleanQuery(index)"
                    :disabled="booleanQueries.length === 1"
                  >
                    <v-icon>mdi-delete</v-icon>
                  </v-btn>
                </v-col>
              </v-row>
            </div>

            <v-btn
              variant="text"
              color="primary"
              @click="addBooleanQuery"
              class="mt-2"
            >
              <v-icon start>mdi-plus</v-icon>
              Add Condition
            </v-btn>
          </div>
        </v-expand-transition>

        <!-- Saved Searches -->
        <v-expand-transition>
          <div v-if="savedSearches.length > 0">
            <v-divider class="my-4" />

            <v-row>
              <v-col>
                <v-select
                  v-model="selectedSavedSearch"
                  :items="savedSearches"
                  item-title="name"
                  item-value="id"
                  label="Load Saved Search"
                  clearable
                  variant="outlined"
                  density="compact"
                  hide-details
                  @update:model-value="loadSavedSearch"
                >
                  <template v-slot:item="{ props, item }">
                    <v-list-item
                      v-bind="props"
                      :subtitle="item.raw.description"
                    >
                      <template v-slot:append>
                        <v-chip
                          size="x-small"
                          :color="item.raw.is_public ? 'success' : 'grey'"
                        >
                          {{ item.raw.is_public ? 'Public' : 'Private' }}
                        </v-chip>
                      </template>
                    </v-list-item>
                  </template>
                </v-select>
              </v-col>
            </v-row>
          </div>
        </v-expand-transition>

        <!-- Action Buttons -->
        <v-row class="mt-4">
          <v-col>
            <v-btn
              type="submit"
              color="primary"
              variant="flat"
              size="large"
              :loading="loading"
              :disabled="!canSearch"
            >
              <v-icon start>mdi-magnify</v-icon>
              Search Patients
            </v-btn>

            <v-btn
              variant="outlined"
              size="large"
              class="ml-2"
              @click="handleClear"
              :disabled="loading"
            >
              <v-icon start>mdi-refresh</v-icon>
              Clear
            </v-btn>

            <v-btn
              variant="text"
              size="large"
              class="ml-2"
              @click="showFilters = !showFilters"
            >
              <v-icon start>mdi-filter-variant</v-icon>
              Filters
              <v-badge
                v-if="activeFilterCount > 0"
                :content="activeFilterCount"
                color="primary"
                inline
              />
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { debounce } from 'lodash-es';
import { usePatientSearchStore } from '@/stores/patientSearch';
import type {
  ConceptSuggestion,
  PatientSearchRequest,
  SavedSearch,
} from '@/types/search';

// Props
interface Props {
  loading?: boolean;
  savedSearches?: SavedSearch[];
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  savedSearches: () => [],
});

// Emits
const emit = defineEmits<{
  search: [request: PatientSearchRequest];
  clear: [];
  'load-saved': [search: SavedSearch];
}>();

const searchStore = usePatientSearchStore();

// Search state
const searchQuery = ref('');
const searchInput = ref('');
const searchMode = ref<'simple' | 'advanced' | 'boolean'>('simple');
const showFilters = ref(false);

// Autocomplete
const suggestions = ref<ConceptSuggestion[]>([]);
const suggestionsLoading = ref(false);

// Advanced search options
const dateFrom = ref('');
const dateTo = ref('');
const documentTypes = ref<string[]>([]);
const departments = ref<string[]>([]);
const confidenceThreshold = ref(0.7);

// Boolean search
const booleanQueries = ref([
  { concept: '', operator: 'AND' },
]);

// Saved searches
const selectedSavedSearch = ref<string | null>(null);

// Available options (would be loaded from API)
const availableDocumentTypes = [
  'Discharge Summary',
  'Clinical Note',
  'Progress Note',
  'Consultation',
  'Lab Report',
  'Radiology Report',
];

const availableDepartments = [
  'Cardiology',
  'Endocrinology',
  'Internal Medicine',
  'Oncology',
  'Neurology',
  'Psychiatry',
];

// Computed
const canSearch = computed(() => {
  if (searchMode.value === 'boolean') {
    return booleanQueries.value.some(q => q.concept.trim().length > 0);
  }
  return searchQuery.value.trim().length > 0 || searchInput.value.trim().length > 0;
});

const activeFilterCount = computed(() => {
  let count = 0;
  if (dateFrom.value) count++;
  if (dateTo.value) count++;
  if (documentTypes.value.length > 0) count++;
  if (departments.value.length > 0) count++;
  if (confidenceThreshold.value !== 0.7) count++;
  return count;
});

// Methods
const fetchSuggestions = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    suggestions.value = [];
    return;
  }

  suggestionsLoading.value = true;
  try {
    suggestions.value = await searchStore.getConceptSuggestions(query);
  } catch (error) {
    suggestions.value = [];
  } finally {
    suggestionsLoading.value = false;
  }
}, 300);

function handleSubmit() {
  if (!canSearch.value) return;

  const request: PatientSearchRequest = {
    query: searchInput.value || searchQuery.value || '',
    filters: {
      negation: 'Affirmed',
      temporality: ['Current', 'Recent'],
      experiencer: 'Patient',
      certainty: ['Confirmed'],
      confidence_min: confidenceThreshold.value,
    },
    limit: 50,
    offset: 0,
  };

  // Add advanced options if in advanced mode
  if (searchMode.value === 'advanced') {
    if (dateFrom.value) request.date_from = dateFrom.value;
    if (dateTo.value) request.date_to = dateTo.value;
    if (documentTypes.value.length > 0) {
      request.document_types = documentTypes.value;
    }
    if (departments.value.length > 0) {
      request.department_ids = departments.value;
    }
  }

  // Add boolean queries if in boolean mode
  if (searchMode.value === 'boolean') {
    request.queries = booleanQueries.value
      .filter(q => q.concept.trim())
      .map(q => ({
        concept: q.concept,
        operator: q.operator as 'AND' | 'OR' | 'NOT',
      }));
  }

  emit('search', request);
}

function handleClear() {
  searchQuery.value = '';
  searchInput.value = '';
  dateFrom.value = '';
  dateTo.value = '';
  documentTypes.value = [];
  departments.value = [];
  confidenceThreshold.value = 0.7;
  booleanQueries.value = [{ concept: '', operator: 'AND' }];
  selectedSavedSearch.value = null;
  suggestions.value = [];
  emit('clear');
}

function addBooleanQuery() {
  booleanQueries.value.push({ concept: '', operator: 'AND' });
}

function removeBooleanQuery(index: number) {
  if (booleanQueries.value.length > 1) {
    booleanQueries.value.splice(index, 1);
  }
}

function loadSavedSearch(searchId: string | null) {
  if (!searchId) return;

  const savedSearch = props.savedSearches.find(s => s.id === searchId);
  if (savedSearch) {
    emit('load-saved', savedSearch);
  }
}

function getSemanticTypeIcon(type: string): string {
  const iconMap: Record<string, string> = {
    'Disease': 'mdi-virus',
    'Symptom': 'mdi-thermometer',
    'Procedure': 'mdi-medical-bag',
    'Medication': 'mdi-pill',
    'Lab': 'mdi-test-tube',
    'Finding': 'mdi-stethoscope',
  };
  return iconMap[type] || 'mdi-file-medical';
}

function getSemanticTypeColor(type: string): string {
  const colorMap: Record<string, string> = {
    'Disease': 'error',
    'Symptom': 'warning',
    'Procedure': 'info',
    'Medication': 'success',
    'Lab': 'purple',
    'Finding': 'primary',
  };
  return colorMap[type] || 'grey';
}
</script>

<style scoped>
/* Add any custom styles here */
</style>