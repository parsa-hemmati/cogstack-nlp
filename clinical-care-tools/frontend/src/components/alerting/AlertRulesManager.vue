<template>
  <div class="alert-rules-manager">
    <!-- Search and Filters -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row dense>
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="search"
              prepend-inner-icon="mdi-magnify"
              label="Search rules"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-select
              v-model="severityFilter"
              :items="severityOptions"
              label="Severity"
              density="compact"
              clearable
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-select
              v-model="enabledFilter"
              :items="enabledOptions"
              label="Status"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="2" class="d-flex align-center">
            <v-btn icon variant="text" @click="fetchRules">
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Rules Table -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="filteredRules"
        :loading="loading"
        :search="search"
        item-value="id"
        hover
      >
        <!-- Name Column -->
        <template #item.name="{ item }">
          <div class="d-flex align-center">
            <v-icon
              :color="severityColors[item.severity]"
              size="small"
              class="mr-2"
            >
              mdi-alert-circle
            </v-icon>
            <span class="font-weight-medium">{{ item.name }}</span>
          </div>
        </template>

        <!-- Severity Column -->
        <template #item.severity="{ item }">
          <v-chip
            :color="severityColors[item.severity]"
            size="small"
            label
          >
            {{ item.severity }}
          </v-chip>
        </template>

        <!-- Channels Column -->
        <template #item.notificationChannels="{ item }">
          <div class="d-flex gap-1">
            <v-icon
              v-if="item.notificationChannels.includes('in_app')"
              size="small"
              title="In-App"
            >
              mdi-bell
            </v-icon>
            <v-icon
              v-if="item.notificationChannels.includes('email')"
              size="small"
              title="Email"
            >
              mdi-email
            </v-icon>
            <v-icon
              v-if="item.notificationChannels.includes('sms')"
              size="small"
              title="SMS"
            >
              mdi-message-text
            </v-icon>
          </div>
        </template>

        <!-- Enabled Column -->
        <template #item.enabled="{ item }">
          <v-switch
            :model-value="item.enabled"
            color="primary"
            hide-details
            density="compact"
            @update:model-value="toggleEnabled(item)"
          />
        </template>

        <!-- Actions Column -->
        <template #item.actions="{ item }">
          <v-btn
            icon
            variant="text"
            size="small"
            @click="$emit('edit-rule', item)"
          >
            <v-icon>mdi-pencil</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            @click="viewVersions(item)"
          >
            <v-icon>mdi-history</v-icon>
          </v-btn>
          <v-btn
            icon
            variant="text"
            size="small"
            color="error"
            @click="confirmDelete(item)"
          >
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </template>
      </v-data-table>
    </v-card>

    <!-- Version History Dialog -->
    <v-dialog v-model="showVersions" max-width="700">
      <v-card>
        <v-card-title>
          Version History: {{ selectedRuleForVersions?.name }}
        </v-card-title>
        <v-card-text>
          <v-timeline density="compact" side="end">
            <v-timeline-item
              v-for="version in ruleVersions"
              :key="version.id"
              dot-color="primary"
              size="small"
            >
              <template #opposite>
                <span class="text-caption text-grey">
                  v{{ version.version }}
                </span>
              </template>
              <v-card variant="outlined" density="compact">
                <v-card-text class="py-2">
                  <div class="text-caption text-grey">
                    {{ formatDate(version.changedAt) }}
                  </div>
                  <div v-if="version.changeReason" class="text-body-2 mt-1">
                    {{ version.changeReason }}
                  </div>
                </v-card-text>
              </v-card>
            </v-timeline-item>
          </v-timeline>
          <div v-if="ruleVersions.length === 0" class="text-center py-4 text-grey">
            No version history available
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showVersions = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Delete Confirmation Dialog -->
    <v-dialog v-model="showDeleteConfirm" max-width="400">
      <v-card>
        <v-card-title>Delete Rule</v-card-title>
        <v-card-text>
          Are you sure you want to delete the rule "{{ ruleToDelete?.name }}"?
          This action cannot be undone.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showDeleteConfirm = false">Cancel</v-btn>
          <v-btn color="error" @click="deleteRule">Delete</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useAlertStore } from '@/stores/alertStore';
import { storeToRefs } from 'pinia';
import type { AlertRule, AlertRuleVersion } from '@/types/alerting';
import { alertApi } from '@/api/alertApi';
import { format, parseISO } from 'date-fns';

const emit = defineEmits<{
  'edit-rule': [rule: AlertRule];
}>();

const alertStore = useAlertStore();
const { rules, loading } = storeToRefs(alertStore);

const search = ref('');
const severityFilter = ref<string | null>(null);
const enabledFilter = ref<boolean | null>(null);
const showVersions = ref(false);
const showDeleteConfirm = ref(false);
const selectedRuleForVersions = ref<AlertRule | null>(null);
const ruleVersions = ref<AlertRuleVersion[]>([]);
const ruleToDelete = ref<AlertRule | null>(null);

const headers = [
  { title: 'Name', key: 'name', sortable: true },
  { title: 'Severity', key: 'severity', sortable: true, width: 120 },
  { title: 'Channels', key: 'notificationChannels', sortable: false, width: 100 },
  { title: 'Enabled', key: 'enabled', sortable: true, width: 100 },
  { title: 'Actions', key: 'actions', sortable: false, width: 140 },
];

const severityOptions = [
  { title: 'Critical', value: 'critical' },
  { title: 'High', value: 'high' },
  { title: 'Medium', value: 'medium' },
  { title: 'Low', value: 'low' },
];

const enabledOptions = [
  { title: 'All', value: null },
  { title: 'Enabled', value: true },
  { title: 'Disabled', value: false },
];

const severityColors: Record<string, string> = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'success',
};

const filteredRules = computed(() => {
  let result = rules.value;

  if (severityFilter.value) {
    result = result.filter((r) => r.severity === severityFilter.value);
  }

  if (enabledFilter.value !== null) {
    result = result.filter((r) => r.enabled === enabledFilter.value);
  }

  return result;
});

onMounted(() => {
  fetchRules();
});

async function fetchRules() {
  await alertStore.fetchRules();
}

async function toggleEnabled(rule: AlertRule) {
  await alertStore.updateRule(rule.id, { enabled: !rule.enabled });
}

async function viewVersions(rule: AlertRule) {
  selectedRuleForVersions.value = rule;
  try {
    ruleVersions.value = await alertApi.getRuleVersions(rule.id);
  } catch (err) {
    console.error('Failed to fetch versions:', err);
    ruleVersions.value = [];
  }
  showVersions.value = true;
}

function confirmDelete(rule: AlertRule) {
  ruleToDelete.value = rule;
  showDeleteConfirm.value = true;
}

async function deleteRule() {
  if (ruleToDelete.value) {
    await alertStore.deleteRule(ruleToDelete.value.id);
    showDeleteConfirm.value = false;
    ruleToDelete.value = null;
  }
}

function formatDate(date: string): string {
  try {
    return format(parseISO(date), 'MMM d, yyyy HH:mm');
  } catch {
    return date;
  }
}
</script>
