/**
 * Pinia store for Alert Management - Sprint 7
 */
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type {
  AlertRule,
  AlertRuleCreate,
  AlertRuleUpdate,
  TriggeredAlert,
  AlertFilters,
  AlertStatistics,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  RuleTestResult,
} from '@/types/alerting';
import { alertApi } from '@/api/alertApi';

export const useAlertStore = defineStore('alerts', () => {
  // State
  const rules = ref<AlertRule[]>([]);
  const alerts = ref<TriggeredAlert[]>([]);
  const statistics = ref<AlertStatistics | null>(null);
  const preferences = ref<NotificationPreferences | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);

  // Filters & pagination
  const filters = ref<AlertFilters>({});
  const pagination = ref({
    limit: 20,
    offset: 0,
    total: 0,
    hasMore: false,
  });

  // Computed
  const activeRules = computed(() => rules.value.filter((r) => r.enabled));

  const newAlerts = computed(() => alerts.value.filter((a) => a.status === 'new'));

  const criticalAlerts = computed(() =>
    alerts.value.filter((a) => a.severity === 'critical' && a.status === 'new')
  );

  const alertsByStatus = computed(() => {
    const grouped: Record<string, TriggeredAlert[]> = {
      new: [],
      acknowledged: [],
      dismissed: [],
      snoozed: [],
    };
    alerts.value.forEach((a) => {
      if (grouped[a.status]) {
        grouped[a.status].push(a);
      }
    });
    return grouped;
  });

  // Actions - Rules
  async function fetchRules(enabledOnly = false) {
    loading.value = true;
    error.value = null;
    try {
      const response = await alertApi.listRules({ enabledOnly });
      rules.value = response;
    } catch (err) {
      error.value = 'Failed to fetch alert rules';
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  async function createRule(ruleData: AlertRuleCreate): Promise<AlertRule | null> {
    loading.value = true;
    error.value = null;
    try {
      const newRule = await alertApi.createRule(ruleData);
      rules.value.push(newRule);
      return newRule;
    } catch (err) {
      error.value = 'Failed to create alert rule';
      console.error(err);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function updateRule(
    ruleId: string,
    updates: AlertRuleUpdate
  ): Promise<AlertRule | null> {
    loading.value = true;
    error.value = null;
    try {
      const updated = await alertApi.updateRule(ruleId, updates);
      const index = rules.value.findIndex((r) => r.id === ruleId);
      if (index !== -1) {
        rules.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = 'Failed to update alert rule';
      console.error(err);
      return null;
    } finally {
      loading.value = false;
    }
  }

  async function deleteRule(ruleId: string): Promise<boolean> {
    loading.value = true;
    error.value = null;
    try {
      await alertApi.deleteRule(ruleId);
      rules.value = rules.value.filter((r) => r.id !== ruleId);
      return true;
    } catch (err) {
      error.value = 'Failed to delete alert rule';
      console.error(err);
      return false;
    } finally {
      loading.value = false;
    }
  }

  async function testRule(
    ruleId: string,
    testData: Record<string, unknown>
  ): Promise<RuleTestResult | null> {
    loading.value = true;
    try {
      return await alertApi.testRule(ruleId, testData);
    } catch (err) {
      error.value = 'Failed to test rule';
      console.error(err);
      return null;
    } finally {
      loading.value = false;
    }
  }

  // Actions - Alerts
  async function fetchAlerts(newFilters?: AlertFilters) {
    if (newFilters) {
      filters.value = newFilters;
      pagination.value.offset = 0;
    }

    loading.value = true;
    error.value = null;
    try {
      const response = await alertApi.listAlerts({
        ...filters.value,
        limit: pagination.value.limit,
        offset: pagination.value.offset,
      });
      alerts.value = response.alerts;
      pagination.value.total = response.total;
      pagination.value.hasMore = response.hasMore;
    } catch (err) {
      error.value = 'Failed to fetch alerts';
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  async function loadMoreAlerts() {
    if (!pagination.value.hasMore || loading.value) return;

    pagination.value.offset += pagination.value.limit;
    loading.value = true;
    try {
      const response = await alertApi.listAlerts({
        ...filters.value,
        limit: pagination.value.limit,
        offset: pagination.value.offset,
      });
      alerts.value.push(...response.alerts);
      pagination.value.hasMore = response.hasMore;
    } catch (err) {
      error.value = 'Failed to load more alerts';
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  async function acknowledgeAlert(
    alertId: string,
    notes?: string
  ): Promise<TriggeredAlert | null> {
    try {
      const updated = await alertApi.acknowledgeAlert(alertId, notes);
      const index = alerts.value.findIndex((a) => a.id === alertId);
      if (index !== -1) {
        alerts.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = 'Failed to acknowledge alert';
      console.error(err);
      return null;
    }
  }

  async function dismissAlert(
    alertId: string,
    notes?: string
  ): Promise<TriggeredAlert | null> {
    try {
      const updated = await alertApi.dismissAlert(alertId, notes);
      const index = alerts.value.findIndex((a) => a.id === alertId);
      if (index !== -1) {
        alerts.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = 'Failed to dismiss alert';
      console.error(err);
      return null;
    }
  }

  async function snoozeAlert(
    alertId: string,
    snoozeMinutes: number
  ): Promise<TriggeredAlert | null> {
    try {
      const updated = await alertApi.snoozeAlert(alertId, snoozeMinutes);
      const index = alerts.value.findIndex((a) => a.id === alertId);
      if (index !== -1) {
        alerts.value[index] = updated;
      }
      return updated;
    } catch (err) {
      error.value = 'Failed to snooze alert';
      console.error(err);
      return null;
    }
  }

  async function bulkAcknowledge(alertIds: string[], notes?: string): Promise<number> {
    try {
      const result = await alertApi.bulkAcknowledge(alertIds, notes);
      // Refresh alerts to get updated states
      await fetchAlerts();
      return result.acknowledgedCount;
    } catch (err) {
      error.value = 'Failed to bulk acknowledge alerts';
      console.error(err);
      return 0;
    }
  }

  // Actions - Statistics
  async function fetchStatistics(startDate?: string, endDate?: string) {
    loading.value = true;
    try {
      statistics.value = await alertApi.getStatistics(startDate, endDate);
    } catch (err) {
      error.value = 'Failed to fetch statistics';
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  // Actions - Preferences
  async function fetchPreferences() {
    loading.value = true;
    try {
      preferences.value = await alertApi.getPreferences();
    } catch (err) {
      error.value = 'Failed to fetch preferences';
      console.error(err);
    } finally {
      loading.value = false;
    }
  }

  async function updatePreferences(
    updates: NotificationPreferencesUpdate
  ): Promise<NotificationPreferences | null> {
    loading.value = true;
    try {
      preferences.value = await alertApi.updatePreferences(updates);
      return preferences.value;
    } catch (err) {
      error.value = 'Failed to update preferences';
      console.error(err);
      return null;
    } finally {
      loading.value = false;
    }
  }

  // Reset
  function reset() {
    rules.value = [];
    alerts.value = [];
    statistics.value = null;
    preferences.value = null;
    filters.value = {};
    pagination.value = { limit: 20, offset: 0, total: 0, hasMore: false };
    error.value = null;
  }

  return {
    // State
    rules,
    alerts,
    statistics,
    preferences,
    loading,
    error,
    filters,
    pagination,
    // Computed
    activeRules,
    newAlerts,
    criticalAlerts,
    alertsByStatus,
    // Actions - Rules
    fetchRules,
    createRule,
    updateRule,
    deleteRule,
    testRule,
    // Actions - Alerts
    fetchAlerts,
    loadMoreAlerts,
    acknowledgeAlert,
    dismissAlert,
    snoozeAlert,
    bulkAcknowledge,
    // Actions - Statistics & Preferences
    fetchStatistics,
    fetchPreferences,
    updatePreferences,
    reset,
  };
});
