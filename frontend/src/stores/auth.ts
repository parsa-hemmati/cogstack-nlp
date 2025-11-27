/**
 * Authentication Store
 *
 * Manages authentication state, token storage, and role-based access control.
 * Uses Pinia for state management with secure token handling.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/services/api'

// Valid roles in the system
export type UserRole = 'admin' | 'clinician' | 'researcher' | 'viewer'

// User interface
export interface AuthUser {
  id: string
  username: string
  email: string
  role: UserRole
  is_active: boolean
  can_break_glass: boolean
}

// Login credentials
export interface LoginCredentials {
  username: string
  password: string
}

// Token payload (decoded from JWT)
interface TokenPayload {
  user_id: string
  role: string
  exp: number
  iat: number
}

/**
 * Decode JWT token payload (without verification - verification happens server-side)
 */
function decodeToken(token: string): TokenPayload | null {
  try {
    const base64Url = token.split('.')[1]
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    )
    return JSON.parse(jsonPayload)
  } catch {
    return null
  }
}

/**
 * Check if token is expired (with 60-second buffer)
 */
function isTokenExpired(token: string): boolean {
  const payload = decodeToken(token)
  if (!payload || !payload.exp) return true

  // Add 60-second buffer to handle clock skew
  const expirationTime = payload.exp * 1000
  return Date.now() > expirationTime - 60000
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))
  const user = ref<AuthUser | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const lastActivity = ref<number>(Date.now())

  // Session timeout (30 minutes of inactivity)
  const SESSION_TIMEOUT = 30 * 60 * 1000

  // Computed
  const isAuthenticated = computed(() => {
    if (!token.value) return false
    return !isTokenExpired(token.value)
  })

  const userRole = computed((): UserRole | null => {
    if (!user.value) {
      // Try to get from token
      if (token.value) {
        const payload = decodeToken(token.value)
        return payload?.role as UserRole || null
      }
      // Fallback to localStorage
      const storedRole = localStorage.getItem('user_role')
      return storedRole as UserRole || null
    }
    return user.value.role
  })

  const isAdmin = computed(() => userRole.value === 'admin')
  const isClinician = computed(() => userRole.value === 'clinician')
  const isResearcher = computed(() => userRole.value === 'researcher')

  const canBreakGlass = computed(() => user.value?.can_break_glass || false)

  const isSessionExpired = computed(() => {
    return Date.now() - lastActivity.value > SESSION_TIMEOUT
  })

  // Actions
  /**
   * Login with username and password
   */
  async function login(credentials: LoginCredentials): Promise<boolean> {
    loading.value = true
    error.value = null

    try {
      const response = await apiClient.post('/api/v1/auth/login', credentials)
      const { access_token, refresh_token, user: userData } = response.data

      // Store tokens
      setTokens(access_token, refresh_token)

      // Store user data
      if (userData) {
        user.value = userData
        localStorage.setItem('user_role', userData.role)
      }

      // Update activity timestamp
      updateActivity()

      return true
    } catch (err: any) {
      error.value = err.response?.data?.detail || 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  /**
   * Logout and clear all auth data
   */
  async function logout(): Promise<void> {
    try {
      // Call logout endpoint to invalidate server session
      if (token.value) {
        await apiClient.post('/api/v1/auth/logout')
      }
    } catch {
      // Ignore errors during logout
    } finally {
      clearAuth()
    }
  }

  /**
   * Refresh the access token
   */
  async function refresh(): Promise<boolean> {
    if (!refreshToken.value) return false

    try {
      const response = await apiClient.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken.value
      })

      const { access_token, refresh_token: newRefreshToken } = response.data
      setTokens(access_token, newRefreshToken || refreshToken.value)

      return true
    } catch {
      // Refresh failed - clear auth and redirect to login
      clearAuth()
      return false
    }
  }

  /**
   * Fetch current user profile
   */
  async function fetchUser(): Promise<void> {
    if (!token.value) return

    try {
      const response = await apiClient.get('/api/v1/users/me')
      user.value = response.data
      localStorage.setItem('user_role', response.data.role)
    } catch (err: any) {
      if (err.response?.status === 401) {
        clearAuth()
      }
    }
  }

  /**
   * Check if user has required role(s)
   */
  function hasRole(...roles: UserRole[]): boolean {
    if (!userRole.value) return false
    return roles.includes(userRole.value)
  }

  /**
   * Check if user can access protected resource
   */
  function canAccess(requiredRoles?: UserRole[]): boolean {
    if (!isAuthenticated.value) return false
    if (!requiredRoles || requiredRoles.length === 0) return true
    return hasRole(...requiredRoles)
  }

  /**
   * Update last activity timestamp
   */
  function updateActivity(): void {
    lastActivity.value = Date.now()
  }

  /**
   * Initialize auth state from storage
   */
  async function initialize(): Promise<void> {
    const storedToken = localStorage.getItem('access_token')

    if (storedToken && !isTokenExpired(storedToken)) {
      token.value = storedToken
      refreshToken.value = localStorage.getItem('refresh_token')
      await fetchUser()
    } else if (refreshToken.value) {
      // Try to refresh expired token
      await refresh()
    } else {
      clearAuth()
    }
  }

  // Private helpers
  function setTokens(accessToken: string, newRefreshToken?: string): void {
    token.value = accessToken
    localStorage.setItem('access_token', accessToken)

    if (newRefreshToken) {
      refreshToken.value = newRefreshToken
      localStorage.setItem('refresh_token', newRefreshToken)
    }
  }

  function clearAuth(): void {
    token.value = null
    refreshToken.value = null
    user.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user_role')
  }

  return {
    // State
    token,
    user,
    loading,
    error,

    // Computed
    isAuthenticated,
    userRole,
    isAdmin,
    isClinician,
    isResearcher,
    canBreakGlass,
    isSessionExpired,

    // Actions
    login,
    logout,
    refresh,
    fetchUser,
    hasRole,
    canAccess,
    updateActivity,
    initialize
  }
})
