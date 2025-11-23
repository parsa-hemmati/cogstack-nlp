/**
 * Users API Service
 *
 * API calls for user management endpoints.
 */

import api from './api'

export interface User {
  id: string
  username: string
  full_name: string
  role: 'admin' | 'clinician' | 'researcher' | 'viewer'
  is_active: boolean
  must_change_password: boolean
  created_at: string
  updated_at: string
}

export interface UserCreate {
  username: string
  full_name: string
  password: string
  role: 'admin' | 'clinician' | 'researcher' | 'viewer'
}

export interface UserUpdate {
  full_name?: string
  role?: 'admin' | 'clinician' | 'researcher' | 'viewer'
  is_active?: boolean
}

/**
 * Fetch all users
 */
export async function fetchUsers(): Promise<User[]> {
  const response = await api.get<User[]>('/users')
  return response.data
}

/**
 * Fetch user by ID
 */
export async function fetchUser(userId: string): Promise<User> {
  const response = await api.get<User>(`/users/${userId}`)
  return response.data
}

/**
 * Create new user
 */
export async function createUser(userData: UserCreate): Promise<User> {
  const response = await api.post<User>('/users', userData)
  return response.data
}

/**
 * Update existing user
 */
export async function updateUser(userId: string, userData: UserUpdate): Promise<User> {
  const response = await api.patch<User>(`/users/${userId}`, userData)
  return response.data
}

/**
 * Delete user
 */
export async function deleteUser(userId: string): Promise<void> {
  await api.delete(`/users/${userId}`)
}
