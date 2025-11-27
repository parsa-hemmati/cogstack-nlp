/**
 * Alert API client for Sprint 7 - Automated Alerting
 */
import { apiClient } from './apiClient';
import type {
  AlertRule,
  AlertRuleCreate,
  AlertRuleUpdate,
  AlertRuleVersion,
  TriggeredAlert,
  AlertListResponse,
  AlertFilters,
  AlertStatistics,
  NotificationPreferences,
  NotificationPreferencesUpdate,
  RuleTestResult,
} from '@/types/alerting';

const BASE_PATH = '/api/v1/alerts';

export const alertApi = {
  // ==================== Alert Rules ====================

  async listRules(params?: { enabledOnly?: boolean; severity?: string }): Promise<AlertRule[]> {
    const response = await apiClient.get(`${BASE_PATH}/rules`, { params });
    return response.data;
  },

  async getRule(ruleId: string): Promise<AlertRule> {
    const response = await apiClient.get(`${BASE_PATH}/rules/${ruleId}`);
    return response.data;
  },

  async createRule(ruleData: AlertRuleCreate): Promise<AlertRule> {
    const response = await apiClient.post(`${BASE_PATH}/rules`, ruleData);
    return response.data;
  },

  async updateRule(ruleId: string, updates: AlertRuleUpdate): Promise<AlertRule> {
    const response = await apiClient.put(`${BASE_PATH}/rules/${ruleId}`, updates);
    return response.data;
  },

  async deleteRule(ruleId: string): Promise<void> {
    await apiClient.delete(`${BASE_PATH}/rules/${ruleId}`);
  },

  async getRuleVersions(ruleId: string): Promise<AlertRuleVersion[]> {
    const response = await apiClient.get(`${BASE_PATH}/rules/${ruleId}/versions`);
    return response.data;
  },

  async testRule(
    ruleId: string,
    testData: Record<string, unknown>
  ): Promise<RuleTestResult> {
    const response = await apiClient.post(`${BASE_PATH}/rules/${ruleId}/test`, {
      test_data: testData,
    });
    return response.data;
  },

  // ==================== Triggered Alerts ====================

  async listAlerts(
    params?: AlertFilters & { limit?: number; offset?: number }
  ): Promise<AlertListResponse> {
    const response = await apiClient.get(BASE_PATH, { params });
    return response.data;
  },

  async getAlert(alertId: string): Promise<TriggeredAlert> {
    const response = await apiClient.get(`${BASE_PATH}/${alertId}`);
    return response.data;
  },

  async acknowledgeAlert(alertId: string, notes?: string): Promise<TriggeredAlert> {
    const response = await apiClient.post(`${BASE_PATH}/${alertId}/acknowledge`, {
      notes,
    });
    return response.data;
  },

  async dismissAlert(alertId: string, notes?: string): Promise<TriggeredAlert> {
    const response = await apiClient.post(`${BASE_PATH}/${alertId}/dismiss`, {
      notes,
    });
    return response.data;
  },

  async snoozeAlert(alertId: string, snoozeMinutes: number): Promise<TriggeredAlert> {
    const response = await apiClient.post(`${BASE_PATH}/${alertId}/snooze`, {
      snooze_minutes: snoozeMinutes,
    });
    return response.data;
  },

  async bulkAcknowledge(
    alertIds: string[],
    notes?: string
  ): Promise<{ acknowledgedCount: number; failedIds: string[] }> {
    const response = await apiClient.post(`${BASE_PATH}/bulk-acknowledge`, {
      alert_ids: alertIds,
      notes,
    });
    return response.data;
  },

  // ==================== Statistics ====================

  async getStatistics(startDate?: string, endDate?: string): Promise<AlertStatistics> {
    const response = await apiClient.get(`${BASE_PATH}/statistics`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  async getNotificationStats(
    startDate?: string,
    endDate?: string
  ): Promise<{ total: number; byStatus: Record<string, number>; successRate: number }> {
    const response = await apiClient.get(`${BASE_PATH}/notifications/stats`, {
      params: { start_date: startDate, end_date: endDate },
    });
    return response.data;
  },

  // ==================== User Preferences ====================

  async getPreferences(): Promise<NotificationPreferences> {
    const response = await apiClient.get(`${BASE_PATH}/preferences`);
    return response.data;
  },

  async updatePreferences(
    updates: NotificationPreferencesUpdate
  ): Promise<NotificationPreferences> {
    const response = await apiClient.put(`${BASE_PATH}/preferences`, updates);
    return response.data;
  },
};

export default alertApi;
