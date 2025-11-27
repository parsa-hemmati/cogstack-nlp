<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="text-h4">
            Welcome to Clinical Care Tools
          </v-card-title>
          <v-card-text>
            <p class="text-body-1 mb-4">
              A comprehensive platform leveraging MedCAT's full NLP capabilities for healthcare
              research, delivery, and governance.
            </p>

            <v-row>
              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>
                    <v-icon left>mdi-magnify</v-icon>
                    Patient Search
                  </v-card-title>
                  <v-card-text>
                    Search and discover patients using medical concepts with advanced NLP filtering.
                  </v-card-text>
                  <v-card-actions>
                    <v-btn to="/patients" color="primary">Explore</v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>

              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>
                    <v-icon left>mdi-timeline</v-icon>
                    Timeline View
                  </v-card-title>
                  <v-card-text>
                    Visualize patient clinical journey over time with annotated medical concepts.
                  </v-card-text>
                  <v-card-actions>
                    <v-btn to="/timeline" color="primary">Explore</v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>

              <v-col cols="12" md="4">
                <v-card variant="outlined">
                  <v-card-title>
                    <v-icon left>mdi-shield-lock</v-icon>
                    Compliance
                  </v-card-title>
                  <v-card-text>
                    HIPAA and GDPR compliant with full audit logging and encryption.
                  </v-card-text>
                  <v-card-actions>
                    <v-btn disabled color="primary">Coming Soon</v-btn>
                  </v-card-actions>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>System Status</v-card-title>
          <v-card-text>
            <v-chip v-if="healthStatus === 'healthy'" color="success" prepend-icon="mdi-check-circle">
              All Systems Operational
            </v-chip>
            <v-chip v-else-if="healthStatus === 'loading'" color="info" prepend-icon="mdi-loading">
              Checking Status...
            </v-chip>
            <v-chip v-else color="error" prepend-icon="mdi-alert-circle">
              System Unhealthy
            </v-chip>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const healthStatus = ref<'loading' | 'healthy' | 'unhealthy'>('loading')

onMounted(async () => {
  try {
    const response = await axios.get('/api/health')
    healthStatus.value = response.data.status === 'healthy' ? 'healthy' : 'unhealthy'
  } catch (error) {
    healthStatus.value = 'unhealthy'
  }
})
</script>
