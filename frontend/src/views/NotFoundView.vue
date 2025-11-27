<template>
  <v-container class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" md="6" class="text-center">
        <v-icon
          size="128"
          color="grey-lighten-1"
          class="mb-4"
        >
          mdi-file-question-outline
        </v-icon>

        <h1 class="text-h2 font-weight-bold text-grey-darken-2 mb-4">404</h1>

        <h2 class="text-h5 text-grey-darken-1 mb-6">Page Not Found</h2>

        <p class="text-body-1 text-grey mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <v-btn
          color="primary"
          size="large"
          :to="{ name: 'home' }"
        >
          <v-icon start>mdi-home</v-icon>
          Back to Home
        </v-btn>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
// 404 Not Found View
</script>

<style scoped>
.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
