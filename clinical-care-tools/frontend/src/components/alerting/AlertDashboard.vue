<template>
  <div class="alert-dashboard">
    <!-- Summary Cards -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3">
        <v-card color="error" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="error" class="mr-4" size="48">
              <v-icon color="white" size="28">mdi-alert-circle</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">
                {{ statistics?.criticalUnacknowledged ?? 0 }}
              </div>
              <div class="text-caption">Critical Alerts</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="warning" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="warning" class="mr-4" size="48">
              <v-icon color="white" size="28">mdi-bell-ring</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">
                {{ statistics?.unacknowledgedCount ?? 0 }}
              </div>
              <div class="text-caption">Unacknowledged</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="info" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="info" class="mr-4" size="48">
              <v-icon color="white" size="28">mdi-clock-fast</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">
                {{ formattedResponseTime }}
              </div>
              <div class="text-caption">Avg Response</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" sm="6" md="3">
        <v-card color="success" variant="tonal">
          <v-card-text class="d-flex align-center">
            <v-avatar color="success" class="mr-4" size="48">
              <v-icon color="white" size="28">mdi-check-all</v-icon>
            </v-avatar>
            <div>
              <div class="text-h4 font-weight-bold">
                {{ statistics?.totalAlerts ?? 0 }}
              </div>
              <div class="text-caption">Total Alerts</div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Charts Row -->
    <v-row class="mb-4">
      <!-- By Severity -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="text-subtitle-1">Alerts by Severity</v-card-title>
          <v-card-text>
            <div v-if="statistics" class="d-flex flex-column gap-2">
              <div
                v-for="severity in severityOrder"
                :key="severity"
                class="d-flex align-center"
              >
                <div class="severity-label text-body-2" style="width: 80px">
                  {{ severity }}
                </div>
                <v-progress-linear
                  :model-value="getSeverityPercent(severity)"
                  :color="severityColors[severity]"
                  height="24"
                  class="flex-grow-1 mx-2"
                  rounded
                >
                  <template #default>
                    <span class="text-caption font-weight-bold">
                      {{ statistics.bySeverity[severity] ?? 0 }}
                    </span>
                  </template>
                </v-progress-linear>
              </div>
            </div>
            <v-skeleton-loader v-else type="list-item@4" />
          </v-card-text>
        </v-card>
      </v-col>

      <!-- By Status -->
      <v-col cols="12" md="6">
        <v-card>
          <v-card-title class="text-subtitle-1">Alerts by Status</v-card-title>
          <v-card-text>
            <div v-if="statistics" class="d-flex flex-column gap-2">
              <div
                v-for="status in statusOrder"
                :key="status"
                class="d-flex align-center"
              >
                <div class="status-label text-body-2" style="width: 100px">
                  {{ status }}
                </div>
                <v-progress-linear
                  :model-value="getStatusPercent(status)"
                  :color="statusColors[status]"
                  height="24"
                  class="flex-grow-1 mx-2"
                  rounded
                >
                  <template #default>
                    <span class="text-caption font-weight-bold">
                      {{ statistics.byStatus[status] ?? 0 }}
                    </span>
                  </template>
                </v-progress-linear>
              </div>
            </div>
            <v-skeleton-loader v-else type="list-item@4" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- Recent Critical Alerts -->
    <v-card>
      <v-card-title class="d-flex align-center">
        <span class="text-subtitle-1">Recent Critical Alerts</span>
        <v-spacer />
        <v-btn
          variant="text"
          color="primary"
          size="small"
          @click="$emit('view-all')"
        >
          View All
        </v-btn>
      </v-card-title>
      <v-card-text>
        <v-list v-if="criticalAlerts.length > 0" density="compact">
          <v-list-item
            v-for="alert in criticalAlerts.slice(0, 5)"
            :key="alert.id"
            @click="$emit('view-alert', alert)"
          >
            <template #prepend>
              <v-icon color="error">mdi-alert-circle</v-icon>
            </template>
            <v-list-item-title>
              {{ alert.ruleName || 'Alert' }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ formatTime(alert.triggeredAt) }}
            </v-list-item-subtitle>
            <template #append>
              <v-btn
                icon
                size="small"
                variant="text"
                color="primary"
                @click.stop="$emit('acknowledge', alert.id)"
              >
                <v-icon>mdi-check</v-icon>
              </v-btn>
            </template>
          </v-list-item>
        </v-list>
        <div v-else class="text-center py-4 text-grey">
          <v-icon size="48" color="grey-lighten-1">mdi-check-circle</v-icon>
          <p class="mt-2">No critical alerts</p>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useAlertStore } from '@/stores/alertStore';
import { storeToRefs } from 'pinia';
import type { TriggeredAlert } from '@/types/alerting';
import { formatDistanceToNow, parseISO } from 'date-fns';

const emit = defineEmits<{
  'view-all': [];
  'view-alert': [alert: TriggeredAlert];
  acknowledge: [id: string];
}>();

const alertStore = useAlertStore();
const { statistics, criticalAlerts } = storeToRefs(alertStore);

const severityOrder = ['critical', 'high', 'medium', 'low'] as const;
const statusOrder = ['new', 'acknowledged', 'snoozed', 'dismissed'] as const;

const severityColors: Record<string, string> = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'success',
};

const statusColors: Record<string, string> = {
  new: 'error',
  acknowledged: 'info',
  snoozed: 'warning',
  dismissed: 'grey',
};

const formattedResponseTime = computed(() => {
  if (!statistics.value) return '-';
  const seconds = statistics.value.avgResponseTimeSeconds;
  if (seconds < 60) return `${Math.round(seconds)}s`;
  if (seconds < 3600) return `${Math.round(seconds / 60)}m`;
  return `${Math.round(seconds / 3600)}h`;
});

onMounted(() => {
  alertStore.fetchStatistics();
  alertStore.fetchAlerts({ severity: 'critical', status: 'new' });
});

function getSeverityPercent(severity: string): number {
  if (!statistics.value || statistics.value.totalAlerts === 0) return 0;
  return ((statistics.value.bySeverity[severity] ?? 0) / statistics.value.totalAlerts) * 100;
}

function getStatusPercent(status: string): number {
  if (!statistics.value || statistics.value.totalAlerts === 0) return 0;
  return ((statistics.value.byStatus[status] ?? 0) / statistics.value.totalAlerts) * 100;
}

function formatTime(time: string): string {
  try {
    return formatDistanceToNow(parseISO(time), { addSuffix: true });
  } catch {
    return time;
  }
}
</script>

<style scoped>
.alert-dashboard {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
