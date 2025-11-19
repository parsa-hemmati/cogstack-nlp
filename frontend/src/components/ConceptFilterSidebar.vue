<template>
  <v-navigation-drawer
    v-model="visible"
    location="right"
    width="380"
    temporary
  >
    <v-card flat>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2">mdi-filter-variant</v-icon>
        Timeline Filters
        <v-spacer />
        <v-btn
          icon="mdi-close"
          variant="text"
          size="small"
          @click="visible = false"
        />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <!-- Concept Filter -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3">
            Clinical Concepts
          </v-card-title>
          <v-card-text>
            <v-autocomplete
              v-model="selectedConcepts"
              v-model:search="conceptSearch"
              :items="conceptSuggestions"
              :loading="loadingConcepts"
              label="Search concepts"
              placeholder="Type to search (e.g., diabetes, hypertension)"
              item-title="display"
              item-value="cui"
              multiple
              chips
              closable-chips
              clearable
              hide-details="auto"
              prepend-inner-icon="mdi-magnify"
            >
              <template #chip="{ props, item }">
                <v-chip
                  v-bind="props"
                  closable
                  size="small"
                  @click:close="removeConcept(item.raw.cui)"
                >
                  {{ item.raw.name }}
                </v-chip>
              </template>
            </v-autocomplete>
          </v-card-text>
        </v-card>

        <!-- Date Range Filter -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3">
            Date Range
          </v-card-title>
          <v-card-text>
            <v-select
              v-model="dateRangePreset"
              :items="dateRangePresets"
              label="Quick select"
              hide-details="auto"
              class="mb-3"
              @update:model-value="applyDatePreset"
            />

            <v-text-field
              v-model="dateFrom"
              label="From date"
              type="date"
              hide-details="auto"
              class="mb-2"
            />

            <v-text-field
              v-model="dateTo"
              label="To date"
              type="date"
              hide-details="auto"
            />
          </v-card-text>
        </v-card>

        <!-- Meta-Annotation Filters -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3">
            Meta-Annotations
            <v-tooltip location="top">
              <template #activator="{ props }">
                <v-icon
                  v-bind="props"
                  size="small"
                  class="ml-1"
                >
                  mdi-information-outline
                </v-icon>
              </template>
              <div style="max-width: 300px">
                Filters for concept context. Defaults exclude negated conditions,
                family history, and historical mentions for safer clinical queries.
              </div>
            </v-tooltip>
          </v-card-title>
          <v-card-text>
            <!-- Negation -->
            <div class="mb-3">
              <div class="text-subtitle-2 mb-1">Negation</div>
              <v-chip-group
                v-model="metaNegation"
                mandatory
                column
              >
                <v-chip
                  value="Affirmed"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Affirmed
                </v-chip>
                <v-chip
                  value="Negated"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Negated
                </v-chip>
              </v-chip-group>
            </div>

            <!-- Experiencer -->
            <div class="mb-3">
              <div class="text-subtitle-2 mb-1">Experiencer</div>
              <v-chip-group
                v-model="metaExperiencer"
                mandatory
                column
              >
                <v-chip
                  value="Patient"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Patient
                </v-chip>
                <v-chip
                  value="Family"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Family
                </v-chip>
                <v-chip
                  value="Other"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Other
                </v-chip>
              </v-chip-group>
            </div>

            <!-- Temporality -->
            <div class="mb-3">
              <div class="text-subtitle-2 mb-1">Temporality</div>
              <v-chip-group
                v-model="metaTemporality"
                multiple
                column
              >
                <v-chip
                  value="Current"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Current
                </v-chip>
                <v-chip
                  value="Recent"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Recent
                </v-chip>
                <v-chip
                  value="Historical"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Historical
                </v-chip>
              </v-chip-group>
            </div>

            <!-- Certainty -->
            <div>
              <div class="text-subtitle-2 mb-1">Certainty (Optional)</div>
              <v-chip-group
                v-model="metaCertainty"
                column
              >
                <v-chip
                  value="High"
                  filter
                  variant="outlined"
                  size="small"
                >
                  High
                </v-chip>
                <v-chip
                  value="Medium"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Medium
                </v-chip>
                <v-chip
                  value="Low"
                  filter
                  variant="outlined"
                  size="small"
                >
                  Low
                </v-chip>
              </v-chip-group>
            </div>
          </v-card-text>
        </v-card>

        <!-- Document Type Filters -->
        <v-card variant="outlined" class="mb-4">
          <v-card-title class="text-subtitle-1 pa-3">
            Document Types
          </v-card-title>
          <v-card-text>
            <v-checkbox
              v-for="docType in documentTypeOptions"
              :key="docType.value"
              v-model="selectedDocumentTypes"
              :label="docType.label"
              :value="docType.value"
              hide-details
              density="compact"
            />
          </v-card-text>
        </v-card>
      </v-card-text>

      <v-divider />

      <!-- Action Buttons -->
      <v-card-actions class="pa-4">
        <v-btn
          color="primary"
          variant="flat"
          block
          prepend-icon="mdi-filter"
          @click="handleApplyFilters"
        >
          Apply Filters
        </v-btn>
      </v-card-actions>

      <v-card-actions class="pa-4 pt-0">
        <v-btn
          variant="outlined"
          block
          prepend-icon="mdi-filter-off"
          @click="handleClearFilters"
        >
          Clear Filters
        </v-btn>
      </v-card-actions>

      <v-card-actions class="pa-4 pt-0">
        <v-btn
          variant="text"
          block
          prepend-icon="mdi-content-save"
          @click="handleSavePreset"
        >
          Save as Preset
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useTimelineFilters } from '@/composables/useTimelineFilters'

