/**
 * Analytics Types for Sprint 9 - Advanced Analytics & Quality Dashboard
 */

// =============================================================================
// ML Model Types
// =============================================================================

export type ModelStatus = 'draft' | 'training' | 'trained' | 'active' | 'deprecated' | 'archived';
export type ModelType = 'classification' | 'regression' | 'clustering' | 'nlp';

export interface AnalyticsModel {
  id: string;
  name: string;
  description?: string;
  modelType: ModelType;
  version: string;
  status: ModelStatus;
  algorithm?: string;
  framework?: string;
  hyperparameters?: Record<string, unknown>;
  featureColumns?: string[];
  targetColumn?: string;
  preprocessingConfig?: Record<string, unknown>;
  modelPath?: string;
  modelSizeBytes?: number;
  trainingMetrics?: Record<string, number>;
  validationMetrics?: Record<string, number>;
  testMetrics?: Record<string, number>;
  trainingSamples?: number;
  trainingStartedAt?: string;
  trainingCompletedAt?: string;
  trainingDurationSeconds?: number;
  deployedAt?: string;
  endpointUrl?: string;
  createdBy: string;
  createdAt: string;
  updatedAt?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ModelCreate {
  name: string;
  modelType: ModelType;
  version: string;
  description?: string;
  algorithm?: string;
  framework?: string;
  hyperparameters?: Record<string, unknown>;
  featureColumns?: string[];
  targetColumn?: string;
  preprocessingConfig?: Record<string, unknown>;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ModelUpdate {
  name?: string;
  description?: string;
  algorithm?: string;
  framework?: string;
  hyperparameters?: Record<string, unknown>;
  featureColumns?: string[];
  targetColumn?: string;
  preprocessingConfig?: Record<string, unknown>;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ModelTrainingComplete {
  modelPath: string;
  trainingMetrics: Record<string, number>;
  validationMetrics?: Record<string, number>;
  testMetrics?: Record<string, number>;
  trainingSamples?: number;
  modelSizeBytes?: number;
}

export interface ModelStatistics {
  totalModels: number;
  byStatus: Record<ModelStatus, number>;
  byType: Record<ModelType, number>;
  activeCount: number;
}

export interface ModelComparison {
  models: Record<string, {
    name: string;
    version: string;
    trainingMetrics?: Record<string, number>;
    validationMetrics?: Record<string, number>;
    testMetrics?: Record<string, number>;
  }>;
}

// =============================================================================
// Prediction Types
// =============================================================================

export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type FeedbackStatus = 'correct' | 'incorrect' | 'partial';

export interface Prediction {
  id: string;
  modelId: string;
  patientId?: string;
  documentId?: string;
  predictionType: string;
  predictionResult: Record<string, unknown>;
  confidenceScore?: number;
  probabilities?: Record<string, number>;
  riskLevel?: RiskLevel;
  riskFactors?: RiskFactor[];
  feedbackStatus?: FeedbackStatus;
  feedbackNotes?: string;
  inferenceTimeMs?: number;
  predictedAt: string;
}

export interface RiskFactor {
  name: string;
  value: unknown;
  contribution: number;
  description?: string;
}

export interface PredictionCreate {
  modelId: string;
  predictionType: string;
  predictionResult: Record<string, unknown>;
  patientId?: string;
  documentId?: string;
  inputData?: Record<string, unknown>;
  confidenceScore?: number;
  probabilities?: Record<string, number>;
  riskLevel?: RiskLevel;
  riskFactors?: RiskFactor[];
  inferenceTimeMs?: number;
}

export interface PredictionFeedback {
  feedbackStatus: FeedbackStatus;
  actualOutcome?: Record<string, unknown>;
  notes?: string;
}

export interface PredictionStatistics {
  periodDays: number;
  totalPredictions: number;
  averageDaily: number;
  riskDistribution: Record<RiskLevel, number>;
  typeDistribution: Record<string, number>;
  averageConfidence?: number;
  averageInferenceTimeMs?: number;
}

export interface PatientRiskSummary {
  patientId: string;
  totalPredictions: number;
  highestRisk?: RiskLevel;
  riskCounts: Record<RiskLevel, number>;
  latestPrediction?: Record<string, unknown>;
}

export interface ModelAccuracy {
  totalWithFeedback: number;
  accuracy?: number;
  correct: number;
  incorrect: number;
  partial: number;
}

// =============================================================================
// Quality Metric Types
// =============================================================================

export type MetricCategory = 'nlp_accuracy' | 'data_quality' | 'clinical_outcomes' | 'operational';
export type MetricType = 'percentage' | 'count' | 'ratio' | 'score' | 'time';
export type CalculationMethod = 'automated' | 'manual' | 'hybrid';
export type ComparisonOperator = '>=' | '<=' | '==' | '>' | '<';
export type MetricStatus = 'on_target' | 'warning' | 'critical' | 'unknown';

export interface QualityMetric {
  id: string;
  name: string;
  description?: string;
  category: MetricCategory;
  metricType: MetricType;
  calculationMethod: CalculationMethod;
  calculationFrequency?: string;
  targetValue?: number;
  warningThreshold?: number;
  criticalThreshold?: number;
  comparisonOperator: ComparisonOperator;
  unit?: string;
  decimalPlaces?: number;
  displayFormat?: string;
  chartType?: string;
  isActive: boolean;
  isPublic: boolean;
  lastCalculatedAt?: string;
  nextCalculationAt?: string;
  createdAt: string;
  tags?: string[];
}

export interface QualityMetricCreate {
  name: string;
  category: MetricCategory;
  metricType: MetricType;
  calculationMethod: CalculationMethod;
  description?: string;
  calculationQuery?: string;
  calculationParams?: Record<string, unknown>;
  targetValue?: number;
  warningThreshold?: number;
  criticalThreshold?: number;
  comparisonOperator?: ComparisonOperator;
  unit?: string;
  decimalPlaces?: number;
  displayFormat?: string;
  chartType?: string;
  calculationFrequency?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface QualityMetricUpdate {
  name?: string;
  description?: string;
  targetValue?: number;
  warningThreshold?: number;
  criticalThreshold?: number;
  comparisonOperator?: ComparisonOperator;
  unit?: string;
  decimalPlaces?: number;
  displayFormat?: string;
  chartType?: string;
  calculationFrequency?: string;
  calculationQuery?: string;
  calculationParams?: Record<string, unknown>;
  isActive?: boolean;
  isPublic?: boolean;
  tags?: string[];
}

export interface QualityScore {
  id: string;
  metricId: string;
  value: number;
  previousValue?: number;
  changePercentage?: number;
  status: MetricStatus;
  cohortId?: string;
  timePeriod?: string;
  periodStart?: string;
  periodEnd?: string;
  breakdown?: Record<string, unknown>;
  sampleSize?: number;
  calculatedAt: string;
}

export interface QualityScoreCreate {
  metricId: string;
  value: number;
  cohortId?: string;
  timePeriod?: string;
  periodStart?: string;
  periodEnd?: string;
  breakdown?: Record<string, unknown>;
  sampleSize?: number;
  calculationDetails?: Record<string, unknown>;
}

export interface QualitySummary {
  totalMetrics: number;
  onTarget: number;
  warning: number;
  critical: number;
  unknown: number;
  healthScore: number;
  byCategory: Record<MetricCategory, {
    on_target: number;
    warning: number;
    critical: number;
    unknown: number;
  }>;
}

export interface QualityTrend {
  metricId: string;
  metricName: string;
  data: TrendDataPoint[];
}

export interface TrendDataPoint {
  date: string;
  value: number;
  status: MetricStatus;
}

export interface MetricWithScore {
  metric: QualityMetric;
  score?: QualityScore;
}

// =============================================================================
// Dashboard Types
// =============================================================================

export type DashboardType = 'quality' | 'predictive' | 'operational' | 'custom';
export type WidgetType = 'gauge' | 'metric' | 'line_chart' | 'bar_chart' | 'pie_chart' | 'table' | 'alert_list';

export interface WidgetConfig {
  id: string;
  type: WidgetType;
  title: string;
  config?: Record<string, unknown>;
  layout?: WidgetLayout;
}

export interface WidgetLayout {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface AnalyticsDashboard {
  id: string;
  name: string;
  description?: string;
  dashboardType: DashboardType;
  layout?: Record<string, unknown>;
  widgets?: WidgetConfig[];
  theme?: string;
  defaultFilters?: Record<string, unknown>;
  defaultDateRange?: string;
  defaultCohortId?: string;
  autoRefresh: boolean;
  refreshIntervalSeconds?: number;
  isPublic: boolean;
  isDefault: boolean;
  allowedRoles?: string[];
  createdBy: string;
  createdAt: string;
  updatedAt?: string;
  tags?: string[];
}

export interface DashboardCreate {
  name: string;
  dashboardType: DashboardType;
  description?: string;
  layout?: Record<string, unknown>;
  widgets?: WidgetConfig[];
  theme?: string;
  defaultFilters?: Record<string, unknown>;
  defaultDateRange?: string;
  defaultCohortId?: string;
  autoRefresh?: boolean;
  refreshIntervalSeconds?: number;
  isPublic?: boolean;
  allowedRoles?: string[];
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface DashboardUpdate {
  name?: string;
  description?: string;
  layout?: Record<string, unknown>;
  widgets?: WidgetConfig[];
  theme?: string;
  defaultFilters?: Record<string, unknown>;
  defaultDateRange?: string;
  defaultCohortId?: string;
  autoRefresh?: boolean;
  refreshIntervalSeconds?: number;
  isPublic?: boolean;
  allowedRoles?: string[];
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface WidgetDataRequest {
  widgetConfig: Record<string, unknown>;
  cohortId?: string;
  dateRange?: string;
}

export interface WidgetData {
  widgetId?: string;
  data: Record<string, unknown>;
}

export interface DashboardStatistics {
  totalDashboards: number;
  byType: Record<DashboardType, number>;
  publicDashboards: number;
  privateDashboards: number;
}

// =============================================================================
// Report Types
// =============================================================================

export type ReportType = 'quality_summary' | 'trend_analysis' | 'model_performance' | 'custom';
export type ReportFormat = 'pdf' | 'xlsx' | 'csv' | 'html';
export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed' | 'cancelled';
export type DateRangeType = 'fixed' | 'relative';
export type RelativePeriod = 'last_7_days' | 'last_30_days' | 'this_month' | 'last_month' | 'this_quarter' | 'this_year';

export interface AnalyticsReport {
  id: string;
  name: string;
  description?: string;
  reportType: ReportType;
  dashboardId?: string;
  metrics?: string[];
  parameters?: Record<string, unknown>;
  dateRangeType?: DateRangeType;
  startDate?: string;
  endDate?: string;
  relativePeriod?: RelativePeriod;
  cohortId?: string;
  fileFormat: ReportFormat;
  includeCharts: boolean;
  includeRawData: boolean;
  status: ReportStatus;
  progressPercentage?: number;
  errorMessage?: string;
  filePath?: string;
  fileSizeBytes?: number;
  generatedAt?: string;
  expiresAt?: string;
  isScheduled: boolean;
  scheduleCron?: string;
  nextRunAt?: string;
  emailRecipients?: string[];
  autoSend: boolean;
  createdBy: string;
  createdAt: string;
  tags?: string[];
}

export interface ReportCreate {
  name: string;
  reportType: ReportType;
  fileFormat: ReportFormat;
  description?: string;
  dashboardId?: string;
  metrics?: string[];
  parameters?: Record<string, unknown>;
  dateRangeType?: DateRangeType;
  startDate?: string;
  endDate?: string;
  relativePeriod?: RelativePeriod;
  cohortId?: string;
  includeCharts?: boolean;
  includeRawData?: boolean;
  isScheduled?: boolean;
  scheduleCron?: string;
  emailRecipients?: string[];
  autoSend?: boolean;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ReportUpdate {
  name?: string;
  description?: string;
  metrics?: string[];
  parameters?: Record<string, unknown>;
  dateRangeType?: DateRangeType;
  startDate?: string;
  endDate?: string;
  relativePeriod?: RelativePeriod;
  cohortId?: string;
  includeCharts?: boolean;
  includeRawData?: boolean;
  isScheduled?: boolean;
  scheduleCron?: string;
  emailRecipients?: string[];
  autoSend?: boolean;
  tags?: string[];
  metadata?: Record<string, unknown>;
}

export interface ReportStatistics {
  periodDays: number;
  totalReports: number;
  byStatus: Record<ReportStatus, number>;
  byType: Record<ReportType, number>;
  byFormat: Record<ReportFormat, number>;
  scheduledReports: number;
  successRate?: number;
}

export interface ReportDownload {
  downloadUrl: string;
  filename: string;
  fileSizeBytes?: number;
  expiresAt?: string;
}
