<template>
  <v-container fluid class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card elevation="12" class="pa-4">
          <v-card-title class="text-h4 text-center mb-6">
            Clinical Care Tools
          </v-card-title>

          <v-card-subtitle class="text-center mb-6">
            Sign in to continue
          </v-card-subtitle>

          <v-card-text>
            <v-form
              ref="form"
              v-model="valid"
              lazy-validation
              @submit.prevent="handleLogin"
            >
              <v-text-field
                v-model="credentials.username"
                :rules="usernameRules"
                label="Username"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                required
                autofocus
                autocomplete="username"
                class="mb-4"
              />

              <v-text-field
                v-model="credentials.password"
                :rules="passwordRules"
                :type="showPassword ? 'text' : 'password'"
                label="Password"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                variant="outlined"
                required
                autocomplete="current-password"
                class="mb-4"
                @click:append-inner="showPassword = !showPassword"
                @keyup.enter="handleLogin"
              />

              <v-checkbox
                v-model="rememberMe"
                label="Remember me"
                class="mb-4"
              />

              <v-alert
                v-if="authStore.error"
                type="error"
                variant="tonal"
                closable
                class="mb-4"
                @click:close="authStore.error = null"
              >
                {{ authStore.error }}
              </v-alert>

              <v-btn
                :disabled="!valid || authStore.isLoading"
                :loading="authStore.isLoading"
                block
                color="primary"
                size="large"
                type="submit"
                variant="elevated"
              >
                Sign In
              </v-btn>
            </v-form>
          </v-card-text>

          <v-divider class="my-4" />

          <v-card-actions class="justify-center">
            <v-btn
              variant="text"
              color="primary"
              @click="showForgotPassword = true"
            >
              Forgot Password?
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-card class="mt-4" variant="text">
          <v-card-text class="text-center text-caption">
            <p>For demonstration purposes, use:</p>
            <p>Username: <code>demo</code> | Password: <code>demo123</code></p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Forgot Password Dialog -->
    <v-dialog v-model="showForgotPassword" max-width="500">
      <v-card>
        <v-card-title>Reset Password</v-card-title>
        <v-card-text>
          <p class="mb-4">Enter your email address and we'll send you a link to reset your password.</p>
          <v-text-field
            v-model="resetEmail"
            label="Email Address"
            type="email"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showForgotPassword = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="flat"
            @click="handlePasswordReset"
          >
            Send Reset Link
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive, inject } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { LoginCredentials } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notify = inject<(message: string, color?: string) => void>('notify')

// Form state
const form = ref()
const valid = ref(true)
const showPassword = ref(false)
const rememberMe = ref(false)
const showForgotPassword = ref(false)
const resetEmail = ref('')

// Form data
const credentials = reactive<LoginCredentials>({
  username: '',
  password: ''
})

// Validation rules
const usernameRules = [
  (v: string) => !!v || 'Username is required',
  (v: string) => v.length >= 3 || 'Username must be at least 3 characters'
]

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 6 || 'Password must be at least 6 characters'
]

// Methods
async function handleLogin() {
  const { valid } = await form.value.validate()

  if (!valid) return

  try {
    await authStore.login(credentials)

    // Show success message
    notify?.('Login successful!', 'success')

    // Redirect to intended page or dashboard
    const redirect = route.query.redirect as string
    router.push(redirect || '/dashboard')
  } catch (error) {
  }
}

async function handlePasswordReset() {
  showForgotPassword.value = false

  // NOTE: Implement password reset API call
  notify?.('Password reset link sent to your email', 'info')

  resetEmail.value = ''
}
</script>

<style scoped>
.v-container {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>