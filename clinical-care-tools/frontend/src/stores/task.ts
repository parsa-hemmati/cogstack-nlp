/**
 * Task Management Store
 *
 * Manages task CRUD operations within projects.
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Task, TaskCreate, TaskUpdate } from '../services/tasks'
import * as tasksService from '../services/tasks'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const currentProjectId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  // Filters
  const statusFilter = ref<string | null>(null)
  const priorityFilter = ref<string | null>(null)
  const assignedToFilter = ref<string | null>(null)

  /**
   * Filtered tasks based on current filters
   */
  const filteredTasks = computed(() => {
    let filtered = tasks.value

    if (statusFilter.value) {
      filtered = filtered.filter((t) => t.status === statusFilter.value)
    }

    if (priorityFilter.value) {
      filtered = filtered.filter((t) => t.priority === priorityFilter.value)
    }

    if (assignedToFilter.value) {
      filtered = filtered.filter((t) => t.assigned_to === assignedToFilter.value)
    }

    return filtered
  })

  /**
   * Fetch all tasks for a project
   */
  async function fetchTasks(projectId: string) {
    loading.value = true
    error.value = null
    currentProjectId.value = projectId

    try {
      tasks.value = await tasksService.fetchProjectTasks(projectId)
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch tasks'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single task by ID
   */
  async function fetchTask(taskId: string) {
    loading.value = true
    error.value = null

    try {
      currentTask.value = await tasksService.fetchTask(taskId)
      return currentTask.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch task'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create new task
   */
  async function createTask(projectId: string, taskData: TaskCreate): Promise<Task> {
    loading.value = true
    error.value = null

    try {
      const newTask = await tasksService.createTask(projectId, taskData)
      tasks.value.unshift(newTask) // Add to beginning
      return newTask
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to create task'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update existing task
   */
  async function updateTask(taskId: string, taskData: TaskUpdate): Promise<Task> {
    loading.value = true
    error.value = null

    try {
      const updatedTask = await tasksService.updateTask(taskId, taskData)

      // Update in local state
      const index = tasks.value.findIndex((t) => t.id === taskId)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }

      // Update current task if it's the one being edited
      if (currentTask.value?.id === taskId) {
        currentTask.value = updatedTask
      }

      return updatedTask
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to update task'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete task
   */
  async function deleteTask(taskId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await tasksService.deleteTask(taskId)

      // Remove from local state
      tasks.value = tasks.value.filter((t) => t.id !== taskId)

      // Clear current task if it was deleted
      if (currentTask.value?.id === taskId) {
        currentTask.value = null
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to delete task'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Set status filter
   */
  function setStatusFilter(status: string | null) {
    statusFilter.value = status
  }

  /**
   * Set priority filter
   */
  function setPriorityFilter(priority: string | null) {
    priorityFilter.value = priority
  }

  /**
   * Set assigned to filter
   */
  function setAssignedToFilter(userId: string | null) {
    assignedToFilter.value = userId
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    statusFilter.value = null
    priorityFilter.value = null
    assignedToFilter.value = null
  }

  /**
   * Clear error message
   */
  function clearError() {
    error.value = null
  }

  /**
   * Clear current task
   */
  function clearCurrentTask() {
    currentTask.value = null
  }

  /**
   * Clear all tasks
   */
  function clearTasks() {
    tasks.value = []
    currentProjectId.value = null
  }

  return {
    tasks,
    filteredTasks,
    currentTask,
    currentProjectId,
    loading,
    error,
    statusFilter,
    priorityFilter,
    assignedToFilter,
    fetchTasks,
    fetchTask,
    createTask,
    updateTask,
    deleteTask,
    setStatusFilter,
    setPriorityFilter,
    setAssignedToFilter,
    clearFilters,
    clearError,
    clearCurrentTask,
    clearTasks,
  }
})
