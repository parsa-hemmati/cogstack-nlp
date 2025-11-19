import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.url),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    },
    {
      path: '/users',
      name: 'user-management',
      component: () => import('../views/UserManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('../views/Profile.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../views/DocumentsView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/patients/search',
      name: 'patient-search',
      component: () => import('../views/PatientSearchView.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/timeline/:patientId',
      name: 'timeline',
      component: () => import('../views/TimelineView.vue'),
      meta: { requiresAuth: true }
    }
  ]
})

// Navigation guard for authentication
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access_token')

  if (to.meta.requiresAuth && !token) {
    // Redirect to login if route requires auth and no token
    next({ name: 'login', query: { redirect: to.fullPath } })
  } else {
    next()
  }
})

export default router
