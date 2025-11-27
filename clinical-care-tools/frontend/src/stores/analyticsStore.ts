/**
 * Analytics Store for Sprint 9 - Advanced Analytics & Quality Dashboard
 */

import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { analyticsApi } from '@/api/analyticsApi';
import type {
  AnalyticsModel,
  ModelCreate,
  ModelUpdate,
  ModelTrainingComplete,
  ModelStatistics,
  Prediction,
  PredictionFeedback,
  PredictionStatistics,
  QualityMetric,
  QualityMetricCreate,
  QualityMetricUpdate,
  QualityScore,
  QualitySummary,
  QualityTrend,
  MetricWithScore,
  AnalyticsDashboard,
  DashboardCreate,
  DashboardUpdate,
  DashboardStatistics,
  AnalyticsReport,
  ReportCreate,
  ReportUpdate,
  ReportStatistics,
} from '@/types/analytics';

export const useAnalyticsStore = defineStore('analytics', () => {
  // ==========================================================================
  // State
  // ==========================================================================

  // Models
  const models = ref<AnalyticsModel[]>([]);
  const selectedModel = ref<AnalyticsModel | null>(null);
  const modelStatistics = ref<ModelStatistics | null>(null);
  const modelsLoading = ref(false);

  // Predictions
  const predictions = ref<Prediction[]>([]);
  const highRiskPredictions = ref<Prediction[]>([]);
  const predictionStatistics = ref<PredictionStatistics | null>(null);
  const predictionsLoading = ref(false);

  // Quality Metrics
  const metrics = ref<QualityMetric[]>([]);
  const metricsWithScores = ref<MetricWithScore[]>([]);
  const qualitySummary = ref<QualitySummary | null>(null);
  const metricTrends = ref<Map<string, QualityTrend>>(new Map());
  const metricsLoading = ref(false);

  // Dashboards
  const dashboards = ref<AnalyticsDashboard[]>([]);
  const selectedDashboard = ref<AnalyticsDashboard | null>(null);
  const dashboardStatistics = ref<DashboardStatistics | null>(null);
  const dashboardsLoading = ref(false);

  // Reports
  const reports = ref<AnalyticsReport[]>([]);
  const scheduledReports = ref<AnalyticsReport[]>([]);
  const reportStatistics = ref<ReportStatistics | null>(null);
  const reportsLoading = ref(false);

  // General
  const error = ref<string | null>(null);

  // ==========================================================================
  // Computed
  // ==========================================================================

  const activeModels = computed(() =>
    models.value.filter(m => m.status === 'active')
  );

  const healthScore = computed(() =>
    qualitySummary.value?.healthScore ?? 0
  );

  const criticalMetrics = computed(() =>
    metricsWithScores.value.filter(m => m.score?.status === 'critical')
  );

  const warningMetrics = computed(() =>
    metricsWithScores.value.filter(m => m.score?.status === 'warning')
  );

  const recentHighRiskCount = computed(() =>
    highRiskPredictions.value.length
  );

  // ==========================================================================
  // Model Actions
  // ==========================================================================

  async function fetchModels(params?: { modelType?: string; status?: string }) {
    modelsLoading.value = true;
    error.value = null;
    try {
      models.value = await analyticsApi.models.list(params);
    } catch (e) {
      error.value = 'Failed to fetch models';
      console.error('fetchModels error:', e);
    } finally {
      modelsLoading.value = false;
    }
  }

  async function fetchModel(modelId: string) {
    modelsLoading.value = true;
    error.value = null;
    try {
      selectedModel.value = await analyticsApi.models.get(modelId);
    } catch (e) {
      error.value = 'Failed to fetch model';
      console.error('fetchModel error:', e);
    } finally {
      modelsLoading.value = false;
    }
  }

  async function createModel(data: ModelCreate) {
    error.value = null;
    try {
      const model = await analyticsApi.models.create(data);
      models.value.push(model);
      return model;
    } catch (e) {
      error.value = 'Failed to create model';
      console.error('createModel error:', e);
      throw e;
    }
  }

  async function updateModel(modelId: string, data: ModelUpdate) {
    error.value = null;
    try {
      const updated = await analyticsApi.models.update(modelId, data);
      const index = models.value.findIndex(m => m.id === modelId);
      if (index !== -1) {
        models.value[index] = updated;
      }
      if (selectedModel.value?.id === modelId) {
        selectedModel.value = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to update model';
      console.error('updateModel error:', e);
      throw e;
    }
  }

  async function deleteModel(modelId: string) {
    error.value = null;
    try {
      await analyticsApi.models.delete(modelId);
      models.value = models.value.filter(m => m.id !== modelId);
      if (selectedModel.value?.id === modelId) {
        selectedModel.value = null;
      }
    } catch (e) {
      error.value = 'Failed to delete model';
      console.error('deleteModel error:', e);
      throw e;
    }
  }

  async function activateModel(modelId: string, endpointUrl?: string) {
    error.value = null;
    try {
      const updated = await analyticsApi.models.activate(modelId, endpointUrl);
      const index = models.value.findIndex(m => m.id === modelId);
      if (index !== -1) {
        models.value[index] = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to activate model';
      console.error('activateModel error:', e);
      throw e;
    }
  }

  async function fetchModelStatistics() {
    try {
      modelStatistics.value = await analyticsApi.models.getStatistics();
    } catch (e) {
      console.error('fetchModelStatistics error:', e);
    }
  }

  // ==========================================================================
  // Prediction Actions
  // ==========================================================================

  async function fetchPredictions(params?: {
    modelId?: string;
    patientId?: string;
    riskLevel?: string;
  }) {
    predictionsLoading.value = true;
    error.value = null;
    try {
      predictions.value = await analyticsApi.predictions.list(params);
    } catch (e) {
      error.value = 'Failed to fetch predictions';
      console.error('fetchPredictions error:', e);
    } finally {
      predictionsLoading.value = false;
    }
  }

  async function fetchHighRiskPredictions(limit?: number) {
    try {
      highRiskPredictions.value = await analyticsApi.predictions.getHighRisk({ limit });
    } catch (e) {
      console.error('fetchHighRiskPredictions error:', e);
    }
  }

  async function addPredictionFeedback(predictionId: string, feedback: PredictionFeedback) {
    error.value = null;
    try {
      const updated = await analyticsApi.predictions.addFeedback(predictionId, feedback);
      const index = predictions.value.findIndex(p => p.id === predictionId);
      if (index !== -1) {
        predictions.value[index] = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to add feedback';
      console.error('addPredictionFeedback error:', e);
      throw e;
    }
  }

  async function fetchPredictionStatistics(days?: number) {
    try {
      predictionStatistics.value = await analyticsApi.predictions.getStatistics({ days });
    } catch (e) {
      console.error('fetchPredictionStatistics error:', e);
    }
  }

  // ==========================================================================
  // Quality Metric Actions
  // ==========================================================================

  async function fetchMetrics(category?: string) {
    metricsLoading.value = true;
    error.value = null;
    try {
      metrics.value = await analyticsApi.quality.listMetrics({ category });
    } catch (e) {
      error.value = 'Failed to fetch metrics';
      console.error('fetchMetrics error:', e);
    } finally {
      metricsLoading.value = false;
    }
  }

  async function fetchMetricsWithScores(category?: string) {
    metricsLoading.value = true;
    error.value = null;
    try {
      metricsWithScores.value = await analyticsApi.quality.getMetricsWithScores(category);
    } catch (e) {
      error.value = 'Failed to fetch metrics with scores';
      console.error('fetchMetricsWithScores error:', e);
    } finally {
      metricsLoading.value = false;
    }
  }

  async function fetchQualitySummary(cohortId?: string) {
    try {
      qualitySummary.value = await analyticsApi.quality.getSummary(cohortId);
    } catch (e) {
      console.error('fetchQualitySummary error:', e);
    }
  }

  async function fetchMetricTrend(metricId: string, days?: number) {
    try {
      const trend = await analyticsApi.quality.getMetricTrend(metricId, days);
      metricTrends.value.set(metricId, trend);
      return trend;
    } catch (e) {
      console.error('fetchMetricTrend error:', e);
      throw e;
    }
  }

  async function createMetric(data: QualityMetricCreate) {
    error.value = null;
    try {
      const metric = await analyticsApi.quality.createMetric(data);
      metrics.value.push(metric);
      return metric;
    } catch (e) {
      error.value = 'Failed to create metric';
      console.error('createMetric error:', e);
      throw e;
    }
  }

  async function updateMetric(metricId: string, data: QualityMetricUpdate) {
    error.value = null;
    try {
      const updated = await analyticsApi.quality.updateMetric(metricId, data);
      const index = metrics.value.findIndex(m => m.id === metricId);
      if (index !== -1) {
        metrics.value[index] = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to update metric';
      console.error('updateMetric error:', e);
      throw e;
    }
  }

  async function deleteMetric(metricId: string) {
    error.value = null;
    try {
      await analyticsApi.quality.deleteMetric(metricId);
      metrics.value = metrics.value.filter(m => m.id !== metricId);
    } catch (e) {
      error.value = 'Failed to delete metric';
      console.error('deleteMetric error:', e);
      throw e;
    }
  }

  async function calculateMetric(metricId: string, cohortId?: string) {
    error.value = null;
    try {
      const score = await analyticsApi.quality.calculateMetric(metricId, cohortId);
      // Refresh metrics with scores after calculation
      await fetchMetricsWithScores();
      return score;
    } catch (e) {
      error.value = 'Failed to calculate metric';
      console.error('calculateMetric error:', e);
      throw e;
    }
  }

  async function initializeTemplates() {
    error.value = null;
    try {
      const newMetrics = await analyticsApi.quality.initializeTemplates();
      metrics.value = [...metrics.value, ...newMetrics];
      return newMetrics;
    } catch (e) {
      error.value = 'Failed to initialize templates';
      console.error('initializeTemplates error:', e);
      throw e;
    }
  }

  // ==========================================================================
  // Dashboard Actions
  // ==========================================================================

  async function fetchDashboards(dashboardType?: string) {
    dashboardsLoading.value = true;
    error.value = null;
    try {
      dashboards.value = await analyticsApi.dashboards.list({ dashboardType });
    } catch (e) {
      error.value = 'Failed to fetch dashboards';
      console.error('fetchDashboards error:', e);
    } finally {
      dashboardsLoading.value = false;
    }
  }

  async function fetchDashboard(dashboardId: string) {
    dashboardsLoading.value = true;
    error.value = null;
    try {
      selectedDashboard.value = await analyticsApi.dashboards.get(dashboardId);
    } catch (e) {
      error.value = 'Failed to fetch dashboard';
      console.error('fetchDashboard error:', e);
    } finally {
      dashboardsLoading.value = false;
    }
  }

  async function createDashboard(data: DashboardCreate) {
    error.value = null;
    try {
      const dashboard = await analyticsApi.dashboards.create(data);
      dashboards.value.push(dashboard);
      return dashboard;
    } catch (e) {
      error.value = 'Failed to create dashboard';
      console.error('createDashboard error:', e);
      throw e;
    }
  }

  async function updateDashboard(dashboardId: string, data: DashboardUpdate) {
    error.value = null;
    try {
      const updated = await analyticsApi.dashboards.update(dashboardId, data);
      const index = dashboards.value.findIndex(d => d.id === dashboardId);
      if (index !== -1) {
        dashboards.value[index] = updated;
      }
      if (selectedDashboard.value?.id === dashboardId) {
        selectedDashboard.value = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to update dashboard';
      console.error('updateDashboard error:', e);
      throw e;
    }
  }

  async function deleteDashboard(dashboardId: string) {
    error.value = null;
    try {
      await analyticsApi.dashboards.delete(dashboardId);
      dashboards.value = dashboards.value.filter(d => d.id !== dashboardId);
      if (selectedDashboard.value?.id === dashboardId) {
        selectedDashboard.value = null;
      }
    } catch (e) {
      error.value = 'Failed to delete dashboard';
      console.error('deleteDashboard error:', e);
      throw e;
    }
  }

  async function duplicateDashboard(dashboardId: string, newName: string) {
    error.value = null;
    try {
      const dashboard = await analyticsApi.dashboards.duplicate(dashboardId, newName);
      dashboards.value.push(dashboard);
      return dashboard;
    } catch (e) {
      error.value = 'Failed to duplicate dashboard';
      console.error('duplicateDashboard error:', e);
      throw e;
    }
  }

  async function fetchDashboardStatistics() {
    try {
      dashboardStatistics.value = await analyticsApi.dashboards.getStatistics();
    } catch (e) {
      console.error('fetchDashboardStatistics error:', e);
    }
  }

  // ==========================================================================
  // Report Actions
  // ==========================================================================

  async function fetchReports(params?: { reportType?: string; status?: string }) {
    reportsLoading.value = true;
    error.value = null;
    try {
      reports.value = await analyticsApi.reports.list(params);
    } catch (e) {
      error.value = 'Failed to fetch reports';
      console.error('fetchReports error:', e);
    } finally {
      reportsLoading.value = false;
    }
  }

  async function fetchScheduledReports() {
    try {
      scheduledReports.value = await analyticsApi.reports.listScheduled();
    } catch (e) {
      console.error('fetchScheduledReports error:', e);
    }
  }

  async function createReport(data: ReportCreate) {
    error.value = null;
    try {
      const report = await analyticsApi.reports.create(data);
      reports.value.push(report);
      return report;
    } catch (e) {
      error.value = 'Failed to create report';
      console.error('createReport error:', e);
      throw e;
    }
  }

  async function updateReport(reportId: string, data: ReportUpdate) {
    error.value = null;
    try {
      const updated = await analyticsApi.reports.update(reportId, data);
      const index = reports.value.findIndex(r => r.id === reportId);
      if (index !== -1) {
        reports.value[index] = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to update report';
      console.error('updateReport error:', e);
      throw e;
    }
  }

  async function deleteReport(reportId: string) {
    error.value = null;
    try {
      await analyticsApi.reports.delete(reportId);
      reports.value = reports.value.filter(r => r.id !== reportId);
    } catch (e) {
      error.value = 'Failed to delete report';
      console.error('deleteReport error:', e);
      throw e;
    }
  }

  async function generateReport(reportId: string) {
    error.value = null;
    try {
      const updated = await analyticsApi.reports.generate(reportId);
      const index = reports.value.findIndex(r => r.id === reportId);
      if (index !== -1) {
        reports.value[index] = updated;
      }
      return updated;
    } catch (e) {
      error.value = 'Failed to generate report';
      console.error('generateReport error:', e);
      throw e;
    }
  }

  async function downloadReport(reportId: string) {
    error.value = null;
    try {
      return await analyticsApi.reports.download(reportId);
    } catch (e) {
      error.value = 'Failed to download report';
      console.error('downloadReport error:', e);
      throw e;
    }
  }

  async function fetchReportStatistics(days?: number) {
    try {
      reportStatistics.value = await analyticsApi.reports.getStatistics(days);
    } catch (e) {
      console.error('fetchReportStatistics error:', e);
    }
  }

  // ==========================================================================
  // Utility Actions
  // ==========================================================================

  function reset() {
    models.value = [];
    selectedModel.value = null;
    modelStatistics.value = null;
    predictions.value = [];
    highRiskPredictions.value = [];
    predictionStatistics.value = null;
    metrics.value = [];
    metricsWithScores.value = [];
    qualitySummary.value = null;
    metricTrends.value.clear();
    dashboards.value = [];
    selectedDashboard.value = null;
    dashboardStatistics.value = null;
    reports.value = [];
    scheduledReports.value = [];
    reportStatistics.value = null;
    error.value = null;
  }

  async function refreshAll() {
    await Promise.all([
      fetchModels(),
      fetchModelStatistics(),
      fetchPredictionStatistics(),
      fetchHighRiskPredictions(10),
      fetchMetricsWithScores(),
      fetchQualitySummary(),
      fetchDashboards(),
      fetchDashboardStatistics(),
      fetchReports(),
      fetchReportStatistics(),
    ]);
  }

  return {
    // State
    models,
    selectedModel,
    modelStatistics,
    modelsLoading,
    predictions,
    highRiskPredictions,
    predictionStatistics,
    predictionsLoading,
    metrics,
    metricsWithScores,
    qualitySummary,
    metricTrends,
    metricsLoading,
    dashboards,
    selectedDashboard,
    dashboardStatistics,
    dashboardsLoading,
    reports,
    scheduledReports,
    reportStatistics,
    reportsLoading,
    error,

    // Computed
    activeModels,
    healthScore,
    criticalMetrics,
    warningMetrics,
    recentHighRiskCount,

    // Model Actions
    fetchModels,
    fetchModel,
    createModel,
    updateModel,
    deleteModel,
    activateModel,
    fetchModelStatistics,

    // Prediction Actions
    fetchPredictions,
    fetchHighRiskPredictions,
    addPredictionFeedback,
    fetchPredictionStatistics,

    // Quality Metric Actions
    fetchMetrics,
    fetchMetricsWithScores,
    fetchQualitySummary,
    fetchMetricTrend,
    createMetric,
    updateMetric,
    deleteMetric,
    calculateMetric,
    initializeTemplates,

    // Dashboard Actions
    fetchDashboards,
    fetchDashboard,
    createDashboard,
    updateDashboard,
    deleteDashboard,
    duplicateDashboard,
    fetchDashboardStatistics,

    // Report Actions
    fetchReports,
    fetchScheduledReports,
    createReport,
    updateReport,
    deleteReport,
    generateReport,
    downloadReport,
    fetchReportStatistics,

    // Utility Actions
    reset,
    refreshAll,
  };
});
