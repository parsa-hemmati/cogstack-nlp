<template>
  <v-card>
    <v-card-title>
      {{ isEdit ? 'Edit User' : 'Create New User' }}
    </v-card-title>

    <v-card-text>
      <v-form ref="form" v-model="isFormValid" @submit.prevent="handleSubmit">
        <v-container>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.username"
                :disabled="isEdit"
                label="Username"
                prepend-icon="mdi-account"
                :rules="[rules.required, rules.username]"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.email"
                label="Email"
                prepend-icon="mdi-email"
                type="email"
                :rules="[rules.required, rules.email]"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.firstName"
                label="First Name"
                prepend-icon="mdi-account-details"
                :rules="[rules.name]"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="formData.lastName"
                label="Last Name"
                prepend-icon="mdi-account-details"
                :rules="[rules.name]"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col v-if="!isEdit" cols="12">
              <v-text-field
                v-model="formData.password"
                label="Password"
                prepend-icon="mdi-lock"
                :type="showPassword ? 'text' : 'password'"
                :append-inner-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showPassword = !showPassword"
                :rules="[rules.required, rules.password]"
                variant="outlined"
                density="comfortable"
              />
            </v-col>

            <v-col cols="12">
              <v-select
                v-model="formData.roles"
                label="Roles"
                prepend-icon="mdi-shield-account"
                :items="availableRoles"
                multiple
                chips
                closable-chips
                :rules="[rules.rolesRequired]"
                variant="outlined"
                density="comfortable"
              >
                <template #chip="{ props: chipProps, item }">
                  <v-chip
                    v-bind="chipProps"
                    :color="getRoleColor(item.value)"
                    variant="elevated"
                    size="small"
                  >
                    {{ item.title }}
                  </v-chip>
                </template>
              </v-select>
            </v-col>

            <v-col v-if="isEdit" cols="12">
              <v-switch
                v-model="formData.isActive"
                label="Active"
                color="primary"
                hide-details
              />
            </v-col>
          </v-row>
        </v-container>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        variant="text"
        @click="$emit('cancel')"
        :disabled="isSubmitting"
      >
        Cancel
      </v-btn>
      <v-btn
        color="primary"
        variant="elevated"
        :loading="isSubmitting"
        :disabled="!isFormValid"
        @click="handleSubmit"
      >
        {{ isEdit ? 'Update' : 'Create' }}
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useUsersStore } from '@/stores/users'
import type { User, CreateUserRequest, UpdateUserRequest } from '@/types'

// Props
const props = defineProps<{
  user?: User | null
  isEdit?: boolean
}>()

// Emits
const emit = defineEmits<{
  submit: [user: User]
  cancel: []
}>()

// Stores
const usersStore = useUsersStore()

// Refs
const form = ref()
const isFormValid = ref(false)
const isSubmitting = ref(false)
const showPassword = ref(false)

// Data
const formData = reactive({
  username: '',
  email: '',
  firstName: '',
  lastName: '',
  password: '',
  roles: [] as string[],
  isActive: true
})

// Computed
const availableRoles = computed(() => {
  return usersStore.availableRoles.map(role => ({
    title: role.charAt(0).toUpperCase() + role.slice(1),
    value: role
  }))
})

// Validation rules
const rules = {
  required: (v: string) => !!v || 'This field is required',
  email: (v: string) => {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return pattern.test(v) || 'Invalid email address'
  },
  username: (v: string) => {
    const pattern = /^[a-zA-Z0-9_]{3,30}$/
    return pattern.test(v) || 'Username must be 3-30 characters (alphanumeric and underscore only)'
  },
  password: (v: string) => {
    if (v.length < 8) return 'Password must be at least 8 characters'
    if (!/[A-Z]/.test(v)) return 'Password must contain at least one uppercase letter'
    if (!/[a-z]/.test(v)) return 'Password must contain at least one lowercase letter'
    if (!/[0-9]/.test(v)) return 'Password must contain at least one number'
    return true
  },
  name: (v: string) => {
    if (!v) return true // Optional field
    const pattern = /^[a-zA-Z\s]{1,50}$/
    return pattern.test(v) || 'Name must contain only letters and spaces'
  },
  rolesRequired: (v: string[]) => v.length > 0 || 'At least one role is required'
}

// Methods
function getRoleColor(role: string): string {
  const colors: Record<string, string> = {
    admin: 'red',
    clinician: 'blue',
    researcher: 'green',
    viewer: 'grey'
  }
  return colors[role] || 'default'
}

async function handleSubmit() {
  const { valid } = await form.value.validate()
  if (!valid) return

  isSubmitting.value = true

  try {
    let result: User

    if (props.isEdit && props.user) {
      const updateData: UpdateUserRequest = {
        email: formData.email,
        firstName: formData.firstName || undefined,
        lastName: formData.lastName || undefined,
        roles: formData.roles,
        isActive: formData.isActive
      }
      result = await usersStore.updateUser(props.user.id, updateData)
    } else {
      const createData: CreateUserRequest = {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        firstName: formData.firstName || undefined,
        lastName: formData.lastName || undefined,
        roles: formData.roles
      }
      result = await usersStore.createUser(createData)
    }

    emit('submit', result)
  } catch (error) {
  } finally {
    isSubmitting.value = false
  }
}

// Lifecycle
onMounted(async () => {
  // Fetch available roles
  await usersStore.fetchRoles()

  // Populate form if editing
  if (props.isEdit && props.user) {
    formData.username = props.user.username
    formData.email = props.user.email
    formData.firstName = props.user.firstName || ''
    formData.lastName = props.user.lastName || ''
    formData.roles = props.user.roles
    formData.isActive = props.user.isActive
  }
})
</script>