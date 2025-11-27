/**
 * Tasks API Service
 *
 * API calls for task management endpoints.
 */

import api from './api'

export interface Task {
  id: string
  project_id: string
  title: string
  description: string | null
  assigned_to: string | null
  status: 'pending' | 'in_progress' | 'completed' | 'blocked'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  due_date: string | null
  created_by: string
  created_at: string
  updated_at: string
}

export interface TaskCreate {
  title: string
  description?: string | null
  assigned_to?: string | null
  status?: 'pending' | 'in_progress' | 'completed' | 'blocked'
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  due_date?: string | null
}

export interface TaskUpdate {
  title?: string
  description?: string | null
  assigned_to?: string | null
  status?: 'pending' | 'in_progress' | 'completed' | 'blocked'
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  due_date?: string | null
}

/**
 * Fetch all tasks for a project
 */
export async function fetchProjectTasks(projectId: string): Promise<Task[]> {
  const response = await api.get<Task[]>(`/projects/${projectId}/tasks`)
  return response.data
}

/**
 * Fetch task by ID
 */
export async function fetchTask(taskId: string): Promise<Task> {
  const response = await api.get<Task>(`/tasks/${taskId}`)
  return response.data
}

/**
 * Create new task in project
 */
export async function createTask(projectId: string, taskData: TaskCreate): Promise<Task> {
  const response = await api.post<Task>(`/projects/${projectId}/tasks`, taskData)
  return response.data
}

/**
 * Update existing task
 */
export async function updateTask(taskId: string, taskData: TaskUpdate): Promise<Task> {
  const response = await api.patch<Task>(`/tasks/${taskId}`, taskData)
  return response.data
}

/**
 * Delete task
 */
export async function deleteTask(taskId: string): Promise<void> {
  await api.delete(`/tasks/${taskId}`)
}
