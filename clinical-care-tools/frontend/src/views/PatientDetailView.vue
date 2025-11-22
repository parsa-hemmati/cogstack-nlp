<template>
  <div>
    <AppHeader />
    <AppSidebar />
    <v-main>
      <v-container fluid>
        <h1 class="text-h4 mb-6">Patient Details</h1>
        <v-card>
          <v-card-text>
            <p>Patient detail view for ID: {{ $route.params.id }} - To be implemented</p>
          </v-card-text>
        </v-card>
      </v-container>
    </v-main>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppFooter from '@/components/layout/AppFooter.vue'
</script>