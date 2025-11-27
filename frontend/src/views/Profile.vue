<template>
  <v-container>
    <v-row>
      <!-- Profile Card -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>My Profile</v-card-title>
          <v-card-text>
            <v-form ref="profileForm" v-model="profileValid">
              <v-text-field
                v-model="profile.username"
                label="Username"
                disabled
                prepend-icon="mdi-account"
              ></v-text-field>

              <v-text-field
                v-model="profile.email"
                label="Email"
                type="email"
                prepend-icon="mdi-email"
                :rules="[rules.required, rules.email]"
              ></v-text-field>

              <v-text-field
                v-model="profile.role"
                label="Role"
                disabled
                prepend-icon="mdi-shield-account"
              ></v-text-field>

              <v-text-field
                v-model="profile.created_at"
                label="Member Since"
                disabled
                prepend-icon="mdi-calendar"
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="primary" @click="updateProfile" :disabled="!profileValid">
              Update Profile
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Change Password Card -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title>Change Password</v-card-title>
          <v-card-text>
            <v-form ref="passwordForm" v-model="passwordValid">
              <v-text-field
                v-model="passwordData.currentPassword"
                label="Current Password"
                type="password"
                prepend-icon="mdi-lock"
                :rules="[rules.required]"
              ></v-text-field>

              <v-text-field
                v-model="passwordData.newPassword"
                label="New Password"
                type="password"
                prepend-icon="mdi-lock-reset"
                :rules="[rules.required, rules.password]"
                hint="Min 12 chars, uppercase, lowercase, number, special char"
              ></v-text-field>

              <v-text-field
                v-model="passwordData.confirmPassword"
                label="Confirm New Password"
                type="password"
                prepend-icon="mdi-lock-check"
                :rules="[rules.required, rules.passwordMatch]"
              ></v-text-field>
            </v-form>
          </v-card-text>
          <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="warning" @click="changePassword" :disabled="!passwordValid">
              Change Password
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- Active Sessions -->
      <v-col cols="12">
        <v-card>
          <v-card-title>
            Active Sessions
            <v-spacer></v-spacer>
            <v-btn color="error" text @click="revokeAllSessions">
              Logout All Other Devices
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-list>
              <v-list-item v-for="session in sessions" :key="session.session_id">
                <v-list-item-content>
                  <v-list-item-title>
                    {{ session.user_agent || 'Unknown Device' }}
                    <v-chip v-if="session.is_current" color="primary" small class="ml-2">
                      Current Session
                    </v-chip>
                  </v-list-item-title>
                  <v-list-item-subtitle>
                    IP: {{ session.ip_address || 'Unknown' }} |
                    Created: {{ formatDate(session.created_at) }} |
                    Expires: {{ formatDate(session.expires_at) }}
                  </v-list-item-subtitle>
                </v-list-item-content>
                <v-list-item-action v-if="!session.is_current">
                  <v-btn icon small color="error" @click="revokeSession(session.session_id)">
                    <v-icon small>mdi-logout</v-icon>
                  </v-btn>
                </v-list-item-action>
              </v-list-item>
            </v-list>
            <v-alert v-if="sessions.length === 0" type="info" text>
              No active sessions
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row>
      <!-- Activity Log -->
      <v-col cols="12">
        <v-card>
          <v-card-title>Recent Activity</v-card-title>
          <v-card-text>
            <v-data-table
              :headers="activityHeaders"
              :items="activityLogs"
              :loading="activityLoading"
              :items-per-page="10"
              class="elevation-1"
            >
              <!-- Action Badge -->
              <template v-slot:item.action="{ item }">
                <v-chip :color="getActionColor(item.action)" small>
                  {{ item.action }}
                </v-chip>
              </template>

              <!-- Success Status -->
              <template v-slot:item.success="{ item }">
                <v-icon :color="item.success === 'success' ? 'success' : 'error'" small>
                  {{ item.success === 'success' ? 'mdi-check-circle' : 'mdi-alert-circle' }}
                </v-icon>
              </template>

              <!-- Timestamp -->
              <template v-slot:item.timestamp="{ item }">
                {{ formatDate(item.timestamp) }}
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Snackbar -->
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
import userService, { type User, type Session, type AuditLogEntry } from '@/services/userService'

