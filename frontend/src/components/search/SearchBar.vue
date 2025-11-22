<template>
  <v-container fluid class="search-bar-container">
    <!-- Search Input Row with Query Builder Toggle -->
    <v-row class="mb-3">
      <v-col>
        <v-text-field
          v-model="modelValue"
          type="search"
          :placeholder="placeholder"
          :loading="loading"
          :disabled="loading || disabled"
          :error="!!error"
          prepend-inner-icon="mdi-magnify"
          :append-icon="modelValue ? 'mdi-close' : undefined"
          variant="outlined"
          density="compact"
          @keydown.enter="handleSearch"
          @click:append="handleClear"
          @focus="$emit('focus')"
          @blur="$emit('blur')"
        >
          <template #append-inner>
            <v-btn
              icon
              size="small"
              variant="text"
              :color="showQueryBuilder ? 'primary' : 'default'"
              data-testid="toggle-query-builder-btn"
              aria-label="Toggle visual query builder"
              @click="toggleQueryBuilder"
            >
              <v-icon>mdi-code-braces</v-icon>
            </v-btn>
          </template>
        </v-text-field>
      </v-col>
    </v-row>

    <!-- Query Builder (Expandable) -->
    <v-row v-if="showQueryBuilder" class="mb-3">
      <v-col>
        <v-expand-transition>
          <QueryBuilder
            :model-value="props.modelValue"
            @update:model-value="handleQueryBuilderUpdate"
            @close="showQueryBuilder = false"
          />
        </v-expand-transition>
      </v-col>
    </v-row>

    <!-- Error Alert Row -->
    <v-row v-if="error" class="mb-2">
      <v-col>
        <v-alert
          type="error"
          variant="tonal"
          closable
          @click:close="$emit('clear-error')"
        >
          {{ error }}
        </v-alert>
      </v-col>
    </v-row>

    <!-- Hint Row -->
    <v-row v-if="$slots.hint">
      <v-col>
        <div class="text-caption text-medium-emphasis">
          <slot name="hint" />
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// SearchBar Component - Provides search input with debouncing, loading states, and error handling
// Enhanced with visual query builder integration
// See: docs/features/search/components/SearchBar.md for detailed documentation
import { ref, computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'
import QueryBuilder from './QueryBuilder.vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: 'Search documents...'
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  debounce: {
    type: Number,
    default: 300
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:modelValue',
  'search',
  'clear',
  'focus',
  'blur',
  'clear-error'
])

// Query Builder state
const showQueryBuilder = ref(false)

// Debounced update handler for modelValue changes
// Prevents excessive API calls while user is typing (default 300ms)
const debouncedUpdate = useDebounceFn((value: string) => {
  emit('update:modelValue', value)
}, () => props.debounce)

// Computed property for model value with debounced updates
const modelValue = computed({
  get: () => props.modelValue,
  set: (value: string) => {
    debouncedUpdate(value)
  }
})

// Handle search submission (Enter key or button click)
const handleSearch = () => {
  if (props.modelValue && props.modelValue.trim()) {
    emit('search', props.modelValue.trim())
  }
}

// Handle clear button click
const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
}

// Toggle query builder visibility
const toggleQueryBuilder = () => {
  showQueryBuilder.value = !showQueryBuilder.value
}

// Handle query builder updates
const handleQueryBuilderUpdate = (query: string) => {
  emit('update:modelValue', query)
  // Optionally trigger search immediately
  if (query && query.trim()) {
    emit('search', query.trim())
  }
}
</script>

<style scoped>
/**
 * Container padding and spacing
 */
.search-bar-container {
  padding: 0;
}

/**
 * Input field styling
 */
:deep(.v-text-field) {
  border-radius: 4px;
}

/**
 * Focus state with outline
 */
:deep(.v-text-field__input:focus) {
  outline: 2px solid #1976d2;
  outline-offset: 2px;
}

/**
 * Error state styling
 */
:deep(.v-text-field--error) {
  border-color: #d32f2f;
}
</style>
