<template>
  <v-card class="model-card" variant="outlined">
    <v-card-text class="pa-4">
      <div class="d-flex align-center justify-space-between mb-3">
        <div class="d-flex align-center gap-2">
          <v-icon :icon="modelTypeIcon" :color="modelTypeColor" />
          <div>
            <div class="text-subtitle-1 font-weight-bold">{{ model.name }}</div>
            <div class="text-caption text-grey">v{{ model.version }}</div>
          </div>
        </div>
        <v-chip :color="statusColor" size="small" variant="flat">
          {{ statusLabel }}
        </v-chip>
      </div>

      <p v-if="model.description" class="text-body-2 text-grey mb-3">
        {{ model.description }}
      </p>

      <!-- Model Info -->
      <div class="model-info mb-3">
        <div v-if="model.algorithm" class="info-item">
          <span class="info-label">Algorithm:</span>
          <span class="info-value">{{ model.algorithm }}</span>
        </div>
        <div v-if="model.framework" class="info-item">
          <span class="info-label">Framework:</span>
          <span class="info-value">{{ model.framework }}</span>
        </div>
        <div v-if="model.trainingSamples" class="info-item">
          <span class="info-label">Training Samples:</span>
          <span class="info-value">{{ formatNumber(model.trainingSamples) }}</span>
        </div>
      </div>

      <!-- Metrics Display -->
      <div v-if="model.trainingMetrics && Object.keys(model.trainingMetrics).length > 0" class="metrics-section">
        <div class="text-caption font-weight-medium mb-2">Training Metrics</div>
        <div class="metrics-grid">
          <div
            v-for="(value, key) in displayMetrics"
            :key="key"
            class="metric-item"
          >
            <div class="metric-value">{{ formatMetricValue(value) }}</div>
            <div class="metric-label">{{ formatMetricLabel(key as string) }}</div>
          </div>
        </div>
      </div>

      <!-- Tags -->
      <div v-if="model.tags && model.tags.length > 0" class="mt-3">
        <v-chip
          v-for="tag in model.tags"
          :key="tag"
          size="x-small"
          class="mr-1"
          variant="outlined"
        >
          {{ tag }}
        </v-chip>
      </div>
    </v-card-text>

    <v-divider />

    <v-card-actions class="px-4">
      <v-btn
        v-if="model.status === 'trained'"
        size="small"
        color="success"
        variant="flat"
        @click="$emit('activate')"
      >
        <v-icon start size="small">mdi-power</v-icon>
        Activate
      </v-btn>
      <v-btn
        v-if="model.status === 'active'"
        size="small"
        color="primary"
        variant="text"
        @click="$emit('predict')"
      >
        <v-icon start size="small">mdi-brain</v-icon>
        Predict
      </v-btn>
      <v-spacer />
      <v-btn
        icon="mdi-dots-vertical"
        size="small"
        variant="text"
        @click="$emit('menu')"
      />
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { AnalyticsModel, ModelStatus, ModelType } from '@/types/analytics';

interface Props {
  model: AnalyticsModel;
}

const props = defineProps<Props>();

defineEmits<{
  activate: [];
  predict: [];
  menu: [];
}>();

const modelTypeIcon = computed(() => {
  const icons: Record<ModelType, string> = {
    classification: 'mdi-tag-multiple',
    regression: 'mdi-chart-line',
    clustering: 'mdi-chart-bubble',
    nlp: 'mdi-text-recognition',
  };
  return icons[props.model.modelType] ?? 'mdi-brain';
});

const modelTypeColor = computed(() => {
  const colors: Record<ModelType, string> = {
    classification: 'primary',
    regression: 'info',
    clustering: 'secondary',
    nlp: 'success',
  };
  return colors[props.model.modelType] ?? 'grey';
});

const statusColor = computed(() => {
  const colors: Record<ModelStatus, string> = {
    draft: 'grey',
    training: 'info',
    trained: 'success',
    active: 'primary',
    deprecated: 'warning',
    archived: 'grey-darken-1',
  };
  return colors[props.model.status] ?? 'grey';
});

const statusLabel = computed(() => {
  const labels: Record<ModelStatus, string> = {
    draft: 'Draft',
    training: 'Training',
    trained: 'Trained',
    active: 'Active',
    deprecated: 'Deprecated',
    archived: 'Archived',
  };
  return labels[props.model.status] ?? props.model.status;
});

const displayMetrics = computed(() => {
  if (!props.model.trainingMetrics) return {};

  const priorityKeys = ['accuracy', 'precision', 'recall', 'f1', 'auc', 'rmse', 'mae'];
  const metrics: Record<string, number> = {};
  let count = 0;

  for (const key of priorityKeys) {
    if (key in props.model.trainingMetrics && count < 4) {
      metrics[key] = props.model.trainingMetrics[key];
      count++;
    }
  }

  return metrics;
});

function formatNumber(num: number): string {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
}

function formatMetricValue(value: number): string {
  if (value < 1) return (value * 100).toFixed(1) + '%';
  return value.toFixed(2);
}

function formatMetricLabel(key: string): string {
  const labels: Record<string, string> = {
    accuracy: 'Accuracy',
    precision: 'Precision',
    recall: 'Recall',
    f1: 'F1 Score',
    auc: 'AUC',
    rmse: 'RMSE',
    mae: 'MAE',
  };
  return labels[key] ?? key;
}
</script>

<style scoped>
.model-card {
  transition: all 0.2s ease;
}

.model-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.model-info {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.info-item {
  display: flex;
  gap: 4px;
  font-size: 0.875rem;
}

.info-label {
  color: rgba(var(--v-theme-on-surface), 0.6);
}

.info-value {
  font-weight: 500;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.metric-item {
  text-align: center;
  padding: 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border-radius: 4px;
}

.metric-value {
  font-size: 1rem;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}

.metric-label {
  font-size: 0.625rem;
  color: rgba(var(--v-theme-on-surface), 0.6);
  text-transform: uppercase;
}
</style>
