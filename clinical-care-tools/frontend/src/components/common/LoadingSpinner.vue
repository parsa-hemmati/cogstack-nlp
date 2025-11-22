<template>
  <div class="loading-spinner">
    <v-overlay
      :model-value="loading"
      :persistent="persistent"
      :scrim="scrim"
      class="align-center justify-center"
    >
      <v-progress-circular
        :color="color"
        :size="size"
        :width="width"
        indeterminate
      />
      <div v-if="text" class="mt-4 text-center">
        <span :class="`text-${color}`">{{ text }}</span>
      </div>
    </v-overlay>
  </div>
</template>

<script setup lang="ts">
interface Props {
  loading?: boolean
  color?: string
  size?: number | string
  width?: number
  text?: string
  persistent?: boolean
  scrim?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
  color: 'primary',
  size: 64,
  width: 4,
  text: '',
  persistent: false,
  scrim: true
})
</script>

<style scoped>
.loading-spinner {
  position: relative;
}
</style>