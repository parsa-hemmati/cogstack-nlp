<template>
  <v-card class="mb-4">
    <v-card-text>
      <v-combobox
        v-model="localQuery"
        v-model:search="searchInput"
        :items="suggestions"
        :loading="loadingSuggestions"
        label="Search patient documents..."
        prepend-inner-icon="mdi-magnify"
        variant="outlined"
        hide-details="auto"
        clearable
        @update:search="fetchSuggestions"
        @keyup.enter="handleSearch"
        @click:clear="handleClear"
      >
        <template v-slot:append-inner>
          <v-btn
            color="primary"
            variant="text"
            size="small"
            @click="handleSearch"
          >
            Search
          </v-btn>
          <v-divider vertical class="mx-2"></v-divider>
          <v-btn
            variant="text"
            size="small"
            color="grey-darken-1"
            @click="$emit('toggle-advanced')"
          >
            <v-icon :icon="showAdvanced ? 'mdi-chevron-up' : 'mdi-chevron-down'" class="mr-1"></v-icon>
            Advanced
          </v-btn>
        </template>
      </v-combobox>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useSearchStore } from '@/stores/search'
import { debounce } from 'lodash'

const props = defineProps<{
  showAdvanced: boolean
}>()

const emit = defineEmits(['toggle-advanced'])

const searchStore = useSearchStore()
const localQuery = ref(searchStore.query)
const searchInput = ref('')
const suggestions = ref<string[]>([])
const loadingSuggestions = ref(false)

// Sync from store
watch(() => searchStore.query, (newVal) => {
  localQuery.value = newVal
})

// Sync to store
watch(localQuery, (newVal) => {
  searchStore.setQuery(typeof newVal === 'string' ? newVal : '')
})

const fetchSuggestions = debounce(async (val: string) => {
  if (!val || val.length < 2) {
    suggestions.value = []
    return
  }

  loadingSuggestions.value = true
  try {
    const results = await searchStore.getSuggestions(val)
    suggestions.value = results
  } finally {
    loadingSuggestions.value = false
  }
}, 300)

function handleSearch() {
  // If combobox value is an object (selected item), use it
  if (localQuery.value) {
     searchStore.performSearch()
  }
}

function handleClear() {
  searchStore.setQuery('')
  searchStore.performSearch()
}
</script>
