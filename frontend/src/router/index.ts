/**
 * Vue Router Configuration
 *
 * Handles routing and navigation guards for authentication and authorization.
 * Integrates with Pinia auth store for state management.
 */
import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'
import type { UserRole } from '@/stores/auth'

// Route meta types
declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    requiredRoles?: UserRole[]
    requiresAdmin?: boolean
    title?: string
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { title: 'Home' }
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: 'Login' }
    },
    {
      path: '/users',
      name: 'user-management',
      component: () => import('../views/UserManagement.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin'],
        requiresAdmin: true,
        title: 'User Management'
      }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true, title: 'Profile' }
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../views/DocumentsView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician', 'researcher'],
        title: 'Documents'
      }
    },
    {
      path: '/search',
      name: 'search',
      component: () => import('../views/SearchView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician', 'researcher'],
        title: 'Search'
      }
    },
    {
      path: '/patients/search',
      name: 'patient-search',
      component: () => import('../views/PatientSearchView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician'],
        title: 'Patient Search'
      }
    },
    {
      path: '/timeline/:patientId',
      name: 'timeline',
      component: () => import('../views/TimelineView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician'],
        title: 'Patient Timeline'
      }
    },
    {
      path: '/deidentify',
      name: 'deidentify-upload',
      component: () => import('../views/DeidentifyUploadView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician', 'researcher'],
        title: 'De-identification'
      }
    },
    {
      path: '/deidentify/jobs/:jobId',
      name: 'deidentify-job-status',
      component: () => import('../views/DeidentifyJobStatusView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician', 'researcher'],
        title: 'De-identification Job Status'
      }
    },
    {
      path: '/deidentify/jobs/:jobId/review',
      name: 'deidentify-review',
      component: () => import('../views/DeidentifyReviewView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician', 'researcher'],
        title: 'De-identification Review'
      }
    },
    {
      path: '/deidentify/jobs/:jobId/results',
      name: 'deidentify-results',
      component: () => import('../views/DeidentifyResultsView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin', 'clinician', 'researcher'],
        title: 'De-identification Results'
      }
    },
    {
      path: '/admin/search-analytics',
      name: 'admin-search-analytics',
      component: () => import('../views/admin/SearchAnalyticsView.vue'),
      meta: {
        requiresAuth: true,
        requiredRoles: ['admin'],
        requiresAdmin: true,
        title: 'Search Analytics'
      }
    },
    // 404 Not Found
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/NotFoundView.vue'),
      meta: { title: 'Page Not Found' }
    },
    // Access Denied
    {
      path: '/access-denied',
      name: 'access-denied',
      component: () => import('../views/AccessDeniedView.vue'),
      meta: { title: 'Access Denied' }
    }
  ]
})

/**
 * Navigation guard for authentication and authorization
 *
 * Checks:
 * 1. Session expiration (BEFORE updating activity timestamp)
 * 2. If route requires authentication and user is not authenticated
 * 3. If route requires specific roles and user doesn't have them
 * 4. Token expiration and automatic refresh
 */
router.beforeEach(async (to: RouteLocationNormalized, from, next) => {
  // Import auth store dynamically to avoid circular dependency
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()

  // Update page title
  document.title = to.meta.title
    ? `${to.meta.title} | CogStack NLP`
    : 'CogStack NLP Clinical Care Tools'

  // Check if route requires authentication
  if (to.meta.requiresAuth) {
    // CRITICAL: Check session expiration BEFORE updating activity timestamp
    // This prevents the race condition where updateActivity() resets the timer
    // before we can detect an expired session
    if (authStore.isSessionExpired) {
      await authStore.logout()
      return next({
        name: 'login',
        query: { redirect: to.fullPath, reason: 'session_expired' }
      })
    }

    // Check if user is authenticated
    if (!authStore.isAuthenticated) {
      // Try to refresh token if available
      const refreshed = await authStore.refresh()

      if (!refreshed) {
        // Not authenticated - redirect to login
        return next({
          name: 'login',
          query: { redirect: to.fullPath }
        })
      }
    }

    // Check role-based access
    const requiredRoles = to.meta.requiredRoles as UserRole[] | undefined
    if (requiredRoles && requiredRoles.length > 0) {
      if (!authStore.canAccess(requiredRoles)) {
        // User doesn't have required role - redirect to access denied
        return next({ name: 'access-denied' })
      }
    }

    // Check admin access (backwards compatibility)
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      return next({ name: 'access-denied' })
    }

    // Update activity timestamp AFTER all auth checks pass
    // This ensures we only reset the timer for valid authenticated requests
    authStore.updateActivity()
  }

  // Redirect authenticated users away from login page
  if (to.name === 'login' && authStore.isAuthenticated) {
    return next({ name: 'home' })
  }

  next()
})

/**
 * After each navigation, log the route for audit purposes
 */
router.afterEach((to) => {
  // Could log navigation for audit purposes
  console.debug('[Router] Navigated to:', to.name, to.fullPath)
})

export default router
