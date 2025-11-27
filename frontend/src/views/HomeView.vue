<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h3 font-weight-bold mb-4">
          CogStack NLP Clinical Care Tools
        </h1>
        <p class="text-subtitle-1 text-grey-darken-1 mb-8">
          Healthcare NLP platform powered by MedCAT for clinical document analysis,
          patient search, and de-identification.
        </p>
      </v-col>
    </v-row>

    <!-- Authentication Status -->
    <v-row v-if="!authStore.isAuthenticated">
      <v-col cols="12">
        <v-alert type="info" variant="tonal" class="mb-6">
          <v-row align="center">
            <v-col>
              Please sign in to access clinical care tools.
            </v-col>
            <v-col cols="auto">
              <v-btn color="primary" :to="{ name: 'login' }">
                Sign In
              </v-btn>
            </v-col>
          </v-row>
        </v-alert>
      </v-col>
    </v-row>

    <!-- Feature Cards for Authenticated Users -->
    <v-row v-else>
      <v-col cols="12" md="4" v-for="feature in availableFeatures" :key="feature.route">
        <v-card
          :to="{ name: feature.route }"
          class="pa-6 h-100"
          elevation="2"
          hover
        >
          <v-icon
            :color="feature.color"
            size="48"
            class="mb-4"
          >
            {{ feature.icon }}
          </v-icon>

          <h3 class="text-h6 font-weight-bold mb-2">
            {{ feature.title }}
          </h3>

          <p class="text-body-2 text-grey-darken-1">
            {{ feature.description }}
          </p>

          <v-chip
            v-if="feature.roles"
            size="small"
            color="grey-lighten-2"
            class="mt-4"
          >
            {{ feature.roles.join(', ') }}
          </v-chip>
        </v-card>
      </v-col>
    </v-row>

    <!-- Quick Stats for Admins -->
    <v-row v-if="authStore.isAdmin" class="mt-8">
      <v-col cols="12">
        <h2 class="text-h5 font-weight-bold mb-4">System Overview</h2>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" color="primary" variant="tonal">
          <v-icon size="32" class="mb-2">mdi-account-group</v-icon>
          <div class="text-h5 font-weight-bold">--</div>
          <div class="text-caption">Total Users</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" color="success" variant="tonal">
          <v-icon size="32" class="mb-2">mdi-file-document-multiple</v-icon>
          <div class="text-h5 font-weight-bold">--</div>
          <div class="text-caption">Documents</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" color="info" variant="tonal">
          <v-icon size="32" class="mb-2">mdi-magnify</v-icon>
          <div class="text-h5 font-weight-bold">--</div>
          <div class="text-caption">Searches Today</div>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card class="pa-4 text-center" color="warning" variant="tonal">
          <v-icon size="32" class="mb-2">mdi-shield-check</v-icon>
          <div class="text-h5 font-weight-bold">--</div>
          <div class="text-caption">De-ID Jobs</div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

interface Feature {
  title: string
  description: string
  icon: string
  color: string
  route: string
  roles: string[]
}

const features: Feature[] = [
  {
    title: 'Patient Search',
    description: 'Search for patients by clinical concepts, conditions, and meta-annotations.',
    icon: 'mdi-account-search',
    color: 'primary',
    route: 'patient-search',
    roles: ['admin', 'clinician']
  },
  {
    title: 'Document Search',
    description: 'Full-text search across clinical documents with advanced query capabilities.',
    icon: 'mdi-magnify',
    color: 'info',
    route: 'search',
    roles: ['admin', 'clinician', 'researcher']
  },
  {
    title: 'Document Upload',
    description: 'Upload and manage clinical documents for NLP processing.',
    icon: 'mdi-file-upload',
    color: 'success',
    route: 'documents',
    roles: ['admin', 'clinician', 'researcher']
  },
  {
    title: 'De-Identification',
    description: 'Remove PHI from clinical documents for research use.',
    icon: 'mdi-shield-lock',
    color: 'warning',
    route: 'deidentify-upload',
    roles: ['admin', 'clinician', 'researcher']
  },
  {
    title: 'User Management',
    description: 'Manage users, roles, and permissions.',
    icon: 'mdi-account-cog',
    color: 'secondary',
    route: 'user-management',
    roles: ['admin']
  },
  {
    title: 'Search Analytics',
    description: 'View search usage statistics and trends.',
    icon: 'mdi-chart-bar',
    color: 'purple',
    route: 'admin-search-analytics',
    roles: ['admin']
  }
]

const availableFeatures = computed(() => {
  return features.filter(feature => {
    return authStore.canAccess(feature.roles as any[])
  })
})
</script>

<style scoped>
.h-100 {
  height: 100%;
}
</style>
