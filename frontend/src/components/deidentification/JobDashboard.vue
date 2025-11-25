<template>
  <v-card>
    <v-card-title>De-identification Jobs</v-card-title>
    <v-card-subtitle>Manage batch de-identification jobs</v-card-subtitle>

    <v-card-text>
      <!-- Filters -->
      <v-row>
        <v-col cols="12" md="4">
          <v-select
            v-model="statusFilter"
            :items="statusOptions"
            label="Status Filter"
            density="compact"
          ></v-select>
        </v-col>
        <v-col cols="12" md="4">
          <v-text-field
            v-model="searchText"
            label="Search"
            prepend-icon="mdi-magnify"
            density="compact"
            clearable
          ></v-text-field>
        </v-col>
        <v-col cols="12" md="4">
          <v-btn
            @click="loadJobs"
            :loading="loading"
            block
            color="primary"
          >
            Refresh
          </v-btn>
        </v-col>
      </v-row>

      <!-- Jobs table -->
      <v-data-table
        :headers="headers"
        :items="filteredJobs"
        :loading="loading"
        :items-per-page="50"
        @click:row="viewJob"
        class="mt-4"
      >
        <template #item.status="{ item }">
          <v-chip :color="getStatusColor(item.status)" size="small">
            {{ item.status }}
          </v-chip>
        </template>

        <template #item.progress="{ item }">
          <v-progress-linear
            :model-value="(item.processed_notes / item.total_notes) * 100"
            color="primary"
            height="20"
          >
            <template #default="{ value }">
              {{ Math.ceil(value) }}%
            </template>
          </v-progress-linear>
        </template>

        <template #item.actions="{ item }">
          <v-btn
            icon="mdi-eye"
            size="small"
            variant="text"
            @click.stop="viewJob(item)"
          ></v-btn>
          <v-btn
            v-if="item.status === 'processing'"
            icon="mdi-cancel"
            size="small"
            variant="text"
            color="error"
            @click.stop="cancelJob(item.job_id)"
          ></v-btn>
        </template>
      </v-data-table>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

interface Job {
  job_id: string
  status: string
  total_notes: number
  processed_notes: number
  error_count: number
  created_at: string
  method: string
}

const loading = ref(false)
const jobs = ref<Job[]>([])
const statusFilter = ref('All')
const searchText = ref('')

const statusOptions = ['All', 'Pending', 'Processing', 'Completed', 'Failed', 'Cancelled']

const headers = [
  { title: 'Job ID', key: 'job_id', width: '200px' },
  { title: 'Status', key: 'status', width: '120px' },
  { title: 'Method', key: 'method', width: '120px' },
  { title: 'Progress', key: 'progress', width: '150px' },
  { title: 'Notes', key: 'total_notes', width: '100px' },
  { title: 'Errors', key: 'error_count', width: '80px' },
  { title: 'Created', key: 'created_at', width: '180px' },
  { title: 'Actions', key: 'actions', width: '100px', sortable: false }
]

const filteredJobs = computed(() => {
  let filtered = jobs.value

  if (statusFilter.value !== 'All') {
    filtered = filtered.filter(j => j.status.toLowerCase() === statusFilter.value.toLowerCase())
  }

  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    filtered = filtered.filter(j =>
      j.job_id.toLowerCase().includes(search) ||
      j.method.toLowerCase().includes(search)
    )
  }

  return filtered
})

const loadJobs = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/v1/deidentify/jobs', {
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    if (response.ok) {
      jobs.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load jobs:', error)
  } finally {
    loading.value = false
  }
}

const viewJob = (job: Job) => {
  console.log('View job:', job.job_id)
  // Navigate to job details page
}

const cancelJob = async (jobId: string) => {
  if (!confirm('Are you sure you want to cancel this job?')) return

  try {
    const response = await fetch(`/api/v1/deidentify/job/${jobId}/cancel`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getAuthToken()}`
      }
    })
    if (response.ok) {
      await loadJobs()
    }
  } catch (error) {
    console.error('Failed to cancel job:', error)
  }
}

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'grey',
    processing: 'blue',
    completed: 'green',
    failed: 'red',
    cancelled: 'orange'
  }
  return colors[status.toLowerCase()] || 'grey'
}

const getAuthToken = (): string => {
  return localStorage.getItem('authToken') || ''
}

onMounted(() => {
  loadJobs()
})
</script>

<style scoped>
.v-data-table >>> .v-data-table__tr:hover {
  cursor: pointer;
}
</style>
