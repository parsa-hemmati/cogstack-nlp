<template>
  <div class="analytics-view pa-4">
    <v-container fluid>
      <!-- Header -->
      <div class="d-flex align-center mb-4">
        <div>
          <h1 class="text-h4 font-weight-bold">Advanced Analytics</h1>
          <p class="text-body-2 text-grey">
            Quality metrics, ML models, and predictive analytics
          </p>
        </div>
        <v-spacer />
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          variant="outlined"
          @click="refreshAll"
          :loading="isLoading"
          class="mr-2"
        >
          Refresh
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="showCreateDialog"
        >
          Create
        </v-btn>
      </div>

      <!-- Tabs -->
      <v-tabs v-model="activeTab" class="mb-4">
        <v-tab value="quality">
          <v-icon start>mdi-chart-arc</v-icon>
          Quality Dashboard
        </v-tab>
        <v-tab value="models">
          <v-icon start>mdi-brain</v-icon>
          ML Models
          <v-badge
            v-if="activeModelsCount > 0"
            :content="activeModelsCount"
            color="success"
            inline
            class="ml-2"
          />
        </v-tab>
        <v-tab value="predictions">
          <v-icon start>mdi-crystal-ball</v-icon>
          Predictions
          <v-badge
            v-if="highRiskCount > 0"
            :content="highRiskCount"
            color="error"
            inline
            class="ml-2"
          />
        </v-tab>
        <v-tab value="reports">
          <v-icon start>mdi-file-document-outline</v-icon>
          Reports
        </v-tab>
      </v-tabs>

      <!-- Tab Content -->
      <v-window v-model="activeTab">
        <!-- Quality Dashboard Tab -->
        <v-window-item value="quality">
          <div class="quality-tab">
            <!-- Summary Card -->
            <quality-summary-card
              :summary="qualitySummary"
              :loading="metricsLoading"
              @refresh="fetchQualitySummary"
              class="mb-4"
            />

            <!-- Metrics Grid -->
            <div class="d-flex align-center justify-space-between mb-3">
              <h3 class="text-h6">Quality Metrics</h3>
              <div class="d-flex gap-2">
                <v-select
                  v-model="selectedCategory"
                  :items="categoryOptions"
                  label="Category"
                  density="compact"
                  variant="outlined"
                  hide-details
                  style="width: 180px"
                  clearable
                />
                <v-btn
                  v-if="metricsWithScores.length === 0"
                  size="small"
                  color="primary"
                  variant="outlined"
                  @click="initializeTemplates"
                >
                  Initialize Templates
                </v-btn>
              </div>
            </div>

            <v-row v-if="filteredMetrics.length > 0">
              <v-col
                v-for="item in filteredMetrics"
                :key="item.metric.id"
                cols="12"
                sm="6"
                md="4"
                lg="3"
              >
                <quality-metric-card
                  :metric="item.metric"
                  :score="item.score"
                  @view-trend="viewMetricTrend(item.metric)"
                  @calculate="calculateMetric(item.metric.id)"
                />
              </v-col>
            </v-row>

            <v-alert
              v-else-if="!metricsLoading"
              type="info"
              variant="tonal"
              class="mt-4"
            >
              No quality metrics found. Click "Initialize Templates" to create default metrics.
            </v-alert>
          </div>
        </v-window-item>

        <!-- ML Models Tab -->
        <v-window-item value="models">
          <div class="models-tab">
            <!-- Model Statistics -->
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card variant="tonal" color="primary">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ modelStatistics?.totalModels ?? 0 }}</div>
                    <div class="text-caption">Total Models</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="tonal" color="success">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ modelStatistics?.activeCount ?? 0 }}</div>
                    <div class="text-caption">Active</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="tonal" color="info">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ modelStatistics?.byStatus?.training ?? 0 }}</div>
                    <div class="text-caption">Training</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="tonal" color="warning">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ modelStatistics?.byStatus?.deprecated ?? 0 }}</div>
                    <div class="text-caption">Deprecated</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Model List -->
            <v-row v-if="models.length > 0">
              <v-col
                v-for="model in models"
                :key="model.id"
                cols="12"
                sm="6"
                lg="4"
              >
                <model-card
                  :model="model"
                  @activate="activateModel(model.id)"
                  @predict="showPredictDialog(model)"
                  @menu="showModelMenu(model)"
                />
              </v-col>
            </v-row>

            <v-alert
              v-else-if="!modelsLoading"
              type="info"
              variant="tonal"
              class="mt-4"
            >
              No ML models found. Click "Create" to register a new model.
            </v-alert>
          </div>
        </v-window-item>

        <!-- Predictions Tab -->
        <v-window-item value="predictions">
          <div class="predictions-tab">
            <!-- Prediction Statistics -->
            <v-row class="mb-4">
              <v-col cols="12" md="8">
                <v-card>
                  <v-card-text>
                    <div class="text-subtitle-2 mb-3">Prediction Statistics (Last 30 Days)</div>
                    <v-row>
                      <v-col cols="4">
                        <div class="text-h4 font-weight-bold">{{ predictionStatistics?.totalPredictions ?? 0 }}</div>
                        <div class="text-caption text-grey">Total Predictions</div>
                      </v-col>
                      <v-col cols="4">
                        <div class="text-h4 font-weight-bold">{{ predictionStatistics?.averageDaily?.toFixed(1) ?? 0 }}</div>
                        <div class="text-caption text-grey">Daily Average</div>
                      </v-col>
                      <v-col cols="4">
                        <div class="text-h4 font-weight-bold">
                          {{ predictionStatistics?.averageConfidence ? (predictionStatistics.averageConfidence * 100).toFixed(1) + '%' : '--' }}
                        </div>
                        <div class="text-caption text-grey">Avg Confidence</div>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card color="error" variant="tonal">
                  <v-card-text>
                    <div class="text-subtitle-2 mb-2">High Risk Alerts</div>
                    <div class="text-h3 font-weight-bold">{{ highRiskPredictions.length }}</div>
                    <div class="text-caption">Recent high-risk predictions</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- High Risk Predictions -->
            <div v-if="highRiskPredictions.length > 0" class="mb-4">
              <h3 class="text-h6 mb-3">High Risk Predictions</h3>
              <v-data-table
                :headers="predictionHeaders"
                :items="highRiskPredictions"
                :items-per-page="10"
                class="elevation-1"
              >
                <template #item.riskLevel="{ item }">
                  <v-chip :color="getRiskColor(item.riskLevel)" size="small">
                    {{ item.riskLevel }}
                  </v-chip>
                </template>
                <template #item.confidenceScore="{ item }">
                  {{ item.confidenceScore ? (item.confidenceScore * 100).toFixed(1) + '%' : '--' }}
                </template>
                <template #item.predictedAt="{ item }">
                  {{ formatDate(item.predictedAt) }}
                </template>
                <template #item.actions="{ item }">
                  <v-btn
                    icon="mdi-message-reply-text"
                    size="small"
                    variant="text"
                    @click="showFeedbackDialog(item)"
                  />
                </template>
              </v-data-table>
            </div>
          </div>
        </v-window-item>

        <!-- Reports Tab -->
        <v-window-item value="reports">
          <div class="reports-tab">
            <!-- Report Statistics -->
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportStatistics?.totalReports ?? 0 }}</div>
                    <div class="text-caption text-grey">Total Reports</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportStatistics?.scheduledReports ?? 0 }}</div>
                    <div class="text-caption text-grey">Scheduled</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">
                      {{ reportStatistics?.successRate ? (reportStatistics.successRate * 100).toFixed(0) + '%' : '--' }}
                    </div>
                    <div class="text-caption text-grey">Success Rate</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card variant="outlined">
                  <v-card-text class="text-center">
                    <div class="text-h4 font-weight-bold">{{ reportStatistics?.byStatus?.generating ?? 0 }}</div>
                    <div class="text-caption text-grey">Generating</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Reports List -->
            <v-data-table
              :headers="reportHeaders"
              :items="reports"
              :items-per-page="10"
              class="elevation-1"
            >
              <template #item.status="{ item }">
                <v-chip :color="getReportStatusColor(item.status)" size="small">
                  {{ item.status }}
                </v-chip>
              </template>
              <template #item.fileFormat="{ item }">
                <v-chip size="x-small" variant="outlined">
                  {{ item.fileFormat.toUpperCase() }}
                </v-chip>
              </template>
              <template #item.createdAt="{ item }">
                {{ formatDate(item.createdAt) }}
              </template>
              <template #item.actions="{ item }">
                <v-btn
                  v-if="item.status === 'completed'"
                  icon="mdi-download"
                  size="small"
                  variant="text"
                  @click="downloadReport(item.id)"
                />
                <v-btn
                  v-else-if="item.status === 'pending'"
                  icon="mdi-play"
                  size="small"
                  variant="text"
                  color="primary"
                  @click="generateReport(item.id)"
                />
              </template>
            </v-data-table>
          </div>
        </v-window-item>
      </v-window>

      <!-- Loading Overlay -->
      <v-overlay :model-value="isLoading" class="align-center justify-center">
        <v-progress-circular indeterminate size="64" />
      </v-overlay>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useAnalyticsStore } from '@/stores/analyticsStore';
