/**
 * Authentication API endpoints
 */

import type { LoginRequest, LoginResponse, RegisterRequest, User } from '@/types/user'
import apiClient from './client'

export const authApi = {
  /**
   * Login user
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await apiClient.post<LoginResponse>('/v1/auth/login', credentials)
    return response.data
  },

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<User> {
    const response = await apiClient.post<User>('/v1/auth/register', userData)
    return response.data
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    await apiClient.post('/v1/auth/logout')
  },

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/v1/auth/me')
    return response.data
  },
}
