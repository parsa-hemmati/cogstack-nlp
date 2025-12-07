/**
 * Authentication store using Pinia
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginRequest, RegisterRequest } from '@/types/user'
import { authApi } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role || null)
  const canBreakGlass = computed(() => user.value?.can_break_glass || false)

  // Actions
  async function login(credentials: LoginRequest) {
    isLoading.value = true
    error.value = null

    try {
      const response = await authApi.login(credentials)

      // Store tokens
      token.value = response.access_token
      refreshToken.value = response.refresh_token
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)

      // Store user
      user.value = response.user

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function register(userData: RegisterRequest) {
    isLoading.value = true
    error.value = null

    try {
      user.value = await authApi.register(userData)
      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Registration failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    isLoading.value = true

    try {
      await authApi.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      // Clear state
      user.value = null
      token.value = null
      refreshToken.value = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      isLoading.value = false
    }
  }

  async function fetchCurrentUser() {
    if (!token.value) {
      return
    }

    isLoading.value = true
    error.value = null

    try {
      user.value = await authApi.getCurrentUser()
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Failed to fetch user'
      // Clear invalid token
      logout()
    } finally {
      isLoading.value = false
    }
  }

  return {
    // State
    user,
    token,
    refreshToken,
    isLoading,
    error,

    // Getters
    isAuthenticated,
    userRole,
    canBreakGlass,

    // Actions
    login,
    register,
    logout,
    fetchCurrentUser,
  }
})