export default defineComponent({
  name: 'Profile',

  setup() {
    // State
    const profile = ref<Partial<User>>({})
    const sessions = ref<Session[]>([])
    const activityLogs = ref<AuditLogEntry[]>([])
    const activityLoading = ref(false)
    const profileValid = ref(true)
    const passwordValid = ref(false)

    // Password form data
    const passwordData = reactive({
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    })

    // Snackbar
    const snackbar = reactive({
      show: false,
      message: '',
      color: 'success',
    })

    // Activity table headers
    const activityHeaders = [
      { title: 'Action', value: 'action' },
      { title: 'Resource', value: 'resource_type' },
      { title: 'Status', value: 'success' },
      { title: 'Timestamp', value: 'timestamp' },
      { title: 'IP Address', value: 'ip_address' },
    ]

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
      passwordMatch: (v: string) =>
        v === passwordData.newPassword || 'Passwords must match',
    }

    // Methods
    const loadProfile = async () => {
      try {
        profile.value = await userService.getMyProfile()
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to load profile', 'error')
      }
    }

    const loadSessions = async () => {
      try {
        const response = await userService.getMySessions()
        sessions.value = response.sessions
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to load sessions', 'error')
      }
    }

    const loadActivityLog = async () => {
      if (!profile.value.id) return

      activityLoading.value = true
      try {
        const response = await userService.getUserActivity(profile.value.id, 1, 10)
        activityLogs.value = response.items
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to load activity log', 'error')
      } finally {
        activityLoading.value = false
      }
    }

    const updateProfile = async () => {
      if (!profileValid.value || !profile.value.email) return

      try {
        profile.value = await userService.updateMyProfile(profile.value.email)
        showSnackbar('Profile updated successfully', 'success')
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to update profile', 'error')
      }
    }

    const changePassword = async () => {
      if (!passwordValid.value) return

      try {
        await userService.changePassword(
          passwordData.currentPassword,
          passwordData.newPassword
        )
        showSnackbar(
          'Password changed successfully. All other sessions have been logged out.',
          'success'
        )
        // Clear form
        passwordData.currentPassword = ''
        passwordData.newPassword = ''
        passwordData.confirmPassword = ''
        // Reload sessions (all should be invalidated except current)
        loadSessions()
      } catch (error: any) {
        showSnackbar(error.response?.data?.detail || 'Failed to change password', 'error')
      }
    }

    const revokeSession = async (sessionId: string) => {
      if (confirm('Logout from this device?')) {
        try {
          await userService.revokeSession(sessionId)
          showSnackbar('Session revoked successfully', 'success')
          loadSessions()
        } catch (error: any) {
          showSnackbar(error.response?.data?.detail || 'Failed to revoke session', 'error')
        }
      }
    }

    const revokeAllSessions = async () => {
      if (confirm('Logout from all other devices? Your current session will remain active.')) {
        try {
          await userService.revokeAllSessions()
          showSnackbar('All other sessions revoked successfully', 'success')
          loadSessions()
        } catch (error: any) {
          showSnackbar(error.response?.data?.detail || 'Failed to revoke sessions', 'error')
        }
      }
    }

    const formatDate = (dateStr: string) => {
      return new Date(dateStr).toLocaleString()
    }

    const getActionColor = (action: string) => {
      if (action.includes('LOGIN')) return 'success'
      if (action.includes('LOGOUT')) return 'info'
      if (action.includes('CHANGE_PASSWORD')) return 'warning'
      if (action.includes('FAILED')) return 'error'
      return 'default'
    }

    const showSnackbar = (message: string, color: string) => {
      snackbar.message = message
      snackbar.color = color
      snackbar.show = true
    }

    // Load data on mount
    onMounted(async () => {
      await loadProfile()
      await loadSessions()
      await loadActivityLog()
    })

    return {
      profile,
      sessions,
      activityLogs,
      activityLoading,
      profileValid,
      passwordValid,
      passwordData,
      activityHeaders,
      rules,
      snackbar,
      updateProfile,
      changePassword,
      revokeSession,
      revokeAllSessions,
      formatDate,
      getActionColor,
    }
  },
})
</script>

<style scoped>
.v-card {
  margin-bottom: 24px;
}
</style>