import type { AnalyticsModel, Prediction, RiskLevel, ReportStatus } from '@/types/analytics';
import QualitySummaryCard from '@/components/analytics/QualitySummaryCard.vue';
import QualityMetricCard from '@/components/analytics/QualityMetricCard.vue';
import ModelCard from '@/components/analytics/ModelCard.vue';

const analyticsStore = useAnalyticsStore();
const {
  models,
  modelStatistics,
  modelsLoading,
  highRiskPredictions,
  predictionStatistics,
  predictionsLoading,
  metricsWithScores,
  qualitySummary,
  metricsLoading,
  reports,
  reportStatistics,
  reportsLoading,
} = storeToRefs(analyticsStore);

const activeTab = ref('quality');
const selectedCategory = ref<string | null>(null);
let refreshInterval: ReturnType<typeof setInterval> | null = null;

const categoryOptions = [
  { title: 'All Categories', value: null },
  { title: 'NLP Accuracy', value: 'nlp_accuracy' },
  { title: 'Data Quality', value: 'data_quality' },
  { title: 'Clinical Outcomes', value: 'clinical_outcomes' },
  { title: 'Operational', value: 'operational' },
];

const predictionHeaders = [
  { title: 'Type', key: 'predictionType' },
  { title: 'Risk Level', key: 'riskLevel' },
  { title: 'Confidence', key: 'confidenceScore' },
  { title: 'Patient ID', key: 'patientId' },
  { title: 'Predicted At', key: 'predictedAt' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const reportHeaders = [
  { title: 'Name', key: 'name' },
  { title: 'Type', key: 'reportType' },
  { title: 'Format', key: 'fileFormat' },
  { title: 'Status', key: 'status' },
  { title: 'Created', key: 'createdAt' },
  { title: 'Actions', key: 'actions', sortable: false },
];

const isLoading = computed(() =>
  modelsLoading.value || predictionsLoading.value || metricsLoading.value || reportsLoading.value
);

const activeModelsCount = computed(() =>
  models.value.filter(m => m.status === 'active').length
);

const highRiskCount = computed(() =>
  highRiskPredictions.value.length
);

const filteredMetrics = computed(() => {
  if (!selectedCategory.value) return metricsWithScores.value;
  return metricsWithScores.value.filter(m => m.metric.category === selectedCategory.value);
});

onMounted(async () => {
  await refreshAll();

  // Auto-refresh every 60 seconds
  refreshInterval = setInterval(() => {
    analyticsStore.fetchQualitySummary();
    analyticsStore.fetchHighRiskPredictions(10);
  }, 60000);
});

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
  analyticsStore.reset();
});

