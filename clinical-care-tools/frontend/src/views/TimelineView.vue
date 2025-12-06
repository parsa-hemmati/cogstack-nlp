<template>
  <v-container fluid class="fill-height align-start bg-grey-lighten-5 pa-0">
    <div class="d-flex flex-column fill-height w-100">
      
      <!-- Patient Header -->
      <v-toolbar color="white" density="comfortable" border>
        <v-btn icon="mdi-arrow-left" to="/patients" class="mr-2"></v-btn>
        <v-toolbar-title class="text-subtitle-1 font-weight-bold">
          <span v-if="timelineStore.patient">
             {{ timelineStore.patient.firstName }} {{ timelineStore.patient.lastName }}
             <span class="text-caption text-grey ml-2">{{ timelineStore.patient.mrn }}</span>
          </span>
          <span v-else>Loading Patient...</span>
        </v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn variant="outlined" size="small" prepend-icon="mdi-filter-variant" class="mr-2">
           Filters
        </v-btn>
        <v-btn variant="outlined" size="small" prepend-icon="mdi-export-variant">
           Export
        </v-btn>
      </v-toolbar>

      <!-- Main Content Area -->
      <div class="d-flex flex-grow-1 overflow-hidden">
        
        <!-- Left Panel: Chart & List -->
        <div class="d-flex flex-column" :style="{ width: selectedDocument ? '400px' : '100%', transition: 'width 0.3s' }">
           <div class="pa-4 flex-grow-1 overflow-y-auto">
              <v-alert v-if="timelineStore.error" type="error" class="mb-4">
                 {{ timelineStore.error }}
              </v-alert>

              <div v-if="timelineStore.loading" class="d-flex justify-center py-8">
                 <v-progress-circular indeterminate color="primary"></v-progress-circular>
              </div>

              <div v-else>
                 <!-- Visualization -->
                 <timeline-chart :documents="timelineStore.filteredDocuments" />
                 
                 <div class="d-flex justify-space-between align-center mb-2">
                    <div class="text-subtitle-2 text-grey-darken-1">
                       {{ timelineStore.documentCount }} Documents
                    </div>
                    
                    <!-- View toggle could go here -->
                 </div>

                 <!-- Feed -->
                 <document-list 
                    :documents="timelineStore.filteredDocuments" 
                    :selected-id="selectedDocument?.id"
                    @select="handleSelectDocument"
                 />
              </div>
           </div>
        </div>

        <!-- Right Panel: Document Viewer -->
        <div 
           class="border-s bg-white fill-height transition-swing"
           :class="selectedDocument ? 'flex-grow-1' : 'w-0'"
           v-if="selectedDocument"
        >
           <document-viewer 
              :document-id="selectedDocument.id" 
              @close="selectedDocument = null"
           />
        </div>

      </div>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useTimelineStore } from '@/stores/timeline'
import { storeToRefs } from 'pinia'
import TimelineChart from '@/components/timeline/TimelineChart.vue'
import DocumentList from '@/components/timeline/DocumentList.vue'
import DocumentViewer from '@/components/timeline/DocumentViewer.vue'
import type { TimelineDocument } from '@/types/timeline'

const route = useRoute()
const timelineStore = useTimelineStore()
const selectedDocument = ref<TimelineDocument | null>(null)

onMounted(() => {
  const patientId = route.params.id as string
  if (patientId) {
     timelineStore.fetchTimeline(patientId)
  }
})

// Update selection if document ID in query param changes (optional deep linking)
// For now just local state

function handleSelectDocument(doc: TimelineDocument) {
  selectedDocument.value = doc
}
</script>

<style scoped>
.transition-swing {
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.5, 1);
}
.w-0 {
    width: 0 !important;
    overflow: hidden; 
}
</style>
