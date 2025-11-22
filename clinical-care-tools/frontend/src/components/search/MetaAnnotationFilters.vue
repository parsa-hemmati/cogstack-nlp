<template>
  <v-card elevation="2">
    <v-card-title class="text-h6">
      <v-icon start>mdi-filter-variant</v-icon>
      Meta-Annotation Filters
      <v-spacer />
      <v-chip size="small" color="success" variant="tonal">
        95% Precision Mode
      </v-chip>
    </v-card-title>

    <v-card-subtitle>
      Fine-tune search results by filtering medical concept attributes
    </v-card-subtitle>

    <v-card-text>
      <v-alert
        type="info"
        variant="tonal"
        density="compact"
        class="mb-4"
      >
        <strong>Meta-annotations</strong> help achieve 95% precision by excluding:
        negated mentions, historical conditions, family history, and hypothetical scenarios.
      </v-alert>

      <v-row>
        <!-- Negation Filter -->
        <v-col cols="12" md="6">
          <div class="mb-2">
            <strong>Negation</strong>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small" class="ml-1">
                  mdi-information-outline
                </v-icon>
              </template>
              <div>
                <strong>Affirmed:</strong> Patient HAS the condition<br>
                <strong>Negated:</strong> Patient DOES NOT have it (e.g., "denies chest pain")<br>
                <strong>Possible:</strong> Uncertain negation
              </div>
            </v-tooltip>
          </div>

          <v-radio-group
            v-model="localFilters.negation"
            density="compact"
            hide-details
          >
            <v-radio
              label="Affirmed (patient has condition)"
              value="Affirmed"
              color="success"
            />
            <v-radio
              label="Negated (patient doesn't have)"
              value="Negated"
              color="error"
            />
            <v-radio
              label="Possible (uncertain)"
              value="Possible"
              color="warning"
            />
          </v-radio-group>
        </v-col>

        <!-- Temporality Filter -->
        <v-col cols="12" md="6">
          <div class="mb-2">
            <strong>Temporality</strong>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small" class="ml-1">
                  mdi-information-outline
                </v-icon>
              </template>
              <div>
                <strong>Current:</strong> Active conditions<br>
                <strong>Recent:</strong> Within past few months<br>
                <strong>Historical:</strong> Past medical history<br>
                <strong>Future:</strong> Planned or risk of
              </div>
            </v-tooltip>
          </div>

          <v-checkbox
            v-for="option in temporalityOptions"
            :key="option.value"
            v-model="localFilters.temporality"
            :label="option.label"
            :value="option.value"
            :color="option.color"
            density="compact"
            hide-details
          />
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <v-row>
        <!-- Experiencer Filter -->
        <v-col cols="12" md="6">
          <div class="mb-2">
            <strong>Experiencer</strong>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small" class="ml-1">
                  mdi-information-outline
                </v-icon>
              </template>
              <div>
                <strong>Patient:</strong> The patient themselves<br>
                <strong>Family:</strong> Family history (e.g., "mother had diabetes")<br>
                <strong>Other:</strong> Someone else mentioned
              </div>
            </v-tooltip>
          </div>

          <v-radio-group
            v-model="localFilters.experiencer"
            density="compact"
            hide-details
          >
            <v-radio
              label="Patient (self)"
              value="Patient"
              color="primary"
            />
            <v-radio
              label="Family (family history)"
              value="Family"
              color="orange"
            />
            <v-radio
              label="Other (someone else)"
              value="Other"
              color="grey"
            />
          </v-radio-group>
        </v-col>

        <!-- Certainty Filter -->
        <v-col cols="12" md="6">
          <div class="mb-2">
            <strong>Certainty</strong>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small" class="ml-1">
                  mdi-information-outline
                </v-icon>
              </template>
              <div>
                <strong>Confirmed:</strong> Definite diagnosis<br>
                <strong>Suspected:</strong> Likely but not confirmed<br>
                <strong>Hypothetical:</strong> "If patient develops..."<br>
                <strong>Negative:</strong> Ruled out
              </div>
            </v-tooltip>
          </div>

          <v-checkbox
            v-for="option in certaintyOptions"
            :key="option.value"
            v-model="localFilters.certainty"
            :label="option.label"
            :value="option.value"
            :color="option.color"
            density="compact"
            hide-details
          />
        </v-col>
      </v-row>

      <v-divider class="my-4" />

      <!-- Confidence Threshold -->
      <v-row>
        <v-col>
          <div class="mb-2">
            <strong>Confidence Threshold</strong>
            <v-tooltip location="top">
              <template v-slot:activator="{ props }">
                <v-icon v-bind="props" size="small" class="ml-1">
                  mdi-information-outline
                </v-icon>
              </template>
              <div>
                Minimum confidence score for concept matches.<br>
                Higher values = fewer but more accurate results.<br>
                Recommended: 0.7 (70%) or higher.
              </div>
            </v-tooltip>
          </div>

          <v-slider
            v-model="localFilters.confidence_min"
            :min="0"
            :max="1"
            :step="0.05"
            thumb-label="always"
            :color="getConfidenceColor(localFilters.confidence_min)"
          >
            <template v-slot:thumb-label="{ modelValue }">
              {{ (modelValue * 100).toFixed(0) }}%
            </template>
            <template v-slot:prepend>
              <v-icon>mdi-gauge-low</v-icon>
            </template>
            <template v-slot:append>
              <v-icon>mdi-gauge-full</v-icon>
            </template>
          </v-slider>

          <div class="text-center">
            <v-chip
              size="small"
              :color="getConfidenceColor(localFilters.confidence_min)"
              variant="tonal"
            >
              {{ getConfidenceLabel(localFilters.confidence_min) }}
            </v-chip>
          </div>
        </v-col>
      </v-row>

      <!-- Presets -->
      <v-divider class="my-4" />

      <div class="mb-2"><strong>Quick Presets</strong></div>
      <v-chip-group
        v-model="selectedPreset"
        @update:model-value="applyPreset"
      >
        <v-chip
          v-for="preset in presets"
          :key="preset.name"
          :value="preset.name"
          variant="outlined"
        >
          <v-icon start size="small">{{ preset.icon }}</v-icon>
          {{ preset.label }}
        </v-chip>
      </v-chip-group>

      <!-- Actions -->
      <v-row class="mt-4">
        <v-col>
          <v-btn
            color="primary"
            variant="flat"
            @click="applyFilters"
            :disabled="!hasChanges"
          >
            <v-icon start>mdi-check</v-icon>
            Apply Filters
          </v-btn>

          <v-btn
            variant="outlined"
            class="ml-2"
            @click="resetFilters"
          >
            <v-icon start>mdi-restore</v-icon>
            Reset to Default
          </v-btn>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { cloneDeep, isEqual } from 'lodash-es';
