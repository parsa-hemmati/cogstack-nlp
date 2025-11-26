<template>
  <v-card class="alert-details-card">
    <v-card-title class="d-flex align-center">
      <v-icon :color="severityConfig.color" class="mr-2">
        {{ severityConfig.icon }}
      </v-icon>
      <span>Alert Details</span>
      <v-spacer />
      <v-chip :color="statusConfig.color" size="small" label>
        {{ statusConfig.label }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <!-- Alert Info -->
      <v-list density="compact" class="bg-transparent">
        <v-list-item>
          <template #prepend>
            <v-icon size="small">mdi-bell</v-icon>
          </template>
          <v-list-item-title>Rule</v-list-item-title>
          <v-list-item-subtitle>{{ alert.ruleName || alert.ruleId }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item v-if="alert.patientId">
          <template #prepend>
            <v-icon size="small">mdi-account</v-icon>
          </template>
          <v-list-item-title>Patient ID</v-list-item-title>
          <v-list-item-subtitle>{{ alert.patientId }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item>
          <template #prepend>
            <v-icon size="small">mdi-clock</v-icon>
          </template>
          <v-list-item-title>Triggered</v-list-item-title>
          <v-list-item-subtitle>{{ formattedTriggeredAt }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item v-if="alert.acknowledgedAt">
          <template #prepend>
            <v-icon size="small">mdi-check</v-icon>
          </template>
          <v-list-item-title>Acknowledged</v-list-item-title>
          <v-list-item-subtitle>{{ formattedAcknowledgedAt }}</v-list-item-subtitle>
        </v-list-item>

        <v-list-item v-if="alert.snoozeUntil">
          <template #prepend>
            <v-icon size="small">mdi-clock-outline</v-icon>
          </template>
          <v-list-item-title>Snoozed Until</v-list-item-title>
          <v-list-item-subtitle>{{ formattedSnoozeUntil }}</v-list-item-subtitle>
        </v-list-item>
      </v-list>

      <!-- Trigger Data -->
      <div v-if="alert.triggerData" class="mt-4">
        <div class="text-subtitle-2 mb-2">Trigger Data</div>
        <v-card variant="outlined" class="pa-2">
          <pre class="text-caption">{{ JSON.stringify(alert.triggerData, null, 2) }}</pre>
        </v-card>
      </div>

      <!-- Notes -->
      <div v-if="alert.notes" class="mt-4">
        <div class="text-subtitle-2 mb-2">Notes</div>
        <p class="text-body-2">{{ alert.notes }}</p>
      </div>
    </v-card-text>

    <v-divider />

    <v-card-actions>
      <v-btn text @click="$emit('close')">Close</v-btn>
      <v-spacer />

      <v-btn
        v-if="alert.status === 'new'"
        color="primary"
        variant="elevated"
        @click="$emit('acknowledge', alert.id)"
      >
        <v-icon left>mdi-check</v-icon>
        Acknowledge
      </v-btn>

      <v-menu v-if="alert.status !== 'dismissed'">
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            color="warning"
            variant="outlined"
          >
            <v-icon left>mdi-clock</v-icon>
            Snooze
          </v-btn>
        </template>
        <v-list density="compact">
          <v-list-item
            v-for="option in snoozeOptions"
            :key="option.value"
            @click="$emit('snooze', alert.id, option.value)"
          >
            <v-list-item-title>{{ option.title }}</v-list-item-title>
          </v-list-item>
        </v-list>
      </v-menu>

      <v-btn
        v-if="alert.status !== 'dismissed'"
        color="grey"
        variant="outlined"
        @click="showDismissDialog = true"
      >
        <v-icon left>mdi-close</v-icon>
        Dismiss
      </v-btn>
    </v-card-actions>

    <!-- Dismiss Dialog -->
    <v-dialog v-model="showDismissDialog" max-width="400">
      <v-card>
        <v-card-title>Dismiss Alert</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="dismissNotes"
            label="Reason for dismissing"
            rows="3"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showDismissDialog = false">Cancel</v-btn>
          <v-btn color="error" @click="confirmDismiss">Dismiss</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { TriggeredAlert } from '@/types/alerting';
import { SEVERITY_CONFIG, STATUS_CONFIG } from '@/types/alerting';
import { format, parseISO } from 'date-fns';

const props = defineProps<{
  alert: TriggeredAlert;
}>();

const emit = defineEmits<{
  close: [];
  acknowledge: [id: string];
  dismiss: [id: string, notes?: string];
  snooze: [id: string, minutes: number];
}>();

const showDismissDialog = ref(false);
const dismissNotes = ref('');

const severityConfig = computed(() => SEVERITY_CONFIG[props.alert.severity]);
const statusConfig = computed(() => STATUS_CONFIG[props.alert.status]);

const snoozeOptions = [
  { title: '15 minutes', value: 15 },
  { title: '30 minutes', value: 30 },
  { title: '1 hour', value: 60 },
  { title: '4 hours', value: 240 },
  { title: '8 hours', value: 480 },
];

const formattedTriggeredAt = computed(() => formatDateTime(props.alert.triggeredAt));
const formattedAcknowledgedAt = computed(() =>
  props.alert.acknowledgedAt ? formatDateTime(props.alert.acknowledgedAt) : ''
);
const formattedSnoozeUntil = computed(() =>
  props.alert.snoozeUntil ? formatDateTime(props.alert.snoozeUntil) : ''
);

function formatDateTime(date: string): string {
  try {
    return format(parseISO(date), 'MMM d, yyyy HH:mm:ss');
  } catch {
    return date;
  }
}

function confirmDismiss() {
  emit('dismiss', props.alert.id, dismissNotes.value || undefined);
  showDismissDialog.value = false;
}
</script>

<style scoped>
pre {
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  font-family: monospace;
}
</style>
