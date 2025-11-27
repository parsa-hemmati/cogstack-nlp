/**
 * User Management Store
 *
 * Manages user CRUD operations for admin user management.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User, UserCreate, UserUpdate } from '../services/users'
import * as usersService from '../services/users'

export const useUserStore = defineStore('user', () => {
  const users = ref<User[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch all users from API
   */
  async function fetchUsers() {
    loading.value = true
    error.value = null

    try {
      users.value = await usersService.fetchUsers()
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch users'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create new user
   */
  async function createUser(userData: UserCreate): Promise<User> {
    loading.value = true
    error.value = null

    try {
      const newUser = await usersService.createUser(userData)
      users.value.push(newUser)
      return newUser
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to create user'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update existing user
   */
  async function updateUser(userId: string, userData: UserUpdate): Promise<User> {
    loading.value = true
    error.value = null

    try {
      const updatedUser = await usersService.updateUser(userId, userData)

      // Update in local state
      const index = users.value.findIndex((u) => u.id === userId)
      if (index !== -1) {
        users.value[index] = updatedUser
      }

      return updatedUser
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to update user'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete user
   */
  async function deleteUser(userId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await usersService.deleteUser(userId)

      // Remove from local state
      users.value = users.value.filter((u) => u.id !== userId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to delete user'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error message
   */
  function clearError() {
    error.value = null
  }

  return {
    users,
    loading,
    error,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    clearError,
  }
})
