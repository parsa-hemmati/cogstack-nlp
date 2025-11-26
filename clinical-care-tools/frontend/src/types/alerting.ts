/**
 * TypeScript types for Sprint 7 - Automated Alerting
 */

export type AlertSeverity = 'critical' | 'high' | 'medium' | 'low';
export type AlertStatus = 'new' | 'acknowledged' | 'dismissed' | 'snoozed';
export type NotificationChannel = 'email' | 'sms' | 'in_app';
export type ConditionOperator =
  | 'equals'
  | 'not_equals'
  | 'greater_than'
  | 'less_than'
  | 'greater_than_or_equals'
  | 'less_than_or_equals'
  | 'contains'
  | 'not_contains'
  | 'in'
  | 'not_in'
  | 'is_null'
  | 'is_not_null'
  | 'starts_with'
  | 'ends_with'
  | 'regex_match';

export interface Condition {
  field: string;
  operator: ConditionOperator;
  value: unknown;
}

export interface RuleConditions {
  match_type: 'all' | 'any';
  conditions: Condition[];
}

export interface AlertRule {
  id: string;
  name: string;
  description?: string;
  conditions: RuleConditions;
  severity: AlertSeverity;
  notificationChannels: NotificationChannel[];
  escalationMinutes?: number;
  enabled: boolean;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface AlertRuleCreate {
  name: string;
  description?: string;
  conditions: RuleConditions;
  severity: AlertSeverity;
  notificationChannels?: NotificationChannel[];
  escalationMinutes?: number;
  enabled?: boolean;
}

export interface AlertRuleUpdate {
  name?: string;
  description?: string;
  conditions?: RuleConditions;
  severity?: AlertSeverity;
  notificationChannels?: NotificationChannel[];
  escalationMinutes?: number;
  enabled?: boolean;
  changeReason?: string;
}

export interface AlertRuleVersion {
  id: string;
  ruleId: string;
  version: number;
  conditions: RuleConditions;
  changedBy: string;
  changedAt: string;
  changeReason?: string;
}

export interface TriggeredAlert {
  id: string;
  ruleId: string;
  ruleName?: string;
  patientId?: string;
  severity: AlertSeverity;
  status: AlertStatus;
  triggerData?: Record<string, unknown>;
  triggeredAt: string;
  acknowledgedBy?: string;
  acknowledgedAt?: string;
  dismissedBy?: string;
  dismissedAt?: string;
  snoozeUntil?: string;
  notes?: string;
}

export interface AlertListResponse {
  alerts: TriggeredAlert[];
  total: number;
  limit: number;
  offset: number;
  hasMore: boolean;
}

export interface AlertFilters {
  status?: AlertStatus;
  severity?: AlertSeverity;
  patientId?: string;
  startDate?: string;
  endDate?: string;
  ruleId?: string;
}

export interface NotificationPreferences {
  id: string;
  userId: string;
  emailEnabled: boolean;
  smsEnabled: boolean;
  inAppEnabled: boolean;
  quietHoursStart?: string;
  quietHoursEnd?: string;
  minSeverity: AlertSeverity;
  phoneNumber?: string;
  updatedAt: string;
}

export interface NotificationPreferencesUpdate {
  emailEnabled?: boolean;
  smsEnabled?: boolean;
  inAppEnabled?: boolean;
  quietHoursStart?: string;
  quietHoursEnd?: string;
  minSeverity?: AlertSeverity;
  phoneNumber?: string;
}

export interface AlertStatistics {
  totalAlerts: number;
  byStatus: Record<AlertStatus, number>;
  bySeverity: Record<AlertSeverity, number>;
  avgResponseTimeSeconds: number;
  unacknowledgedCount: number;
  criticalUnacknowledged: number;
}

export interface RuleTestResult {
  ruleId: string;
  ruleName: string;
  matched: boolean;
  matchType: 'all' | 'any';
  conditionResults: Array<{
    condition: Condition;
    matched: boolean;
    actualValue: unknown;
  }>;
}

// Severity configuration for UI
export const SEVERITY_CONFIG: Record<
  AlertSeverity,
  { color: string; icon: string; label: string; priority: number }
> = {
  critical: { color: 'error', icon: 'mdi-alert-circle', label: 'Critical', priority: 4 },
  high: { color: 'warning', icon: 'mdi-alert', label: 'High', priority: 3 },
  medium: { color: 'info', icon: 'mdi-information', label: 'Medium', priority: 2 },
  low: { color: 'success', icon: 'mdi-information-outline', label: 'Low', priority: 1 },
};

// Status configuration for UI
export const STATUS_CONFIG: Record<
  AlertStatus,
  { color: string; icon: string; label: string }
> = {
  new: { color: 'error', icon: 'mdi-bell-ring', label: 'New' },
  acknowledged: { color: 'info', icon: 'mdi-check', label: 'Acknowledged' },
  dismissed: { color: 'grey', icon: 'mdi-close', label: 'Dismissed' },
  snoozed: { color: 'warning', icon: 'mdi-clock', label: 'Snoozed' },
};

// Operator display names
export const OPERATOR_LABELS: Record<ConditionOperator, string> = {
  equals: 'Equals',
  not_equals: 'Does not equal',
  greater_than: 'Greater than',
  less_than: 'Less than',
  greater_than_or_equals: 'Greater than or equals',
  less_than_or_equals: 'Less than or equals',
  contains: 'Contains',
  not_contains: 'Does not contain',
  in: 'Is one of',
  not_in: 'Is not one of',
  is_null: 'Is empty',
  is_not_null: 'Is not empty',
  starts_with: 'Starts with',
  ends_with: 'Ends with',
  regex_match: 'Matches pattern',
};
