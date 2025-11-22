<template>
  <v-container>
    <v-row>
      <v-col cols="12" md="8" offset-md="2">
        <DeidentifyJobStatus :job-id="jobId" />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import DeidentifyJobStatus from '@/components/deidentification/DeidentifyJobStatus.vue'

const route = useRoute()
const jobId = computed(() => route.params.jobId as string)
</script>
