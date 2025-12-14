<template>
  <app-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-4">Dashboard</h1>
        </v-col>
      </v-row>

      <!-- Loading State -->
      <v-row v-if="isLoading">
        <v-col cols="12" class="text-center">
          <v-progress-circular indeterminate color="primary" size="64" />
          <p class="mt-4">Loading dashboard...</p>
        </v-col>
      </v-row>

      <!-- Error State -->
      <v-alert v-else-if="error" type="error" class="mb-4">
        {{ error }}
        <template v-slot:append>
          <v-btn variant="text" @click="fetchDashboardData">Retry</v-btn>
        </template>
      </v-alert>

      <!-- Stats Cards -->
      <v-row v-else>
        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-primary">{{ stats.total_patients }}</div>
              <div class="text-body-1">Total Patients</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-success">{{ stats.documents_today }}</div>
              <div class="text-body-1">Documents Today</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="3">
          <v-card elevation="2">
            <v-card-text>
              <div class="text-h2 text-info">{{ stats.active_projects }}</div>
              <div class="text-body-1">Active Projects</div>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="3">
          <v-card elevation="2" :class="stats.critical_patients > 0 ? 'border-error' : ''">
            <v-card-text>
              <div class="text-h2" :class="stats.critical_patients > 0 ? 'text-error' : 'text-warning'">
                {{ stats.critical_patients }}
              </div>
              <div class="text-body-1">Critical Patients</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4" v-if="!isLoading && !error">
        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title>Recent Activity</v-card-title>
            <v-card-text>
              <v-list v-if="recentActivity.length > 0">
                <v-list-item v-for="(activity, index) in recentActivity" :key="index">
                  <template v-slot:prepend>
                    <v-icon :color="getActivityColor(activity.type)">
                      {{ getActivityIcon(activity.type) }}
                    </v-icon>
                  </template>
                  <v-list-item-title>{{ activity.item }}</v-list-item-title>
                  <v-list-item-subtitle>{{ activity.action }} • {{ activity.time }}</v-list-item-subtitle>
                </v-list-item>
              </v-list>
              <v-list v-else>
                <v-list-item>
                  <v-list-item-title>No recent activity</v-list-item-title>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title>Quick Actions</v-card-title>
            <v-card-text>
              <v-btn block color="primary" class="mb-2" to="/patients">
                <v-icon left>mdi-account-search</v-icon>
                Search Patients
              </v-btn>

              <v-btn block color="secondary" class="mb-2" to="/projects">
                <v-icon left>mdi-folder-open</v-icon>
                View Projects ({{ stats.active_projects }})
              </v-btn>

              <v-btn block color="warning" to="/alerts" v-if="stats.unread_alerts > 0">
                <v-icon left>mdi-alert</v-icon>
                View Alerts ({{ stats.unread_alerts }} unread)
              </v-btn>
              <v-btn block color="info" to="/timeline" v-else>
                <v-icon left>mdi-timeline</v-icon>
                View Timeline
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </app-layout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import apiClient from '@/api/client'

interface DashboardStats {
  total_patients: number
  active_projects: number
  pending_tasks: number
  unread_alerts: number
  documents_today: number
  critical_patients: number
}

interface Activity {
  type: string
  action: string
  item: string
  time: string
}

const isLoading = ref(true)
const error = ref<string | null>(null)
const stats = ref<DashboardStats>({
  total_patients: 0,
  active_projects: 0,
  pending_tasks: 0,
  unread_alerts: 0,
  documents_today: 0,
  critical_patients: 0
})
const recentActivity = ref<Activity[]>([])

async function fetchDashboardData() {
  isLoading.value = true
  error.value = null
  
  try {
    const response = await apiClient.get('/v1/dashboard')
    stats.value = response.data.stats
    recentActivity.value = response.data.recent_activity || []
  } catch (err: any) {
    console.error('Failed to fetch dashboard data:', err)
    error.value = err.response?.data?.detail || 'Failed to load dashboard data'
  } finally {
    isLoading.value = false
  }
}

function getActivityIcon(type: string): string {
  const icons: Record<string, string> = {
    document: 'mdi-file-document',
    alert: 'mdi-alert',
    patient: 'mdi-account',
    task: 'mdi-check-circle'
  }
  return icons[type] || 'mdi-information'
}

function getActivityColor(type: string): string {
  const colors: Record<string, string> = {
    document: 'success',
    alert: 'warning',
    patient: 'primary',
    task: 'info'
  }
  return colors[type] || 'grey'
}

onMounted(() => {
  fetchDashboardData()
})
</script>

<style scoped>
.border-error {
  border-left: 4px solid rgb(var(--v-theme-error));
}
</style>

