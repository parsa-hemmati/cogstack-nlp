<template>
  <div class="quality-gauge">
    <div class="gauge-container">
      <svg :width="size" :height="size" viewBox="0 0 100 100">
        <!-- Background circle -->
        <circle
          cx="50"
          cy="50"
          :r="radius"
          fill="none"
          :stroke="backgroundColor"
          :stroke-width="strokeWidth"
        />
        <!-- Progress arc -->
        <circle
          cx="50"
          cy="50"
          :r="radius"
          fill="none"
          :stroke="gaugeColor"
          :stroke-width="strokeWidth"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="dashOffset"
          stroke-linecap="round"
          transform="rotate(-90 50 50)"
          class="progress-circle"
        />
        <!-- Center text -->
        <text
          x="50"
          y="50"
          text-anchor="middle"
          dominant-baseline="middle"
          :class="['gauge-value', sizeClass]"
        >
          {{ displayValue }}
        </text>
        <text
          x="50"
          y="65"
          text-anchor="middle"
          class="gauge-label"
        >
          {{ label }}
        </text>
      </svg>
    </div>

    <div v-if="showLegend" class="gauge-legend mt-3">
      <div class="legend-item">
        <span class="legend-dot success"></span>
        <span class="text-caption">On Target</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot warning"></span>
        <span class="text-caption">Warning</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot error"></span>
        <span class="text-caption">Critical</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  value: number;
  maxValue?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  showLegend?: boolean;
  suffix?: string;
}

const props = withDefaults(defineProps<Props>(), {
  maxValue: 100,
  size: 160,
  strokeWidth: 10,
  label: 'Health Score',
  showLegend: false,
  suffix: '%',
});

const radius = computed(() => (100 - props.strokeWidth) / 2);
const circumference = computed(() => 2 * Math.PI * radius.value);

const normalizedValue = computed(() => {
  return Math.min(Math.max(props.value, 0), props.maxValue);
});

const dashOffset = computed(() => {
  const progress = normalizedValue.value / props.maxValue;
  return circumference.value * (1 - progress);
});

const gaugeColor = computed(() => {
  const percent = (normalizedValue.value / props.maxValue) * 100;
  if (percent >= 80) return 'rgb(var(--v-theme-success))';
  if (percent >= 60) return 'rgb(var(--v-theme-warning))';
  return 'rgb(var(--v-theme-error))';
});

const backgroundColor = computed(() => {
  return 'rgba(var(--v-theme-on-surface), 0.1)';
});

const displayValue = computed(() => {
  return `${Math.round(normalizedValue.value)}${props.suffix}`;
});

const sizeClass = computed(() => {
  if (props.size >= 200) return 'large';
  if (props.size >= 120) return 'medium';
  return 'small';
});
</script>

<style scoped>
.quality-gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gauge-container {
  position: relative;
}

.progress-circle {
  transition: stroke-dashoffset 0.5s ease-out;
}

.gauge-value {
  font-weight: 700;
  fill: currentColor;
}

.gauge-value.large {
  font-size: 24px;
}

.gauge-value.medium {
  font-size: 20px;
}

.gauge-value.small {
  font-size: 16px;
}

.gauge-label {
  font-size: 10px;
  fill: rgba(var(--v-theme-on-surface), 0.6);
}

.gauge-legend {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.legend-dot.success {
  background-color: rgb(var(--v-theme-success));
}

.legend-dot.warning {
  background-color: rgb(var(--v-theme-warning));
}

.legend-dot.error {
  background-color: rgb(var(--v-theme-error));
}
</style>
