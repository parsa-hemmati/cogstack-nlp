<template>
  <v-card :class="['quality-metric-card', statusClass]" variant="outlined">
    <v-card-text class="pa-4">
      <div class="d-flex align-center justify-space-between mb-2">
        <div class="metric-name text-body-2 text-grey-darken-1">
          {{ metric.name }}
        </div>
        <v-chip :color="statusColor" size="x-small" variant="flat">
          {{ statusLabel }}
        </v-chip>
      </div>

      <div class="d-flex align-center">
        <div class="metric-value text-h4 font-weight-bold">
          {{ formattedValue }}
        </div>
        <div v-if="score?.changePercentage" class="ml-2">
          <v-icon
            :icon="changeIcon"
            :color="changeColor"
            size="small"
          />
          <span :class="['text-caption', changeColor + '--text']">
            {{ Math.abs(score.changePercentage).toFixed(1) }}%
          </span>
        </div>
      </div>

      <div v-if="metric.targetValue" class="mt-2">
        <v-progress-linear
          :model-value="progressValue"
          :color="statusColor"
          height="6"
          rounded
        />
        <div class="d-flex justify-space-between mt-1">
          <span class="text-caption text-grey">Current</span>
          <span class="text-caption text-grey">Target: {{ metric.targetValue }}{{ metric.unit }}</span>
        </div>
      </div>

      <div v-if="metric.description" class="mt-2 text-caption text-grey">
        {{ metric.description }}
      </div>
    </v-card-text>

    <v-card-actions v-if="showActions" class="px-4 pb-3">
      <v-btn
        size="small"
        variant="text"
        color="primary"
        @click="$emit('view-trend')"
      >
        <v-icon start size="small">mdi-chart-line</v-icon>
        Trend
      </v-btn>
      <v-btn
        size="small"
        variant="text"
        @click="$emit('calculate')"
        :loading="calculating"
      >
        <v-icon start size="small">mdi-refresh</v-icon>
        Calculate
      </v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { QualityMetric, QualityScore, MetricStatus } from '@/types/analytics';

interface Props {
  metric: QualityMetric;
  score?: QualityScore | null;
  showActions?: boolean;
  calculating?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  showActions: true,
  calculating: false,
});

defineEmits<{
  'view-trend': [];
  'calculate': [];
}>();

const status = computed<MetricStatus>(() => {
  return props.score?.status ?? 'unknown';
});

const statusColor = computed(() => {
  switch (status.value) {
    case 'on_target': return 'success';
    case 'warning': return 'warning';
    case 'critical': return 'error';
    default: return 'grey';
  }
});

const statusLabel = computed(() => {
  switch (status.value) {
    case 'on_target': return 'On Target';
    case 'warning': return 'Warning';
    case 'critical': return 'Critical';
    default: return 'Unknown';
  }
});

const statusClass = computed(() => {
  return `status-${status.value}`;
});

const formattedValue = computed(() => {
  if (!props.score) return '--';

  const value = props.score.value;
  const decimals = props.metric.decimalPlaces ?? 2;

  if (props.metric.metricType === 'percentage') {
    return `${value.toFixed(decimals)}%`;
  }
  if (props.metric.unit) {
    return `${value.toFixed(decimals)}${props.metric.unit}`;
  }
  return value.toFixed(decimals);
});

const progressValue = computed(() => {
  if (!props.score || !props.metric.targetValue) return 0;

  const value = props.score.value;
  const target = props.metric.targetValue;
  const operator = props.metric.comparisonOperator;

  if (operator === '>=' || operator === '>') {
    return Math.min((value / target) * 100, 100);
  }
  if (operator === '<=' || operator === '<') {
    return Math.min((target / value) * 100, 100);
  }
  return value === target ? 100 : Math.abs(1 - Math.abs(value - target) / target) * 100;
});

const changeIcon = computed(() => {
  if (!props.score?.changePercentage) return '';
  return props.score.changePercentage >= 0 ? 'mdi-arrow-up' : 'mdi-arrow-down';
});

const changeColor = computed(() => {
  if (!props.score?.changePercentage) return 'grey';
  const isPositiveGood = ['>=', '>'].includes(props.metric.comparisonOperator);
  const isPositive = props.score.changePercentage >= 0;

  if (isPositiveGood) {
    return isPositive ? 'success' : 'error';
  }
  return isPositive ? 'error' : 'success';
});
</script>

<style scoped>
.quality-metric-card {
  transition: all 0.2s ease;
}

.quality-metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.status-on_target {
  border-left: 4px solid rgb(var(--v-theme-success));
}

.status-warning {
  border-left: 4px solid rgb(var(--v-theme-warning));
}

.status-critical {
  border-left: 4px solid rgb(var(--v-theme-error));
}

.status-unknown {
  border-left: 4px solid rgb(var(--v-theme-grey));
}
</style>
