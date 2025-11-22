import { ApiService } from './api'
import type { User, CreateUserRequest, UpdateUserRequest, SearchResult } from '@/types'

export class UsersService {
  /**
   * Get paginated list of users
   */
  static async list(params?: {
    skip?: number
    limit?: number
    search?: string
    role?: string
  }): Promise<SearchResult<User>> {
    const response = await ApiService.users.list(params)
    return response.data
  }

  /**
   * Get a single user by ID
   */
  static async get(id: string): Promise<User> {
    const response = await ApiService.users.get(id)
    return response.data
  }

  /**
   * Create a new user
   */
  static async create(data: CreateUserRequest): Promise<User> {
    const response = await ApiService.users.create(data)
    return response.data
  }

  /**
   * Update an existing user
   */
  static async update(id: string, data: UpdateUserRequest): Promise<User> {
    const response = await ApiService.users.update(id, data)
    return response.data
  }

  /**
   * Delete a user
   */
  static async delete(id: string): Promise<void> {
    await ApiService.users.delete(id)
  }

  /**
   * Reset a user's password
   */
  static async resetPassword(id: string, newPassword: string): Promise<void> {
    await ApiService.users.resetPassword(id, newPassword)
  }

  /**
   * Toggle user active status
   */
  static async toggleStatus(id: string, isActive: boolean): Promise<User> {
    const response = await ApiService.users.toggleStatus(id, isActive)
    return response.data
  }

  /**
   * Get available roles
   */
  static async getRoles(): Promise<string[]> {
    const response = await ApiService.users.getRoles()
    return response.data
  }

  /**
   * Get available permissions
   */
  static async getPermissions(): Promise<string[]> {
    const response = await ApiService.users.getPermissions()
    return response.data
  }
}