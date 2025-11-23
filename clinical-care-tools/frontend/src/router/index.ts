/**
 * Vue Router Configuration
 *
 * Defines application routes and navigation.
 */

import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/patients',
    name: 'patients',
    component: () => import('@/views/PatientSearchView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/timeline',
    name: 'timeline',
    component: () => import('@/views/TimelineView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('@/views/UserManagement.vue'),
    meta: { requiresAuth: true, requiresAdmin: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guard for authentication
router.beforeEach((to, _from, next) => {
  const isAuthenticated = false // TODO: Implement authentication check

  if (to.meta.requiresAuth && !isAuthenticated) {
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
