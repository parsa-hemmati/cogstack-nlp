<template>
  <v-container fluid class="fill-height">
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card elevation="8">
          <v-card-title class="text-h4 text-center pa-6"> Register Account </v-card-title>

          <v-card-text class="px-8 py-4">
            <v-form ref="formRef" v-model="valid" @submit.prevent="handleRegister">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.username"
                    label="Username"
                    prepend-inner-icon="mdi-account"
                    :rules="usernameRules"
                    :disabled="isLoading"
                    required
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.email"
                    label="Email"
                    prepend-inner-icon="mdi-email"
                    type="email"
                    :rules="emailRules"
                    :disabled="isLoading"
                    required
                  />
                </v-col>

                <v-col cols="12">
                  <v-text-field
                    v-model="formData.full_name"
                    label="Full Name"
                    prepend-inner-icon="mdi-card-account-details"
                    :rules="fullNameRules"
                    :disabled="isLoading"
                    required
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formData.password"
                    label="Password"
                    prepend-inner-icon="mdi-lock"
                    :type="showPassword ? 'text' : 'password'"
                    :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                    @click:append-inner="showPassword = !showPassword"
                    :rules="passwordRules"
                    :disabled="isLoading"
                    required
                  />
                </v-col>

                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="confirmPassword"
                    label="Confirm Password"
                    prepend-inner-icon="mdi-lock-check"
                    :type="showPassword ? 'text' : 'password'"
                    :rules="confirmPasswordRules"
                    :disabled="isLoading"
                    required
                  />
                </v-col>
              </v-row>

              <v-alert v-if="error" type="error" class="mb-4">
                {{ error }}
              </v-alert>

              <v-alert v-if="success" type="success" class="mb-4">
                Registration successful! Redirecting to login...
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                size="large"
                block
                :loading="isLoading"
                :disabled="!valid || success"
              >
                Register
              </v-btn>
            </v-form>
          </v-card-text>

          <v-divider />

          <v-card-actions class="px-8 py-4">
            <v-spacer />
            <span class="text-body-2">Already have an account?</span>
            <v-btn variant="text" color="primary" to="/login"> Login </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

// Form state
const formRef = ref()
const valid = ref(false)
const showPassword = ref(false)
const confirmPassword = ref('')
const isLoading = ref(false)
const error = ref<string | null>(null)
const success = ref(false)

const formData = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
})

// Validation rules
const usernameRules = [
  (v: string) => !!v || 'Username is required',
  (v: string) => v.length >= 3 || 'Username must be at least 3 characters',
]

const emailRules = [
  (v: string) => !!v || 'Email is required',
  (v: string) => /.+@.+\..+/.test(v) || 'Email must be valid',
]

const fullNameRules = [(v: string) => !!v || 'Full name is required']

const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 8 || 'Password must be at least 8 characters',
]

const confirmPasswordRules = [
  (v: string) => !!v || 'Please confirm password',
  (v: string) => v === formData.password || 'Passwords do not match',
]

// Handle registration
async function handleRegister() {
  if (!valid.value) return

  isLoading.value = true
  error.value = null

  try {
    await authStore.register(formData)
    success.value = true

    // Redirect to login after 2 seconds
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } catch (err: any) {
    error.value = err.response?.data?.detail || 'Registration failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.fill-height {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
</style>
