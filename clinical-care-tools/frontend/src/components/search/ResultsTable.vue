<template>
  <v-card elevation="2">
    <!-- Toolbar -->
    <v-toolbar density="compact" color="primary" dark>
      <v-toolbar-title>Search Results</v-toolbar-title>
      <v-spacer />

      <!-- Export Button -->
      <v-btn
        icon
        @click="$emit('export')"
        title="Export results"
      >
        <v-icon>mdi-download</v-icon>
      </v-btn>

      <!-- View Toggle -->
      <v-btn-toggle
        v-model="viewMode"
        mandatory
        density="compact"
        divided
      >
        <v-btn value="table" icon>
          <v-icon>mdi-table</v-icon>
        </v-btn>
        <v-btn value="cards" icon>
          <v-icon>mdi-view-grid</v-icon>
        </v-btn>
      </v-btn-toggle>
    </v-toolbar>

    <!-- Table View -->
    <v-data-table
      v-if="viewMode === 'table'"
      :headers="headers"
      :items="results"
      :loading="loading"
      :items-per-page="itemsPerPage"
      :server-items-length="total"
      :page="page"
      @update:page="$emit('update:page', $event)"
      @update:items-per-page="$emit('update:items-per-page', $event)"
      hover
      class="elevation-0"
    >
      <!-- Patient Column -->
      <template v-slot:item.patient="{ item }">
        <div>
          <div class="font-weight-medium">{{ item.patient_mrn }}</div>
          <div class="text-caption text-grey">
            {{ item.age ? `${item.age}y` : '' }}
            {{ item.gender ? `/ ${item.gender}` : '' }}
          </div>
        </div>
      </template>

      <!-- Matched Concepts Column -->
      <template v-slot:item.concepts="{ item }">
        <v-chip-group>
          <v-tooltip
            v-for="(concept, idx) in item.matched_concepts.slice(0, 3)"
            :key="idx"
            location="top"
          >
            <template v-slot:activator="{ props }">
              <v-chip
                v-bind="props"
                size="small"
                :color="getConfidenceColor(concept.confidence)"
                variant="tonal"
              >
                {{ concept.pretty_name }}
                <span class="ml-1 text-caption">
                  ({{ (concept.confidence * 100).toFixed(0) }}%)
                </span>
              </v-chip>
            </template>
            <div>
              <div><strong>CUI:</strong> {{ concept.cui }}</div>
              <div><strong>Text:</strong> "{{ concept.text }}"</div>
              <div><strong>Negation:</strong> {{ concept.negation }}</div>
              <div><strong>Temporality:</strong> {{ concept.temporality }}</div>
              <div><strong>Experiencer:</strong> {{ concept.experiencer }}</div>
              <div><strong>Certainty:</strong> {{ concept.certainty }}</div>
            </div>
          </v-tooltip>
        </v-chip-group>
        <div v-if="item.matched_concepts.length > 3" class="text-caption text-grey">
          +{{ item.matched_concepts.length - 3 }} more
        </div>
      </template>

      <!-- Relevance Column -->
      <template v-slot:item.relevance="{ item }">
        <v-progress-linear
          :model-value="item.relevance_score * 100"
          :color="getRelevanceColor(item.relevance_score)"
          height="20"
          rounded
        >
          <template v-slot:default>
            <strong>{{ (item.relevance_score * 100).toFixed(0) }}%</strong>
          </template>
        </v-progress-linear>
      </template>

      <!-- Documents Column -->
      <template v-slot:item.documents="{ item }">
        <div class="text-center">
          <v-chip size="small" variant="outlined">
            {{ item.document_count }}
          </v-chip>
        </div>
      </template>

      <!-- Latest Match Column -->
      <template v-slot:item.latest_match="{ item }">
        <div class="text-caption">
          {{ formatDate(item.latest_match_date) }}
        </div>
      </template>

      <!-- Actions Column -->
      <template v-slot:item.actions="{ item }">
        <v-btn
          icon
          variant="text"
          size="small"
          @click="$emit('view-patient', item)"
          title="View patient timeline"
        >
          <v-icon>mdi-timeline</v-icon>
        </v-btn>
      </template>
    </v-data-table>

    <!-- Cards View -->
    <v-container v-else fluid>
      <v-row>
        <v-col
          v-for="item in results"
          :key="item.patient_id"
          cols="12"
          md="6"
          lg="4"
        >
          <v-card
            @click="$emit('view-patient', item)"
            hover
            class="cursor-pointer"
          >
            <v-card-title>
              <v-icon start color="primary">mdi-account</v-icon>
              {{ item.patient_mrn }}
              <v-spacer />
              <v-chip
                size="small"
                :color="getRelevanceColor(item.relevance_score)"
                variant="tonal"
              >
                {{ (item.relevance_score * 100).toFixed(0) }}% match
              </v-chip>
            </v-card-title>

            <v-card-subtitle>
              {{ item.age ? `${item.age} years` : '' }}
              {{ item.gender ? `• ${item.gender}` : '' }}
              • {{ item.document_count }} documents
            </v-card-subtitle>

            <v-card-text>
              <!-- Summary -->
              <div v-if="item.summary" class="mb-3">
                <div class="text-caption text-grey mb-1">Summary</div>
                <div class="text-body-2">{{ item.summary }}</div>
              </div>

              <!-- Matched Concepts -->
              <div>
                <div class="text-caption text-grey mb-1">Matched Concepts</div>
                <v-chip-group>
                  <v-chip
                    v-for="(concept, idx) in item.matched_concepts.slice(0, 4)"
                    :key="idx"
                    size="small"
                    variant="outlined"
                  >
                    {{ concept.pretty_name }}
                  </v-chip>
                </v-chip-group>
                <div v-if="item.matched_concepts.length > 4" class="text-caption text-grey">
                  +{{ item.matched_concepts.length - 4 }} more concepts
                </div>
              </div>

              <!-- Latest Match -->
              <div class="mt-3">
                <div class="text-caption text-grey">Latest Match</div>
                <div class="text-body-2">{{ formatDate(item.latest_match_date) }}</div>
              </div>
            </v-card-text>

            <v-card-actions>
              <v-btn
                variant="text"
                color="primary"
                @click.stop="$emit('view-patient', item)"
              >
                View Timeline
                <v-icon end>mdi-arrow-right</v-icon>
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>

      <!-- Pagination for cards view -->
      <v-pagination
        v-if="totalPages > 1"
        v-model="currentPage"
        :length="totalPages"
        :total-visible="7"
        @update:model-value="$emit('update:page', $event)"
        class="mt-4"
      />
    </v-container>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { format } from 'date-fns';
