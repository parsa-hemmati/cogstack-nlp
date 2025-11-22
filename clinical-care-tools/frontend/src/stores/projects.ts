import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ProjectsService } from '@/services/projects'
import type {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
  ProjectMember,
  SearchResult
} from '@/types'

export const useProjectsStore = defineStore('projects', () => {
  // State
  const projects = ref<Project[]>([])
  const currentProject = ref<Project | null>(null)
  const currentProjectMembers = ref<ProjectMember[]>([])
  const totalProjects = ref(0)
  const isLoading = ref(false)
  const error = ref<string | null>(null)
  const searchQuery = ref('')
  const statusFilter = ref<string | null>(null)
  const currentPage = ref(1)
  const pageSize = ref(12) // For card grid display

  // Getters
  const activeProjects = computed(() =>
    projects.value.filter(p => p.status === 'active')
  )

  const archivedProjects = computed(() =>
    projects.value.filter(p => p.status === 'archived')
  )

  const draftProjects = computed(() =>
    projects.value.filter(p => p.status === 'draft')
  )

  const filteredProjects = computed(() => {
    let filtered = [...projects.value]

    if (searchQuery.value) {
      const query = searchQuery.value.toLowerCase()
      filtered = filtered.filter(
        project =>
          project.name.toLowerCase().includes(query) ||
          project.description?.toLowerCase().includes(query) ||
          project.tags?.some(tag => tag.toLowerCase().includes(query))
      )
    }

    if (statusFilter.value) {
      filtered = filtered.filter(project => project.status === statusFilter.value)
    }

    return filtered
  })

  const hasNextPage = computed(() => currentPage.value * pageSize.value < totalProjects.value)

  const hasPreviousPage = computed(() => currentPage.value > 1)

  const projectStats = computed(() => ({
    total: totalProjects.value,
    active: activeProjects.value.length,
    archived: archivedProjects.value.length,
    draft: draftProjects.value.length
  }))

  // Actions
  async function fetchProjects(page = 1, limit = 12, search?: string, status?: string) {
    isLoading.value = true
    error.value = null

    try {
      const params = {
        skip: (page - 1) * limit,
        limit,
        search: search || searchQuery.value || undefined,
        status: status || statusFilter.value || undefined
      }

      const result: SearchResult<Project> = await ProjectsService.list(params)
      projects.value = result.items
      totalProjects.value = result.total
      currentPage.value = page
      pageSize.value = limit
    } catch (err: any) {
      error.value = err.message || 'Failed to fetch projects'
    } finally {
      isLoading.value = false
    }
  }

  async function getProject(id: string) {
    isLoading.value = true
    error.value = null

    try {
      currentProject.value = await ProjectsService.get(id)
      await fetchProjectMembers(id)
      return currentProject.value
    } catch (err: any) {
      error.value = err.message || 'Failed to get project'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function createProject(data: CreateProjectRequest) {
    isLoading.value = true
    error.value = null

    try {
      const newProject = await ProjectsService.create(data)
      projects.value.push(newProject)
      totalProjects.value++
      return newProject
    } catch (err: any) {
      error.value = err.message || 'Failed to create project'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateProject(id: string, data: UpdateProjectRequest) {
    isLoading.value = true
    error.value = null

    try {
      const updatedProject = await ProjectsService.update(id, data)
      const index = projects.value.findIndex(p => p.id === id)
      if (index !== -1) {
        projects.value[index] = updatedProject
      }
      if (currentProject.value?.id === id) {
        currentProject.value = updatedProject
      }
      return updatedProject
    } catch (err: any) {
      error.value = err.message || 'Failed to update project'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function deleteProject(id: string) {
    isLoading.value = true
    error.value = null

    try {
      await ProjectsService.delete(id)
      projects.value = projects.value.filter(p => p.id !== id)
      totalProjects.value--
      if (currentProject.value?.id === id) {
        currentProject.value = null
        currentProjectMembers.value = []
      }
    } catch (err: any) {
      error.value = err.message || 'Failed to delete project'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function fetchProjectMembers(id: string) {
    try {
      currentProjectMembers.value = await ProjectsService.getMembers(id)
      return currentProjectMembers.value
    } catch (err: any) {
      return []
    }
  }

  async function addProjectMember(projectId: string, userId: string, role: string) {
    isLoading.value = true
    error.value = null

    try {
      const newMember = await ProjectsService.addMember(projectId, userId, role)
      currentProjectMembers.value.push(newMember)
      return newMember
    } catch (err: any) {
      error.value = err.message || 'Failed to add project member'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function updateProjectMember(projectId: string, userId: string, role: string) {
    isLoading.value = true
    error.value = null

    try {
      const updatedMember = await ProjectsService.updateMember(projectId, userId, role)
      const index = currentProjectMembers.value.findIndex(m => m.userId === userId)
      if (index !== -1) {
        currentProjectMembers.value[index] = updatedMember
      }
      return updatedMember
    } catch (err: any) {
      error.value = err.message || 'Failed to update project member'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function removeProjectMember(projectId: string, userId: string) {
    isLoading.value = true
    error.value = null

    try {
      await ProjectsService.removeMember(projectId, userId)
      currentProjectMembers.value = currentProjectMembers.value.filter(
        m => m.userId !== userId
      )
    } catch (err: any) {
      error.value = err.message || 'Failed to remove project member'
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function getProjectStats(id: string) {
    try {
      const stats = await ProjectsService.getStats(id)
      return stats
    } catch (err: any) {
      return null
    }
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
    fetchProjects(1, pageSize.value)
  }

  function setStatusFilter(status: string | null) {
    statusFilter.value = status
    fetchProjects(1, pageSize.value)
  }

  function clearFilters() {
    searchQuery.value = ''
    statusFilter.value = null
    fetchProjects(1, pageSize.value)
  }

  return {
    // State
    projects,
    currentProject,
    currentProjectMembers,
    totalProjects,
    isLoading,
    error,
    searchQuery,
    statusFilter,
    currentPage,
    pageSize,

    // Getters
    activeProjects,
    archivedProjects,
    draftProjects,
    filteredProjects,
    hasNextPage,
    hasPreviousPage,
    projectStats,

    // Actions
    fetchProjects,
    getProject,
    createProject,
    updateProject,
    deleteProject,
    fetchProjectMembers,
    addProjectMember,
    updateProjectMember,
    removeProjectMember,
    getProjectStats,
    setSearchQuery,
    setStatusFilter,
    clearFilters
  }
})