<template>
  <v-container class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" md="6" class="text-center">
        <v-icon
          size="128"
          color="error"
          class="mb-4"
        >
          mdi-shield-lock-outline
        </v-icon>

        <h1 class="text-h2 font-weight-bold text-error mb-4">403</h1>

        <h2 class="text-h5 text-grey-darken-1 mb-6">Access Denied</h2>

        <p class="text-body-1 text-grey mb-4">
          You don't have permission to access this page.
        </p>

        <p class="text-body-2 text-grey-darken-1 mb-8">
          If you believe this is an error, please contact your administrator
          or request appropriate access permissions.
        </p>

        <v-alert
          v-if="authStore.userRole"
          type="info"
          variant="tonal"
          class="mb-8 text-left"
        >
          <strong>Your current role:</strong> {{ authStore.userRole }}
        </v-alert>

        <div class="d-flex justify-center gap-4">
          <v-btn
            color="primary"
            size="large"
            :to="{ name: 'home' }"
          >
            <v-icon start>mdi-home</v-icon>
            Back to Home
          </v-btn>

          <v-btn
            v-if="!authStore.isAuthenticated"
            color="secondary"
            size="large"
            :to="{ name: 'login' }"
            variant="outlined"
          >
            <v-icon start>mdi-login</v-icon>
            Sign In
          </v-btn>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
</script>

<style scoped>
.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
