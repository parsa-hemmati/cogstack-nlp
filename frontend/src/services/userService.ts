/**
 * User Management API Service
 * Handles all user-related API calls
 */
import apiClient from './api'

export interface User {
  id: string
  username: string
  email: string
  role: 'clinician' | 'researcher' | 'admin'
  is_active: boolean
  can_break_glass: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  email: string
  password: string
  role: 'clinician' | 'researcher' | 'admin'
  is_active?: boolean
  can_break_glass?: boolean
}

export interface UserUpdate {
  email?: string
  role?: string
  is_active?: boolean
  can_break_glass?: boolean
}

export interface UserListResponse {
  items: User[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface Session {
  session_id: string
  user_id: string
  created_at: string
  expires_at: string
  ip_address: string | null
  user_agent: string | null
  is_current: boolean
}

export interface SessionListResponse {
  sessions: Session[]
  total: number
}

export interface AuditLogEntry {
  id: string
  user_id: string
  username: string
  action: string
  resource_type: string
  resource_id: string | null
  details: Record<string, any> | null
  timestamp: string
  ip_address: string | null
  user_agent: string | null
  success: string
  error_message: string | null
}

export interface AuditLogListResponse {
  items: AuditLogEntry[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * User Management Service
 */
export const userService = {
  /**
   * List users with pagination
   */
  async listUsers(page = 1, pageSize = 20, role?: string, isActive?: boolean): Promise<UserListResponse> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (role) params.role = role
    if (isActive !== undefined) params.is_active = isActive

    const response = await apiClient.get('/api/v1/users', { params })
    return response.data
  },

  /**
   * Search users by username or email
   */
  async searchUsers(query: string, page = 1, pageSize = 20): Promise<UserListResponse> {
    const response = await apiClient.get('/api/v1/users/search', {
      params: { query, page, page_size: pageSize },
    })
    return response.data
  },

  /**
   * Get user by ID
   */
  async getUser(userId: string): Promise<User> {
    const response = await apiClient.get(`/api/v1/users/${userId}`)
    return response.data
  },

  /**
   * Create new user (admin only)
   */
  async createUser(userData: UserCreate): Promise<User> {
    const response = await apiClient.post('/api/v1/users', userData)
    return response.data
  },

  /**
   * Update user (admin only)
   */
  async updateUser(userId: string, userData: UserUpdate): Promise<User> {
    const response = await apiClient.put(`/api/v1/users/${userId}`, userData)
    return response.data
  },

  /**
   * Delete user (soft delete, admin only)
   */
  async deleteUser(userId: string): Promise<void> {
    await apiClient.delete(`/api/v1/users/${userId}`)
  },

  /**
   * Get current user's profile
   */
  async getMyProfile(): Promise<User> {
    const response = await apiClient.get('/api/v1/users/me')
    return response.data
  },

  /**
   * Update current user's profile
   */
  async updateMyProfile(email: string): Promise<User> {
    const response = await apiClient.put('/api/v1/users/me', { email })
    return response.data
  },

  /**
   * Change current user's password
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/api/v1/users/me/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },

  /**
   * Get user's active sessions
   */
  async getMySessions(): Promise<SessionListResponse> {
    const response = await apiClient.get('/api/v1/sessions/me')
    return response.data
  },

  /**
   * Revoke a specific session
   */
  async revokeSession(sessionId: string): Promise<void> {
    await apiClient.delete(`/api/v1/sessions/${sessionId}`)
  },

  /**
   * Revoke all sessions except current
   */
  async revokeAllSessions(): Promise<void> {
    await apiClient.delete('/api/v1/sessions/me/all')
  },

  /**
   * Get user's activity logs
   */
  async getUserActivity(
    userId: string,
    page = 1,
    pageSize = 20,
    action?: string
  ): Promise<AuditLogListResponse> {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (action) params.action = action

    const response = await apiClient.get(`/api/v1/users/${userId}/activity`, { params })
    return response.data
  },
}

export default userService