import type { PatientSearchResult } from '@/types/search';

// Props
interface Props {
  results: PatientSearchResult[];
  loading?: boolean;
  total: number;
  page: number;
  itemsPerPage: number;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
});

// Emits
const emit = defineEmits<{
  'view-patient': [patient: PatientSearchResult];
  'export': [];
  'update:page': [page: number];
  'update:items-per-page': [items: number];
}>();

// State
const viewMode = ref<'table' | 'cards'>('table');
const currentPage = ref(props.page);

// Computed
const totalPages = computed(() => {
  return Math.ceil(props.total / props.itemsPerPage);
});

// Table headers
const headers = [
  {
    title: 'Patient',
    key: 'patient',
    sortable: false,
  },
  {
    title: 'Matched Concepts',
    key: 'concepts',
    sortable: false,
  },
  {
    title: 'Relevance',
    key: 'relevance',
    sortable: true,
  },
  {
    title: 'Documents',
    key: 'documents',
    sortable: true,
    align: 'center' as const,
  },
  {
    title: 'Latest Match',
    key: 'latest_match',
    sortable: true,
  },
  {
    title: 'Actions',
    key: 'actions',
    sortable: false,
    align: 'center' as const,
  },
];

// Methods
function formatDate(dateString: string): string {
  try {
    return format(new Date(dateString), 'MMM dd, yyyy');
  } catch {
    return dateString;
  }
}

function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.9) return 'success';
  if (confidence >= 0.7) return 'warning';
  return 'error';
}

function getRelevanceColor(relevance: number): string {
  if (relevance >= 0.8) return 'success';
  if (relevance >= 0.6) return 'primary';
  if (relevance >= 0.4) return 'warning';
  return 'error';
}
</script>

<style scoped>
.cursor-pointer {
  cursor: pointer;
}

:deep(.v-data-table) {
  font-size: 0.875rem;
}

:deep(.v-chip__content) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>