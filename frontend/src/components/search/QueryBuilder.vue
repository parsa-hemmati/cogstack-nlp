<template>
  <v-card data-testid="query-builder" class="query-builder" elevation="4">
    <v-card-title class="d-flex justify-space-between align-center">
      <span>Visual Query Builder</span>
      <v-btn
        icon="mdi-close"
        size="small"
        variant="text"
        data-testid="close-btn"
        aria-label="Close query builder"
        @click="$emit('close')"
      />
    </v-card-title>

    <v-card-text>
      <!-- Empty State -->
      <v-container v-if="conditions.length === 0" data-testid="empty-state" class="text-center py-8">
        <v-icon size="64" color="grey-lighten-1">mdi-code-braces</v-icon>
        <p class="text-h6 mt-4 text-grey">No conditions yet</p>
        <p class="text-caption text-grey">Click "Add Condition" to build your query</p>
      </v-container>

      <!-- Conditions List -->
      <draggable
        v-else
        v-model="conditions"
        item-key="id"
        handle=".drag-handle"
        @end="onDragEnd"
      >
        <template #item="{ element, index }">
          <div :key="element.id" class="mb-3">
            <!-- Condition Row -->
            <v-card
              :data-testid="`condition-row`"
              role="group"
              :aria-label="`Condition ${index + 1}`"
              variant="outlined"
              class="condition-row"
            >
              <v-card-text>
                <v-row align="center">
                  <!-- Drag Handle -->
                  <v-col cols="auto">
                    <v-icon
                      class="drag-handle"
                      data-testid="drag-handle"
                      style="cursor: move"
                      color="grey"
                    >
                      mdi-drag-vertical
                    </v-icon>
                  </v-col>

                  <!-- Field Selector -->
                  <v-col cols="3">
                    <v-select
                      v-model="element.field"
                      :items="fieldOptions"
                      label="Field"
                      density="compact"
                      variant="outlined"
                      data-testid="field-select"
                      :error="element.showErrors && !element.field"
                      :error-messages="element.showErrors && !element.field ? 'Select a field' : ''"
                    >
                      <template #item="{ item, props }">
                        <v-list-item v-bind="props" :title="item.title">
                          <template #prepend>
                            <v-icon :icon="getFieldIcon(item.value)" />
                          </template>
                        </v-list-item>
                      </template>
                    </v-select>
                    <span v-if="element.showErrors && !element.field" data-testid="field-error" class="text-error text-caption">
                      Select a field
                    </span>
                  </v-col>

                  <!-- Value Input (Dynamic based on field type) -->
                  <v-col cols="6">
                    <!-- Text input for concept field -->
                    <v-text-field
                      v-if="element.field === 'concept'"
                      v-model="element.value"
                      label="Value"
                      placeholder="e.g., diabetes, hypertension"
                      density="compact"
                      variant="outlined"
                      data-testid="value-input-text"
                      :error="element.showErrors && !element.value"
                      :error-messages="element.showErrors && !element.value ? 'Enter a value' : ''"
                    />

                    <!-- Date picker for date field -->
                    <v-text-field
                      v-else-if="element.field === 'date'"
                      v-model="element.value"
                      label="Date"
                      type="date"
                      density="compact"
                      variant="outlined"
                      data-testid="value-input-date"
                      :error="element.showErrors && !element.value"
                      :error-messages="element.showErrors && !element.value ? 'Enter a date' : ''"
                    />

                    <!-- Slider for confidence field -->
                    <div v-else-if="element.field === 'confidence'" class="px-2">
                      <v-slider
                        v-model="element.value"
                        :min="0"
                        :max="1"
                        :step="0.1"
                        label="Confidence"
                        thumb-label
                        data-testid="value-input-slider"
                      />
                    </div>

                    <!-- Placeholder when no field selected -->
                    <v-text-field
                      v-else
                      disabled
                      label="Select a field first"
                      density="compact"
                      variant="outlined"
                    />
                  </v-col>

                  <!-- Remove Button -->
                  <v-col cols="auto">
                    <v-btn
                      icon="mdi-delete"
                      size="small"
                      color="error"
                      variant="text"
                      data-testid="remove-condition-btn"
                      :aria-label="`Remove condition ${index + 1}`"
                      @click="removeCondition(index)"
                    />
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>

            <!-- Operator Selector (between conditions) -->
            <div v-if="index < conditions.length - 1" class="text-center my-2">
              <v-btn-toggle
                v-model="conditions[index].operator"
                mandatory
                divided
                variant="outlined"
                data-testid="operator-select"
              >
                <v-btn value="AND" size="small">
                  <v-icon>mdi-ampersand</v-icon>
                  AND
                </v-btn>
                <v-btn value="OR" size="small">
                  <v-icon>mdi-pipe</v-icon>
                  OR
                </v-btn>
                <v-btn value="NOT" size="small">
                  <v-icon>mdi-exclamation</v-icon>
                  NOT
                </v-btn>
              </v-btn-toggle>
            </div>
          </div>
        </template>
      </draggable>

      <!-- Add Condition Button -->
      <v-btn
        block
        variant="outlined"
        prepend-icon="mdi-plus"
        data-testid="add-condition-btn"
        :disabled="conditions.length >= maxConditions"
        aria-label="Add new condition"
        @click="addCondition"
      >
        Add Condition
        <span v-if="conditions.length >= maxConditions" class="text-caption ml-2">
          (Max {{ maxConditions }})
        </span>
      </v-btn>

      <!-- Query Preview Section -->
      <v-divider class="my-4" />
      <div data-testid="query-preview" class="query-preview">
        <v-card variant="outlined" class="pa-3">
          <div class="d-flex justify-space-between align-center mb-2">
            <span class="text-subtitle-2">Query Preview</span>
            <v-chip size="small" :color="isValid ? 'success' : 'warning'">
              {{ isValid ? 'Valid' : 'Invalid' }}
            </v-chip>
          </div>
          <pre
            data-testid="query-preview-text"
            class="query-preview-text"
            v-html="highlightedQuery"
          />
        </v-card>
      </div>

      <!-- Validation Section -->
      <div
        data-testid="validation-section"
        class="mt-3"
        aria-live="polite"
        aria-atomic="true"
      >
        <v-alert
          v-if="validationError"
          type="error"
          variant="tonal"
          density="compact"
          data-testid="validation-error"
        >
          {{ validationError }}
        </v-alert>
        <v-alert
          v-else-if="isValid && conditions.length > 0"
          type="success"
          variant="tonal"
          density="compact"
          data-testid="validation-success"
        >
          Valid query ready to apply
        </v-alert>
      </div>
    </v-card-text>

    <!-- Action Buttons -->
    <v-card-actions class="justify-end">
      <v-btn
        variant="text"
        data-testid="clear-btn"
        @click="clearAllConditions"
      >
        Clear All
      </v-btn>
      <v-btn
        color="primary"
        variant="elevated"
        data-testid="apply-btn"
        :disabled="!isValid"
        @click="applyQuery"
      >
        Apply Query
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import draggable from 'vuedraggable'