interface Props {
  modelValue: boolean
  patientId: string
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'filters-applied', filters: any): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Sidebar visibility (v-model)
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

// Concept search
const conceptSearch = ref('')
const loadingConcepts = ref(false)
const conceptSuggestions = ref<Array<{ cui: string; name: string; display: string }>>([])
const selectedConcepts = ref<string[]>([])

// Watch concept search with debounce
let searchTimeout: NodeJS.Timeout
watch(conceptSearch, (newValue) => {
  if (!newValue || newValue.length < 2) {
    conceptSuggestions.value = []
    return
  }

  loadingConcepts.value = true
  clearTimeout(searchTimeout)

  searchTimeout = setTimeout(async () => {
    try {
      // Mock concept search for now (integrate with real API later)
      const mockConcepts = [
        { cui: 'C0011849', name: 'Diabetes Mellitus', display: 'Diabetes Mellitus (C0011849)' },
        { cui: 'C0020538', name: 'Hypertension', display: 'Hypertension (C0020538)' },
        { cui: 'C0004238', name: 'Atrial Fibrillation', display: 'Atrial Fibrillation (C0004238)' },
        { cui: 'C0018802', name: 'Heart Failure', display: 'Heart Failure (C0018802)' },
        { cui: 'C0011860', name: 'Type 2 Diabetes', display: 'Type 2 Diabetes (C0011860)' }
      ]

      conceptSuggestions.value = mockConcepts.filter(c =>
        c.name.toLowerCase().includes(newValue.toLowerCase())
      )
    } finally {
      loadingConcepts.value = false
    }
  }, 300)
})

// Date range
const dateFrom = ref('')
const dateTo = ref('')
const dateRangePreset = ref('')
const dateRangePresets = [
  { title: 'All time', value: 'all' },
  { title: 'Last 3 months', value: '3m' },
  { title: 'Last 6 months', value: '6m' },
  { title: 'Last year', value: '1y' },
  { title: 'Custom range', value: 'custom' }
]

function applyDatePreset(preset: string) {
  const now = new Date()
  const today = now.toISOString().split('T')[0]

  if (preset === 'all') {
    dateFrom.value = ''
    dateTo.value = ''
  } else if (preset === '3m') {
    const threeMonthsAgo = new Date(now.setMonth(now.getMonth() - 3))
    dateFrom.value = threeMonthsAgo.toISOString().split('T')[0]
    dateTo.value = today
  } else if (preset === '6m') {
    const sixMonthsAgo = new Date(now.setMonth(now.getMonth() - 6))
    dateFrom.value = sixMonthsAgo.toISOString().split('T')[0]
    dateTo.value = today
  } else if (preset === '1y') {
    const oneYearAgo = new Date(now.setFullYear(now.getFullYear() - 1))
    dateFrom.value = oneYearAgo.toISOString().split('T')[0]
    dateTo.value = today
  }
  // preset === 'custom' does nothing, user sets manually
}

// Meta-annotations (with safe clinical defaults)
const metaNegation = ref('Affirmed')
const metaExperiencer = ref('Patient')
const metaTemporality = ref<string[]>(['Current', 'Recent'])
const metaCertainty = ref<string | null>(null)

// Document types
const documentTypeOptions = [
  { label: 'Clinical Notes', value: 'clinical_note' },
  { label: 'Discharge Summaries', value: 'discharge_summary' },
  { label: 'Lab Reports', value: 'lab_result' },
  { label: 'Radiology Reports', value: 'radiology' },
  { label: 'Pathology Reports', value: 'pathology' }
]
const selectedDocumentTypes = ref<string[]>([])

// Remove concept from selection
function removeConcept(cui: string) {
  selectedConcepts.value = selectedConcepts.value.filter(c => c !== cui)
}

// Apply filters
function handleApplyFilters() {
  const filters = {
    conceptCuis: selectedConcepts.value,
    dateFrom: dateFrom.value ? new Date(dateFrom.value) : null,
    dateTo: dateTo.value ? new Date(dateTo.value) : null,
    metaAnnotations: {
      Negation: metaNegation.value,
      Experiencer: metaExperiencer.value,
      Temporality: metaTemporality.value,
      ...(metaCertainty.value && { Certainty: metaCertainty.value })
    },
    documentTypes: selectedDocumentTypes.value,
    includeDocuments: true,
    includeConcepts: true
  }

  emit('filters-applied', filters)
  visible.value = false
}

// Clear all filters
function handleClearFilters() {
  selectedConcepts.value = []
  dateFrom.value = ''
  dateTo.value = ''
  dateRangePreset.value = 'all'
  metaNegation.value = 'Affirmed'
  metaExperiencer.value = 'Patient'
  metaTemporality.value = ['Current', 'Recent']
  metaCertainty.value = null
  selectedDocumentTypes.value = []

  handleApplyFilters()
}

// Save preset (emit event for parent to handle)
function handleSavePreset() {
  // Future: Open dialog to save preset
  console.log('Save preset clicked - to be implemented in Task 5.4.6')
}
</script>

<style scoped>
.v-card {
  box-shadow: none !important;
}
</style>
