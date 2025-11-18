<template>
  <v-app>
    <v-app-bar app color="primary" dark v-if="isAuthenticated">
      <v-toolbar-title>
        <v-icon class="mr-2">mdi-hospital-building</v-icon>
        Clinical Care Tools
      </v-toolbar-title>

      <v-spacer />

      <v-btn to="/" exact>
        <v-icon start>mdi-home</v-icon>
        Home
      </v-btn>

      <v-btn to="/documents">
        <v-icon start>mdi-file-document-multiple</v-icon>
        Documents
      </v-btn>

      <v-btn to="/users" v-if="isAdmin">
        <v-icon start>mdi-account-group</v-icon>
        Users
      </v-btn>

      <v-btn to="/profile">
        <v-icon start>mdi-account</v-icon>
        Profile
      </v-btn>

      <v-btn @click="logout">
        <v-icon start>mdi-logout</v-icon>
        Logout
      </v-btn>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Check if user is authenticated
const isAuthenticated = computed(() => {
  return !!localStorage.getItem('access_token')
})

// Check if user is admin (simplified, should check user role from API)
const isAdmin = computed(() => {
  const role = localStorage.getItem('user_role')
  return role === 'admin'
})

// Logout function
const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('user_role')
  router.push({ name: 'login' })
}
</script>
