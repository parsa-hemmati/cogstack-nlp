<template>
  <div>
    <AppHeader />
    <AppSidebar />
    <v-main>
      <v-container fluid>
        <h1 class="text-h4 mb-6">Patients</h1>
        <v-card>
          <v-card-text>
            <p>Patients view - To be implemented</p>
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