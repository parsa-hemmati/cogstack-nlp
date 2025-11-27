<template>
  <v-container fluid class="search-analytics-view">
    <!-- Breadcrumbs -->
    <v-breadcrumbs :items="breadcrumbItems" class="px-0 pt-2">
      <template #divider>
        <v-icon>mdi-chevron-right</v-icon>
      </template>
    </v-breadcrumbs>

    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center mb-6">
          <div>
            <h1 class="text-h3 mb-2">Search Analytics</h1>
            <p class="text-body-1 text-grey-darken-1">
              Monitor search performance, user behavior, and identify optimization opportunities.
            </p>
          </div>
        </div>
      </v-col>
    </v-row>

    <!-- Info Cards -->
    <v-row>
      <v-col cols="12" md="4">
        <v-card color="blue-lighten-5" variant="tonal">
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="48" color="blue" class="mr-3">mdi-trending-up</v-icon>
              <div>
                <div class="text-h6">Top Queries</div>
                <div class="text-caption">Most frequently searched terms</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card color="orange-lighten-5" variant="tonal">
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="48" color="orange" class="mr-3">mdi-alert-circle</v-icon>
              <div>
                <div class="text-h6">Zero Results</div>
                <div class="text-caption">Queries with no results found</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <v-card color="red-lighten-5" variant="tonal">
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="48" color="red" class="mr-3">mdi-speedometer-slow</v-icon>
              <div>
                <div class="text-h6">Slow Queries</div>
                <div class="text-caption">Performance optimization candidates</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Search Analytics Component -->
    <v-row>
      <v-col cols="12">
        <SearchAnalytics />
      </v-col>
    </v-row>

    <!-- Help Section -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>How to Use Search Analytics</v-card-title>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <template #prepend>
                  <v-icon color="primary">mdi-information</v-icon>
                </template>
                <v-list-item-title>Top Queries</v-list-item-title>
                <v-list-item-subtitle>
                  Identify popular search terms to understand user intent and improve content relevance
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon color="warning">mdi-magnify-remove-outline</v-icon>
                </template>
                <v-list-item-title>Zero Result Queries</v-list-item-title>
                <v-list-item-subtitle>
                  Find gaps in your content - queries that return no results may indicate missing documentation or poor query formulation
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon color="error">mdi-timer-alert</v-icon>
                </template>
                <v-list-item-title>Slow Queries</v-list-item-title>
                <v-list-item-subtitle>
                  Queries exceeding 2000ms execution time - candidates for optimization through indexing or query refinement
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon color="info">mdi-chart-line</v-icon>
                </template>
                <v-list-item-title>Search Trends</v-list-item-title>
                <v-list-item-subtitle>
                  Daily search volume helps identify usage patterns and capacity planning needs
                </v-list-item-subtitle>
              </v-list-item>

              <v-list-item>
                <template #prepend>
                  <v-icon color="success">mdi-download</v-icon>
                </template>
                <v-list-item-title>Export to CSV</v-list-item-title>
                <v-list-item-subtitle>
                  Download all analytics data for further analysis in Excel or other tools
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import SearchAnalytics from '@/components/search/SearchAnalytics.vue'

const router = useRouter()

// Breadcrumb items
const breadcrumbItems = computed(() => [
  {
    title: 'Home',
    disabled: false,
    to: '/',
  },
  {
    title: 'Admin',
    disabled: false,
    to: '/admin',
  },
  {
    title: 'Search Analytics',
    disabled: true,
  },
])
</script>

<style scoped>
.search-analytics-view {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
