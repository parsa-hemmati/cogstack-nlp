/**
 * Projects API Service
 *
 * API calls for project management endpoints.
 */

import api from './api'

export interface ProjectMember {
  id: string
  project_id: string
  user_id: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
  added_by: string
  added_at: string
}

export interface Project {
  id: string
  name: string
  description: string | null
  created_by: string
  created_at: string
  updated_at: string
  members: ProjectMember[]
}

export interface ProjectCreate {
  name: string
  description?: string | null
}

export interface ProjectUpdate {
  name?: string
  description?: string | null
}

export interface ProjectMemberAdd {
  user_id: string
  role: 'owner' | 'admin' | 'member' | 'viewer'
}

/**
 * Fetch all projects for current user
 */
export async function fetchProjects(): Promise<Project[]> {
  const response = await api.get<Project[]>('/projects')
  return response.data
}

/**
 * Fetch project by ID
 */
export async function fetchProject(projectId: string): Promise<Project> {
  const response = await api.get<Project>(`/projects/${projectId}`)
  return response.data
}

/**
 * Create new project
 */
export async function createProject(projectData: ProjectCreate): Promise<Project> {
  const response = await api.post<Project>('/projects', projectData)
  return response.data
}

/**
 * Update existing project
 */
export async function updateProject(projectId: string, projectData: ProjectUpdate): Promise<Project> {
  const response = await api.patch<Project>(`/projects/${projectId}`, projectData)
  return response.data
}

/**
 * Add member to project
 */
export async function addProjectMember(
  projectId: string,
  memberData: ProjectMemberAdd
): Promise<ProjectMember> {
  const response = await api.post<ProjectMember>(`/projects/${projectId}/members`, memberData)
  return response.data
}

/**
 * Remove member from project
 */
export async function removeProjectMember(projectId: string, userId: string): Promise<void> {
  await api.delete(`/projects/${projectId}/members/${userId}`)
}
