<template>
  <v-card>
    <v-card-title>
      Manage Project Members
      <v-chip class="ml-2" size="small" color="primary">
        {{ members.length }} {{ members.length === 1 ? 'member' : 'members' }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <!-- Add Member Form -->
      <v-container>
        <v-row>
          <v-col cols="12">
            <h3 class="text-h6 mb-3">Add New Member</h3>
            <v-form ref="form" v-model="isFormValid" @submit.prevent="handleAddMember">
              <v-row>
                <v-col cols="12" md="6">
                  <v-autocomplete
                    v-model="selectedUserId"
                    :items="availableUsers"
                    item-title="display"
                    item-value="id"
                    label="Select User"
                    prepend-icon="mdi-account-plus"
                    :rules="[rules.required]"
                    variant="outlined"
                    density="comfortable"
                    clearable
                  >
                    <template #item="{ props: itemProps, item }">
                      <v-list-item v-bind="itemProps">
                        <template #prepend>
                          <v-avatar size="32" :color="getAvatarColor(item.raw.id)">
                            <span class="text-caption">
                              {{ getInitials(item.raw) }}
                            </span>
                          </v-avatar>
                        </template>
                      </v-list-item>
                    </template>
                  </v-autocomplete>
                </v-col>

                <v-col cols="12" md="4">
                  <v-select
                    v-model="selectedRole"
                    :items="roleOptions"
                    label="Role"
                    prepend-icon="mdi-shield-account"
                    :rules="[rules.required]"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>

                <v-col cols="12" md="2">
                  <v-btn
                    color="primary"
                    variant="elevated"
                    :disabled="!isFormValid"
                    :loading="isAdding"
                    @click="handleAddMember"
                    block
                  >
                    Add
                  </v-btn>
                </v-col>
              </v-row>
            </v-form>
          </v-col>
        </v-row>

        <v-divider class="my-4" />

        <!-- Current Members List -->
        <v-row>
          <v-col cols="12">
            <h3 class="text-h6 mb-3">Current Members</h3>

            <v-list v-if="members.length > 0">
              <v-list-item
                v-for="member in members"
                :key="member.userId"
                class="px-0"
              >
                <template #prepend>
                  <v-avatar :color="getAvatarColor(member.userId)" class="mr-3">
                    <span>{{ getInitials(member.user) }}</span>
                  </v-avatar>
                </template>

                <v-list-item-title>
                  {{ getDisplayName(member.user) }}
                  <v-chip
                    v-if="member.role === 'owner'"
                    size="x-small"
                    color="warning"
                    class="ml-2"
                  >
                    Owner
                  </v-chip>
                </v-list-item-title>

                <v-list-item-subtitle>
                  {{ member.user?.email }}
                </v-list-item-subtitle>

                <template #append>
                  <div class="d-flex align-center">
                    <v-select
                      v-if="member.role !== 'owner'"
                      :model-value="member.role"
                      :items="roleOptions.filter(r => r.value !== 'owner')"
                      density="compact"
                      variant="outlined"
                      hide-details
                      style="max-width: 150px"
                      class="mr-2"
                      @update:model-value="(role) => handleUpdateRole(member, role)"
                    />
                    <v-chip
                      v-else
                      color="warning"
                      variant="elevated"
                      size="small"
                      class="mr-2"
                    >
                      Owner
                    </v-chip>

                    <v-btn
                      v-if="member.role !== 'owner'"
                      icon="mdi-delete"
                      size="small"
                      variant="text"
                      color="error"
                      @click="handleRemoveMember(member)"
                      aria-label="Remove member"
                    />
                  </div>
                </template>
              </v-list-item>
            </v-list>

            <v-alert v-else type="info" variant="tonal" class="mt-2">
              No members added yet. Add members using the form above.
            </v-alert>
          </v-col>
        </v-row>
      </v-container>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn variant="text" @click="$emit('close')">
        Close
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useProjectsStore } from '@/stores/projects'
import { useUsersStore } from '@/stores/users'
import type { Project, ProjectMember, User } from '@/types'

// Props
const props = defineProps<{
  project: Project
}>()

// Emits
const emit = defineEmits<{
  close: []
  updated: []
}>()

// Stores
const projectsStore = useProjectsStore()
const usersStore = useUsersStore()

// Refs
const form = ref()
const isFormValid = ref(false)
const isAdding = ref(false)
const selectedUserId = ref<string | null>(null)
const selectedRole = ref('member')

// Data
const members = ref<ProjectMember[]>([])
const allUsers = ref<User[]>([])

// Computed
const availableUsers = computed(() => {
  // Filter out users who are already members
  const memberIds = members.value.map(m => m.userId)
  return allUsers.value
    .filter(user => !memberIds.includes(user.id))
    .map(user => ({
      id: user.id,
      display: `${getDisplayName(user)} (${user.email})`,
      ...user
    }))
})

const roleOptions = [
  { title: 'Admin', value: 'admin' },
  { title: 'Member', value: 'member' },
  { title: 'Viewer', value: 'viewer' }
]

// Validation rules
const rules = {
  required: (v: any) => !!v || 'This field is required'
}

// Methods
function getInitials(user?: User): string {
  if (!user) return '?'
  if (user.firstName && user.lastName) {
    return `${user.firstName[0]}${user.lastName[0]}`.toUpperCase()
  }
  return user.username.substring(0, 2).toUpperCase()
}

function getDisplayName(user?: User): string {
  if (!user) return 'Unknown User'
  if (user.firstName || user.lastName) {
    return `${user.firstName || ''} ${user.lastName || ''}`.trim()
  }
  return user.username
}

function getAvatarColor(userId: string): string {
  const colors = ['primary', 'secondary', 'success', 'warning', 'error', 'info']
  const index = userId.charCodeAt(0) % colors.length
  return colors[index]
}

async function handleAddMember() {
  const { valid } = await form.value.validate()
  if (!valid || !selectedUserId.value) return

  isAdding.value = true
  try {
    const newMember = await projectsStore.addProjectMember(
      props.project.id,
      selectedUserId.value,
      selectedRole.value
    )

    // Add user data to the member
    const user = allUsers.value.find(u => u.id === selectedUserId.value)
    if (user) {
      newMember.user = user
    }

    members.value.push(newMember)
    selectedUserId.value = null
    selectedRole.value = 'member'
    form.value.reset()
    emit('updated')
  } catch (error) {
  } finally {
    isAdding.value = false
  }
}

async function handleUpdateRole(member: ProjectMember, newRole: string) {
  try {
    await projectsStore.updateProjectMember(props.project.id, member.userId, newRole)
    member.role = newRole as any
    emit('updated')
  } catch (error) {
  }
}

async function handleRemoveMember(member: ProjectMember) {
  try {
    await projectsStore.removeProjectMember(props.project.id, member.userId)
    members.value = members.value.filter(m => m.userId !== member.userId)
    emit('updated')
  } catch (error) {
  }
}

// Lifecycle
onMounted(async () => {
  // Fetch all users
  await usersStore.fetchUsers(1, 100)
  allUsers.value = usersStore.users

  // Fetch project members
  const projectMembers = await projectsStore.fetchProjectMembers(props.project.id)

  // Match members with user data
  members.value = projectMembers.map(member => {
    const user = allUsers.value.find(u => u.id === member.userId)
    return {
      ...member,
      user
    }
  })
})
</script>