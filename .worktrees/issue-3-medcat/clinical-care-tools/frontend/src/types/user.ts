/**
 * User-related TypeScript types
 */

export enum UserRole {
  ADMIN = 'admin',
  CLINICIAN = 'clinician',
  RESEARCHER = 'researcher',
  AUDITOR = 'auditor',
  VIEWER = 'viewer',
}

export interface User {
  id: string
  username: string
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  is_verified: boolean
  can_break_glass: boolean
  failed_login_attempts: number
  locked_until: string | null
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  user: User
  access_token: string
  refresh_token: string
  token_type: string
}

export interface RegisterRequest {
  username: string
  email: string
  full_name: string
  password: string
  role?: UserRole
  can_break_glass?: boolean
}
