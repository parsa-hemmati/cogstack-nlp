import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { TasksService } from '@/services/tasks'
import type {
  Task,
  CreateTaskRequest,
  UpdateTaskRequest,
  TaskComment,
  TaskStatus,
  TaskPriority,
  SearchResult
} from '@/types'

export const useTasksStore = defineStore('tasks', () => {
  // State
  const tasks = ref<Task[]>([])
  const currentTask = ref<Task | null>(null)
  const currentTaskComments = ref<TaskComment[]>([])
  const totalTasks = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const projectFilter = ref<string | null>(null)
  const statusFilter = ref<TaskStatus | null>(null)
  const priorityFilter = ref<TaskPriority | null>(null)
  const assigneeFilter = ref<string | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const showMyTasksOnly = ref(false)
  const currentUserId = ref<string | null>(null) // Set from auth store

  // Getters
  const tasksByStatus = computed(() => {
    const grouped: Record<TaskStatus, Task[]> = {
      [TaskStatus.Pending]: [],
      [TaskStatus.InProgress]: [],
      [TaskStatus.Completed]: [],
      [TaskStatus.Blocked]: [],
      [TaskStatus.Cancelled]: []
    }

    tasks.value.forEach(task => {
      grouped[task.status].push(task)
    })

    return grouped
  })

  const pendingTasks = computed(() => tasksByStatus.value[TaskStatus.Pending])
  const inProgressTasks = computed(() => tasksByStatus.value[TaskStatus.InProgress])
  const completedTasks = computed(() => tasksByStatus.value[TaskStatus.Completed])
  const blockedTasks = computed(() => tasksByStatus.value[TaskStatus.Blocked])

  const myTasks = computed(() => {
    if (!currentUserId.value) return []
    return tasks.value.filter(task => task.assigneeId === currentUserId.value)
  })

  const unassignedTasks = computed(() =>
    tasks.value.filter(task => !task.assigneeId)
  )

  const overdueTasks = computed(() => {
    const now = new Date()
    return tasks.value.filter(task => {
      if (!task.dueDate || task.status === TaskStatus.Completed) return false
      return new Date(task.dueDate) < now
    })
  })

  const urgentTasks = computed(() =>
    tasks.value.filter(task => task.priority === TaskPriority.Urgent)
  )

  const filteredTasks = computed(() => {
    let filtered = [...tasks.value]

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        task =>
          task.title.toLowerCase().includes(query) ||
          task.description?.toLowerCase().includes(query) ||
          task.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    if (projectFilter.value) {
      filtered = filtered.filter(task => task.projectId === projectFilter.value)
    }

    if (statusFilter.value) {
      filtered = filtered.filter(task => task.status === statusFilter.value)
    }

    if (priorityFilter.value) {
      filtered = filtered.filter(task => task.priority === priorityFilter.value)
    }

    if (assigneeFilter.value) {
      filtered = filtered.filter(task => task.assigneeId === assigneeFilter.value)
    }

    if (showMyTasksOnly.value && currentUserId.value) {
      filtered = filtered.filter(task => task.assigneeId === currentUserId.value)
    }

    return filtered
  })

  const hasNextPage = computed(() => currentPage.value * pageSize.value < totalTasks.value)

  const hasPreviousPage = computed(() => currentPage.value > 1)

  const taskStats = computed(() => ({
    total: totalTasks.value,
    pending: pendingTasks.value.length,
    inProgress: inProgressTasks.value.length,
    completed: completedTasks.value.length,
    blocked: blockedTasks.value.length,
    overdue: overdueTasks.value.length,
    urgent: urgentTasks.value.length
  }))

  // Actions
  async function fetchTasks(
    page = 1,
    limit = 20,
    filters?: {
      project_id?: string
      status?: string
      assignee?: string
      priority?: string
      search?: string
    }
  ) {
    isLoading.value = true
    error.value = null

    try {
      const params = {
        skip: (page - 1) * limit,
        limit,
        project_id: filters?.project_id || projectFilter.value || undefined,
        status: filters?.status || statusFilter.value || undefined,
        assignee: filters?.assignee || assigneeFilter.value || undefined,
        priority: filters?.priority || priorityFilter.value || undefined,
        search: filters?.search || searchQuery.value || undefined
      }

      const result: SearchResult<Task> = await TasksService.list(params)
      tasks.value = result.items
      totalTasks.value = result.total
      currentPage.value = page
      pageSize.value = limit
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch tasks'
    } finally {
      isLoading.value = false
    }
  }

  async function getTask(id: string) {
    isLoading.value = true
    error.value = null

    try {
      currentTask.value = await TasksService.get(id)
      await fetchTaskComments(id)
      return currentTask.value
    } catch (err: any) {
      error.value = err.message || 'Failed to get task'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createTask(data: CreateTaskRequest) {
    isLoading.value = true
    error.value = null

    try {
      const newTask = await TasksService.create(data)
      tasks.value.push(newTask)
      totalTasks.value++
      return newTask
    } catch (err: any) {
      error.value = err.message || 'Failed to create task'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateTask(id: string, data: UpdateTaskRequest) {
    isLoading.value = true
    error.value = null

    try {
      const updatedTask = await TasksService.update(id, data)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updatedTask
      }
      return updatedTask
    } catch (err: any) {
      error.value = err.message || 'Failed to update task'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteTask(id: string) {
    isLoading.value = true
    error.value = null

    try {
      await TasksService.delete(id)
      tasks.value = tasks.value.filter(t => t.id !== id)
      totalTasks.value--
      if (currentTask.value?.id === id) {
        currentTask.value = null
        currentTaskComments.value = []
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete task'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateTaskStatus(id: string, status: TaskStatus) {
    isLoading.value = true
    error.value = null

    try {
      const updatedTask = await TasksService.updateStatus(id, status)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updatedTask
      }
      return updatedTask
    } catch (err: any) {
      error.value = err.message || 'Failed to update task status'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function assignTask(id: string, userId: string) {
    isLoading.value = true
    error.value = null

    try {
      const updatedTask = await TasksService.assign(id, userId)
      const index = tasks.value.findIndex(t => t.id === id)
      if (index !== -1) {
        tasks.value[index] = updatedTask
      }
      if (currentTask.value?.id === id) {
        currentTask.value = updatedTask
      }
      return updatedTask
    } catch (err: any) {
      error.value = err.message || 'Failed to assign task'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchTaskComments(id: string) {
    try {
      currentTaskComments.value = await TasksService.getComments(id)
      return currentTaskComments.value
    } catch (err: any) {
      return []
    }
  }

  async function addTaskComment(id: string, content: string) {
    isLoading.value = true
    error.value = null

    try {
      const newComment = await TasksService.addComment(id, content)
      currentTaskComments.value.push(newComment)
      return newComment
    } catch (err: any) {
      error.value = err.message || 'Failed to add comment'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  function moveTask(taskId: string, newStatus: TaskStatus) {
    const task = tasks.value.find(t => t.id === taskId)
    if (task) {
      task.status = newStatus
      // This will be persisted via API call
      updateTaskStatus(taskId, newStatus)
    }
  }

  function setCurrentUserId(userId: string) {
    currentUserId.value = userId
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
    fetchTasks(1, pageSize.value)
  }

  function setProjectFilter(projectId: string | null) {
    projectFilter.value = projectId
    fetchTasks(1, pageSize.value)
  }

  function setStatusFilter(status: TaskStatus | null) {
    statusFilter.value = status
    fetchTasks(1, pageSize.value)
  }

  function setPriorityFilter(priority: TaskPriority | null) {
    priorityFilter.value = priority
    fetchTasks(1, pageSize.value)
  }

  function setAssigneeFilter(userId: string | null) {
    assigneeFilter.value = userId
    fetchTasks(1, pageSize.value)
  }

  function toggleMyTasksOnly() {
    showMyTasksOnly.value = !showMyTasksOnly.value
    fetchTasks(1, pageSize.value)
  }

  function clearFilters() {
    searchQuery.value = ''
    projectFilter.value = null
    statusFilter.value = null
    priorityFilter.value = null
    assigneeFilter.value = null
    showMyTasksOnly.value = false
    fetchTasks(1, pageSize.value)
  }

  return {
    // State
    tasks,
    currentTask,
    currentTaskComments,
    totalTasks,
    isLoading,
    error,
    searchQuery,
    projectFilter,
    statusFilter,
    priorityFilter,
    assigneeFilter,
    currentPage,
    pageSize,
    showMyTasksOnly,
    currentUserId,

    // Getters
    tasksByStatus,
    pendingTasks,
    inProgressTasks,
    completedTasks,
    blockedTasks,
    myTasks,
    unassignedTasks,
    overdueTasks,
    urgentTasks,
    filteredTasks,
    hasNextPage,
    hasPreviousPage,
    taskStats,

    // Actions
    fetchTasks,
    getTask,
    createTask,
    updateTask,
    deleteTask,
    updateTaskStatus,
    assignTask,
    fetchTaskComments,
    addTaskComment,
    moveTask,
    setCurrentUserId,
    setSearchQuery,
    setProjectFilter,
    setStatusFilter,
    setPriorityFilter,
    setAssigneeFilter,
    toggleMyTasksOnly,
    clearFilters
  }
})