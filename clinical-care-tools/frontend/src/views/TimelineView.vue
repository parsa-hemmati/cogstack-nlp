<template>
  <v-container fluid class="timeline-view">
    <v-row>
      <!-- Filter Drawer -->
      <v-navigation-drawer
        v-model="filterDrawerOpen"
        temporary
        width="400"
      >
        <timeline-filters
          v-model="filters"
          :filter-presets="store.filterPresets"
          @apply="applyFilters"
          @clear="clearFilters"
          @save-preset="saveFilterPreset"
        />
      </v-navigation-drawer>

      <v-col>
        <!-- Toolbar -->
        <v-toolbar color="primary" dark>
          <v-btn icon @click="filterDrawerOpen = !filterDrawerOpen">
            <v-icon>mdi-filter</v-icon>
          </v-btn>

          <v-toolbar-title>Patient Timeline</v-toolbar-title>

          <v-spacer />

          <!-- Export Menu -->
          <v-menu>
            <template #activator="{ props }">
              <v-btn icon v-bind="props">
                <v-icon>mdi-download</v-icon>
              </v-btn>
            </template>
            <v-list>
              <v-list-item @click="exportTimeline('pdf')">
                <v-list-item-title>Export as PDF</v-list-item-title>
              </v-list-item>
              <v-list-item @click="exportTimeline('fhir')">
                <v-list-item-title>Export as FHIR</v-list-item-title>
              </v-list-item>
              <v-list-item @click="exportTimeline('json')">
                <v-list-item-title>Export as JSON</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </v-toolbar>

        <!-- Loading State -->
        <div v-if="store.loading" class="loading-container">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4">Loading timeline...</p>
        </div>

        <!-- Error State -->
        <v-alert v-else-if="store.error" type="error" class="ma-4">
          {{ store.error }}
        </v-alert>

        <!-- Timeline Chart -->
        <div v-else-if="store.timeline" class="timeline-container">
          <timeline-chart
            :timeline="store.timeline"
            :loading="store.loading"
            :height="600"
            @concept-click="showConceptDetails"
            @document-click="showDocumentDetails"
          />

          <!-- Timeline Statistics -->
          <v-card class="ma-4">
            <v-card-text>
              <v-row>
                <v-col cols="4">
                  <div class="text-h6">{{ store.timeline.statistics.total_documents }}</div>
                  <div class="text-caption">Documents</div>
                </v-col>
                <v-col cols="4">
                  <div class="text-h6">{{ store.timeline.statistics.total_concepts }}</div>
                  <div class="text-caption">Concepts</div>
                </v-col>
                <v-col cols="4">
                  <div class="text-h6">
                    {{ store.timeline.date_range[0] }} - {{ store.timeline.date_range[1] }}
                  </div>
                  <div class="text-caption">Date Range</div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </div>

        <!-- Concept Details Dialog -->
        <v-dialog v-model="conceptDialog" max-width="800">
          <v-card v-if="selectedConcept">
            <v-card-title>{{ selectedConcept.name }}</v-card-title>
            <v-card-subtitle>
              CUI: {{ selectedConcept.concept_cui }} | Type: {{ selectedConcept.type }}
            </v-card-subtitle>
            <v-card-text>
              <div class="text-subtitle-2 mb-2">Mentions ({{ selectedConcept.mention_count }})</div>
              <v-list>
                <v-list-item v-for="(mention, idx) in selectedConcept.mentions" :key="idx">
                  <v-list-item-title>{{ mention.sentence }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ mention.document_date }} | Confidence: {{ (mention.confidence * 100).toFixed(1) }}%
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="conceptDialog = false">Close</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>

        <!-- Document Details Dialog -->
        <v-dialog v-model="documentDialog" max-width="800">
          <v-card v-if="selectedDocument">
            <v-card-title>{{ selectedDocument.title }}</v-card-title>
            <v-card-subtitle>
              {{ selectedDocument.type }} | {{ selectedDocument.document_date }}
              <span v-if="selectedDocument.author">| {{ selectedDocument.author }}</span>
            </v-card-subtitle>
            <v-card-text>
              <div class="text-subtitle-2 mb-2">Concepts Found: {{ selectedDocument.concept_count }}</div>
            </v-card-text>
            <v-card-actions>
              <v-spacer />
              <v-btn @click="documentDialog = false">Close</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useTimelineStore } from '@/stores/timeline'
import TimelineChart from '@/components/timeline/TimelineChart.vue'
import TimelineFilters from '@/components/timeline/TimelineFilters.vue'
import type {
  TimelineConcept,
  TimelineDocument,
  TimelineFilters as TimelineFiltersType,
  ExportFormat,
} from '@/types/timeline'

// Router
const route = useRoute()
const patientId = route.params.patientId as string

// Store
const store = useTimelineStore()

// Component state
const filterDrawerOpen = ref(false)
const filters = ref<TimelineFiltersType>({
  date_start: undefined,
  date_end: undefined,
  concept_cuis: [],
  document_types: [],
  negation: undefined,
  experiencer: undefined,
  temporality: undefined,
  certainty: undefined,
})

const conceptDialog = ref(false)
const selectedConcept = ref<TimelineConcept | null>(null)

const documentDialog = ref(false)
const selectedDocument = ref<TimelineDocument | null>(null)

// Methods
async function loadTimeline() {
  try {
    await store.fetchTimeline(patientId, filters.value)
  } catch (error) {
    console.error('Failed to load timeline:', error)
  }
}

async function applyFilters() {
  await loadTimeline()
  filterDrawerOpen.value = false
}

function clearFilters() {
  filters.value = {
    date_start: undefined,
    date_end: undefined,
    concept_cuis: [],
    document_types: [],
    negation: undefined,
    experiencer: undefined,
    temporality: undefined,
    certainty: undefined,
  }
  loadTimeline()
}

async function exportTimeline(format: string) {
  try {
    const exportRequest = {
      format: format as ExportFormat,
      filters: filters.value,
      options: {},
    }

    const exportResponse = await store.exportTimeline(patientId, exportRequest)

    // Poll for export completion
    const checkStatus = async () => {
      const status = await store.getExportStatus(exportResponse.id)
      if (status.status === 'completed') {
        await store.downloadExport(exportResponse.id, format)
      } else if (status.status === 'failed') {
        console.error('Export failed:', status.error_message)
      } else {
        setTimeout(checkStatus, 2000)
      }
    }

    setTimeout(checkStatus, 2000)
  } catch (error) {
    console.error('Failed to export timeline:', error)
  }
}

async function saveFilterPreset(
  name: string,
  description: string | undefined,
  presetFilters: TimelineFiltersType,
  isDefault: boolean
) {
  try {
    await store.saveFilterPreset({
      name,
      description,
      filters: presetFilters,
      is_default: isDefault,
    })
  } catch (error) {
    console.error('Failed to save filter preset:', error)
  }
}

function showConceptDetails(concept: TimelineConcept) {
  selectedConcept.value = concept
  conceptDialog.value = true
}

function showDocumentDetails(document: TimelineDocument) {
  selectedDocument.value = document
  documentDialog.value = true
}

// Lifecycle
onMounted(() => {
  loadTimeline()
  store.loadFilterPresets()
})
</script>

<style scoped>
.timeline-view {
  height: 100vh;
  padding: 0;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}

.timeline-container {
  padding: 16px;
}
</style>
