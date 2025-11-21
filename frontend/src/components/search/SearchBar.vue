<template>
  <v-container fluid class="search-bar-container">
    <!-- Search Input Row -->
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
        />
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
/**
 * SearchBar Component
 *
 * Provides a reusable search input field with debouncing, loading states,
 * error handling, and accessibility support. It emits search events when
 * the user submits a query and supports placeholder text customization.
 *
 * The component is designed to be simple and focused on input handling,
 * delegating actual search logic to parent components or the
 * `usePatientSearch` composable.
 *
 * @example
 * ```vue
 * <template>
 *   <SearchBar
 *     v-model="searchQuery"
 *     :loading="isLoading"
 *     :error="error"
 *     @search="handleSearch"
 *   />
 * </template>
 *
 * <script setup>
 * import { ref } from 'vue'
 * import SearchBar from '@/components/search/SearchBar.vue'
 *
 * const searchQuery = ref('')
 * const isLoading = ref(false)
 * const error = ref('')
 *
 * const handleSearch = async (query: string) => {
 *   isLoading.value = true
 *   try {
 *     await performSearch(query)
 *   } catch (err) {
 *     error.value = err.message
 *   } finally {
 *     isLoading.value = false
 *   }
 * }
 * </script>
 * ```
 *
 * @see {@link ../../../docs/features/search/components/SearchBar.md} for detailed documentation
 */
import { computed } from 'vue'
import { useDebounceFn } from '@vueuse/core'

/**
 * Component props interface
 *
 * @typedef {Object} Props
 * @property {string} [modelValue] - Current search query (v-model binding)
 * @property {string} [placeholder] - Placeholder text in input
 * @property {boolean} [loading] - Whether search is in progress
 * @property {string} [error] - Error message to display
 * @property {number} [debounce] - Debounce delay in milliseconds
 * @property {boolean} [disabled] - Disable input while searching
 */
interface Props {
  modelValue?: string
  placeholder?: string
  loading?: boolean
  error?: string
  debounce?: number
  disabled?: boolean
}

/**
 * Component emits interface
 *
 * @typedef {Object} Emits
 * Emitted events for the SearchBar component
 */
const props = withDefaults(defineProps<Props>(), {
  modelValue: '',
  placeholder: 'Search documents...',
  loading: false,
  error: '',
  debounce: 300,
  disabled: false
})

const emit = defineEmits<{
  /**
   * Emitted when user types (with debounce applied)
   * @param {string} value - Updated query value
   */
  'update:modelValue': [value: string]

  /**
   * Emitted when user presses Enter or submits
   * @param {string} value - Current query value
   */
  'search': [value: string]

  /**
   * Emitted when user clears the input
   */
  'clear': []

  /**
   * Emitted when input receives focus
   */
  'focus': []

  /**
   * Emitted when input loses focus
   */
  'blur': []

  /**
   * Emitted when user clicks close button on error alert
   */
  'clear-error': []
}>()

/**
 * Debounced update handler for modelValue changes
 * Prevents excessive API calls while user is typing
 *
 * Default debounce: 300ms
 * Customizable via debounce prop
 */
const debouncedUpdate = useDebounceFn((value: string) => {
  emit('update:modelValue', value)
}, () => props.debounce)

/**
 * Computed property for model value
 * Handles debounced updates when typing
 */
const modelValue = computed({
  get: () => props.modelValue,
  set: (value: string) => {
    debouncedUpdate(value)
  }
})

/**
 * Handle search submission (Enter key or button click)
 *
 * @emits search - With current query value
 */
const handleSearch = () => {
  if (props.modelValue && props.modelValue.trim()) {
    emit('search', props.modelValue.trim())
  }
}

/**
 * Handle clear button click
 *
 * Clears input and emits clear event
 * @emits clear - No payload
 * @emits update:modelValue - With empty string
 */
const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
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
