import { ApiService } from './api'
import type {
  Task,
  CreateTaskRequest,
  UpdateTaskRequest,
  TaskComment,
  TaskAttachment,
  TaskStatus,
  SearchResult
} from '@/types'

export class TasksService {
  /**
   * Get paginated list of tasks
   */
  static async list(params?: {
    skip?: number
    limit?: number
    project_id?: string
    status?: string
    assignee?: string
    priority?: string
    search?: string
  }): Promise<SearchResult<Task>> {
    const response = await ApiService.tasks.list(params)
    return response.data
  }

  /**
   * Get a single task by ID
   */
  static async get(id: string): Promise<Task> {
    const response = await ApiService.tasks.get(id)
    return response.data
  }

  /**
   * Create a new task
   */
  static async create(data: CreateTaskRequest): Promise<Task> {
    const response = await ApiService.tasks.create(data)
    return response.data
  }

  /**
   * Update an existing task
   */
  static async update(id: string, data: UpdateTaskRequest): Promise<Task> {
    const response = await ApiService.tasks.update(id, data)
    return response.data
  }

  /**
   * Delete a task
   */
  static async delete(id: string): Promise<void> {
    await ApiService.tasks.delete(id)
  }

  /**
   * Update task status
   */
  static async updateStatus(id: string, status: TaskStatus): Promise<Task> {
    const response = await ApiService.tasks.updateStatus(id, status)
    return response.data
  }

  /**
   * Assign task to a user
   */
  static async assign(id: string, userId: string): Promise<Task> {
    const response = await ApiService.tasks.assign(id, userId)
    return response.data
  }

  /**
   * Add a comment to a task
   */
  static async addComment(id: string, content: string): Promise<TaskComment> {
    const response = await ApiService.tasks.addComment(id, content)
    return response.data
  }

  /**
   * Get task comments
   */
  static async getComments(id: string): Promise<TaskComment[]> {
    const response = await ApiService.tasks.getComments(id)
    return response.data
  }

  /**
   * Add an attachment to a task
   */
  static async addAttachment(id: string, file: File): Promise<TaskAttachment> {
    const response = await ApiService.tasks.addAttachment(id, file)
    return response.data
  }

  /**
   * Get task attachments
   */
  static async getAttachments(id: string): Promise<TaskAttachment[]> {
    const response = await ApiService.tasks.getAttachments(id)
    return response.data
  }
}