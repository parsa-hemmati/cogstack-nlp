<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title class="d-flex align-center">
            <v-icon left>mdi-account-multiple</v-icon>
            User Management
            <v-spacer></v-spacer>
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              Create User
            </v-btn>
          </v-card-title>

          <v-card-text>
            <!-- Loading State -->
            <v-progress-linear v-if="userStore.loading" indeterminate color="primary"></v-progress-linear>

            <!-- Error Alert -->
            <v-alert
              v-if="userStore.error"
              type="error"
              closable
              @click:close="userStore.clearError()"
              class="mb-4"
            >
              {{ userStore.error }}
            </v-alert>

            <!-- Users Data Table -->
            <v-data-table
              :headers="headers"
              :items="userStore.users"
              :loading="userStore.loading"
              :items-per-page="10"
              class="elevation-1"
            >
              <!-- Role Chip -->
              <template v-slot:item.role="{ item }">
                <v-chip :color="getRoleColor(item.role)" size="small">
                  {{ item.role }}
                </v-chip>
              </template>

              <!-- Active Status -->
              <template v-slot:item.is_active="{ item }">
                <v-chip :color="item.is_active ? 'success' : 'error'" size="small">
                  {{ item.is_active ? 'Active' : 'Inactive' }}
                </v-chip>
              </template>

              <!-- Actions -->
              <template v-slot:item.actions="{ item }">
                <v-btn icon size="small" @click="openEditDialog(item)" class="mr-2">
                  <v-icon>mdi-pencil</v-icon>
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit User Dialog -->
    <v-dialog v-model="dialog" max-width="600px" persistent>
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingUser ? 'Edit User' : 'Create User' }}</span>
        </v-card-title>

        <v-card-text>
          <v-form ref="form" v-model="formValid">
            <!-- Username (create only) -->
            <v-text-field
              v-if="!editingUser"
              v-model="formData.username"
              label="Username"
              :rules="[rules.required]"
              required
              prepend-icon="mdi-account"
            ></v-text-field>

            <!-- Full Name -->
            <v-text-field
              v-model="formData.full_name"
              label="Full Name"
              :rules="[rules.required]"
              required
              prepend-icon="mdi-account-circle"
            ></v-text-field>

            <!-- Password (create only) -->
            <v-text-field
              v-if="!editingUser"
              v-model="formData.password"
              label="Password"
              type="password"
              :rules="[rules.required, rules.minLength]"
              required
              prepend-icon="mdi-lock"
              hint="Minimum 8 characters"
            ></v-text-field>

            <!-- Role -->
            <v-select
              v-model="formData.role"
              :items="roleOptions"
              label="Role"
              :rules="[rules.required]"
              required
              prepend-icon="mdi-shield-account"
            ></v-select>

            <!-- Active Status (edit only) -->
            <v-switch
              v-if="editingUser"
              v-model="formData.is_active"
              label="Active"
              color="success"
              prepend-icon="mdi-check-circle"
            ></v-switch>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn color="grey" variant="text" @click="closeDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            :disabled="!formValid || userStore.loading"
            :loading="userStore.loading"
            @click="saveUser"
          >
            {{ editingUser ? 'Update' : 'Create' }}
          </v-btn>
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
import { ref, onMounted } from 'vue'
import { useUserStore } from '../stores/user'
import type { User, UserCreate, UserUpdate } from '../services/users'

const userStore = useUserStore()

// Data table headers
const headers = [
  { title: 'Username', key: 'username', align: 'start' as const },
  { title: 'Full Name', key: 'full_name', align: 'start' as const },
  { title: 'Role', key: 'role', align: 'center' as const },
  { title: 'Status', key: 'is_active', align: 'center' as const },
  { title: 'Actions', key: 'actions', align: 'center' as const, sortable: false },
]

// Dialog state
const dialog = ref(false)
const formValid = ref(false)
const editingUser = ref<User | null>(null)

// Form data
const formData = ref<Partial<UserCreate & UserUpdate>>({
  username: '',
  full_name: '',
  password: '',
  role: 'viewer',
  is_active: true,
})

// Role options
const roleOptions = [
  { title: 'Admin', value: 'admin' },
  { title: 'Clinician', value: 'clinician' },
  { title: 'Researcher', value: 'researcher' },
  { title: 'Viewer', value: 'viewer' },
]

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'Required',
  minLength: (value: string) => value.length >= 8 || 'Minimum 8 characters',
}

// Snackbar state
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

/**
 * Get color for role chip
 */
function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    admin: 'error',
    clinician: 'primary',
    researcher: 'info',
    viewer: 'secondary',
  }
  return colors[role] || 'grey'
}

/**
 * Open create user dialog
 */
function openCreateDialog() {
  editingUser.value = null
  formData.value = {
    username: '',
    full_name: '',
    password: '',
    role: 'viewer',
    is_active: true,
  }
  dialog.value = true
}

/**
 * Open edit user dialog
 */
function openEditDialog(user: User) {
  editingUser.value = user
  formData.value = {
    full_name: user.full_name,
    role: user.role,
    is_active: user.is_active,
  }
  dialog.value = true
}

/**
 * Close dialog
 */
function closeDialog() {
  dialog.value = false
  editingUser.value = null
  formData.value = {}
}

/**
 * Save user (create or update)
 */
async function saveUser() {
  try {
    if (editingUser.value) {
      // Update existing user
      const updateData: UserUpdate = {
        full_name: formData.value.full_name,
        role: formData.value.role as any,
        is_active: formData.value.is_active,
      }
      await userStore.updateUser(editingUser.value.id, updateData)
      snackbarMessage.value = 'User updated successfully'
    } else {
      // Create new user
      const createData: UserCreate = {
        username: formData.value.username!,
        full_name: formData.value.full_name!,
        password: formData.value.password!,
        role: formData.value.role as any,
      }
      await userStore.createUser(createData)
      snackbarMessage.value = 'User created successfully'
    }

    snackbarColor.value = 'success'
    snackbar.value = true
    closeDialog()
  } catch (error) {
    snackbarMessage.value = 'Operation failed. Please try again.'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
}

/**
 * Load users on mount
 */
onMounted(async () => {
  try {
    await userStore.fetchUsers()
  } catch (error) {
    snackbarMessage.value = 'Failed to load users'
    snackbarColor.value = 'error'
    snackbar.value = true
  }
})
</script>
