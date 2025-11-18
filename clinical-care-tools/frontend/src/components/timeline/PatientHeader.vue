<template>
  <div class="patient-header">
    <div class="patient-info">
      <h1 class="patient-name">{{ patientDisplay }}</h1>
      <div class="patient-details">
        <span v-if="patient.mrn" class="detail-item">
          <strong>MRN:</strong> {{ patient.mrn }}
        </span>
        <span v-if="patient.dateOfBirth" class="detail-item">
          <strong>DOB:</strong> {{ formatDate(patient.dateOfBirth) }}
        </span>
        <span v-if="patient.gender" class="detail-item">
          <strong>Gender:</strong> {{ patient.gender }}
        </span>
      </div>
    </div>

    <div class="header-actions">
      <button @click="goBack" class="btn-secondary">
        ← Back to Search
      </button>
      <button @click="refreshTimeline" class="btn-primary">
        🔄 Refresh
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

// Props
interface Patient {
  id: string
  mrn?: string
  firstName?: string
  lastName?: string
  dateOfBirth?: string
  gender?: string
}

interface Props {
  patient: Patient
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  refresh: []
}>()

const router = useRouter()

// Computed
const patientDisplay = computed(() => {
  if (props.patient.firstName && props.patient.lastName) {
    return `${props.patient.firstName} ${props.patient.lastName}`
  }
  return `Patient ${props.patient.mrn || props.patient.id}`
})

// Methods
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const goBack = () => {
  router.push({ name: 'patients' })
}

const refreshTimeline = () => {
  emit('refresh')
}
</script>

<style scoped>
.patient-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background-color: #ffffff;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 1rem;
}

.patient-info {
  flex: 1;
}

.patient-name {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
  color: #333;
}

.patient-details {
  display: flex;
  gap: 1.5rem;
  font-size: 0.875rem;
  color: #666;
}

.detail-item strong {
  color: #333;
  margin-right: 0.25rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.btn-primary {
  background-color: #3498db;
  color: white;
}

.btn-primary:hover {
  background-color: #2980b9;
}

.btn-secondary {
  background-color: #95a5a6;
  color: white;
}

.btn-secondary:hover {
  background-color: #7f8c8d;
}
</style>
