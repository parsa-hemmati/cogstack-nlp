<template>
  <v-card class="timeline-filters">
    <v-card-title class="text-h6">Timeline Filters</v-card-title>

    <v-card-text>
      <!-- Concept Search Autocomplete -->
      <v-autocomplete
        v-model="localFilters.concept_cuis"
        :items="conceptSuggestions"
        item-title="name"
        item-value="cui"
        label="Search Concepts"
        placeholder="Type to search medical concepts..."
        multiple
        chips
        closable-chips
        clearable
        @update:search="searchConcepts"
      >
        <template #chip="{ item }">
          <v-chip size="small" closable>
            {{ item.title }}
          </v-chip>
        </template>
      </v-autocomplete>

      <!-- Date Range Pickers -->
      <v-text-field
        v-model="localFilters.date_start"
        label="Start Date"
        type="date"
        name="date_start"
        clearable
        @update:model-value="updateFilters"
      />

      <v-text-field
        v-model="localFilters.date_end"
        label="End Date"
        type="date"
        name="date_end"
        clearable
        @update:model-value="updateFilters"
      />

      <!-- Document Types Multi-Select -->
      <v-select
        v-model="localFilters.document_types"
        :items="documentTypeOptions"
        label="Document Types"
        multiple
        chips
        clearable
        @update:model-value="updateFilters"
      />

      <!-- Meta-Annotations Section -->
      <v-divider class="my-4" />
      <div class="text-subtitle-2 mb-2">Meta-Annotations</div>

      <!-- Negation Filter -->
      <v-checkbox
        v-model="negationAffirmed"
        label="Only Affirmed (exclude negated mentions)"
        value="Affirmed"
        @update:model-value="updateNegation"
      />

      <!-- Experiencer Filter -->
      <v-checkbox
        v-model="experiencerPatient"
        label="Only Patient (exclude family history)"
        value="Patient"
        @update:model-value="updateExperiencer"
      />

      <!-- Temporality Filter -->
      <div class="text-caption mb-2">Temporality</div>
      <v-checkbox
        v-model="temporalityCurrent"
        label="Current"
        value="Current"
        dense
        @update:model-value="updateTemporality"
      />
      <v-checkbox
        v-model="temporalityRecent"
        label="Recent"
        value="Recent"
        dense
        @update:model-value="updateTemporality"
      />
      <v-checkbox
        v-model="temporalityHistorical"
        label="Historical"
        value="Historical"
        dense
        @update:model-value="updateTemporality"
      />

      <!-- Load Preset -->
      <v-divider class="my-4" />
      <v-select
        v-model="selectedPreset"
        :items="filterPresets"
        item-title="name"
        item-value="id"
        label="Load Saved Filter"
        clearable
        @update:model-value="loadPreset"
      />
    </v-card-text>

    <v-card-actions class="justify-space-between">
      <div>
        <v-btn
          color="primary"
          variant="flat"
          data-testid="apply-filters"
          @click="handleApply"
        >
          Apply
        </v-btn>
        <v-btn
          variant="text"
          data-testid="clear-filters"
          @click="handleClear"
        >
          Clear
        </v-btn>
      </div>

      <v-btn
        color="secondary"
        variant="outlined"
        data-testid="save-preset"
        @click="handleSavePreset"
      >
        Save Preset
      </v-btn>
    </v-card-actions>

    <!-- Save Preset Dialog -->
    <v-dialog v-model="savePresetDialog" max-width="500">
      <v-card>
        <v-card-title>Save Filter Preset</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="presetName"
            label="Preset Name"
            :rules="[rules.required, rules.minLength]"
          />
          <v-textarea
            v-model="presetDescription"
            label="Description (optional)"
            rows="3"
          />
          <v-checkbox
            v-model="presetIsDefault"
            label="Set as default filter"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="savePresetDialog = false">Cancel</v-btn>
          <v-btn color="primary" variant="flat" @click="savePreset">Save</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type {
  TimelineFilters,
  FilterPresetResponse,
  NegationValue,
  ExperiencerValue,
  TemporalityValue,
} from '@/types/timeline'

