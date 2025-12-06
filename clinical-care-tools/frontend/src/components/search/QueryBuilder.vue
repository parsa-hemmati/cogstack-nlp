<template>
  <v-card variant="outlined" class="mb-4">
    <v-card-title class="text-subtitle-1">
      Query Settings
    </v-card-title>
    <v-card-text>
      <v-row>
        <v-col cols="12" md="4">
          <v-select
            v-model="queryType"
            :items="queryTypes"
            label="Query Type"
            density="compact"
            variant="outlined"
            hide-details
          >
            <template v-slot:item="{ props, item }">
              <v-list-item v-bind="props" :subtitle="item.raw.description"></v-list-item>
            </template>
          </v-select>
        </v-col>
        <v-col cols="12" md="8">
          <v-alert
            density="compact"
            type="info"
            variant="tonal"
            class="mb-0"
            border="start"
            :icon="currentHelp?.icon"
          >
            <div class="text-caption">
              <strong>{{ currentHelp?.title }}</strong>: {{ currentHelp?.description }}
              <div v-if="currentHelp?.example" class="mt-1 font-weight-bold">
                Example: {{ currentHelp.example }}
              </div>
            </div>
          </v-alert>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore } from '@/stores/search'

const searchStore = useSearchStore()

const queryType = computed({
  get: () => searchStore.queryType,
  set: (val) => searchStore.queryType = val
})

const queryTypes = [
  { title: 'Standard', value: 'standard', description: 'Basic search with fuzzy matching' },
  { title: 'Boolean', value: 'boolean', description: 'AND, OR, NOT operators' },
  { title: 'Wildcard', value: 'wildcard', description: '* and ? pattern matching' },
  { title: 'Fuzzy', value: 'fuzzy', description: 'Typo tolerance (~)' },
  { title: 'Proximity', value: 'proximity', description: 'Terms near each other' },
  { title: 'Range', value: 'range', description: 'Numeric or date ranges' },
  { title: 'Regex', value: 'regex', description: 'Regular expressions' },
]

const helpMap: Record<string, { icon: string, title: string, description: string, example: string }> = {
  standard: { icon: 'mdi-magnify', title: 'Standard', description: 'Best for general search.', example: 'diabetes mellitus' },
  boolean: { icon: 'mdi-logic-and', title: 'Boolean', description: 'Combine terms.', example: 'diabetes AND (heart OR kidney)' },
  wildcard: { icon: 'mdi-asterisk', title: 'Wildcard', description: 'Use * for multiple chars.', example: 'cardio*' },
  fuzzy: { icon: 'mdi-blur', title: 'Fuzzy', description: 'Finds similar spellings.', example: 'diabets~' },
  proximity: { icon: 'mdi-arrow-expand-horizontal', title: 'Proximity', description: 'Words within distance.', example: '"heart failure"~5' },
  range: { icon: 'mdi-code-brackets', title: 'Range', description: 'Values between X and Y.', example: 'age:[50 TO 60]' },
  regex: { icon: 'mdi-regex', title: 'Regex', description: 'Pattern matching.', example: '/diabet.*/' },
}

const currentHelp = computed(() => helpMap[queryType.value] || helpMap.standard)
</script>
