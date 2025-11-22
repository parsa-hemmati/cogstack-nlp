import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'
import type { User, LoginCredentials, AuthTokens } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const tokenExpiry = ref<number | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)

  const permissions = computed(() => user.value?.permissions || [])

  const roles = computed(() => user.value?.roles || [])

  const displayName = computed(() => {
    if (!user.value) return ''
    return user.value.displayName || `${user.value.firstName} ${user.value.lastName}`.trim()
  })

  // Actions
  async function login(credentials: LoginCredentials): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await api.post<AuthTokens>('/auth/login', credentials)
      const { access_token, refresh_token, user: userData, expires_in } = response.data

      // Store tokens
      token.value = access_token
      refreshToken.value = refresh_token
      user.value = userData
      tokenExpiry.value = Date.now() + (expires_in * 1000)

      // Save to localStorage (persisted by pinia-plugin-persistedstate)
      localStorage.setItem(import.meta.env.VITE_AUTH_TOKEN_KEY, access_token)
      if (refresh_token) {
        localStorage.setItem(import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY, refresh_token)
      }

      // Set default authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    try {
      // Call logout endpoint if authenticated
      if (isAuthenticated.value) {
        await api.post('/auth/logout')
      }
    } catch (err) {
    } finally {
      // Clear local state
      user.value = null
      token.value = null
      refreshToken.value = null
      tokenExpiry.value = null
      error.value = null

      // Clear localStorage
      localStorage.removeItem(import.meta.env.VITE_AUTH_TOKEN_KEY)
      localStorage.removeItem(import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY)

      // Remove authorization header
      delete api.defaults.headers.common['Authorization']
    }
  }

  async function refreshTokens(): Promise<void> {
    if (!refreshToken.value) {
      throw new Error('No refresh token available')
    }

    try {
      const response = await api.post<AuthTokens>('/auth/refresh', {
        refresh_token: refreshToken.value
      })

      const { access_token, refresh_token: newRefreshToken, expires_in } = response.data

      // Update tokens
      token.value = access_token
      if (newRefreshToken) {
        refreshToken.value = newRefreshToken
      }
      tokenExpiry.value = Date.now() + (expires_in * 1000)

      // Update localStorage
      localStorage.setItem(import.meta.env.VITE_AUTH_TOKEN_KEY, access_token)
      if (newRefreshToken) {
        localStorage.setItem(import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY, newRefreshToken)
      }

      // Update authorization header
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
    } catch (err: any) {
      await logout()
      throw err
    }
  }

  async function validateToken(): Promise<boolean> {
    if (!token.value) return false

    try {
      const response = await api.get<User>('/auth/me')
      user.value = response.data
      return true
    } catch (err) {
      return false
    }
  }

  function shouldRefreshToken(): boolean {
    if (!tokenExpiry.value) return false

    // Refresh if token expires in less than 5 minutes
    const fiveMinutes = 5 * 60 * 1000
    return tokenExpiry.value - Date.now() < fiveMinutes
  }

  function hasPermission(permission: string): boolean {
    return permissions.value.includes(permission)
  }

  function hasRole(role: string): boolean {
    return roles.value.includes(role)
  }

  function hasAnyPermission(permissionList: string[]): boolean {
    return permissionList.some(permission => hasPermission(permission))
  }

  function hasAllPermissions(permissionList: string[]): boolean {
    return permissionList.every(permission => hasPermission(permission))
  }

  // Initialize from localStorage on store creation
  function initialize() {
    const savedToken = localStorage.getItem(import.meta.env.VITE_AUTH_TOKEN_KEY)
    const savedRefreshToken = localStorage.getItem(import.meta.env.VITE_AUTH_REFRESH_TOKEN_KEY)

    if (savedToken) {
      token.value = savedToken
      refreshToken.value = savedRefreshToken
      api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`

      // Validate token on initialization
      validateToken().catch(() => {
        logout()
      })
    }
  }

  // Initialize store
  initialize()

  return {
    // State
    user,
    token,
    refreshToken,
    tokenExpiry,
    isLoading,
    error,

    // Getters
    isAuthenticated,
    permissions,
    roles,
    displayName,

    // Actions
    login,
    logout,
    refreshToken: refreshTokens,
    validateToken,
    shouldRefreshToken,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions
  }
}, {
  persist: {
    key: 'cct-auth',
    storage: localStorage,
    paths: ['user', 'token', 'refreshToken', 'tokenExpiry']
  }
})