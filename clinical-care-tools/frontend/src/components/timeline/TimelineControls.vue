<template>
  <div class="timeline-controls">
    <div class="controls-section">
      <h3>Filters</h3>
      <div class="filter-group">
        <!-- Date range filters -->
        <div class="filter-item">
          <label for="start-date">Start Date:</label>
          <input
            id="start-date"
            v-model="filters.startDate"
            type="date"
            @change="emitFilterChange"
          />
        </div>

        <div class="filter-item">
          <label for="end-date">End Date:</label>
          <input
            id="end-date"
            v-model="filters.endDate"
            type="date"
            @change="emitFilterChange"
          />
        </div>
      </div>

      <!-- Document type filter -->
      <div class="filter-group">
        <div class="filter-item">
          <label for="document-types">Document Types:</label>
          <select
            id="document-types"
            v-model="filters.documentTypes"
            multiple
            @change="emitFilterChange"
          >
            <option value="clinical_note">Clinical Note</option>
            <option value="lab_result">Lab Result</option>
            <option value="discharge_summary">Discharge Summary</option>
            <option value="radiology_report">Radiology Report</option>
          </select>
        </div>
      </div>

      <!-- Concept type filter -->
      <div class="filter-group">
        <div class="filter-item">
          <label for="concept-types">Concept Types:</label>
          <select
            id="concept-types"
            v-model="filters.conceptTypes"
            multiple
            @change="emitFilterChange"
          >
            <option value="condition">Condition</option>
            <option value="medication">Medication</option>
            <option value="procedure">Procedure</option>
            <option value="observation">Observation</option>
          </select>
        </div>
      </div>

      <!-- Meta-annotation filters -->
      <div class="filter-group">
        <div class="filter-item checkbox-item">
          <input
            id="include-negated"
            v-model="filters.includeNegated"
            type="checkbox"
            @change="emitFilterChange"
          />
          <label for="include-negated">Include Negated</label>
        </div>

        <div class="filter-item checkbox-item">
          <input
            id="include-family"
            v-model="filters.includeFamily"
            type="checkbox"
            @change="emitFilterChange"
          />
          <label for="include-family">Include Family History</label>
        </div>
      </div>
    </div>

    <!-- View mode toggle -->
    <div class="controls-section">
      <h3>View Mode</h3>
      <div class="view-mode-toggle">
        <button
          :class="{ active: localViewMode === 'documents' }"
          @click="setViewMode('documents')"
        >
          Documents Only
        </button>
        <button
          :class="{ active: localViewMode === 'concepts' }"
          @click="setViewMode('concepts')"
        >
          Concepts Only
        </button>
        <button
          :class="{ active: localViewMode === 'combined' }"
          @click="setViewMode('combined')"
        >
          Combined
        </button>
      </div>
    </div>

    <!-- Export buttons -->
    <div class="controls-section">
      <h3>Export</h3>
      <div class="export-buttons">
        <button
          :disabled="loading || exporting"
          @click="exportTimeline('pdf')"
          class="export-btn"
        >
          📄 Export PDF
        </button>
        <button
          :disabled="loading || exporting"
          @click="exportTimeline('json')"
          class="export-btn"
        >
          📋 Export JSON
        </button>
        <button
          :disabled="loading || exporting"
          @click="exportTimeline('fhir')"
          class="export-btn"
        >
          🏥 Export FHIR
        </button>
      </div>
      <div v-if="exporting" class="export-status">
        Generating export...
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { TimelineFilters, ViewMode } from '@/types/timeline'

// Props
interface Props {
  loading?: boolean
  patientId?: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  filterChange: [filters: TimelineFilters]
  viewModeChange: [mode: ViewMode]
  export: [format: 'pdf' | 'json' | 'fhir']
}>()

// Local state
const filters = reactive<TimelineFilters>({
  startDate: undefined,
  endDate: undefined,
  documentTypes: [],
  conceptTypes: [],
  includeNegated: false,
  includeFamily: false,
})

const localViewMode = ref<ViewMode>('combined')
const exporting = ref(false)

// Methods
const emitFilterChange = () => {
  emit('filterChange', { ...filters })
}

const setViewMode = (mode: ViewMode) => {
  localViewMode.value = mode
  emit('viewModeChange', mode)
}

const exportTimeline = async (format: 'pdf' | 'json' | 'fhir') => {
  emit('export', format)
}
</script>

<style scoped>
.timeline-controls {
  display: flex;
  gap: 2rem;
  padding: 1rem;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.controls-section {
  flex: 1;
}

.controls-section h3 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: #333;
}

.filter-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.filter-item.checkbox-item {
  flex-direction: row;
  align-items: center;
  gap: 0.5rem;
}

.filter-item label {
  font-size: 0.875rem;
  color: #666;
}

.filter-item input[type="date"],
.filter-item select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
}

.filter-item select[multiple] {
  min-height: 80px;
}

.filter-item input[type="checkbox"] {
  cursor: pointer;
}

.view-mode-toggle {
  display: flex;
  gap: 0.5rem;
}

.view-mode-toggle button {
  padding: 0.5rem 1rem;
  background-color: #ffffff;
  color: #333;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.view-mode-toggle button:hover {
  background-color: #e0e0e0;
}

.view-mode-toggle button.active {
  background-color: #3498db;
  color: white;
  border-color: #3498db;
}

.export-buttons {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.export-btn {
  padding: 0.5rem 1rem;
  background-color: #2ecc71;
  color: white;
  border: 1px solid #27ae60;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.875rem;
}

.export-btn:hover:not(:disabled) {
  background-color: #27ae60;
}

.export-btn:disabled {
  background-color: #95a5a6;
  border-color: #7f8c8d;
  cursor: not-allowed;
  opacity: 0.6;
}

.export-status {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #666;
  font-style: italic;
}
</style>
