<template>
  <div class="alerts-view pa-4">
    <v-container fluid>
      <!-- Header -->
      <div class="d-flex align-center mb-4">
        <div>
          <h1 class="text-h4 font-weight-bold">Alert Management</h1>
          <p class="text-body-2 text-grey">
            Monitor and manage clinical alerts across your organization
          </p>
        </div>
        <v-spacer />
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="showRuleEditor = true"
        >
          Create Rule
        </v-btn>
      </div>

      <!-- Tabs -->
      <v-tabs v-model="activeTab" class="mb-4">
        <v-tab value="dashboard">
          <v-icon start>mdi-view-dashboard</v-icon>
          Dashboard
        </v-tab>
        <v-tab value="alerts">
          <v-icon start>mdi-bell</v-icon>
          Alerts
          <v-badge
            v-if="newAlertCount > 0"
            :content="newAlertCount"
            color="error"
            inline
            class="ml-2"
          />
        </v-tab>
        <v-tab value="rules">
          <v-icon start>mdi-cog</v-icon>
          Rules
        </v-tab>
        <v-tab value="preferences">
          <v-icon start>mdi-account-cog</v-icon>
          Preferences
        </v-tab>
      </v-tabs>

      <!-- Tab Content -->
      <v-window v-model="activeTab">
        <!-- Dashboard Tab -->
        <v-window-item value="dashboard">
          <alert-dashboard
            @view-all="activeTab = 'alerts'"
            @view-alert="viewAlertDetails"
            @acknowledge="handleAcknowledge"
          />
        </v-window-item>

        <!-- Alerts Tab -->
        <v-window-item value="alerts">
          <alert-list
            @view-details="viewAlertDetails"
          />
        </v-window-item>

        <!-- Rules Tab -->
        <v-window-item value="rules">
          <alert-rules-manager
            @edit-rule="editRule"
          />
        </v-window-item>

        <!-- Preferences Tab -->
        <v-window-item value="preferences">
          <notification-preferences-form />
        </v-window-item>
      </v-window>

      <!-- Rule Editor Dialog -->
      <v-dialog v-model="showRuleEditor" max-width="800" persistent>
        <alert-rule-editor
          :rule="selectedRule"
          @cancel="closeRuleEditor"
          @saved="handleRuleSaved"
        />
      </v-dialog>

      <!-- Alert Details Dialog -->
      <v-dialog v-model="showAlertDetails" max-width="600">
        <alert-details-card
          v-if="selectedAlert"
          :alert="selectedAlert"
          @close="showAlertDetails = false"
          @acknowledge="handleAcknowledge"
          @dismiss="handleDismiss"
          @snooze="handleSnooze"
        />
      </v-dialog>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useAlertStore } from '@/stores/alertStore';
import { storeToRefs } from 'pinia';
import type { AlertRule, TriggeredAlert } from '@/types/alerting';
import AlertDashboard from '@/components/alerting/AlertDashboard.vue';
import AlertList from '@/components/alerting/AlertList.vue';
import AlertRuleEditor from '@/components/alerting/AlertRuleEditor.vue';
import AlertRulesManager from '@/components/alerting/AlertRulesManager.vue';
import AlertDetailsCard from '@/components/alerting/AlertDetailsCard.vue';
import NotificationPreferencesForm from '@/components/alerting/NotificationPreferencesForm.vue';

const alertStore = useAlertStore();
const { newAlerts } = storeToRefs(alertStore);

const activeTab = ref('dashboard');
const showRuleEditor = ref(false);
const showAlertDetails = ref(false);
const selectedRule = ref<AlertRule | undefined>();
const selectedAlert = ref<TriggeredAlert | null>(null);

const newAlertCount = computed(() => newAlerts.value.length);

let refreshInterval: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
  // Initial data fetch
  alertStore.fetchRules();
  alertStore.fetchAlerts();
  alertStore.fetchStatistics();
  alertStore.fetchPreferences();

  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(() => {
    alertStore.fetchAlerts();
    alertStore.fetchStatistics();
  }, 30000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
  alertStore.reset();
});

function editRule(rule: AlertRule) {
  selectedRule.value = rule;
  showRuleEditor.value = true;
}

function closeRuleEditor() {
  selectedRule.value = undefined;
  showRuleEditor.value = false;
}

function handleRuleSaved() {
  closeRuleEditor();
  alertStore.fetchRules();
}

function viewAlertDetails(alert: TriggeredAlert) {
  selectedAlert.value = alert;
  showAlertDetails.value = true;
}

async function handleAcknowledge(alertId: string) {
  await alertStore.acknowledgeAlert(alertId);
  showAlertDetails.value = false;
}

async function handleDismiss(alertId: string, notes?: string) {
  await alertStore.dismissAlert(alertId, notes);
  showAlertDetails.value = false;
}

async function handleSnooze(alertId: string, minutes: number) {
  await alertStore.snoozeAlert(alertId, minutes);
  showAlertDetails.value = false;
}
</script>

<style scoped>
.alerts-view {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-background));
}
</style>
