/**
 * Project Management Store
 *
 * Manages project CRUD operations and member management.
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Project, ProjectCreate, ProjectUpdate, ProjectMemberAdd } from '../services/projects'
import * as projectsService from '../services/projects'

export const useProjectStore = defineStore('project', () => {
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  /**
   * Fetch all projects for current user
   */
  async function fetchProjects() {
    loading.value = true
    error.value = null

    try {
      projects.value = await projectsService.fetchProjects()
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch projects'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch single project by ID
   */
  async function fetchProject(projectId: string) {
    loading.value = true
    error.value = null

    try {
      currentProject.value = await projectsService.fetchProject(projectId)
      return currentProject.value
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to fetch project'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Create new project
   */
  async function createProject(projectData: ProjectCreate): Promise<Project> {
    loading.value = true
    error.value = null

    try {
      const newProject = await projectsService.createProject(projectData)
      projects.value.unshift(newProject) // Add to beginning
      return newProject
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to create project'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Update existing project
   */
  async function updateProject(projectId: string, projectData: ProjectUpdate): Promise<Project> {
    loading.value = true
    error.value = null

    try {
      const updatedProject = await projectsService.updateProject(projectId, projectData)

      // Update in local state
      const index = projects.value.findIndex((p) => p.id === projectId)
      if (index !== -1) {
        projects.value[index] = updatedProject
      }

      // Update current project if it's the one being edited
      if (currentProject.value?.id === projectId) {
        currentProject.value = updatedProject
      }

      return updatedProject
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to update project'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Add member to project
   */
  async function addMember(projectId: string, memberData: ProjectMemberAdd) {
    loading.value = true
    error.value = null

    try {
      const newMember = await projectsService.addProjectMember(projectId, memberData)

      // Update project in local state
      const project = projects.value.find((p) => p.id === projectId)
      if (project) {
        project.members.push(newMember)
      }

      // Update current project if applicable
      if (currentProject.value?.id === projectId) {
        currentProject.value.members.push(newMember)
      }

      return newMember
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to add member'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Remove member from project
   */
  async function removeMember(projectId: string, userId: string): Promise<void> {
    loading.value = true
    error.value = null

    try {
      await projectsService.removeProjectMember(projectId, userId)

      // Update project in local state
      const project = projects.value.find((p) => p.id === projectId)
      if (project) {
        project.members = project.members.filter((m) => m.user_id !== userId)
      }

      // Update current project if applicable
      if (currentProject.value?.id === projectId) {
        currentProject.value.members = currentProject.value.members.filter(
          (m) => m.user_id !== userId
        )
      }
    } catch (err: any) {
      error.value = err.response?.data?.detail || err.message || 'Failed to remove member'
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Clear error message
   */
  function clearError() {
    error.value = null
  }

  /**
   * Clear current project
   */
  function clearCurrentProject() {
    currentProject.value = null
  }

  return {
    projects,
    currentProject,
    loading,
    error,
    fetchProjects,
    fetchProject,
    createProject,
    updateProject,
    addMember,
    removeMember,
    clearError,
    clearCurrentProject,
  }
})
