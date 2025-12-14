<template>
  <app-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-4">Patient Search</h1>
        </v-col>
      </v-row>

      <!-- Search Bar -->
      <v-row>
        <v-col cols="12" md="6">
          <v-text-field
            v-model="searchQuery"
            label="Search patients by name, MRN, or diagnosis"
            prepend-inner-icon="mdi-magnify"
            clearable
            variant="outlined"
            @input="handleSearch"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-select
            v-model="statusFilter"
            :items="['all', 'active', 'critical', 'stable']"
            label="Status"
            variant="outlined"
            @update:model-value="handleSearch"
          />
        </v-col>
        <v-col cols="12" md="3">
          <v-btn color="primary" size="large" block @click="handleSearch">
            <v-icon left>mdi-magnify</v-icon>
            Search
          </v-btn>
        </v-col>
      </v-row>

      <!-- Loading State -->
      <v-row v-if="isLoading">
        <v-col cols="12" class="text-center">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4">Loading patients...</p>
        </v-col>
      </v-row>

      <!-- Error State -->
      <v-alert v-else-if="error" type="error" class="mb-4">
        {{ error }}
        <template v-slot:append>
          <v-btn variant="text" @click="fetchPatients">Retry</v-btn>
        </template>
      </v-alert>

      <!-- Results -->
      <template v-else>
        <v-row>
          <v-col cols="12">
            <div class="text-subtitle-1 mb-4">
              Found {{ filteredPatients.length }} patients
            </div>
          </v-col>
        </v-row>

        <!-- Patient Cards -->
        <v-row>
          <v-col v-for="patient in filteredPatients" :key="patient.id" cols="12" md="6" lg="4">
            <v-card elevation="2" class="patient-card" :class="getStatusClass(patient.status)">
              <v-card-item>
                <template v-slot:prepend>
                  <v-avatar :color="getStatusColor(patient.status)" size="48">
                    <v-icon color="white">mdi-account</v-icon>
                  </v-avatar>
                </template>
                <v-card-title>{{ patient.first_name }} {{ patient.last_name }}</v-card-title>
                <v-card-subtitle>{{ patient.mrn }}</v-card-subtitle>
              </v-card-item>

              <v-card-text>
                <div class="mb-2">
                  <v-chip size="small" :color="getStatusColor(patient.status)" class="mr-2">
                    {{ patient.status }}
                  </v-chip>
                  <v-chip size="small" color="info" variant="outlined">
                    Risk: {{ patient.risk_score }}
                  </v-chip>
                </div>
                
                <div class="text-body-2">
                  <strong>Diagnosis:</strong> {{ patient.primary_diagnosis }}
                </div>
                
                <div class="text-body-2 mt-1">
                  <strong>DOB:</strong> {{ formatDate(patient.date_of_birth) }} ({{ patient.age }} yrs)
                </div>

                <div class="mt-2" v-if="patient.allergies && patient.allergies.length">
                  <strong class="text-body-2">Allergies:</strong>
                  <v-chip
                    v-for="allergy in patient.allergies.slice(0, 3)"
                    :key="allergy"
                    size="x-small"
                    color="error"
                    variant="tonal"
                    class="ml-1"
                  >
                    {{ allergy }}
                  </v-chip>
                </div>
              </v-card-text>

              <v-card-actions>
                <v-btn color="primary" variant="text" :to="`/patients/${patient.id}`">
                  View Details
                </v-btn>
                <v-spacer />
                <v-btn color="secondary" variant="text" :to="`/timeline?patient=${patient.id}`">
                  Timeline
                </v-btn>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>

        <!-- Empty State -->
        <v-row v-if="filteredPatients.length === 0 && !isLoading">
          <v-col cols="12">
            <v-alert type="info" variant="tonal">
              No patients found matching your criteria.
            </v-alert>
          </v-col>
        </v-row>
      </template>
    </v-container>
  </app-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import apiClient from '@/api/client'

interface Patient {
  id: string
  mrn: string
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  age: number
  primary_diagnosis: string
  allergies: string[]
  risk_score: number
  status: string
}

const patients = ref<Patient[]>([])
const searchQuery = ref('')
const statusFilter = ref('all')
const isLoading = ref(true)
const error = ref<string | null>(null)

const filteredPatients = computed(() => {
  let result = patients.value

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.first_name.toLowerCase().includes(query) ||
      p.last_name.toLowerCase().includes(query) ||
      p.mrn.toLowerCase().includes(query) ||
      p.primary_diagnosis.toLowerCase().includes(query)
    )
  }

  // Filter by status
  if (statusFilter.value !== 'all') {
    result = result.filter(p => p.status === statusFilter.value)
  }

  return result
})

async function fetchPatients() {
  isLoading.value = true
  error.value = null

  try {
    const response = await apiClient.get('/v1/patients')
    patients.value = response.data.items || response.data
  } catch (err: any) {
    console.error('Failed to fetch patients:', err)
    error.value = err.response?.data?.detail || 'Failed to load patients'
  } finally {
    isLoading.value = false
  }
}

function handleSearch() {
  // For client-side filtering, no API call needed
  // If you want server-side search, call fetchPatients with query params
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: 'success',
    critical: 'error',
    stable: 'info',
    inactive: 'grey'
  }
  return colors[status] || 'grey'
}

function getStatusClass(status: string): string {
  if (status === 'critical') return 'border-error'
  return ''
}

onMounted(() => {
  fetchPatients()
})
</script>

<style scoped>
.patient-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.patient-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.border-error {
  border-left: 4px solid rgb(var(--v-theme-error));
}
</style>

