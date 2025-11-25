<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="8" offset-md="2">
        <DeidentifyUpload />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import DeidentifyUpload from '@/components/deidentification/DeidentifyUpload.vue'
</script>