watch(activeTab, async (tab) => {
  if (tab === 'quality') {
    await analyticsStore.fetchMetricsWithScores();
    await analyticsStore.fetchQualitySummary();
  } else if (tab === 'models') {
    await analyticsStore.fetchModels();
    await analyticsStore.fetchModelStatistics();
  } else if (tab === 'predictions') {
    await analyticsStore.fetchPredictionStatistics();
    await analyticsStore.fetchHighRiskPredictions(20);
  } else if (tab === 'reports') {
    await analyticsStore.fetchReports();
    await analyticsStore.fetchReportStatistics();
  }
});

async function refreshAll() {
  await analyticsStore.refreshAll();
}

async function fetchQualitySummary() {
  await analyticsStore.fetchQualitySummary();
}

async function initializeTemplates() {
  await analyticsStore.initializeTemplates();
  await analyticsStore.fetchMetricsWithScores();
}

function viewMetricTrend(metric: { id: string; name: string }) {
  // TODO: Open trend dialog
  console.log('View trend for:', metric.name);
}

async function calculateMetric(metricId: string) {
  await analyticsStore.calculateMetric(metricId);
}

async function activateModel(modelId: string) {
  await analyticsStore.activateModel(modelId);
}

function showPredictDialog(model: AnalyticsModel) {
  // TODO: Open prediction dialog
  console.log('Predict with model:', model.name);
}

function showModelMenu(model: AnalyticsModel) {
  // TODO: Show model context menu
  console.log('Model menu:', model.name);
}

function showFeedbackDialog(prediction: Prediction) {
  // TODO: Open feedback dialog
  console.log('Feedback for prediction:', prediction.id);
}

async function generateReport(reportId: string) {
  await analyticsStore.generateReport(reportId);
}

async function downloadReport(reportId: string) {
  const download = await analyticsStore.downloadReport(reportId);
  if (download?.downloadUrl) {
    window.open(download.downloadUrl, '_blank');
  }
}

function showCreateDialog() {
  // TODO: Open create dialog based on active tab
  console.log('Create new:', activeTab.value);
}

function getRiskColor(risk?: RiskLevel): string {
  const colors: Record<RiskLevel, string> = {
    low: 'success',
    medium: 'warning',
    high: 'orange',
    critical: 'error',
  };
  return risk ? colors[risk] : 'grey';
}

function getReportStatusColor(status: ReportStatus): string {
  const colors: Record<ReportStatus, string> = {
    pending: 'grey',
    generating: 'info',
    completed: 'success',
    failed: 'error',
    cancelled: 'warning',
  };
  return colors[status] ?? 'grey';
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}
</script>

<style scoped>
.analytics-view {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-background));
}
</style>