import type { MetaAnnotationFilters } from '@/types/search';

// Props & Emits
interface Props {
  modelValue: MetaAnnotationFilters;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: MetaAnnotationFilters];
  'update': [];
}>();

// Default filters
const defaultFilters: MetaAnnotationFilters = {
  negation: 'Affirmed',
  temporality: ['Current', 'Recent'],
  experiencer: 'Patient',
  certainty: ['Confirmed'],
  confidence_min: 0.7,
};

// Local state
const localFilters = ref<MetaAnnotationFilters>(cloneDeep(props.modelValue));
const selectedPreset = ref<string | null>(null);

// Options
const temporalityOptions = [
  { value: 'Current', label: 'Current (active)', color: 'success' },
  { value: 'Recent', label: 'Recent (past few months)', color: 'primary' },
  { value: 'Historical', label: 'Historical (past)', color: 'warning' },
  { value: 'Future', label: 'Future (planned/risk)', color: 'info' },
];

const certaintyOptions = [
  { value: 'Confirmed', label: 'Confirmed', color: 'success' },
  { value: 'Suspected', label: 'Suspected', color: 'warning' },
  { value: 'Hypothetical', label: 'Hypothetical', color: 'info' },
  { value: 'Negative', label: 'Negative (ruled out)', color: 'error' },
];

// Presets
const presets = [
  {
    name: 'active',
    label: 'Active Conditions',
    icon: 'mdi-heart-pulse',
    filters: {
      negation: 'Affirmed',
      temporality: ['Current'],
      experiencer: 'Patient',
      certainty: ['Confirmed'],
      confidence_min: 0.8,
    },
  },
  {
    name: 'recent',
    label: 'Recent & Current',
    icon: 'mdi-calendar-clock',
    filters: {
      negation: 'Affirmed',
      temporality: ['Current', 'Recent'],
      experiencer: 'Patient',
      certainty: ['Confirmed', 'Suspected'],
      confidence_min: 0.7,
    },
  },
  {
    name: 'comprehensive',
    label: 'Comprehensive',
    icon: 'mdi-select-all',
    filters: {
      negation: 'Affirmed',
      temporality: ['Current', 'Recent', 'Historical'],
      experiencer: 'Patient',
      certainty: ['Confirmed', 'Suspected'],
      confidence_min: 0.6,
    },
  },
  {
    name: 'family',
    label: 'Family History',
    icon: 'mdi-account-group',
    filters: {
      negation: 'Affirmed',
      temporality: ['Current', 'Recent', 'Historical'],
      experiencer: 'Family',
      certainty: ['Confirmed'],
      confidence_min: 0.7,
    },
  },
];

// Computed
const hasChanges = computed(() => {
  return !isEqual(localFilters.value, props.modelValue);
});

// Methods
function applyFilters() {
  emit('update:modelValue', cloneDeep(localFilters.value));
  emit('update');
}

function resetFilters() {
  localFilters.value = cloneDeep(defaultFilters);
  selectedPreset.value = null;
}

function applyPreset(presetName: string) {
  const preset = presets.find(p => p.name === presetName);
  if (preset) {
    localFilters.value = cloneDeep(preset.filters) as MetaAnnotationFilters;
  }
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'success';
  if (confidence >= 0.7) return 'primary';
  if (confidence >= 0.5) return 'warning';
  return 'error';
}

function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.9) return 'Very High Confidence';
  if (confidence >= 0.7) return 'High Confidence';
  if (confidence >= 0.5) return 'Medium Confidence';
  return 'Low Confidence';
}

// Watch for external changes
watch(() => props.modelValue, (newValue) => {
  localFilters.value = cloneDeep(newValue);
}, { deep: true });
</script>

<style scoped>
/* Add any custom styles here */
</style>