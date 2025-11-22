<template>
  <v-container fluid class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" class="text-center">
        <v-icon size="120" color="warning">mdi-alert-circle-outline</v-icon>
        <h1 class="text-h2 mt-6 mb-4">404</h1>
        <h2 class="text-h4 mb-4">Page Not Found</h2>
        <p class="text-body-1 mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <v-btn
          color="primary"
          size="large"
          @click="$router.push('/dashboard')"
        >
          Go to Dashboard
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// Error page for 404 Not Found
</script>