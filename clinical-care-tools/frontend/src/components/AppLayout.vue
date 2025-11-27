<template>
  <v-app>
    <v-app-bar color="primary" prominent>
      <v-app-bar-nav-icon @click="drawer = !drawer" />

      <v-toolbar-title>
        <v-icon icon="mdi-hospital-box" class="mr-2"></v-icon>
        Clinical Care Tools
      </v-toolbar-title>

      <v-spacer />

      <v-badge v-if="authStore.user" color="success" dot>
        <v-btn icon>
          <v-icon>mdi-bell</v-icon>
        </v-btn>
      </v-badge>

      <v-menu v-if="authStore.user">
        <template #activator="{ props }">
          <v-btn icon v-bind="props">
            <v-avatar size="40">
              <v-icon>mdi-account-circle</v-icon>
            </v-avatar>
          </v-btn>
        </template>

        <v-list>
          <v-list-item>
            <v-list-item-title>{{ authStore.user.full_name }}</v-list-item-title>
            <v-list-item-subtitle>{{ authStore.user.email }}</v-list-item-subtitle>
          </v-list-item>

          <v-divider />

          <v-list-item prepend-icon="mdi-account" to="/profile"> Profile </v-list-item>

          <v-list-item prepend-icon="mdi-cog" to="/settings"> Settings </v-list-item>

          <v-divider />

          <v-list-item prepend-icon="mdi-logout" @click="handleLogout"> Logout </v-list-item>
        </v-list>
      </v-menu>
    </v-app-bar>

    <v-navigation-drawer v-model="drawer" app>
      <v-list>
        <v-list-item
          prepend-icon="mdi-view-dashboard"
          title="Dashboard"
          to="/dashboard"
        ></v-list-item>

        <v-list-item
          prepend-icon="mdi-account-search"
          title="Patient Search"
          to="/patients"
        ></v-list-item>

        <v-divider class="my-2" />

        <v-list-subheader>Tools</v-list-subheader>

        <v-list-item prepend-icon="mdi-file-document" title="Documents" to="/documents"></v-list-item>

        <v-list-item prepend-icon="mdi-chart-timeline-variant" title="Timeline" to="/timeline"></v-list-item>

        <v-list-item prepend-icon="mdi-database-search" title="Cohort Builder" to="/cohort"></v-list-item>

        <v-divider class="my-2" />

        <v-list-subheader v-if="authStore.userRole === 'admin'">Admin</v-list-subheader>

        <v-list-item
          v-if="authStore.userRole === 'admin'"
          prepend-icon="mdi-account-multiple"
          title="Users"
          to="/admin/users"
        ></v-list-item>

        <v-list-item
          v-if="authStore.userRole === 'admin'"
          prepend-icon="mdi-file-document-multiple"
          title="Audit Logs"
          to="/admin/audit"
        ></v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-main>
      <router-view />
    </v-main>

    <v-footer app>
      <v-spacer />
      <span class="text-caption">© 2025 Clinical Care Tools</span>
    </v-footer>
  </v-app>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const drawer = ref(true)

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>
