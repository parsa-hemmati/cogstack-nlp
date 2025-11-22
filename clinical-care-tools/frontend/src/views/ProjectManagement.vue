<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex justify-space-between align-center">
          <div>
            <h1 class="text-h4 font-weight-bold mb-1">Project Management</h1>
            <p class="text-body-1 text-grey">Manage your research projects and collaborations</p>
          </div>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            variant="elevated"
            @click="openCreateDialog"
          >
            New Project
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- Filters and Search -->
    <v-row class="my-4">
      <v-col cols="12" md="6">
        <v-text-field
          v-model="searchQuery"
          prepend-inner-icon="mdi-magnify"
          label="Search projects..."
          variant="outlined"
          density="comfortable"
          clearable
          hide-details
          @input="handleSearch"
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-select
          v-model="statusFilter"
          :items="statusOptions"
          label="Status"
          variant="outlined"
          density="comfortable"
          clearable
          hide-details
          @update:model-value="handleFilter"
        />
      </v-col>
      <v-col cols="12" md="3">
        <v-btn-toggle
          v-model="viewMode"
          mandatory
          variant="outlined"
          divided
        >
          <v-btn icon="mdi-view-grid" value="grid" />
          <v-btn icon="mdi-view-list" value="list" />
        </v-btn-toggle>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="mb-4">
      <v-col v-for="stat in stats" :key="stat.title" cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center justify-space-between">
              <div>
                <p class="text-caption text-grey mb-1">{{ stat.title }}</p>
                <h3 class="text-h4 font-weight-bold">{{ stat.value }}</h3>
              </div>
              <v-icon :color="stat.color" size="40">{{ stat.icon }}</v-icon>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Projects Grid View -->
    <v-row v-if="viewMode === 'grid'">
      <v-col
        v-for="project in projectsStore.filteredProjects"
        :key="project.id"
        cols="12"
        sm="6"
        md="4"
        lg="3"
      >
        <ProjectCard
          :project="project"
          @view="viewProject"
          @edit="openEditDialog"
          @delete="openDeleteDialog"
          @manage-members="openMembersDialog"
        />
      </v-col>

      <!-- Empty State -->
      <v-col v-if="!projectsStore.isLoading && projectsStore.filteredProjects.length === 0" cols="12">
        <v-card>
          <v-card-text class="text-center py-8">
            <v-icon size="64" color="grey">mdi-folder-open</v-icon>
            <h3 class="text-h5 mt-4 mb-2">No Projects Found</h3>
            <p class="text-body-2 text-grey mb-4">
              {{ searchQuery || statusFilter ? 'No projects match your filters' : 'Create your first project to get started' }}
            </p>
            <v-btn
              v-if="!searchQuery && !statusFilter"
              color="primary"
              prepend-icon="mdi-plus"
              @click="openCreateDialog"
            >
              Create First Project
            </v-btn>
            <v-btn
              v-else
              variant="text"
              @click="clearFilters"
            >
              Clear Filters
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Loading State -->
      <v-col v-if="projectsStore.isLoading" v-for="i in 8" :key="`skeleton-${i}`" cols="12" sm="6" md="4" lg="3">
        <v-skeleton-loader type="card" />
      </v-col>
    </v-row>

    <!-- Projects List View -->
    <v-row v-else>
      <v-col cols="12">
        <v-data-table
          :headers="tableHeaders"
          :items="projectsStore.filteredProjects"
          :loading="projectsStore.isLoading"
          :items-per-page="10"
          class="elevation-1"
        >
          <template #item.name="{ item }">
            <div class="d-flex align-center py-2">
              <v-icon color="primary" class="mr-2">mdi-folder</v-icon>
              <span class="font-weight-medium">{{ item.name }}</span>
            </div>
          </template>

          <template #item.status="{ item }">
            <v-chip
              :color="getStatusColor(item.status)"
              size="small"
            >
              {{ item.status }}
            </v-chip>
          </template>

          <template #item.members="{ item }">
            <v-avatar-group max="3">
              <v-avatar
                v-for="member in item.members.slice(0, 3)"
                :key="member.userId"
                size="28"
                :color="getAvatarColor(member.userId)"
              >
                <span class="text-caption">
                  {{ getInitials(member.user) }}
                </span>
              </v-avatar>
            </v-avatar-group>
            <span class="text-caption text-grey ml-2">
              {{ item.members.length }}
            </span>
          </template>

          <template #item.createdAt="{ item }">
            {{ formatDate(item.createdAt) }}
          </template>

          <template #item.actions="{ item }">
            <v-btn
              icon="mdi-eye"
              size="small"
              variant="text"
              @click="viewProject(item)"
            />
            <v-btn
              icon="mdi-pencil"
              size="small"
              variant="text"
              @click="openEditDialog(item)"
            />
            <v-btn
              icon="mdi-account-plus"
              size="small"
              variant="text"
              @click="openMembersDialog(item)"
            />
            <v-btn
              icon="mdi-delete"
              size="small"
              variant="text"
              color="error"
              @click="openDeleteDialog(item)"
            />
          </template>
        </v-data-table>
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="formDialog" max-width="600px" persistent>
      <ProjectForm
        :project="selectedProject"
        :is-edit="isEditMode"
        @submit="handleFormSubmit"
        @cancel="closeFormDialog"
      />
    </v-dialog>

    <!-- Members Dialog -->
    <v-dialog v-model="membersDialog" max-width="800px" persistent>
      <MemberManager
        v-if="selectedProject"
        :project="selectedProject"
        @close="closeMembersDialog"
        @updated="handleMembersUpdated"
      />
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500px">
      <v-card>
        <v-card-title>
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          Delete Project
        </v-card-title>
        <v-card-text>
          Are you sure you want to delete project <strong>{{ selectedProject?.name }}</strong>?
          This will also delete all associated tasks and data. This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeDeleteDialog">Cancel</v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="confirmDelete"
            :loading="isDeleting"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar
      v-model="snackbar"
      :color="snackbarColor"
      :timeout="3000"
      location="top"
    >
      {{ snackbarMessage }}
      <template #actions>
        <v-btn variant="text" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectsStore } from '@/stores/projects'
