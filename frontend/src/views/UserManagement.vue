<template>
  <v-container fluid>
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <span class="text-h5">User Management</span>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="showCreateDialog = true">
              <v-icon left>mdi-plus</v-icon>
              Create User
            </v-btn>
          </v-card-title>

          <!-- Search Bar -->
          <v-card-text>
            <v-text-field
              v-model="searchQuery"
              label="Search users"
              prepend-inner-icon="mdi-magnify"
              clearable
              @input="handleSearch"
              hint="Search by username or email"
            ></v-text-field>
          </v-card-text>

          <!-- User List Table -->
          <v-data-table
            :headers="headers"
            :items="users"
            :loading="loading"
            :items-per-page="pageSize"
            :server-items-length="totalUsers"
            @update:options="loadUsers"
            class="elevation-1"
          >
            <!-- Role Badge -->
            <template v-slot:item.role="{ item }">
              <v-chip :color="getRoleColor(item.role)" small>
                {{ item.role }}
              </v-chip>
            </template>

            <!-- Active Status -->
            <template v-slot:item.is_active="{ item }">
              <v-chip :color="item.is_active ? 'success' : 'error'" small>
                {{ item.is_active ? 'Active' : 'Inactive' }}
              </v-chip>
            </template>

            <!-- Break Glass Permission -->
            <template v-slot:item.can_break_glass="{ item }">
              <v-icon :color="item.can_break_glass ? 'success' : 'grey'">
                {{ item.can_break_glass ? 'mdi-check' : 'mdi-close' }}
              </v-icon>
            </template>

            <!-- Actions -->
            <template v-slot:item.actions="{ item }">
              <v-btn icon small @click="editUser(item)">
                <v-icon small>mdi-pencil</v-icon>
              </v-btn>
              <v-btn icon small @click="deleteUser(item)" color="error">
                <v-icon small>mdi-delete</v-icon>
              </v-btn>
            </template>
          </v-data-table>
        </v-card>
      </v-col>
    </v-row>

    <!-- Create/Edit User Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600px">
      <v-card>
        <v-card-title>
          <span class="text-h5">{{ editingUser ? 'Edit User' : 'Create User' }}</span>
        </v-card-title>
        <v-card-text>
          <v-form ref="userForm" v-model="formValid">
            <v-text-field
              v-model="userForm.username"
              label="Username"
              :rules="[rules.required]"
              :disabled="editingUser !== null"
            ></v-text-field>

            <v-text-field
              v-model="userForm.email"
              label="Email"
              type="email"
              :rules="[rules.required, rules.email]"
            ></v-text-field>

            <v-text-field
              v-if="!editingUser"
              v-model="userForm.password"
              label="Password"
              type="password"
              :rules="[rules.required, rules.password]"
              hint="Min 12 characters, uppercase, lowercase, number, special char"
            ></v-text-field>

            <v-select
              v-model="userForm.role"
              :items="roles"
              label="Role"
              :rules="[rules.required]"
            ></v-select>

            <v-switch
              v-model="userForm.is_active"
              label="Active"
              color="success"
            ></v-switch>

            <v-switch
              v-model="userForm.can_break_glass"
              label="Break-Glass Permission"
              color="warning"
            ></v-switch>
          </v-form>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="closeDialog">Cancel</v-btn>
          <v-btn color="primary" @click="saveUser" :disabled="!formValid">
            {{ editingUser ? 'Update' : 'Create' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar for notifications -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" :timeout="3000">
      {{ snackbar.message }}
      <template v-slot:action="{ attrs }">
        <v-btn text v-bind="attrs" @click="snackbar.show = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-container>
</template>

<script lang="ts">
import { defineComponent, ref, reactive, onMounted } from 'vue'
import userService, { type User, type UserCreate } from '@/services/userService'

export default defineComponent({
  name: 'UserManagement',

  setup() {
    // State
    const users = ref<User[]>([])
    const loading = ref(false)
    const searchQuery = ref('')
    const showCreateDialog = ref(false)
    const formValid = ref(false)
    const editingUser = ref<User | null>(null)
    const pageSize = ref(20)
    const totalUsers = ref(0)

    // Form data
    const userForm = reactive({
      username: '',
      email: '',
      password: '',
      role: 'clinician' as 'clinician' | 'researcher' | 'admin',
      is_active: true,
      can_break_glass: false,
    })

    // Snackbar
    const snackbar = reactive({
      show: false,
      message: '',
      color: 'success',
    })

    // Table headers
    const headers = [
      { title: 'Username', value: 'username' },
      { title: 'Email', value: 'email' },
      { title: 'Role', value: 'role' },
      { title: 'Active', value: 'is_active' },
      { title: 'Break-Glass', value: 'can_break_glass' },
      { title: 'Created', value: 'created_at' },
      { title: 'Actions', value: 'actions', sortable: false },
    ]

    const roles = ['clinician', 'researcher', 'admin']

    // Validation rules
    const rules = {
      required: (v: any) => !!v || 'Required',
      email: (v: string) => /.+@.+\..+/.test(v) || 'Invalid email',
      password: (v: string) => {
        if (!v) return 'Required'
        if (v.length < 12) return 'Min 12 characters'
        if (!/[A-Z]/.test(v)) return 'Must contain uppercase'
        if (!/[a-z]/.test(v)) return 'Must contain lowercase'
        if (!/[0-9]/.test(v)) return 'Must contain number'
        if (!/[^A-Za-z0-9]/.test(v)) return 'Must contain special char'
        return true
      },
    }

    // Methods
    const loadUsers = async (options: any = {}) => {
      loading.value = true
      try {
        const { page = 1, itemsPerPage = 20 } = options
        const response = await userService.listUsers(page, itemsPerPage)
        users.value = response.items
        totalUsers.value = response.total
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to load users', 'error')
      } finally {
        loading.value = false
      }
    }

    const handleSearch = async () => {
      if (searchQuery.value && searchQuery.value.length >= 2) {
        loading.value = true
        try {
          const response = await userService.searchUsers(searchQuery.value)
          users.value = response.items
          totalUsers.value = response.total
        } catch (error: any) {
          showSnackbar(error.response?.data?.detail || 'Search failed', 'error')
        } finally {
          loading.value = false
        }
      } else if (!searchQuery.value) {
        loadUsers()
      }
    }

    const editUser = (user: User) => {
      editingUser.value = user
      userForm.username = user.username
      userForm.email = user.email
      userForm.role = user.role
      userForm.is_active = user.is_active
      userForm.can_break_glass = user.can_break_glass
      showCreateDialog.value = true
    }

    const deleteUser = async (user: User) => {
      if (confirm(`Delete user ${user.username}? This will deactivate the user.`)) {
        try {
          await userService.deleteUser(user.id)
          showSnackbar('User deleted successfully', 'success')
          loadUsers()
        } catch (error: any) {
          showSnackbar(error.response?.data?.detail || 'Failed to delete user', 'error')
        }
      }
    }

    const saveUser = async () => {
      if (!formValid.value) return

      try {
        if (editingUser.value) {
          // Update existing user
          await userService.updateUser(editingUser.value.id, {
            email: userForm.email,
            role: userForm.role,
            is_active: userForm.is_active,
            can_break_glass: userForm.can_break_glass,
          })
          showSnackbar('User updated successfully', 'success')
        } else {
          // Create new user
          const createData: UserCreate = {
            username: userForm.username,
            email: userForm.email,
            password: userForm.password,
            role: userForm.role,
            is_active: userForm.is_active,
            can_break_glass: userForm.can_break_glass,
          }
          await userService.createUser(createData)
          showSnackbar('User created successfully', 'success')
        }

        closeDialog()
        loadUsers()
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to save user', 'error')
      }
    }

    const closeDialog = () => {
      showCreateDialog.value = false
      editingUser.value = null
      userForm.username = ''
      userForm.email = ''
      userForm.password = ''
      userForm.role = 'clinician'
      userForm.is_active = true
      userForm.can_break_glass = false
    }

    const getRoleColor = (role: string) => {
      switch (role) {
        case 'admin':
          return 'error'
        case 'researcher':
          return 'info'
        case 'clinician':
          return 'success'
        default:
          return 'grey'
      }
    }

    const showSnackbar = (message: string, color: string) => {
      snackbar.message = message
      snackbar.color = color
      snackbar.show = true
    }

    // Load users on mount
    onMounted(() => {
      loadUsers()
    })

    return {
      users,
      loading,
      searchQuery,
      showCreateDialog,
      formValid,
      editingUser,
      pageSize,
      totalUsers,
      userForm,
      headers,
      roles,
      rules,
      snackbar,
      loadUsers,
      handleSearch,
      editUser,
      deleteUser,
      saveUser,
      closeDialog,
      getRoleColor,
    }
  },
})
</script>

<style scoped>
.v-data-table {
  margin-top: 16px;
}
</style>
