<template>
  <app-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h3 mb-4">Patient Search</h1>
        </v-col>
      </v-row>

      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-text>
              <v-text-field
                v-model="searchQuery"
                label="Search patients..."
                prepend-inner-icon="mdi-magnify"
                clearable
                @keyup.enter="handleSearch"
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <v-col cols="12">
          <v-card>
            <v-card-title>Search Results</v-card-title>
            <v-card-text>
              <p class="text-center text-body-1">
                Enter search criteria above to find patients
              </p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </app-layout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/AppLayout.vue'

const searchQuery = ref('')

function handleSearch() {
  console.log('Searching for:', searchQuery.value)
  // TODO: Implement patient search
}
</script>