import ProjectCard from '@/components/projects/ProjectCard.vue'
import ProjectForm from '@/components/projects/ProjectForm.vue'
import MemberManager from '@/components/projects/MemberManager.vue'
import type { Project, User } from '@/types'

// Router
const router = useRouter()

// Stores
const projectsStore = useProjectsStore()

// Refs
const formDialog = ref(false)
const membersDialog = ref(false)
const deleteDialog = ref(false)
const selectedProject = ref<Project | null>(null)
const isEditMode = ref(false)
const isDeleting = ref(false)
const viewMode = ref<'grid' | 'list'>('grid')
const searchQuery = ref('')
const statusFilter = ref<string | null>(null)

// Snackbar
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Data
const statusOptions = [
  { title: 'All', value: null },
  { title: 'Active', value: 'active' },
  { title: 'Draft', value: 'draft' },
  { title: 'Archived', value: 'archived' }
]

const tableHeaders = [
  { title: 'Project', key: 'name', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
  { title: 'Members', key: 'members', sortable: false },
  { title: 'Created', key: 'createdAt', sortable: true },
  { title: 'Actions', key: 'actions', sortable: false, align: 'center' }
]

// Computed
const stats = computed(() => [
  {
    title: 'Total Projects',
    value: projectsStore.totalProjects,
    icon: 'mdi-folder',
    color: 'primary'
  },
  {
    title: 'Active',
    value: projectsStore.activeProjects.length,
    icon: 'mdi-folder-open',
    color: 'success'
  },
  {
    title: 'Draft',
    value: projectsStore.draftProjects.length,
    icon: 'mdi-folder-edit',
    color: 'warning'
  },
  {
    title: 'Archived',
    value: projectsStore.archivedProjects.length,
    icon: 'mdi-folder-lock',
    color: 'grey'
  }
])

// Methods
function openCreateDialog() {
  selectedProject.value = null
  isEditMode.value = false
  formDialog.value = true
}

function openEditDialog(project: Project) {
  selectedProject.value = project
  isEditMode.value = true
  formDialog.value = true
}

function openDeleteDialog(project: Project) {
  selectedProject.value = project
  deleteDialog.value = true
}

function openMembersDialog(project: Project) {
  selectedProject.value = project
  membersDialog.value = true
}

function closeFormDialog() {
  formDialog.value = false
  selectedProject.value = null
}

function closeDeleteDialog() {
  deleteDialog.value = false
  selectedProject.value = null
}

function closeMembersDialog() {
  membersDialog.value = false
  selectedProject.value = null
}

function viewProject(project: Project) {
  // Navigate to project detail view (to be implemented)
  router.push(`/projects/${project.id}`)
}

async function handleFormSubmit(project: Project) {
  closeFormDialog()
  showSnackbar(
    `Project ${isEditMode.value ? 'updated' : 'created'} successfully`,
    'success'
  )
  await projectsStore.fetchProjects()
}

async function handleMembersUpdated() {
  showSnackbar('Project members updated successfully', 'success')
  await projectsStore.fetchProjects()
}

async function confirmDelete() {
  if (!selectedProject.value) return

  isDeleting.value = true
  try {
    await projectsStore.deleteProject(selectedProject.value.id)
    showSnackbar('Project deleted successfully', 'success')
    closeDeleteDialog()
  } catch (error) {
    showSnackbar('Failed to delete project', 'error')
  } finally {
    isDeleting.value = false
  }
}

function handleSearch() {
  projectsStore.setSearchQuery(searchQuery.value)
}

function handleFilter() {
  projectsStore.setStatusFilter(statusFilter.value)
}

function clearFilters() {
  searchQuery.value = ''
  statusFilter.value = null
  projectsStore.clearFilters()
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    active: 'success',
    draft: 'warning',
    archived: 'grey'
  }
  return colors[status] || 'default'
}

function getInitials(user?: User): string {
  if (!user) return '?'
  if (user.firstName && user.lastName) {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase()
  }
  return user.username.substring(0, 2).toUpperCase()
}

function getAvatarColor(userId: string): string {
  const colors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
  const index = userId.charCodeAt(0) % colors.length
  return colors[index]
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

function showSnackbar(message: string, color: string) {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}

// Lifecycle
onMounted(async () => {
  await projectsStore.fetchProjects()
})
</script>