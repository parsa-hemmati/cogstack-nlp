import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * Authentication composable for managing auth state and operations
 *
 * @example
 * ```typescript
 * const { isAuthenticated, user, login, logout } = useAuth()
 *
 * await login({ username: 'john', password: 'secret' })
 * ```
 */
export function useAuth() {
  const authStore = useAuthStore()
  const router = useRouter()
  const isLoggingOut = ref(false)

  // Computed properties
  const isAuthenticated = computed(() => authStore.isAuthenticated)
  const user = computed(() => authStore.user)
  const displayName = computed(() => authStore.displayName)
  const permissions = computed(() => authStore.permissions)
  const roles = computed(() => authStore.roles)
  const isLoading = computed(() => authStore.isLoading)

  // Methods
  async function login(credentials: { username: string; password: string }) {
    try {
      await authStore.login(credentials)
      return true
    } catch (error) {
      return false
    }
  }

  async function logout(redirect = true) {
    isLoggingOut.value = true
    try {
      await authStore.logout()
      if (redirect) {
        await router.push('/login')
      }
    } finally {
      isLoggingOut.value = false
    }
  }

  async function refreshToken() {
    try {
      await authStore.refreshToken()
      return true
    } catch (error) {
      return false
    }
  }

  function hasPermission(permission: string): boolean {
    return authStore.hasPermission(permission)
  }

  function hasRole(role: string): boolean {
    return authStore.hasRole(role)
  }

  function hasAnyPermission(permissions: string[]): boolean {
    return authStore.hasAnyPermission(permissions)
  }

  function hasAllPermissions(permissions: string[]): boolean {
    return authStore.hasAllPermissions(permissions)
  }

  /**
   * Check if user can access a route based on permissions
   */
  function canAccessRoute(routeName: string): boolean {
    // Define route permission mappings
    const routePermissions: Record<string, string[]> = {
      'patients': ['view_patients'],
      'patient-detail': ['view_patients'],
      'search': ['search_patients'],
      'documents': ['view_documents'],
      'reports': ['view_reports'],
      'admin-users': ['admin'],
      'admin-models': ['admin']
    }

    const requiredPermissions = routePermissions[routeName]
    if (!requiredPermissions) {
      return true // No permissions required
    }

    return hasAllPermissions(requiredPermissions)
  }

  /**
   * Get user's primary role
   */
  function getPrimaryRole(): string | null {
    const roleHierarchy = ['admin', 'clinician', 'researcher', 'viewer']
    for (const role of roleHierarchy) {
      if (hasRole(role)) {
        return role
      }
    }
    return null
  }

  return {
    // State
    isAuthenticated,
    user,
    displayName,
    permissions,
    roles,
    isLoading,
    isLoggingOut,

    // Methods
    login,
    logout,
    refreshToken,
    hasPermission,
    hasRole,
    hasAnyPermission,
    hasAllPermissions,
    canAccessRoute,
    getPrimaryRole
  }
}