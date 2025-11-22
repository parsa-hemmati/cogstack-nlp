<template>
  <v-footer app color="primary" dark>
    <v-row no-gutters align="center">
      <v-col cols="12" md="4">
        <div class="text-center text-md-left">
          &copy; {{ currentYear }} Clinical Care Tools
        </div>
      </v-col>

      <v-col cols="12" md="4">
        <div class="text-center">
          <v-btn
            v-for="link in footerLinks"
            :key="link.title"
            :href="link.href"
            variant="text"
            size="small"
            class="mx-2"
          >
            {{ link.title }}
          </v-btn>
        </div>
      </v-col>

      <v-col cols="12" md="4">
        <div class="text-center text-md-right">
          <span class="text-caption">
            Version {{ version }} |
            <span :class="statusColor">{{ systemStatus }}</span>
          </span>
        </div>
      </v-col>
    </v-row>
  </v-footer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Current year for copyright
const currentYear = computed(() => new Date().getFullYear())

// Application version
const version = import.meta.env.VITE_APP_VERSION || '0.1.0'

// System status
const systemStatus = ref('Operational')
const statusColor = computed(() => {
  switch (systemStatus.value) {
    case 'Operational':
      return 'text-success'
    case 'Degraded':
      return 'text-warning'
    case 'Offline':
      return 'text-error'
    default:
      return ''
  }
})

// Footer links
const footerLinks = [
  {
    title: 'Documentation',
    href: '/docs'
  },
  {
    title: 'Privacy Policy',
    href: '/privacy'
  },
  {
    title: 'Terms of Service',
    href: '/terms'
  },
  {
    title: 'Support',
    href: '/support'
  }
]
</script>