// ============================================================================
// TYPES
// ============================================================================

interface QueryCondition {
  id: string
  field: 'concept' | 'date' | 'confidence' | ''
  value: string | number
  operator: 'AND' | 'OR' | 'NOT'
  showErrors: boolean
}

interface FieldOption {
  title: string
  value: string
}

// ============================================================================
// PROPS & EMITS
// ============================================================================

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'close': []
}>()

// ============================================================================
// STATE
// ============================================================================

const conditions = ref<QueryCondition[]>([])
const maxConditions = 10
let conditionIdCounter = 0

// Field options with labels
const fieldOptions: FieldOption[] = [
  { title: 'Concept (Medical Term)', value: 'concept' },
  { title: 'Date', value: 'date' },
  { title: 'Confidence Score', value: 'confidence' },
]

// ============================================================================
// COMPUTED PROPERTIES
// ============================================================================

/**
 * Generate query string from conditions
 */
const generatedQuery = computed(() => {
  if (conditions.value.length === 0) {
    return ''
  }

  let query = ''

  for (let i = 0; i < conditions.value.length; i++) {
    const condition = conditions.value[i]

    // Skip invalid conditions
    if (!condition.field || !condition.value) {
      continue
    }

    // Add condition
    if (condition.field === 'concept') {
      query += condition.value
    } else if (condition.field === 'date') {
      query += `date:${condition.value}`
    } else if (condition.field === 'confidence') {
      query += `confidence:${condition.value}`
    }

    // Add operator between conditions
    if (i < conditions.value.length - 1) {
      query += ` ${condition.operator} `
    }
  }

  return query.trim()
})

/**
 * Syntax-highlighted query for preview
 */