// Props
interface Props {
  modelValue: TimelineFilters
  filterPresets?: FilterPresetResponse[]
}

const props = withDefaults(defineProps<Props>(), {
  filterPresets: () => [],
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [filters: TimelineFilters]
  apply: []
  clear: []
  'save-preset': [name: string, description: string | undefined, filters: TimelineFilters, isDefault: boolean]
}>()

// Local state
const localFilters = ref<TimelineFilters>({ ...props.modelValue })
const conceptSuggestions = ref<Array<{ cui: string; name: string }>>([])
const selectedPreset = ref<string | null>(null)

// Meta-annotation checkbox states
const negationAffirmed = ref(props.modelValue.negation === 'Affirmed')
const experiencerPatient = ref(props.modelValue.experiencer === 'Patient')
const temporalityCurrent = ref(props.modelValue.temporality === 'Current')
const temporalityRecent = ref(props.modelValue.temporality === 'Recent')
const temporalityHistorical = ref(props.modelValue.temporality === 'Historical')

// Save preset dialog state
const savePresetDialog = ref(false)
const presetName = ref('')
const presetDescription = ref('')
const presetIsDefault = ref(false)

// Document type options
const documentTypeOptions = ['discharge', 'clinic', 'pathology', 'radiology', 'lab']

// Validation rules
const rules = {
  required: (value: string) => !!value || 'Required',
  minLength: (value: string) => value.length >= 3 || 'Minimum 3 characters',
}

// Methods
function updateFilters() {
  emit('update:modelValue', { ...localFilters.value })
}

function updateNegation(value: boolean) {
  localFilters.value.negation = value ? ('Affirmed' as NegationValue) : undefined
  updateFilters()
}

function updateExperiencer(value: boolean) {
  localFilters.value.experiencer = value ? ('Patient' as ExperiencerValue) : undefined
  updateFilters()
}

function updateTemporality() {
  const selected: TemporalityValue[] = []
  if (temporalityCurrent.value) selected.push('Current' as TemporalityValue)
  if (temporalityRecent.value) selected.push('Recent' as TemporalityValue)
  if (temporalityHistorical.value) selected.push('Historical' as TemporalityValue)

  localFilters.value.temporality = selected.length > 0 ? selected[0] : undefined
  updateFilters()
}

function searchConcepts(query: string) {
  // In production, this would call an API to search SNOMED-CT concepts
  // For now, use mock data
  if (query && query.length >= 2) {
    conceptSuggestions.value = [
      { cui: 'C0011860', name: 'Diabetes Mellitus' },
      { cui: 'C0020538', name: 'Hypertension' },
      { cui: 'C0004238', name: 'Atrial Fibrillation' },
    ]
  }
}

function loadPreset(presetId: string | null) {
  if (!presetId) return

  const preset = props.filterPresets.find((p) => p.id === presetId)
  if (preset) {
    localFilters.value = { ...preset.filters as TimelineFilters }
    updateFilters()
  }
}

function handleApply() {
  emit('apply')
}

function handleClear() {
  localFilters.value = {
    date_start: undefined,
    date_end: undefined,
    concept_cuis: [],
    document_types: [],
    negation: undefined,
    experiencer: undefined,
    temporality: undefined,
    certainty: undefined,
  }
  updateFilters()
  emit('clear')
}

function handleSavePreset() {
  savePresetDialog.value = true
}

function savePreset() {
  if (!presetName.value || presetName.value.length < 3) return

  emit('save-preset', presetName.value, presetDescription.value, localFilters.value, presetIsDefault.value)

  // Reset dialog
  savePresetDialog.value = false
  presetName.value = ''
  presetDescription.value = ''
  presetIsDefault.value = false
}

// Watch for external changes to modelValue
watch(
  () => props.modelValue,
  (newValue) => {
    localFilters.value = { ...newValue }
  },
  { deep: true }
)
</script>

<style scoped>
.timeline-filters {
  height: 100%;
  overflow-y: auto;
}
</style>
