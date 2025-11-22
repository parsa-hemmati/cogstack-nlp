<template>
  <v-container fluid>
    <!-- Page Header -->
    <v-row>
      <v-col cols="12">
        <h1 class="text-h4 font-weight-bold mb-1">User Management</h1>
        <p class="text-body-1 text-grey">Manage system users, roles, and permissions</p>
      </v-col>
    </v-row>

    <!-- Stats Cards -->
    <v-row class="my-4">
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

    <!-- Users Table -->
    <v-row>
      <v-col cols="12">
        <UserTable
          :users="usersStore.filteredUsers"
          :loading="usersStore.isLoading"
          @create="openCreateDialog"
          @edit="openEditDialog"
          @delete="openDeleteDialog"
          @reset-password="openResetPasswordDialog"
          @toggle-status="toggleUserStatus"
        />
      </v-col>
    </v-row>

    <!-- Create/Edit Dialog -->
    <v-dialog v-model="formDialog" max-width="600px" persistent>
      <UserForm
        :user="selectedUser"
        :is-edit="isEditMode"
        @submit="handleFormSubmit"
        @cancel="closeFormDialog"
      />
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="deleteDialog" max-width="500px">
      <v-card>
        <v-card-title>
          <v-icon color="error" class="mr-2">mdi-alert</v-icon>
          Delete User
        </v-card-title>
        <v-card-text>
          Are you sure you want to delete user <strong>{{ selectedUser?.username }}</strong>?
          This action cannot be undone.
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

    <!-- Reset Password Dialog -->
    <v-dialog v-model="resetPasswordDialog" max-width="500px">
      <v-card>
        <v-card-title>Reset Password</v-card-title>
        <v-card-text>
          <v-form ref="resetForm" v-model="isResetFormValid" @submit.prevent="confirmResetPassword">
            <p class="mb-4">
              Reset password for user <strong>{{ selectedUser?.username }}</strong>
            </p>
            <v-text-field
              v-model="newPassword"
              label="New Password"
              :type="showNewPassword ? 'text' : 'password'"
              :append-inner-icon="showNewPassword ? 'mdi-eye' : 'mdi-eye-off'"
              @click:append-inner="showNewPassword = !showNewPassword"
              :rules="passwordRules"
              variant="outlined"
              density="comfortable"
            />
            <v-text-field
              v-model="confirmPassword"
              label="Confirm Password"
              :type="showConfirmPassword ? 'text' : 'password'"
              :append-inner-icon="showConfirmPassword ? 'mdi-eye' : 'mdi-eye-off'"
              @click:append-inner="showConfirmPassword = !showConfirmPassword"
              :rules="[...passwordRules, passwordMatchRule]"
              variant="outlined"
              density="comfortable"
            />
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeResetPasswordDialog">Cancel</v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="confirmResetPassword"
            :loading="isResetting"
            :disabled="!isResetFormValid"
          >
            Reset Password
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
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import UserTable from '@/components/users/UserTable.vue'
import UserForm from '@/components/users/UserForm.vue'
import type { User } from '@/types'

// Stores
const usersStore = useUsersStore()
const authStore = useAuthStore()

// Refs
const formDialog = ref(false)
const deleteDialog = ref(false)
const resetPasswordDialog = ref(false)
const resetForm = ref()
const selectedUser = ref<User | null>(null)
const isEditMode = ref(false)
const isDeleting = ref(false)
const isResetting = ref(false)
const isResetFormValid = ref(false)
const newPassword = ref('')
const confirmPassword = ref('')
const showNewPassword = ref(false)
const showConfirmPassword = ref(false)

// Snackbar
const snackbar = ref(false)
const snackbarMessage = ref('')
const snackbarColor = ref('success')

// Computed
const stats = computed(() => [
  {
    title: 'Total Users',
    value: usersStore.totalUsers,
    icon: 'mdi-account-group',
    color: 'primary'
  },
  {
    title: 'Active Users',
    value: usersStore.activeUsers.length,
    icon: 'mdi-check-circle',
    color: 'success'
  },
  {
    title: 'Inactive Users',
    value: usersStore.inactiveUsers.length,
    icon: 'mdi-close-circle',
    color: 'error'
  },
  {
    title: 'Admins',
    value: usersStore.users.filter(u => u.roles.includes('admin')).length,
    icon: 'mdi-shield-account',
    color: 'warning'
  }
])

// Validation rules
const passwordRules = [
  (v: string) => !!v || 'Password is required',
  (v: string) => v.length >= 8 || 'Password must be at least 8 characters',
  (v: string) => /[A-Z]/.test(v) || 'Password must contain uppercase letter',
  (v: string) => /[a-z]/.test(v) || 'Password must contain lowercase letter',
  (v: string) => /[0-9]/.test(v) || 'Password must contain number'
]

const passwordMatchRule = (v: string) => v === newPassword.value || 'Passwords must match'

// Methods
function openCreateDialog() {
  selectedUser.value = null
  isEditMode.value = false
  formDialog.value = true
}

function openEditDialog(user: User) {
  selectedUser.value = user
  isEditMode.value = true
  formDialog.value = true
}

function openDeleteDialog(user: User) {
  selectedUser.value = user
  deleteDialog.value = true
}

function openResetPasswordDialog(user: User) {
  selectedUser.value = user
  newPassword.value = ''
  confirmPassword.value = ''
  resetPasswordDialog.value = true
}

function closeFormDialog() {
  formDialog.value = false
  selectedUser.value = null
}

function closeDeleteDialog() {
  deleteDialog.value = false
  selectedUser.value = null
}

function closeResetPasswordDialog() {
  resetPasswordDialog.value = false
  selectedUser.value = null
  newPassword.value = ''
  confirmPassword.value = ''
}

async function handleFormSubmit(user: User) {
  closeFormDialog()
  showSnackbar(
    `User ${isEditMode.value ? 'updated' : 'created'} successfully`,
    'success'
  )
  await usersStore.fetchUsers()
}

async function confirmDelete() {
  if (!selectedUser.value) return

  isDeleting.value = true
  try {
    await usersStore.deleteUser(selectedUser.value.id)
    showSnackbar('User deleted successfully', 'success')
    closeDeleteDialog()
  } catch (error) {
    showSnackbar('Failed to delete user', 'error')
  } finally {
    isDeleting.value = false
  }
}

async function confirmResetPassword() {
  if (!selectedUser.value) return

  const { valid } = await resetForm.value.validate()
  if (!valid) return

  isResetting.value = true
  try {
    await usersStore.resetPassword(selectedUser.value.id, newPassword.value)
    showSnackbar('Password reset successfully', 'success')
    closeResetPasswordDialog()
  } catch (error) {
    showSnackbar('Failed to reset password', 'error')
  } finally {
    isResetting.value = false
  }
}

async function toggleUserStatus(user: User) {
  try {
    await usersStore.toggleUserStatus(user.id, !user.isActive)
    showSnackbar(
      `User ${user.isActive ? 'deactivated' : 'activated'} successfully`,
      'success'
    )
    await usersStore.fetchUsers()
  } catch (error) {
    showSnackbar('Failed to update user status', 'error')
  }
}

function showSnackbar(message: string, color: string) {
  snackbarMessage.value = message
  snackbarColor.value = color
  snackbar.value = true
}

// Lifecycle
onMounted(async () => {
  await usersStore.fetchUsers()
  await usersStore.fetchRoles()
})
</script>