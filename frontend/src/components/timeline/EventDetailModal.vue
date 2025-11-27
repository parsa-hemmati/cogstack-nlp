<template>
  <v-dialog
    :model-value="modelValue"
    max-width="600"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card v-if="event">
      <v-card-title class="d-flex align-center justify-space-between">
        <span>{{ event.title }}</span>
        <v-btn
          icon="mdi-close"
          size="small"
          variant="text"
          data-test="close-button"
          @click="$emit('update:modelValue', false)"
        />
      </v-card-title>

      <v-divider />

      <v-card-text class="pa-4">
        <!-- Event Metadata -->
        <div class="event-metadata mb-4">
          <v-row dense>
            <v-col cols="6">
              <div class="metadata-item">
                <v-icon size="small" class="mr-1">mdi-calendar</v-icon>
                <span class="metadata-label">Date:</span>
                <span class="metadata-value" data-test="event-date">
                  {{ formatDate(event.date) }}
                </span>
              </div>
            </v-col>

            <v-col cols="6">
              <div class="metadata-item">
                <v-icon size="small" class="mr-1">mdi-tag</v-icon>
                <span class="metadata-label">Type:</span>
                <span class="metadata-value">{{ event.event_type }}</span>
              </div>
            </v-col>

            <v-col v-if="event.specialty" cols="6">
              <div class="metadata-item" data-test="event-specialty">
                <v-icon size="small" class="mr-1">mdi-medical-bag</v-icon>
                <span class="metadata-label">Specialty:</span>
                <span class="metadata-value">{{ event.specialty }}</span>
              </div>
            </v-col>

            <v-col v-if="event.provider" cols="6">
              <div class="metadata-item" data-test="event-provider">
                <v-icon size="small" class="mr-1">mdi-doctor</v-icon>
                <span class="metadata-label">Provider:</span>
                <span class="metadata-value">{{ event.provider }}</span>
              </div>
            </v-col>

            <v-col v-if="event.location" cols="12">
              <div class="metadata-item" data-test="event-location">
                <v-icon size="small" class="mr-1">mdi-map-marker</v-icon>
                <span class="metadata-label">Location:</span>
                <span class="metadata-value">{{ event.location }}</span>
              </div>
            </v-col>
          </v-row>
        </div>

        <!-- Event Description -->
        <div v-if="event.description" class="event-description mb-4">
          <h4 class="section-title">Description</h4>
          <p data-test="event-description">{{ event.description }}</p>
        </div>

        <!-- Clinical Coding -->
        <div v-if="event.concept_cui || event.concept_name" class="clinical-coding mb-4">
          <h4 class="section-title">Clinical Coding</h4>
          <div class="d-flex align-center">
            <v-chip
              v-if="event.concept_cui"
              size="small"
              class="mr-2"
              data-test="concept-cui"
            >
              <v-icon size="small" class="mr-1">mdi-code-tags</v-icon>
              {{ event.concept_cui }}
            </v-chip>
            <span v-if="event.concept_name" data-test="concept-name">
              {{ event.concept_name }}
            </span>
          </div>
        </div>

        <!-- Confidence Score -->
        <div v-if="event.confidence !== undefined" class="confidence-score mb-4">
          <h4 class="section-title">Confidence</h4>
          <div class="d-flex align-center">
            <v-progress-linear
              :model-value="event.confidence * 100"
              :color="getConfidenceColor(event.confidence)"
              height="10"
              rounded
              class="mr-2"
              style="max-width: 200px;"
            />
            <span data-test="confidence-score">{{ (event.confidence * 100).toFixed(0) }}%</span>
          </div>
        </div>

        <!-- Meta-Annotations -->
        <div v-if="event.meta_annotations" class="meta-annotations mb-4">
          <h4 class="section-title">Meta-Annotations</h4>

          <div class="meta-annotation-grid">
            <!-- Negation -->
            <div class="meta-annotation-item">
              <span class="meta-label">Negation:</span>
              <v-chip
                :color="event.meta_annotations.Negation === 'Affirmed' ? 'success' : 'error'"
                size="small"
                :class="{
                  'badge--affirmed': event.meta_annotations.Negation === 'Affirmed',
                  'badge--negated': event.meta_annotations.Negation === 'Negated'
                }"
                data-test="meta-negation"
              >
                {{ event.meta_annotations.Negation }}
              </v-chip>
            </div>

            <!-- Temporality -->
            <div class="meta-annotation-item">
              <span class="meta-label">Temporality:</span>
              <v-chip
                size="small"
                data-test="meta-temporality"
              >
                <v-icon size="small" class="mr-1">
                  {{ getTemporalityIcon(event.meta_annotations.Temporality) }}
                </v-icon>
                {{ event.meta_annotations.Temporality }}
              </v-chip>
            </div>

            <!-- Experiencer -->
            <div class="meta-annotation-item">
              <span class="meta-label">Experiencer:</span>
              <v-chip
                size="small"
                :class="{
                  'badge--patient': event.meta_annotations.Experiencer === 'Patient',
                  'badge--family': event.meta_annotations.Experiencer === 'Family'
                }"
                data-test="meta-experiencer"
              >
                {{ event.meta_annotations.Experiencer }}
              </v-chip>
            </div>

            <!-- Certainty -->
            <div class="meta-annotation-item">
              <span class="meta-label">Certainty:</span>
              <div class="certainty-stars">
                <v-icon
                  v-for="n in getCertaintyStars(event.meta_annotations.Certainty)"
                  :key="n"
                  size="small"
                  color="amber"
                  data-test="certainty-star"
                >
                  mdi-star
                </v-icon>
                <v-icon
                  v-for="n in (5 - getCertaintyStars(event.meta_annotations.Certainty))"
                  :key="'empty-' + n"
                  size="small"
                  color="grey-lighten-2"
                >
                  mdi-star-outline
                </v-icon>
              </div>
            </div>
          </div>
        </div>

        <!-- Source Document -->
        <div v-if="event.source_document_id" class="source-document mb-4">
          <h4 class="section-title">Source Document</h4>
          <v-btn
            variant="outlined"
            size="small"
            :href="`/documents/${event.source_document_id}`"
            target="_blank"
            data-test="source-document-link"
          >
            <v-icon size="small" class="mr-1">mdi-file-document</v-icon>
            View Document
            <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
          </v-btn>
        </div>

        <!-- Related Events -->
        <div v-if="relatedEvents && relatedEvents.length > 0" class="related-events" data-test="related-events">
          <h4 class="section-title">Related Events</h4>
          <v-list density="compact">
            <v-list-item
              v-for="(relatedEvent, index) in relatedEvents"
              :key="relatedEvent.id"
              :data-test="`related-event-${index}`"
              @click="$emit('event-clicked', relatedEvent.id)"
            >
              <template #prepend>
                <v-icon size="small">mdi-calendar</v-icon>
              </template>
              <v-list-item-title>{{ relatedEvent.title }}</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(relatedEvent.date) }}</v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </div>
      </v-card-text>

      <v-divider />

      <v-card-actions>
        <v-btn
          variant="text"
          data-test="copy-details-button"
          @click="copyEventDetails"
        >
          <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
          Copy Details
        </v-btn>
        <v-spacer />
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          Close
        </v-btn>
      </v-card-actions>

      <!-- Copy Success Snackbar -->
      <v-snackbar
        v-model="copySuccess"
        timeout="2000"
        color="success"
        data-test="copy-success-message"
      >
        Copied to clipboard!
      </v-snackbar>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { TimelineEvent } from '@/types/timeline'

