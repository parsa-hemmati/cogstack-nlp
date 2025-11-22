<template>
  <div>
    <!-- App Bar -->
    <AppHeader />

    <!-- Navigation Drawer -->
    <AppSidebar />

    <!-- Main Content -->
    <v-main>
      <v-container fluid>
        <v-row>
          <v-col cols="12">
            <h1 class="text-h4 mb-6">Dashboard</h1>
          </v-col>
        </v-row>

        <!-- Stats Cards -->
        <v-row>
          <v-col
            v-for="stat in stats"
            :key="stat.title"
            cols="12"
            sm="6"
            md="3"
          >
            <v-card>
              <v-card-text class="d-flex align-center">
                <div class="flex-grow-1">
                  <div class="text-caption text-medium-emphasis">
                    {{ stat.title }}
                  </div>
                  <div class="text-h5 font-weight-bold">
                    {{ stat.value }}
                  </div>
                  <div
                    class="text-caption"
                    :class="stat.trend > 0 ? 'text-success' : 'text-error'"
                  >
                    <v-icon size="x-small">
                      {{ stat.trend > 0 ? 'mdi-trending-up' : 'mdi-trending-down' }}
                    </v-icon>
                    {{ Math.abs(stat.trend) }}% from last month
                  </div>
                </div>
                <v-avatar
                  :color="stat.color"
                  size="64"
                  variant="tonal"
                >
                  <v-icon :icon="stat.icon" size="32" />
                </v-avatar>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Recent Activity & Quick Actions -->
        <v-row class="mt-6">
          <!-- Recent Activity -->
          <v-col cols="12" md="8">
            <v-card>
              <v-card-title>Recent Activity</v-card-title>
              <v-card-text>
                <v-list lines="two">
                  <v-list-item
                    v-for="activity in recentActivities"
                    :key="activity.id"
                    :prepend-icon="activity.icon"
                  >
                    <v-list-item-title>{{ activity.title }}</v-list-item-title>
                    <v-list-item-subtitle>{{ activity.description }}</v-list-item-subtitle>
                    <template v-slot:append>
                      <v-list-item-subtitle>{{ activity.time }}</v-list-item-subtitle>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
              <v-card-actions>
                <v-btn variant="text" color="primary">View All Activity</v-btn>
              </v-card-actions>
            </v-card>
          </v-col>

          <!-- Quick Actions -->
          <v-col cols="12" md="4">
            <v-card>
              <v-card-title>Quick Actions</v-card-title>
              <v-card-text>
                <v-list>
                  <v-list-item
                    v-for="action in quickActions"
                    :key="action.title"
                    :prepend-icon="action.icon"
                    :to="action.to"
                    link
                  >
                    <v-list-item-title>{{ action.title }}</v-list-item-title>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- System Status -->
        <v-row class="mt-6">
          <v-col cols="12">
            <v-card>
              <v-card-title>System Status</v-card-title>
              <v-card-text>
                <v-row>
                  <v-col
                    v-for="service in systemServices"
                    :key="service.name"
                    cols="12"
                    sm="6"
                    md="3"
                  >
                    <div class="d-flex align-center mb-2">
                      <v-icon
                        :color="service.status === 'operational' ? 'success' : 'error'"
                        size="small"
                        class="mr-2"
                      >
                        {{ service.status === 'operational' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                      </v-icon>
                      <span class="font-weight-medium">{{ service.name }}</span>
                    </div>
                    <div class="text-caption text-medium-emphasis ml-6">
                      {{ service.description }}
                    </div>
                  </v-col>
                </v-row>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>

    <!-- Footer -->
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppFooter from '@/components/layout/AppFooter.vue'

const authStore = useAuthStore()

// Dashboard statistics
const stats = ref([
  {
    title: 'Total Patients',
    value: '1,234',
    trend: 12,
    icon: 'mdi-account-group',
    color: 'primary'
  },
  {
    title: 'Documents Processed',
    value: '5,678',
    trend: -5,
    icon: 'mdi-file-document',
    color: 'success'
  },
  {
    title: 'Active Sessions',
    value: '23',
    trend: 8,
    icon: 'mdi-monitor',
    color: 'info'
  },
  {
    title: 'Accuracy Rate',
    value: '95.2%',
    trend: 2,
    icon: 'mdi-chart-line',
    color: 'warning'
  }
])

// Recent activities
const recentActivities = ref([
  {
    id: 1,
    icon: 'mdi-file-upload',
    title: 'Document uploaded',
    description: 'Patient record for John Doe processed successfully',
    time: '2 min ago'
  },
  {
    id: 2,
    icon: 'mdi-magnify',
    title: 'Search performed',
    description: 'Cohort search for "diabetes mellitus type 2"',
    time: '15 min ago'
  },
  {
    id: 3,
    icon: 'mdi-export',
    title: 'FHIR export completed',
    description: '250 patient records exported to FHIR R4',
    time: '1 hour ago'
  },
  {
    id: 4,
    icon: 'mdi-account-plus',
    title: 'New patient added',
    description: 'Patient ID #P-2024-001 registered',
    time: '3 hours ago'
  }
])

// Quick actions
const quickActions = ref([
  {
    icon: 'mdi-magnify',
    title: 'Search Patients',
    to: '/search'
  },
  {
    icon: 'mdi-file-upload',
    title: 'Upload Documents',
    to: '/documents/upload'
  },
  {
    icon: 'mdi-chart-box',
    title: 'Generate Report',
    to: '/reports/new'
  },
  {
    icon: 'mdi-export',
    title: 'Export to FHIR',
    to: '/export/fhir'
  }
])

// System services status
const systemServices = ref([
  {
    name: 'API Server',
    status: 'operational',
    description: 'All endpoints responding'
  },
  {
    name: 'MedCAT Service',
    status: 'operational',
    description: 'NLP processing active'
  },
  {
    name: 'Database',
    status: 'operational',
    description: 'PostgreSQL running'
  },
  {
    name: 'Search Index',
    status: 'operational',
    description: 'Elasticsearch healthy'
  }
])

onMounted(() => {
  // Load dashboard data
  // NOTE: Fetch real data from API
})
</script>