<template>
  <div class="alert-list">
    <!-- Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" sm="3">
            <v-select
              v-model="localFilters.status"
              :items="statusOptions"
              label="Status"
              clearable
              density="compact"
              @update:model-value="applyFilters"
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-select
              v-model="localFilters.severity"
              :items="severityOptions"
              label="Severity"
              clearable
              density="compact"
              @update:model-value="applyFilters"
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-text-field
              v-model="localFilters.patientId"
              label="Patient ID"
              clearable
              density="compact"
              @update:model-value="debouncedApply"
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-btn
              color="primary"
              variant="outlined"
              @click="fetchAlerts"
              :loading="loading"
            >
              <v-icon left>mdi-refresh</v-icon>
              Refresh
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Bulk Actions -->
    <v-card v-if="selectedAlerts.length > 0" class="mb-4">
      <v-card-text class="d-flex align-center">
        <span class="mr-4">{{ selectedAlerts.length }} selected</span>
        <v-btn
          color="primary"
          size="small"
          class="mr-2"
          @click="bulkAcknowledge"
          :loading="bulkLoading"
        >
          <v-icon left size="small">mdi-check-all</v-icon>
          Acknowledge All
        </v-btn>
        <v-btn
          variant="text"
          size="small"
          @click="selectedAlerts = []"
        >
          Clear Selection
        </v-btn>
      </v-card-text>
    </v-card>

    <!-- Alert Cards -->
    <v-card v-if="alerts.length === 0 && !loading">
      <v-card-text class="text-center py-8">
        <v-icon size="64" color="grey-lighten-1">mdi-bell-off</v-icon>
        <p class="text-h6 mt-4 text-grey">No alerts found</p>
      </v-card-text>
    </v-card>

    <div v-else>
      <alert-card
        v-for="alert in alerts"
        :key="alert.id"
        :alert="alert"
        :selected="selectedAlerts.includes(alert.id)"
        @toggle-select="toggleSelect(alert.id)"
        @acknowledge="handleAcknowledge"
        @dismiss="handleDismiss"
        @snooze="handleSnooze"
        @view-details="$emit('view-details', alert)"
        class="mb-2"
      />
    </div>

    <!-- Loading -->
    <v-progress-linear v-if="loading" indeterminate color="primary" />

    <!-- Load More -->
    <div v-if="hasMore && !loading" class="text-center mt-4">
      <v-btn
        variant="outlined"
        @click="loadMore"
      >
        Load More
      </v-btn>
    </div>

    <!-- Snooze Dialog -->
    <v-dialog v-model="snoozeDialog" max-width="400">
      <v-card>
        <v-card-title>Snooze Alert</v-card-title>
        <v-card-text>
          <v-select
            v-model="snoozeMinutes"
            :items="snoozeOptions"
            label="Snooze duration"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="snoozeDialog = false">Cancel</v-btn>
          <v-btn color="primary" @click="confirmSnooze">Snooze</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useAlertStore } from '@/stores/alertStore';
import { storeToRefs } from 'pinia';
import type { AlertFilters, TriggeredAlert } from '@/types/alerting';
import AlertCard from './AlertCard.vue';
import { useDebounceFn } from '@vueuse/core';

const emit = defineEmits<{
  'view-details': [alert: TriggeredAlert];
}>();

const alertStore = useAlertStore();
const { alerts, loading, pagination } = storeToRefs(alertStore);
const hasMore = computed(() => pagination.value.hasMore);

const selectedAlerts = ref<string[]>([]);
const bulkLoading = ref(false);
const snoozeDialog = ref(false);
const snoozeMinutes = ref(30);
const snoozeAlertId = ref<string | null>(null);

const localFilters = ref<AlertFilters>({
  status: undefined,
  severity: undefined,
  patientId: undefined,
});

const statusOptions = [
  { title: 'New', value: 'new' },
  { title: 'Acknowledged', value: 'acknowledged' },
  { title: 'Dismissed', value: 'dismissed' },
  { title: 'Snoozed', value: 'snoozed' },
];

const severityOptions = [
  { title: 'Critical', value: 'critical' },
  { title: 'High', value: 'high' },
  { title: 'Medium', value: 'medium' },
  { title: 'Low', value: 'low' },
];

const snoozeOptions = [
  { title: '15 minutes', value: 15 },
  { title: '30 minutes', value: 30 },
  { title: '1 hour', value: 60 },
  { title: '4 hours', value: 240 },
  { title: '8 hours', value: 480 },
  { title: '24 hours', value: 1440 },
];

onMounted(() => {
  fetchAlerts();
});

async function fetchAlerts() {
  await alertStore.fetchAlerts(localFilters.value);
}

function applyFilters() {
  alertStore.fetchAlerts(localFilters.value);
}

const debouncedApply = useDebounceFn(applyFilters, 500);

async function loadMore() {
  await alertStore.loadMoreAlerts();
}

function toggleSelect(alertId: string) {
  const index = selectedAlerts.value.indexOf(alertId);
  if (index === -1) {
    selectedAlerts.value.push(alertId);
  } else {
    selectedAlerts.value.splice(index, 1);
  }
}

async function handleAcknowledge(alertId: string) {
  await alertStore.acknowledgeAlert(alertId);
}

async function handleDismiss(alertId: string, notes?: string) {
  await alertStore.dismissAlert(alertId, notes);
}

function handleSnooze(alertId: string) {
  snoozeAlertId.value = alertId;
  snoozeDialog.value = true;
}

async function confirmSnooze() {
  if (snoozeAlertId.value) {
    await alertStore.snoozeAlert(snoozeAlertId.value, snoozeMinutes.value);
    snoozeDialog.value = false;
    snoozeAlertId.value = null;
  }
}

async function bulkAcknowledge() {
  bulkLoading.value = true;
  try {
    await alertStore.bulkAcknowledge(selectedAlerts.value);
    selectedAlerts.value = [];
  } finally {
    bulkLoading.value = false;
  }
}
</script>

<style scoped>
.alert-list {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