const highlightedQuery = computed(() => {
  let highlighted = generatedQuery.value

  if (!highlighted) {
    return '<span class="text-grey">No conditions added</span>'
  }

  // Highlight operators
  highlighted = highlighted.replace(/\b(AND|OR|NOT)\b/g, '<span class="highlight-operator text-blue font-weight-bold">$1</span>')

  // Highlight field names
  highlighted = highlighted.replace(/(concept|date|confidence):/g, '<span class="highlight-field text-purple font-weight-medium">$1:</span>')

  // Highlight values (anything not an operator or field)
  highlighted = highlighted.replace(/(?<!<span[^>]*>)([a-zA-Z0-9_\-\.]+)(?![^<]*<\/span>)/g, '<span class="highlight-value text-green">$1</span>')

  return highlighted
})

/**
 * Validation error message (if any)
 */
const validationError = computed(() => {
  if (conditions.value.length === 0) {
    return 'Add at least one condition to build a query'
  }

  for (let i = 0; i < conditions.value.length; i++) {
    const condition = conditions.value[i]

    if (!condition.field) {
      return `Condition ${i + 1}: Select a field`
    }

    if (!condition.value) {
      return `Condition ${i + 1}: Enter a value`
    }
  }

  return null
})

/**
 * Whether the query is valid
 */
const isValid = computed(() => {
  return conditions.value.length > 0 && validationError.value === null
})

// ============================================================================
// METHODS
// ============================================================================

/**
 * Add a new condition
 */
function addCondition() {
  if (conditions.value.length >= maxConditions) {
    return
  }

  conditions.value.push({
    id: `condition-${conditionIdCounter++}`,
    field: '',
    value: '',
    operator: 'AND',
    showErrors: false,
  })
}

/**
 * Remove a condition by index
 */
function removeCondition(index: number) {
  conditions.value.splice(index, 1)
}

/**
 * Clear all conditions
 */
function clearAllConditions() {
  conditions.value = []
}

/**
 * Apply the query (emit to parent)
 */
function applyQuery() {
  // Show validation errors on all conditions
  conditions.value.forEach((c) => (c.showErrors = true))

  if (!isValid.value) {
    return
  }

  emit('update:modelValue', generatedQuery.value)
}

/**
 * Handle drag end event
 */
function onDragEnd() {
  // Conditions reordered, no action needed
  // Vue reactivity handles the update
}

/**
 * Get icon for field type
 */
function getFieldIcon(fieldValue: string): string {
  const icons: Record<string, string> = {
    concept: 'mdi-stethoscope',
    date: 'mdi-calendar',
    confidence: 'mdi-gauge',
  }
  return icons[fieldValue] || 'mdi-help-circle'
}

/**
 * Parse modelValue into conditions (for initialization)
 */
function parseQuery(query: string) {
  if (!query || query.trim() === '') {
    return
  }

  // Simple parser for basic queries
  // Format: "concept:diabetes AND date:2024-01-01"
  const parts = query.split(/\s+(AND|OR|NOT)\s+/)

  for (let i = 0; i < parts.length; i += 2) {
    const part = parts[i].trim()
    const operator = parts[i + 1] as 'AND' | 'OR' | 'NOT' | undefined

    if (part.includes(':')) {
      const [field, value] = part.split(':')
      conditions.value.push({
        id: `condition-${conditionIdCounter++}`,
        field: field as 'concept' | 'date' | 'confidence',
        value: value,
        operator: operator || 'AND',
        showErrors: false,
      })
    } else {
      // Plain text query (concept)
      conditions.value.push({
        id: `condition-${conditionIdCounter++}`,
        field: 'concept',
        value: part,
        operator: operator || 'AND',
        showErrors: false,
      })
    }
  }
}

// ============================================================================
// WATCHERS
// ============================================================================

// Parse initial query if provided
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue && conditions.value.length === 0) {
      parseQuery(newValue)
    }
  },
  { immediate: true }
)
</script>

<style scoped>
.query-builder {
  max-width: 900px;
  margin: 0 auto;
}

.condition-row {
  transition: all 0.2s ease;
}

.condition-row:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.drag-handle {
  opacity: 0.5;
  transition: opacity 0.2s;
}

.drag-handle:hover {
  opacity: 1;
}

.query-preview-text {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Syntax highlighting colors */
:deep(.highlight-operator) {
  color: #1976d2;
  font-weight: bold;
}

:deep(.highlight-field) {
  color: #7b1fa2;
  font-weight: 500;
}

:deep(.highlight-value) {
  color: #388e3c;
}
</style>
