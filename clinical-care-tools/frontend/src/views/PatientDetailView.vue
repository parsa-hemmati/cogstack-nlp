<template>
  <app-layout>
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <v-btn icon @click="$router.back()">
            <v-icon>mdi-arrow-left</v-icon>
          </v-btn>
          <h1 class="text-h3 d-inline-block ml-4">Patient Details</h1>
        </v-col>
      </v-row>

      <v-row class="mt-4">
        <v-col cols="12">
          <v-card>
            <v-card-text>
              <p>Patient ID: {{ $route.params.id }}</p>
              <p class="text-body-1">Patient details will be displayed here</p>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </app-layout>
</template>

<script setup lang="ts">
import AppLayout from '@/components/AppLayout.vue'
</script>
