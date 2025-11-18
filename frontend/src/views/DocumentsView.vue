<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 mb-4">
          <v-icon class="mr-2">mdi-file-document-multiple</v-icon>
          Clinical Documents
        </h1>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="8" lg="6">
        <DocumentUpload />
      </v-col>
    </v-row>

    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-file-document-outline</v-icon>
            Recent Documents
          </v-card-title>
          <v-card-text>
            <v-alert type="info" variant="tonal">
              Document list view coming soon. Uploaded documents will be processed in the background
              and their entities will be available for patient search.
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import DocumentUpload from '@/components/documents/DocumentUpload.vue'
</script>
