<template>
  <v-menu
    v-model="visible"
    :position-x="position.x"
    :position-y="position.y"
    absolute
  >
    <v-card v-if="concept" max-width="400">
      <v-card-title>
        {{ concept.concept_name }} ({{ concept.concept_cui }})
      </v-card-title>

      <v-card-subtitle>
        {{ formatDate(concept.date) }}
      </v-card-subtitle>

      <v-card-text>
        <p class="text-body-2 mb-4">
          "{{ concept.sentence }}"
        </p>

        <div class="mb-2">
          <strong>Meta-Annotations:</strong>
        </div>

        <v-chip-group>
          <v-chip
            v-for="(value, key) in concept.meta_annotations"
            :key="key"
            :color="getMetaColor(value)"
            size="small"
          >
            {{ key }}: {{ value }}
          </v-chip>
        </v-chip-group>

        <div class="mt-4">
          <strong>Confidence:</strong> {{ (concept.confidence * 100).toFixed(0) }}%
        </div>
      </v-card-text>

      <v-card-actions>
        <v-btn @click="viewDocument">View Document</v-btn>
        <v-spacer />
        <v-btn @click="visible = false">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-menu>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue: boolean
  concept: any
  position: { x: number; y: number }
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'view-document': [documentId: string]
}>()

const visible = ref(props.modelValue)

watch(() => props.modelValue, (val) => {
  visible.value = val
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const getMetaColor = (value: string) => {
  if (['Affirmed', 'Current', 'Patient'].includes(value)) return 'green'
  if (['Negated', 'Historical', 'Family'].includes(value)) return 'red'
  return 'grey'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString()
}

const viewDocument = () => {
  if (props.concept?.document_id) {
    emit('view-document', props.concept.document_id)
  }
}
</script>
