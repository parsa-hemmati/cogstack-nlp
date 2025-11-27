/**
 * Base API client configuration
 *
 * Handles token injection and 401 response handling with proper
 * coordination with the auth store to prevent race conditions.
 */
import axios, { type AxiosInstance, type AxiosError } from 'axios'
import router from '@/router'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Track if we're currently handling a 401 to prevent multiple redirects
let isHandling401 = false

/**
 * Create axios instance with base configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Add JWT token to requests
 */
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

/**
 * Handle 401 unauthorized responses
 *
 * IMPORTANT: This interceptor coordinates with the auth store to prevent
 * race conditions. Key behaviors:
 * 1. Uses a flag to prevent multiple concurrent 401 handlers
 * 2. Attempts token refresh through auth store (which has mutex)
 * 3. Uses Vue Router instead of window.location for proper SPA navigation
 * 4. Skips handling for refresh endpoint itself to prevent infinite loops
 */
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config

    // Skip 401 handling if:
    // 1. Already handling a 401 (prevent race condition)
    // 2. This IS the refresh request itself (prevent infinite loop)
    // 3. This IS the login request (don't redirect on login failures)
    const isRefreshRequest = originalRequest?.url?.includes('/auth/refresh')
    const isLoginRequest = originalRequest?.url?.includes('/auth/login')

    if (error.response?.status === 401 && !isHandling401 && !isRefreshRequest && !isLoginRequest) {
      isHandling401 = true

      try {
        // Dynamically import auth store to avoid circular dependency
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()

        // Try to refresh the token using the store's mutex-protected method
        const refreshed = await authStore.refresh()

        if (refreshed && originalRequest) {
          // Token refreshed successfully - retry the original request
          const token = localStorage.getItem('access_token')
          if (token) {
            originalRequest.headers.Authorization = `Bearer ${token}`
          }
          return apiClient(originalRequest)
        } else {
          // Refresh failed - logout and redirect to login
          await authStore.logout()
          router.push({
            name: 'login',
            query: { redirect: router.currentRoute.value.fullPath }
          })
        }
      } catch (refreshError) {
        // Refresh threw an error - logout and redirect
        const { useAuthStore } = await import('@/stores/auth')
        const authStore = useAuthStore()
        await authStore.logout()
        router.push({
          name: 'login',
          query: { redirect: router.currentRoute.value.fullPath }
        })
      } finally {
        isHandling401 = false
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
