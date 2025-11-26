<template>
  <v-card class="quality-summary-card">
    <v-card-text class="pa-6">
      <div class="d-flex align-center mb-4">
        <div>
          <h3 class="text-h5 font-weight-bold">Quality Overview</h3>
          <p class="text-body-2 text-grey">System health and metric status</p>
        </div>
        <v-spacer />
        <v-btn
          v-if="showRefresh"
          icon="mdi-refresh"
          variant="text"
          size="small"
          @click="$emit('refresh')"
          :loading="loading"
        />
      </div>

      <div class="d-flex flex-column flex-md-row align-center gap-6">
        <!-- Health Score Gauge -->
        <div class="gauge-section">
          <quality-gauge
            :value="summary?.healthScore ?? 0"
            :size="180"
            label="Health Score"
            show-legend
          />
        </div>

        <!-- Status Breakdown -->
        <div class="status-breakdown flex-grow-1">
          <div class="status-grid">
            <div class="status-item on-target">
              <div class="status-value text-h4 font-weight-bold text-success">
                {{ summary?.onTarget ?? 0 }}
              </div>
              <div class="status-label text-caption text-grey">On Target</div>
            </div>

            <div class="status-item warning">
              <div class="status-value text-h4 font-weight-bold text-warning">
                {{ summary?.warning ?? 0 }}
              </div>
              <div class="status-label text-caption text-grey">Warning</div>
            </div>

            <div class="status-item critical">
              <div class="status-value text-h4 font-weight-bold text-error">
                {{ summary?.critical ?? 0 }}
              </div>
              <div class="status-label text-caption text-grey">Critical</div>
            </div>

            <div class="status-item unknown">
              <div class="status-value text-h4 font-weight-bold text-grey">
                {{ summary?.unknown ?? 0 }}
              </div>
              <div class="status-label text-caption text-grey">Unknown</div>
            </div>
          </div>

          <v-divider class="my-4" />

          <!-- Category Breakdown -->
          <div v-if="summary?.byCategory" class="category-breakdown">
            <div class="text-subtitle-2 mb-2">By Category</div>
            <div class="category-grid">
              <div
                v-for="(counts, category) in summary.byCategory"
                :key="category"
                class="category-item"
              >
                <div class="category-name text-caption">{{ formatCategory(category) }}</div>
                <div class="category-bars">
                  <div
                    v-if="counts.on_target"
                    class="bar success"
                    :style="{ width: getBarWidth(counts.on_target, category) }"
                  />
                  <div
                    v-if="counts.warning"
                    class="bar warning"
                    :style="{ width: getBarWidth(counts.warning, category) }"
                  />
                  <div
                    v-if="counts.critical"
                    class="bar error"
                    :style="{ width: getBarWidth(counts.critical, category) }"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import type { QualitySummary, MetricCategory } from '@/types/analytics';
import QualityGauge from './QualityGauge.vue';

interface Props {
  summary: QualitySummary | null;
  loading?: boolean;
  showRefresh?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  showRefresh: true,
});

defineEmits<{
  refresh: [];
}>();

function formatCategory(category: string): string {
  const labels: Record<MetricCategory, string> = {
    nlp_accuracy: 'NLP Accuracy',
    data_quality: 'Data Quality',
    clinical_outcomes: 'Clinical Outcomes',
    operational: 'Operational',
  };
  return labels[category as MetricCategory] ?? category;
}

function getBarWidth(count: number, category: string): string {
  if (!props.summary?.byCategory) return '0%';
  const categoryData = props.summary.byCategory[category as MetricCategory];
  if (!categoryData) return '0%';

  const total = categoryData.on_target + categoryData.warning + categoryData.critical + categoryData.unknown;
  if (total === 0) return '0%';

  return `${(count / total) * 100}%`;
}
</script>

<style scoped>
.quality-summary-card {
  background: linear-gradient(135deg, rgba(var(--v-theme-surface), 1) 0%, rgba(var(--v-theme-surface-variant), 0.3) 100%);
}

.gauge-section {
  flex-shrink: 0;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.status-item {
  text-align: center;
  padding: 16px;
  border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.category-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.category-name {
  width: 120px;
  flex-shrink: 0;
}

.category-bars {
  flex-grow: 1;
  height: 8px;
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(var(--v-theme-on-surface), 0.1);
}

.bar {
  height: 100%;
  transition: width 0.3s ease;
}

.bar.success {
  background-color: rgb(var(--v-theme-success));
}

.bar.warning {
  background-color: rgb(var(--v-theme-warning));
}

.bar.error {
  background-color: rgb(var(--v-theme-error));
}

@media (max-width: 960px) {
  .status-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
