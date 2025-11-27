/**
 * Analytics API Client for Sprint 9 - Advanced Analytics & Quality Dashboard
 */

import axios from 'axios';
import type {
  AnalyticsModel,
  ModelCreate,
  ModelUpdate,
  ModelTrainingComplete,
  ModelStatistics,
  ModelComparison,
  Prediction,
  PredictionCreate,
  PredictionFeedback,
  PredictionStatistics,
  PatientRiskSummary,
  ModelAccuracy,
  QualityMetric,
  QualityMetricCreate,
  QualityMetricUpdate,
  QualityScore,
  QualityScoreCreate,
  QualitySummary,
  QualityTrend,
  MetricWithScore,
  AnalyticsDashboard,
  DashboardCreate,
  DashboardUpdate,
  WidgetDataRequest,
  WidgetData,
  DashboardStatistics,
  AnalyticsReport,
  ReportCreate,
  ReportUpdate,
  ReportStatistics,
  ReportDownload,
} from '@/types/analytics';

const API_BASE = '/api/v1/analytics';

// =============================================================================
// ML Model API
// =============================================================================

export const modelApi = {
  async list(params?: {
    modelType?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<AnalyticsModel[]> {
    const response = await axios.get(`${API_BASE}/models`, { params });
    return response.data;
  },

  async get(modelId: string): Promise<AnalyticsModel> {
    const response = await axios.get(`${API_BASE}/models/${modelId}`);
    return response.data;
  },

  async create(data: ModelCreate): Promise<AnalyticsModel> {
    const response = await axios.post(`${API_BASE}/models`, data);
    return response.data;
  },

  async update(modelId: string, data: ModelUpdate): Promise<AnalyticsModel> {
    const response = await axios.patch(`${API_BASE}/models/${modelId}`, data);
    return response.data;
  },

  async delete(modelId: string): Promise<void> {
    await axios.delete(`${API_BASE}/models/${modelId}`);
  },

  async startTraining(modelId: string): Promise<AnalyticsModel> {
    const response = await axios.post(`${API_BASE}/models/${modelId}/train`);
    return response.data;
  },

  async completeTraining(modelId: string, data: ModelTrainingComplete): Promise<AnalyticsModel> {
    const response = await axios.post(`${API_BASE}/models/${modelId}/training-complete`, data);
    return response.data;
  },

  async activate(modelId: string, endpointUrl?: string): Promise<AnalyticsModel> {
    const response = await axios.post(`${API_BASE}/models/${modelId}/activate`, { endpoint_url: endpointUrl });
    return response.data;
  },

  async deprecate(modelId: string): Promise<AnalyticsModel> {
    const response = await axios.post(`${API_BASE}/models/${modelId}/deprecate`);
    return response.data;
  },

  async archive(modelId: string): Promise<AnalyticsModel> {
    const response = await axios.post(`${API_BASE}/models/${modelId}/archive`);
    return response.data;
  },

  async getVersions(modelId: string): Promise<AnalyticsModel[]> {
    const response = await axios.get(`${API_BASE}/models/${modelId}/versions`);
    return response.data;
  },

  async compare(modelIds: string[]): Promise<ModelComparison> {
    const response = await axios.post(`${API_BASE}/models/compare`, modelIds);
    return response.data;
  },

  async getStatistics(): Promise<ModelStatistics> {
    const response = await axios.get(`${API_BASE}/models/statistics`);
    return response.data;
  },

  async getAccuracy(modelId: string): Promise<ModelAccuracy> {
    const response = await axios.get(`${API_BASE}/models/${modelId}/accuracy`);
    return response.data;
  },
};

// =============================================================================
// Prediction API
// =============================================================================

export const predictionApi = {
  async list(params?: {
    modelId?: string;
    patientId?: string;
    riskLevel?: string;
    startDate?: string;
    endDate?: string;
    skip?: number;
    limit?: number;
  }): Promise<Prediction[]> {
    const response = await axios.get(`${API_BASE}/predictions`, { params });
    return response.data;
  },

  async get(predictionId: string): Promise<Prediction> {
    const response = await axios.get(`${API_BASE}/predictions/${predictionId}`);
    return response.data;
  },

  async create(data: PredictionCreate): Promise<Prediction> {
    const response = await axios.post(`${API_BASE}/predictions`, data);
    return response.data;
  },

  async execute(modelId: string, inputData: Record<string, unknown>, patientId?: string, documentId?: string): Promise<Prediction> {
    const response = await axios.post(`${API_BASE}/models/${modelId}/predict`, {
      input_data: inputData,
      patient_id: patientId,
      document_id: documentId,
    });
    return response.data;
  },

  async addFeedback(predictionId: string, feedback: PredictionFeedback): Promise<Prediction> {
    const response = await axios.post(`${API_BASE}/predictions/${predictionId}/feedback`, feedback);
    return response.data;
  },

  async getHighRisk(params?: { modelId?: string; limit?: number }): Promise<Prediction[]> {
    const response = await axios.get(`${API_BASE}/predictions/high-risk`, { params });
    return response.data;
  },

  async getStatistics(params?: { modelId?: string; days?: number }): Promise<PredictionStatistics> {
    const response = await axios.get(`${API_BASE}/predictions/statistics`, { params });
    return response.data;
  },

  async getPatientRiskSummary(patientId: string): Promise<PatientRiskSummary> {
    const response = await axios.get(`${API_BASE}/patients/${patientId}/risk-summary`);
    return response.data;
  },
};

// =============================================================================
// Quality Metric API
// =============================================================================

export const qualityApi = {
  async listMetrics(params?: {
    category?: string;
    isActive?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<QualityMetric[]> {
    const response = await axios.get(`${API_BASE}/quality/metrics`, { params });
    return response.data;
  },

  async getMetric(metricId: string): Promise<QualityMetric> {
    const response = await axios.get(`${API_BASE}/quality/metrics/${metricId}`);
    return response.data;
  },

  async createMetric(data: QualityMetricCreate): Promise<QualityMetric> {
    const response = await axios.post(`${API_BASE}/quality/metrics`, data);
    return response.data;
  },

  async updateMetric(metricId: string, data: QualityMetricUpdate): Promise<QualityMetric> {
    const response = await axios.patch(`${API_BASE}/quality/metrics/${metricId}`, data);
    return response.data;
  },

  async deleteMetric(metricId: string): Promise<void> {
    await axios.delete(`${API_BASE}/quality/metrics/${metricId}`);
  },

  async calculateMetric(metricId: string, cohortId?: string): Promise<QualityScore> {
    const response = await axios.post(`${API_BASE}/quality/metrics/${metricId}/calculate`, null, {
      params: { cohort_id: cohortId },
    });
    return response.data;
  },

  async recordScore(data: QualityScoreCreate): Promise<QualityScore> {
    const response = await axios.post(`${API_BASE}/quality/scores`, data);
    return response.data;
  },

  async getMetricScores(metricId: string, params?: {
    startDate?: string;
    endDate?: string;
    limit?: number;
  }): Promise<QualityScore[]> {
    const response = await axios.get(`${API_BASE}/quality/metrics/${metricId}/scores`, { params });
    return response.data;
  },

  async getMetricTrend(metricId: string, days?: number): Promise<QualityTrend> {
    const response = await axios.get(`${API_BASE}/quality/metrics/${metricId}/trend`, {
      params: { days },
    });
    return response.data;
  },

  async getMetricsWithScores(category?: string): Promise<MetricWithScore[]> {
    const response = await axios.get(`${API_BASE}/quality/metrics/with-scores`, {
      params: { category },
    });
    return response.data;
  },

  async getSummary(cohortId?: string): Promise<QualitySummary> {
    const response = await axios.get(`${API_BASE}/quality/summary`, {
      params: { cohort_id: cohortId },
    });
    return response.data;
  },

  async initializeTemplates(): Promise<QualityMetric[]> {
    const response = await axios.post(`${API_BASE}/quality/initialize-templates`);
    return response.data;
  },
};

// =============================================================================
// Dashboard API
// =============================================================================

export const dashboardApi = {
  async list(params?: {
    dashboardType?: string;
    isPublic?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<AnalyticsDashboard[]> {
    const response = await axios.get(`${API_BASE}/dashboards`, { params });
    return response.data;
  },

  async get(dashboardId: string): Promise<AnalyticsDashboard> {
    const response = await axios.get(`${API_BASE}/dashboards/${dashboardId}`);
    return response.data;
  },

  async create(data: DashboardCreate): Promise<AnalyticsDashboard> {
    const response = await axios.post(`${API_BASE}/dashboards`, data);
    return response.data;
  },

  async update(dashboardId: string, data: DashboardUpdate): Promise<AnalyticsDashboard> {
    const response = await axios.patch(`${API_BASE}/dashboards/${dashboardId}`, data);
    return response.data;
  },

  async delete(dashboardId: string): Promise<void> {
    await axios.delete(`${API_BASE}/dashboards/${dashboardId}`);
  },

  async duplicate(dashboardId: string, newName: string): Promise<AnalyticsDashboard> {
    const response = await axios.post(`${API_BASE}/dashboards/${dashboardId}/duplicate`, {
      new_name: newName,
    });
    return response.data;
  },

  async setDefault(dashboardId: string): Promise<AnalyticsDashboard> {
    const response = await axios.post(`${API_BASE}/dashboards/${dashboardId}/set-default`);
    return response.data;
  },

  async addWidget(dashboardId: string, widgetConfig: Record<string, unknown>): Promise<AnalyticsDashboard> {
    const response = await axios.post(`${API_BASE}/dashboards/${dashboardId}/widgets`, {
      widget_config: widgetConfig,
    });
    return response.data;
  },

  async updateWidget(dashboardId: string, widgetId: string, widgetConfig: Record<string, unknown>): Promise<AnalyticsDashboard> {
    const response = await axios.patch(`${API_BASE}/dashboards/${dashboardId}/widgets/${widgetId}`, {
      widget_config: widgetConfig,
    });
    return response.data;
  },

  async removeWidget(dashboardId: string, widgetId: string): Promise<AnalyticsDashboard> {
    const response = await axios.delete(`${API_BASE}/dashboards/${dashboardId}/widgets/${widgetId}`);
    return response.data;
  },

  async getWidgetData(dashboardId: string, widgetId: string, request: WidgetDataRequest): Promise<WidgetData> {
    const response = await axios.post(`${API_BASE}/dashboards/${dashboardId}/widgets/${widgetId}/data`, request);
    return response.data;
  },

  async getStatistics(): Promise<DashboardStatistics> {
    const response = await axios.get(`${API_BASE}/dashboards/statistics`);
    return response.data;
  },
};

// =============================================================================
// Report API
// =============================================================================

export const reportApi = {
  async list(params?: {
    reportType?: string;
    status?: string;
    skip?: number;
    limit?: number;
  }): Promise<AnalyticsReport[]> {
    const response = await axios.get(`${API_BASE}/reports`, { params });
    return response.data;
  },

  async get(reportId: string): Promise<AnalyticsReport> {
    const response = await axios.get(`${API_BASE}/reports/${reportId}`);
    return response.data;
  },

  async create(data: ReportCreate): Promise<AnalyticsReport> {
    const response = await axios.post(`${API_BASE}/reports`, data);
    return response.data;
  },

  async update(reportId: string, data: ReportUpdate): Promise<AnalyticsReport> {
    const response = await axios.patch(`${API_BASE}/reports/${reportId}`, data);
    return response.data;
  },

  async delete(reportId: string): Promise<void> {
    await axios.delete(`${API_BASE}/reports/${reportId}`);
  },

  async generate(reportId: string): Promise<AnalyticsReport> {
    const response = await axios.post(`${API_BASE}/reports/${reportId}/generate`);
    return response.data;
  },

  async download(reportId: string): Promise<ReportDownload> {
    const response = await axios.get(`${API_BASE}/reports/${reportId}/download`);
    return response.data;
  },

  async cancel(reportId: string): Promise<AnalyticsReport> {
    const response = await axios.post(`${API_BASE}/reports/${reportId}/cancel`);
    return response.data;
  },

  async listScheduled(): Promise<AnalyticsReport[]> {
    const response = await axios.get(`${API_BASE}/reports/scheduled`);
    return response.data;
  },

  async getStatistics(days?: number): Promise<ReportStatistics> {
    const response = await axios.get(`${API_BASE}/reports/statistics`, {
      params: { days },
    });
    return response.data;
  },
};

// Export all APIs
export const analyticsApi = {
  models: modelApi,
  predictions: predictionApi,
  quality: qualityApi,
  dashboards: dashboardApi,
  reports: reportApi,
};

export default analyticsApi;
