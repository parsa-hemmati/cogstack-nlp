<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon left>mdi-folder-multiple</v-icon>
            Project Management
            <v-spacer></v-spacer>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              Create Project
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Loading State -->
            <v-progress-linear
              v-if="projectStore.loading"
              indeterminate
              color="primary"
            ></v-progress-linear>

            <!-- Error Alert -->
            <v-alert
              v-if="projectStore.error"
              type="error"
              closable
              @click:close="projectStore.clearError()"
              class="mb-4"
            >
              {{ projectStore.error }}
            </v-alert>

            <!-- Projects Data Table -->
            <v-data-table
              :headers="headers"
              :items="projectStore.projects"
              :loading="projectStore.loading"
              :items-per-page="10"
              class="elevation-1"
            >
              <!-- Description -->
              <template v-slot:item.description="{ item }">
                {{ item.description || 'No description' }}
              </template>

              <!-- Member Count -->
              <template v-slot:item.members="{ item }">
                <v-chip size="small" prepend-icon="mdi-account-multiple">
                  {{ item.members.length }}
                </v-chip>
              </template>

              <!-- Created At -->
              <template v-slot:item.created_at="{ item }">
                {{ formatDate(item.created_at) }}
              </template>

              <!-- Actions -->
              <template v-slot:item.actions="{ item }">
                <v-btn icon size="small" @click="openEditDialog(item)" class="mr-2">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon size="small" @click="openMembersDialog(item)" class="mr-2">
                  <v-icon>mdi-account-multiple</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit Project Dialog -->
    <v-dialog v-model="projectDialog" max-width="600px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingProject ? 'Edit Project' : 'Create Project' }}</span>
        </v-card-title>

        <v-card-text>
          <v-form ref="projectForm" v-model="projectFormValid">
            <!-- Name -->
            <v-text-field
              v-model="projectFormData.name"
              label="Project Name"
              :rules="[rules.required]"
              required
              prepend-icon="mdi-folder"
            ></v-text-field>

            <!-- Description -->
            <v-textarea
              v-model="projectFormData.description"
              label="Description"
              rows="3"
              prepend-icon="mdi-text"
            ></v-textarea>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeProjectDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :disabled="!projectFormValid || projectStore.loading"
            :loading="projectStore.loading"
            @click="saveProject"
          >
            {{ editingProject ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Manage Members Dialog -->
    <v-dialog v-model="membersDialog" max-width="800px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">Manage Project Members</span>
        </v-card-title>

        <v-card-text>
          <!-- Current Members List -->
          <v-list>
            <v-list-item v-for="member in currentProjectMembers" :key="member.id">
              <template v-slot:prepend>
                <v-avatar color="primary">
                  <v-icon>mdi-account</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title>User ID: {{ member.user_id }}</v-list-item-title>
              <v-list-item-subtitle>
                <v-chip :color="getRoleColor(member.role)" size="small" class="mr-2">
                  {{ member.role }}
                </v-chip>
                Added {{ formatDate(member.added_at) }}
              </v-list-item-subtitle>

              <template v-slot:append>
                <v-btn
                  icon
                  size="small"
                  color="error"
                  @click="confirmRemoveMember(member.user_id)"
                  :disabled="!canRemoveMember(member)"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>

          <v-divider class="my-4"></v-divider>

          <!-- Add Member Form -->
          <v-card variant="outlined">
            <v-card-title class="text-h6">Add New Member</v-card-title>
            <v-card-text>
              <v-form ref="memberForm" v-model="memberFormValid">
                <v-text-field
                  v-model="memberFormData.user_id"
                  label="User ID"
                  :rules="[rules.required]"
                  required
                  prepend-icon="mdi-account"
                  hint="Enter the user ID to add"
                ></v-text-field>

                <v-select
                  v-model="memberFormData.role"
                  :items="memberRoleOptions"
                  label="Role"
                  :rules="[rules.required]"
                  required
                  prepend-icon="mdi-shield-account"
                ></v-select>

                <v-btn
                  color="primary"
                  prepend-icon="mdi-plus"
                  :disabled="!memberFormValid || projectStore.loading"
                  :loading="projectStore.loading"
                  @click="addNewMember"
                  block
                >
                  Add Member
                </v-btn>
              </v-form>
            </v-card-text>
          </v-card>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeMembersDialog">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
    <v-snackbar v-model="snackbar" :color="snackbarColor" :timeout="3000">
      {{ snackbarMessage }}
      <template v-slot:actions>
        <v-btn variant="text" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectStore } from '../stores/project'
import type { Project, ProjectCreate, ProjectUpdate, ProjectMemberAdd } from '../services/projects'

const projectStore = useProjectStore()

// Data table headers
const headers = [
  { title: 'Name', key: 'name', align: 'start' as const },
  { title: 'Description', key: 'description', align: 'start' as const },
  { title: 'Members', key: 'members', align: 'center' as const },
  { title: 'Created', key: 'created_at', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Project dialog state
const projectDialog = ref(false)
const projectFormValid = ref(false)
const editingProject = ref<Project | null>(null)

// Project form data
const projectFormData = ref<Partial<ProjectCreate & ProjectUpdate>>({
  name: '',
  description: '',
})

// Members dialog state
const membersDialog = ref(false)
const currentProjectForMembers = ref<Project | null>(null)
const memberFormValid = ref(false)

// Member form data
const memberFormData = ref<ProjectMemberAdd>({
  user_id: '',
  role: 'member',
})

// Member role options
const memberRoleOptions = [
  { title: 'Owner', value: 'owner' },
  { title: 'Admin', value: 'admin' },
  { title: 'Member', value: 'member' },
  { title: 'Viewer', value: 'viewer' },
]

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'Required',
}

// Snackbar state
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

/**
 * Get current project members
 */
const currentProjectMembers = computed(() => {
  return currentProjectForMembers.value?.members || []
})

/**
 * Format date for display
 */
function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString()
}

/**
 * Get color for role chip
 */
function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    owner: 'error',
    admin: 'warning',
    member: 'primary',
    viewer: 'secondary',
  }
  return colors[role] || 'grey'
}

