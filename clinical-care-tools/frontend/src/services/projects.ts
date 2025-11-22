import { ApiService } from './api'
import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectMember,
  Task,
  SearchResult
} from '@/types'

export class ProjectsService {
  /**
   * Get paginated list of projects
   */
  static async list(params?: {
    skip?: number
    limit?: number
    status?: string
    search?: string
  }): Promise<SearchResult<Project>> {
    const response = await ApiService.projects.list(params)
    return response.data
  }

  /**
   * Get a single project by ID
   */
  static async get(id: string): Promise<Project> {
    const response = await ApiService.projects.get(id)
    return response.data
  }

  /**
   * Create a new project
   */
  static async create(data: CreateProjectRequest): Promise<Project> {
    const response = await ApiService.projects.create(data)
    return response.data
  }

  /**
   * Update an existing project
   */
  static async update(id: string, data: UpdateProjectRequest): Promise<Project> {
    const response = await ApiService.projects.update(id, data)
    return response.data
  }

  /**
   * Delete a project
   */
  static async delete(id: string): Promise<void> {
    await ApiService.projects.delete(id)
  }

  /**
   * Get project members
   */
  static async getMembers(id: string): Promise<ProjectMember[]> {
    const response = await ApiService.projects.getMembers(id)
    return response.data
  }

  /**
   * Add a member to a project
   */
  static async addMember(id: string, userId: string, role: string): Promise<ProjectMember> {
    const response = await ApiService.projects.addMember(id, userId, role)
    return response.data
  }

  /**
   * Update a project member's role
   */
  static async updateMember(id: string, userId: string, role: string): Promise<ProjectMember> {
    const response = await ApiService.projects.updateMember(id, userId, role)
    return response.data
  }

  /**
   * Remove a member from a project
   */
  static async removeMember(id: string, userId: string): Promise<void> {
    await ApiService.projects.removeMember(id, userId)
  }

  /**
   * Get project tasks
   */
  static async getTasks(id: string, params?: {
    status?: string
    assignee?: string
  }): Promise<Task[]> {
    const response = await ApiService.projects.getTasks(id, params)
    return response.data
  }

  /**
   * Get project statistics
   */
  static async getStats(id: string): Promise<{
    totalTasks: number
    completedTasks: number
    activeTasks: number
    blockedTasks: number
    totalMembers: number
    completionRate: number
  }> {
    const response = await ApiService.projects.getStats(id)
    return response.data
  }
}