<template>
  <v-card variant="flat">
    <v-card-title class="text-subtitle-2 px-0">
      Filters
      <v-btn
        v-if="hasActiveFilters"
        density="compact"
        variant="text"
        color="error"
        class="float-right"
        @click="searchStore.clearFilters()"
      >
        Clear All
      </v-btn>
    </v-card-title>
    <v-card-text class="px-0">
      <!-- Date Range -->
      <div class="mb-4">
        <label class="text-caption font-weight-bold mb-1 d-block">Date Range</label>
        <v-row dense>
          <v-col cols="6">
            <v-text-field
              v-model="filters.dateFrom"
              type="date"
              density="compact"
              variant="outlined"
              label="From"
              hide-details
            ></v-text-field>
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="filters.dateTo"
              type="date"
              density="compact"
              variant="outlined"
              label="To"
              hide-details
            ></v-text-field>
          </v-col>
        </v-row>
      </div>

      <!-- Document Type Facet -->
      <div class="mb-4">
        <label class="text-caption font-weight-bold mb-1 d-block">Document Type</label>
        <v-select
          v-model="filters.documentType"
          :items="docTypeItems"
          density="compact"
          variant="outlined"
          placeholder="Any"
          clearable
          hide-details
        ></v-select>
      </div>

       <!-- Department Facet -->
      <div class="mb-4">
        <label class="text-caption font-weight-bold mb-1 d-block">Department</label>
        <v-autocomplete
          v-model="filters.department"
          :items="deptItems"
          density="compact"
          variant="outlined"
          placeholder="Any"
          clearable
          hide-details
        ></v-autocomplete>
      </div>

       <!-- Author Facet -->
      <div class="mb-4">
        <label class="text-caption font-weight-bold mb-1 d-block">Author</label>
        <v-autocomplete
          v-model="filters.author"
          :items="authorItems"
          density="compact"
          variant="outlined"
          placeholder="Any"
          clearable
          hide-details
        ></v-autocomplete>
      </div>
      
      <v-btn block color="primary" variant="tonal" @click="searchStore.performSearch()">
        Apply Filters
      </v-btn>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore } from '@/stores/search'
import { storeToRefs } from 'pinia'

const searchStore = useSearchStore()
const { filters, facets } = storeToRefs(searchStore)

const hasActiveFilters = computed(() => {
  return Object.values(filters.value).some(val => val !== null && val !== '')
})

// Helper to map facet to selection item
const mapFacet = (facetItems: any[]) => {
  if (!facetItems) return []
  return facetItems.map(f => ({
    title: `${f.value} (${f.count})`,
    value: f.value
  }))
}

const docTypeItems = computed(() => mapFacet(facets.value?.document_types || []))
const deptItems = computed(() => mapFacet(facets.value?.departments || []))
const authorItems = computed(() => mapFacet(facets.value?.authors || []))
</script>