interface Props {
  modelValue: boolean
  event: TimelineEvent | null
  relatedEvents?: TimelineEvent[]
}

const props = withDefaults(defineProps<Props>(), {
  event: null,
  relatedEvents: () => []
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'event-clicked': [eventId: string]
}>()

const copySuccess = ref(false)

// Format date for display
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// Get confidence color
const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.9) return 'success'
  if (confidence >= 0.7) return 'warning'
  return 'error'
}

// Get temporality icon
const getTemporalityIcon = (temporality: string) => {
  switch (temporality) {
    case 'Current':
      return 'mdi-clock-outline'
    case 'Recent':
      return 'mdi-clock-time-four-outline'
    case 'Historical':
      return 'mdi-history'
    default:
      return 'mdi-clock'
  }
}

// Get certainty stars (1-5)
const getCertaintyStars = (certainty: string) => {
  switch (certainty) {
    case 'High':
    case 'Definite':
      return 5
    case 'Medium':
    case 'Probable':
      return 3
    case 'Low':
    case 'Possible':
      return 1
    default:
      return 3
  }
}

// Copy event details to clipboard
const copyEventDetails = async () => {
  if (!props.event) return

  const details = `
Event: ${props.event.title}
Type: ${props.event.event_type}
Date: ${formatDate(props.event.date)}
${props.event.description ? `Description: ${props.event.description}\n` : ''}
${props.event.concept_cui ? `SNOMED CT Code: ${props.event.concept_cui}\n` : ''}
${props.event.concept_name ? `Concept: ${props.event.concept_name}\n` : ''}
${props.event.confidence !== undefined ? `Confidence: ${(props.event.confidence * 100).toFixed(0)}%\n` : ''}
${props.event.specialty ? `Specialty: ${props.event.specialty}\n` : ''}
${props.event.provider ? `Provider: ${props.event.provider}\n` : ''}
${props.event.location ? `Location: ${props.event.location}\n` : ''}
${props.event.meta_annotations ? `\nMeta-Annotations:
- Negation: ${props.event.meta_annotations.Negation}
- Temporality: ${props.event.meta_annotations.Temporality}
- Experiencer: ${props.event.meta_annotations.Experiencer}
- Certainty: ${props.event.meta_annotations.Certainty}
` : ''}
  `.trim()

  try {
    await navigator.clipboard.writeText(details)
    copySuccess.value = true
  } catch (error) {
    console.error('Failed to copy to clipboard:', error)
  }
}
</script>

<style scoped>
.event-metadata {
  background-color: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
}

.metadata-item {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.metadata-label {
  font-weight: 600;
  margin-right: 4px;
  margin-left: 4px;
  font-size: 13px;
}

.metadata-value {
  font-size: 13px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  color: rgba(0, 0, 0, 0.87);
}

.event-description p {
  margin: 0;
  line-height: 1.5;
}

.meta-annotation-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.meta-annotation-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.meta-label {
  font-weight: 600;
  font-size: 13px;
}

.certainty-stars {
  display: flex;
  align-items: center;
}

.badge--affirmed {
  background-color: #4caf50 !important;
  color: white !important;
}

.badge--negated {
  background-color: #f44336 !important;
  color: white !important;
}

.badge--patient {
  background-color: #2196f3 !important;
  color: white !important;
}

.badge--family {
  background-color: #ff9800 !important;
  color: white !important;
}

@media (max-width: 600px) {
  .meta-annotation-grid {
    grid-template-columns: 1fr;
  }
}
</style>
