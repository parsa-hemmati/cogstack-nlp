<template>
  <v-container fluid class="fill-height align-start bg-grey-lighten-5 pa-6">
    <v-row>
      <!-- Left Sidebar: Filters & Query Builder -->
      <v-col cols="12" md="3" lg="3">
        <div class="sticky-top" style="top: 80px">
          <facet-panel />
          
           <!-- Additional Info -->
           <v-card variant="outlined" class="mt-4 bg-white">
            <v-card-text class="text-caption text-grey">
              <v-icon size="small" class="mr-1">mdi-information-outline</v-icon>
              Search uses <strong>Elasticsearch</strong> with NLP enhancement.
            </v-card-text>
           </v-card>
        </div>
      </v-col>

      <!-- Main Content: Search Box & Results -->
      <v-col cols="12" md="9" lg="7">
        <h1 class="text-h4 mb-6 font-weight-bold text-grey-darken-3">Patient Discovery</h1>
        
        <search-box 
          :show-advanced="showAdvanced" 
          @toggle-advanced="showAdvanced = !showAdvanced" 
        />
        
        <v-expand-transition>
          <div v-show="showAdvanced" class="mb-4">
            <query-builder />
          </div>
        </v-expand-transition>

        <v-divider class="my-4"></v-divider>

        <div class="d-flex align-center justify-space-between mb-4">
          <div class="text-subtitle-1 font-weight-medium">
            <span v-if="searchStore.loading">Searching...</span>
            <span v-else-if="searchStore.totalResults > 0">
              Found {{ searchStore.totalResults }} documents
            </span>
            <span v-else>Use the search bar to find patients</span>
          </div>
        </div>

        <patient-list />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSearchStore } from '@/stores/search'
import SearchBox from '@/components/search/SearchBox.vue'
import QueryBuilder from '@/components/search/QueryBuilder.vue'
import FacetPanel from '@/components/search/FacetPanel.vue'
import PatientList from '@/components/search/PatientList.vue'

const searchStore = useSearchStore()
const showAdvanced = ref(false)
</script>
