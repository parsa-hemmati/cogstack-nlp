import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { UsersService } from '@/services/users'
import type { User, CreateUserRequest, UpdateUserRequest, SearchResult } from '@/types'

export const useUsersStore = defineStore('users', () => {
  // State
  const users = ref<User[]>([])
  const currentUser = ref<User | null>(null)
  const totalUsers = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const selectedRole = ref<string | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(10)
  const availableRoles = ref<string[]>([])
  const availablePermissions = ref<string[]>([])

  // Getters
  const filteredUsers = computed(() => {
    let filtered = [...users.value]

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        user =>
          user.username.toLowerCase().includes(query) ||
          user.email.toLowerCase().includes(query) ||
          `${user.firstName} ${user.lastName}`.toLowerCase().includes(query)
      )
    }

    if (selectedRole.value) {
      filtered = filtered.filter(user => user.roles.includes(selectedRole.value!))
    }

    return filtered
  })

  const activeUsers = computed(() => users.value.filter(user => user.isActive))

  const inactiveUsers = computed(() => users.value.filter(user => !user.isActive))

  const hasNextPage = computed(() => currentPage.value * pageSize.value < totalUsers.value)

  const hasPreviousPage = computed(() => currentPage.value > 1)

  // Actions
  async function fetchUsers(page = 1, limit = 10, search?: string, role?: string) {
    isLoading.value = true
    error.value = null

    try {
      const params = {
        skip: (page - 1) * limit,
        limit,
        search: search || searchQuery.value || undefined,
        role: role || selectedRole.value || undefined
      }

      const result: SearchResult<User> = await UsersService.list(params)
      users.value = result.items
      totalUsers.value = result.total
      currentPage.value = page
      pageSize.value = limit
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch users'
    } finally {
      isLoading.value = false
    }
  }

  async function getUser(id: string) {
    isLoading.value = true
    error.value = null

    try {
      currentUser.value = await UsersService.get(id)
      return currentUser.value
    } catch (err: any) {
      error.value = err.message || 'Failed to get user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createUser(data: CreateUserRequest) {
    isLoading.value = true
    error.value = null

    try {
      const newUser = await UsersService.create(data)
      users.value.push(newUser)
      totalUsers.value++
      return newUser
    } catch (err: any) {
      error.value = err.message || 'Failed to create user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateUser(id: string, data: UpdateUserRequest) {
    isLoading.value = true
    error.value = null

    try {
      const updatedUser = await UsersService.update(id, data)
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = updatedUser
      }
      if (currentUser.value?.id === id) {
        currentUser.value = updatedUser
      }
      return updatedUser
    } catch (err: any) {
      error.value = err.message || 'Failed to update user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteUser(id: string) {
    isLoading.value = true
    error.value = null

    try {
      await UsersService.delete(id)
      users.value = users.value.filter(u => u.id !== id)
      totalUsers.value--
      if (currentUser.value?.id === id) {
        currentUser.value = null
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete user'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function resetPassword(id: string, newPassword: string) {
    isLoading.value = true
    error.value = null

    try {
      await UsersService.resetPassword(id, newPassword)
    } catch (err: any) {
      error.value = err.message || 'Failed to reset password'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function toggleUserStatus(id: string, isActive: boolean) {
    isLoading.value = true
    error.value = null

    try {
      const updatedUser = await UsersService.toggleStatus(id, isActive)
      const index = users.value.findIndex(u => u.id === id)
      if (index !== -1) {
        users.value[index] = updatedUser
      }
      if (currentUser.value?.id === id) {
        currentUser.value = updatedUser
      }
      return updatedUser
    } catch (err: any) {
      error.value = err.message || 'Failed to toggle user status'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchRoles() {
    try {
      availableRoles.value = await UsersService.getRoles()
    } catch (err: any) {
    }
  }

  async function fetchPermissions() {
    try {
      availablePermissions.value = await UsersService.getPermissions()
    } catch (err: any) {
    }
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
    fetchUsers(1, pageSize.value)
  }

  function setSelectedRole(role: string | null) {
    selectedRole.value = role
    fetchUsers(1, pageSize.value)
  }

  function clearFilters() {
    searchQuery.value = ''
    selectedRole.value = null
    fetchUsers(1, pageSize.value)
  }

  return {
    // State
    users,
    currentUser,
    totalUsers,
    isLoading,
    error,
    searchQuery,
    selectedRole,
    currentPage,
    pageSize,
    availableRoles,
    availablePermissions,

    // Getters
    filteredUsers,
    activeUsers,
    inactiveUsers,
    hasNextPage,
    hasPreviousPage,

    // Actions
    fetchUsers,
    getUser,
    createUser,
    updateUser,
    deleteUser,
    resetPassword,
    toggleUserStatus,
    fetchRoles,
    fetchPermissions,
    setSearchQuery,
    setSelectedRole,
    clearFilters
  }
})