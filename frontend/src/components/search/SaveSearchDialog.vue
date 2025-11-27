<template>
  <v-dialog
    :model-value="modelValue"
    max-width="500"
    persistent
    data-testid="save-search-dialog"
    aria-labelledby="dialog-title"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title id="dialog-title">
        Save Search
      </v-card-title>

      <v-card-text>
        <!-- Error Alert -->
        <v-alert
          v-if="error"
          type="error"
          variant="tonal"
          closable
          data-testid="error-alert"
          class="mb-4"
          @click:close="error = ''"
        >
          {{ error }}
        </v-alert>

        <!-- Form -->
        <v-form ref="formRef" @submit.prevent="handleSave">
          <!-- Name Input (Required) -->
          <v-text-field
            v-model="name"
            label="Search Name"
            placeholder="e.g., Diabetes Clinical Notes"
            variant="outlined"
            density="comfortable"
            data-testid="name-input"
            :rules="nameRules"
            :error-messages="nameError"
            required
            autofocus
          />

          <!-- Description Input (Optional) -->
          <v-textarea
            v-model="description"
            label="Description (optional)"
            placeholder="Describe what this search is for"
            variant="outlined"
            density="comfortable"
            rows="3"
            data-testid="description-input"
            :error-messages="descriptionError"
          />

          <!-- Query Preview -->
          <v-card variant="outlined" class="pa-3 mb-3">
            <div class="text-caption text-grey mb-1">Query Preview:</div>
            <div class="query-preview">{{ query }}</div>
          </v-card>

          <!-- Filters Preview (if any) -->
          <v-card v-if="hasFilters" variant="outlined" class="pa-3">
            <div class="text-caption text-grey mb-1">Filters:</div>
            <v-chip
              v-for="(value, key) in filters"
              :key="key"
              size="small"
              class="mr-2 mb-2"
            >
              {{ key }}: {{ formatFilterValue(value) }}
            </v-chip>
          </v-card>
        </v-form>
      </v-card-text>

      <v-card-actions>
        <v-spacer />
        <v-btn
          variant="text"
          data-testid="close-btn"
          @click="handleClose"
        >
          Cancel
        </v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          data-testid="save-btn"
          :disabled="!isFormValid"
          :loading="loading"
          @click="handleSave"
        >
          Save Search
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// ============================================================================
// TYPES
// ============================================================================

interface SavedSearchData {
  name: string
  description?: string
  query: string
  filters?: Record<string, any>
}

// ============================================================================
// PROPS & EMITS
// ============================================================================

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false,
  },
  query: {
    type: String,
    required: true,
  },
  filters: {
    type: Object as () => Record<string, any>,
    default: () => ({}),
  },
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'saved': [data: SavedSearchData]
}>()

// ============================================================================
// STATE
// ============================================================================

const formRef = ref<any>(null)
const name = ref('')
const description = ref('')
const loading = ref(false)
const error = ref('')

// Validation
const nameError = ref('')
const descriptionError = ref('')

// Validation rules
const nameRules = [
  (v: string) => !!v || 'Name is required',
  (v: string) => (v && v.length >= 3) || 'Name must be at least 3 characters',
]

// ============================================================================
// COMPUTED PROPERTIES
// ============================================================================

/**
 * Check if filters object has any values
 */
const hasFilters = computed(() => {
  return Object.keys(props.filters).length > 0
})

/**
 * Check if form is valid
 */
const isFormValid = computed(() => {
  return name.value.trim().length >= 3
})

// ============================================================================
// METHODS
// ============================================================================

/**
 * Format filter value for display
 */
function formatFilterValue(value: any): string {
  if (Array.isArray(value)) {
    return value.join(', ')
  }
  return String(value)
}

/**
 * Validate form
 */
function validateForm(): boolean {
  nameError.value = ''
  descriptionError.value = ''

  if (!name.value.trim()) {
    nameError.value = 'Name is required'
    return false
  }

  if (name.value.trim().length < 3) {
    nameError.value = 'Name must be at least 3 characters'
    return false
  }

  return true
}

/**
 * Handle save button click
 */
async function handleSave() {
  if (!validateForm()) {
    return
  }

  loading.value = true
  error.value = ''

  try {
    const savedSearchData: SavedSearchData = {
      name: name.value.trim(),
      description: description.value.trim() || undefined,
      query: props.query,
      filters: hasFilters.value ? props.filters : undefined,
    }

    emit('saved', savedSearchData)

    // Clear form
    name.value = ''
    description.value = ''
    loading.value = false
  } catch (err: any) {
    error.value = err.message || 'Failed to save search'
    loading.value = false
  }
}

/**
 * Handle close button click
 */
function handleClose() {
  // Clear form and errors
  name.value = ''
  description.value = ''
  error.value = ''
  nameError.value = ''
  descriptionError.value = ''

  emit('update:modelValue', false)
}
</script>

<style scoped>
.query-preview {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #333;
  padding: 8px;
  background-color: #f5f5f5;
  border-radius: 4px;
  word-break: break-word;
}
</style>
