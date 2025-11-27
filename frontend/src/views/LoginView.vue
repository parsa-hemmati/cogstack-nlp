<template>
  <v-container class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="pa-6" elevation="4">
          <!-- Logo / Title -->
          <div class="text-center mb-6">
            <v-icon
              size="64"
              color="primary"
              class="mb-4"
            >
              mdi-brain
            </v-icon>
            <h1 class="text-h5 font-weight-bold">
              CogStack NLP
            </h1>
            <p class="text-body-2 text-grey">
              Clinical Care Tools
            </p>
          </div>

          <!-- Session Expired Message -->
          <v-alert
            v-if="sessionExpired"
            type="warning"
            variant="tonal"
            class="mb-4"
          >
            Your session has expired. Please sign in again.
          </v-alert>

          <!-- Error Message -->
          <v-alert
            v-if="authStore.error"
            type="error"
            variant="tonal"
            class="mb-4"
            closable
            @click:close="authStore.error = null"
          >
            {{ authStore.error }}
          </v-alert>

          <!-- Login Form -->
          <v-form @submit.prevent="handleLogin" ref="formRef">
            <v-text-field
              v-model="username"
              label="Username"
              prepend-inner-icon="mdi-account"
              :rules="[rules.required]"
              :disabled="authStore.loading"
              variant="outlined"
              density="comfortable"
              class="mb-2"
              autocomplete="username"
            />

            <v-text-field
              v-model="password"
              label="Password"
              prepend-inner-icon="mdi-lock"
              :type="showPassword ? 'text' : 'password'"
              :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
              @click:append-inner="showPassword = !showPassword"
              :rules="[rules.required]"
              :disabled="authStore.loading"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              autocomplete="current-password"
            />

            <v-btn
              type="submit"
              color="primary"
              size="large"
              block
              :loading="authStore.loading"
              :disabled="authStore.loading"
            >
              <v-icon start>mdi-login</v-icon>
              Sign In
            </v-btn>
          </v-form>

          <!-- Security Notice -->
          <v-alert
            type="info"
            variant="text"
            density="compact"
            class="mt-6"
            icon="mdi-shield-check"
          >
            <span class="text-caption">
              This is a secure healthcare application. All access is logged
              and audited for HIPAA compliance.
            </span>
          </v-alert>
        </v-card>

        <!-- Support Link -->
        <div class="text-center mt-4">
          <span class="text-caption text-grey">
            Having trouble signing in?
            <a href="mailto:support@cogstack.org" class="text-primary">
              Contact support
            </a>
          </span>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form state
const formRef = ref()
const username = ref('')
const password = ref('')
const showPassword = ref(false)

// Validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required'
}

// Check if redirected due to session expiration
const sessionExpired = computed(() => {
  return route.query.reason === 'session_expired'
})

// Handle login
async function handleLogin() {
  const { valid } = await formRef.value.validate()
  if (!valid) return

  const success = await authStore.login({
    username: username.value,
    password: password.value
  })

  if (success) {
    // Redirect to original destination or home
    const redirect = route.query.redirect as string || '/'
    router.push(redirect)
  }
}

// Focus username field on mount
onMounted(() => {
  // Clear any previous errors
  authStore.error = null
})
</script>

<style scoped>
.fill-height {
  min-height: calc(100vh - 64px);
}
</style>
