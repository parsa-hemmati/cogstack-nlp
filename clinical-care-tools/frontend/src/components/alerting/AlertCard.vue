<template>
  <v-card
    :class="[
      'alert-card',
      `severity-${alert.severity}`,
      { 'alert-selected': selected }
    ]"
    :elevation="selected ? 4 : 1"
  >
    <v-card-text class="d-flex align-center">
      <!-- Selection Checkbox -->
      <v-checkbox
        v-if="alert.status === 'new'"
        :model-value="selected"
        @update:model-value="$emit('toggle-select')"
        hide-details
        class="mr-2 flex-shrink-0"
      />

      <!-- Severity Icon -->
      <v-avatar
        :color="severityConfig.color"
        size="40"
        class="mr-4 flex-shrink-0"
      >
        <v-icon color="white" size="24">{{ severityConfig.icon }}</v-icon>
      </v-avatar>

      <!-- Content -->
      <div class="flex-grow-1 mr-4 overflow-hidden">
        <div class="d-flex align-center mb-1">
          <span class="text-subtitle-1 font-weight-medium mr-2 text-truncate">
            {{ alert.ruleName || 'Alert' }}
          </span>
          <v-chip
            :color="statusConfig.color"
            size="x-small"
            label
          >
            {{ statusConfig.label }}
          </v-chip>
        </div>

        <div class="text-body-2 text-grey-darken-1">
          <span v-if="alert.patientId">
            Patient: {{ alert.patientId.substring(0, 8) }}...
          </span>
          <span class="mx-2">•</span>
          <span>{{ formattedTime }}</span>
        </div>

        <div v-if="alert.notes" class="text-caption text-grey mt-1 text-truncate">
          {{ alert.notes }}
        </div>
      </div>

      <!-- Actions -->
      <div class="d-flex align-center flex-shrink-0">
        <v-btn
          v-if="alert.status === 'new'"
          icon
          size="small"
          variant="text"
          color="primary"
          @click.stop="$emit('acknowledge', alert.id)"
          title="Acknowledge"
        >
          <v-icon>mdi-check</v-icon>
        </v-btn>

        <v-btn
          v-if="alert.status === 'new' || alert.status === 'acknowledged'"
          icon
          size="small"
          variant="text"
          color="warning"
          @click.stop="$emit('snooze', alert.id)"
          title="Snooze"
        >
          <v-icon>mdi-clock-outline</v-icon>
        </v-btn>

        <v-btn
          v-if="alert.status !== 'dismissed'"
          icon
          size="small"
          variant="text"
          color="grey"
          @click.stop="showDismissDialog = true"
          title="Dismiss"
        >
          <v-icon>mdi-close</v-icon>
        </v-btn>

        <v-btn
          icon
          size="small"
          variant="text"
          @click.stop="$emit('view-details', alert)"
          title="View Details"
        >
          <v-icon>mdi-chevron-right</v-icon>
        </v-btn>
      </div>
    </v-card-text>

    <!-- Dismiss Dialog -->
    <v-dialog v-model="showDismissDialog" max-width="400">
      <v-card>
        <v-card-title>Dismiss Alert</v-card-title>
        <v-card-text>
          <v-textarea
            v-model="dismissNotes"
            label="Reason for dismissing"
            rows="3"
            placeholder="Optional: Enter reason for dismissing this alert"
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
import { formatDistanceToNow, parseISO } from 'date-fns';

const props = defineProps<{
  alert: TriggeredAlert;
  selected?: boolean;
}>();

const emit = defineEmits<{
  'toggle-select': [];
  acknowledge: [id: string];
  dismiss: [id: string, notes?: string];
  snooze: [id: string];
  'view-details': [alert: TriggeredAlert];
}>();

const showDismissDialog = ref(false);
const dismissNotes = ref('');

const severityConfig = computed(() => SEVERITY_CONFIG[props.alert.severity]);
const statusConfig = computed(() => STATUS_CONFIG[props.alert.status]);

const formattedTime = computed(() => {
  try {
    return formatDistanceToNow(parseISO(props.alert.triggeredAt), { addSuffix: true });
  } catch {
    return props.alert.triggeredAt;
  }
});

function confirmDismiss() {
  emit('dismiss', props.alert.id, dismissNotes.value || undefined);
  showDismissDialog.value = false;
  dismissNotes.value = '';
}
</script>

<style scoped>
.alert-card {
  border-left: 4px solid;
  transition: all 0.2s ease;
}

.alert-card.severity-critical {
  border-left-color: rgb(var(--v-theme-error));
}

.alert-card.severity-high {
  border-left-color: rgb(var(--v-theme-warning));
}

.alert-card.severity-medium {
  border-left-color: rgb(var(--v-theme-info));
}

.alert-card.severity-low {
  border-left-color: rgb(var(--v-theme-success));
}

.alert-card.alert-selected {
  background-color: rgba(var(--v-theme-primary), 0.08);
}

.alert-card:hover {
  transform: translateX(2px);
}
</style>