/**
 * Check if member can be removed (not last owner)
 */
function canRemoveMember(member: any): boolean {
  if (member.role !== 'owner') return true
  const ownerCount = currentProjectMembers.value.filter((m) => m.role === 'owner').length
  return ownerCount > 1
}

/**
 * Open create project dialog
 */
function openCreateDialog() {
  editingProject.value = null
  projectFormData.value = {
    name: '',
    description: '',
  }
  projectDialog.value = true
}

/**
 * Open edit project dialog
 */
function openEditDialog(project: Project) {
  editingProject.value = project
  projectFormData.value = {
    name: project.name,
    description: project.description,
  }
  projectDialog.value = true
}

/**
 * Close project dialog
 */
function closeProjectDialog() {
  projectDialog.value = false
  editingProject.value = null
  projectFormData.value = {}
}

/**
 * Save project (create or update)
 */
async function saveProject() {
  try {
    if (editingProject.value) {
      // Update existing project
      const updateData: ProjectUpdate = {
        name: projectFormData.value.name,
        description: projectFormData.value.description,
      }
      await projectStore.updateProject(editingProject.value.id, updateData)
      snackbarMessage.value = 'Project updated successfully'
    } else {
      // Create new project
      const createData: ProjectCreate = {
        name: projectFormData.value.name!,
        description: projectFormData.value.description,
      }
      await projectStore.createProject(createData)
      snackbarMessage.value = 'Project created successfully'
    }

    snackbarColor.value = 'success'
    snackbar.value = true
    closeProjectDialog()
  } catch (error) {
    snackbarMessage.value = 'Operation failed. Please try again.'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

/**
 * Open members management dialog
 */
function openMembersDialog(project: Project) {
  currentProjectForMembers.value = project
  memberFormData.value = {
    user_id: '',
    role: 'member',
  }
  membersDialog.value = true
}

/**
 * Close members dialog
 */
function closeMembersDialog() {
  membersDialog.value = false
  currentProjectForMembers.value = null
  memberFormData.value = {
    user_id: '',
    role: 'member',
  }
}

/**
 * Add new member to project
 */
async function addNewMember() {
  if (!currentProjectForMembers.value) return

  try {
    await projectStore.addMember(currentProjectForMembers.value.id, memberFormData.value)
    snackbarMessage.value = 'Member added successfully'
    snackbarColor.value = 'success'
    snackbar.value = true

    // Reset form
    memberFormData.value = {
      user_id: '',
      role: 'member',
    }

    // Refresh project to get updated members
    await projectStore.fetchProjects()
    const updatedProject = projectStore.projects.find(
      (p) => p.id === currentProjectForMembers.value!.id
    )
    if (updatedProject) {
      currentProjectForMembers.value = updatedProject
    }
  } catch (error) {
    snackbarMessage.value = 'Failed to add member. Please try again.'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

/**
 * Confirm and remove member from project
 */
async function confirmRemoveMember(userId: string) {
  if (!currentProjectForMembers.value) return

  if (confirm('Are you sure you want to remove this member?')) {
    try {
      await projectStore.removeMember(currentProjectForMembers.value.id, userId)
      snackbarMessage.value = 'Member removed successfully'
      snackbarColor.value = 'success'
      snackbar.value = true

      // Refresh project
      await projectStore.fetchProjects()
      const updatedProject = projectStore.projects.find(
        (p) => p.id === currentProjectForMembers.value!.id
      )
      if (updatedProject) {
        currentProjectForMembers.value = updatedProject
      }
    } catch (error) {
      snackbarMessage.value = 'Failed to remove member. Please try again.'
      snackbarColor.value = 'error'
      snackbar.value = true
    }
  }
}

/**
 * Load projects on mount
 */
onMounted(async () => {
  try {
    await projectStore.fetchProjects()
  } catch (error) {
    snackbarMessage.value = 'Failed to load projects'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
})
</script>
