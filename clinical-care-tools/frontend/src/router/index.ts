import { createRouter, createWebHistory, type RouteRecordRaw, type NavigationGuardNext, type RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Route definitions
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      requiresAuth: false,
      title: 'Login'
    }
  },
  {
    path: '/',
    redirect: '/dashboard',
    meta: { requiresAuth: true }
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/views/DashboardView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Dashboard'
    }
  },
  {
    path: '/patients',
    name: 'patients',
    component: () => import('@/views/PatientsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Patients',
      permissions: ['view_patients']
    }
  },
  {
    path: '/patients/:id',
    name: 'patient-detail',
    component: () => import('@/views/PatientDetailView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Patient Details',
      permissions: ['view_patients']
    }
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/SearchView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Search',
      permissions: ['search_patients']
    }
  },
  {
    path: '/reports',
    name: 'reports',
    component: () => import('@/views/ReportsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Reports',
      permissions: ['view_reports']
    }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: {
      requiresAuth: true,
      title: 'Settings'
    }
  },
  {
    path: '/403',
    name: 'forbidden',
    component: () => import('@/views/errors/ForbiddenView.vue'),
    meta: {
      title: 'Access Denied'
    }
  },
  {
    path: '/404',
    name: 'not-found',
    component: () => import('@/views/errors/NotFoundView.vue'),
    meta: {
      title: 'Page Not Found'
    }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

// Create router instance
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else if (to.hash) {
      return { el: to.hash, behavior: 'smooth' }
    } else {
      return { top: 0, behavior: 'smooth' }
    }
  }
})

// Navigation guards
router.beforeEach(async (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  next: NavigationGuardNext
) => {
  const authStore = useAuthStore()

  // Set page title
  const title = to.meta.title as string
  document.title = title ? `${title} - Clinical Care Tools` : 'Clinical Care Tools'

  // Check if route requires authentication
  const requiresAuth = to.meta.requiresAuth as boolean

  if (requiresAuth) {
    if (!authStore.isAuthenticated) {
      // Redirect to login with return URL
      next({
        name: 'login',
        query: { redirect: to.fullPath }
      })
      return
    }

    // Check permissions if specified
    const requiredPermissions = to.meta.permissions as string[] | undefined
    if (requiredPermissions && requiredPermissions.length > 0) {
      const hasPermission = requiredPermissions.every(
        permission => authStore.hasPermission(permission)
      )

      if (!hasPermission) {
        next({ name: 'forbidden' })
        return
      }
    }

    // Validate token if needed
    try {
      if (authStore.shouldRefreshToken()) {
        await authStore.refreshToken()
      }
    } catch (error) {
      await authStore.logout()
      next({
        name: 'login',
        query: { redirect: to.fullPath }
      })
      return
    }
  } else if (to.name === 'login' && authStore.isAuthenticated) {
    // Redirect to dashboard if already authenticated
    next({ name: 'dashboard' })
    return
  }

  next()
})

// Global error handler for navigation failures
router.onError((error) => {
})

export default router