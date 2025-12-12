/**
 * Authentication Store
 *
 * Manages user authentication state and session management.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User, LoginRequest } from '@/types/user'

const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const USER_KEY = 'auth_user'

export const useAuthStore = defineStore('auth', () => {
  // Initialize from localStorage if available
  const storedUser = localStorage.getItem(USER_KEY)
  const storedToken = localStorage.getItem(TOKEN_KEY)

  const user = ref<User | null>(storedUser ? JSON.parse(storedUser) : null)
  const accessToken = ref<string | null>(storedToken)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)

  async function login(credentials: LoginRequest) {
    isLoading.value = true
    error.value = null

    try {
      const response = await authApi.login(credentials)

      // Store tokens in localStorage
      localStorage.setItem(TOKEN_KEY, response.access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh_token)
      localStorage.setItem(USER_KEY, JSON.stringify(response.user))

      // Update state
      accessToken.value = response.access_token
      user.value = response.user

      return response
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } catch (err) {
      // Ignore logout errors - we're logging out anyway
      console.warn('Logout API call failed:', err)
    } finally {
      // Clear local state regardless of API success
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
      accessToken.value = null
      user.value = null
    }
  }

  async function fetchCurrentUser() {
    if (!accessToken.value) return null

    isLoading.value = true
    try {
      const currentUser = await authApi.getCurrentUser()
      user.value = currentUser
      localStorage.setItem(USER_KEY, JSON.stringify(currentUser))
      return currentUser
    } catch (err) {
      // Token might be invalid, clear it
      await logout()
      return null
    } finally {
      isLoading.value = false
    }
  }

  function getToken() {
    return accessToken.value || localStorage.getItem(TOKEN_KEY)
  }

  return {
    user,
    accessToken,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    fetchCurrentUser,
    getToken,
  }
})
