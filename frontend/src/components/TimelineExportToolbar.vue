<template>
  <v-toolbar density="compact" color="transparent" class="timeline-export-toolbar">
    <v-toolbar-title class="text-body-2">Export</v-toolbar-title>

    <v-spacer></v-spacer>

    <!-- PDF Export Button -->
    <v-btn
      variant="outlined"
      color="error"
      prepend-icon="mdi-file-pdf-box"
      @click="showExportDialog('pdf')"
      :loading="exportLoading.pdf"
      :disabled="!patientId"
      size="small"
      class="mr-2"
    >
      PDF
    </v-btn>

    <!-- FHIR Export Button -->
    <v-btn
      variant="outlined"
      color="primary"
      prepend-icon="mdi-hospital-box"
      @click="showExportDialog('fhir')"
      :loading="exportLoading.fhir"
      :disabled="!patientId"
      size="small"
      class="mr-2"
    >
      FHIR
    </v-btn>

    <!-- JSON Export Button -->
    <v-btn
      variant="outlined"
      color="success"
      prepend-icon="mdi-code-json"
      @click="showExportDialog('json')"
      :loading="exportLoading.json"
      :disabled="!patientId"
      size="small"
    >
      JSON
    </v-btn>

    <!-- Export Options Dialog -->
    <v-dialog v-model="dialog" max-width="500">
      <v-card>
        <v-card-title class="text-h6">
          Export Timeline ({{ exportFormat.toUpperCase() }})
        </v-card-title>

        <v-card-text>
          <v-form ref="formRef">
            <!-- De-identification Option -->
            <v-checkbox
              v-model="exportOptions.de_identified"
              label="De-identify patient data"
              hint="Remove patient name and identifiers from export"
              persistent-hint
              color="primary"
              class="mb-2"
            ></v-checkbox>

            <!-- Watermark Option (PDF only) -->
            <v-checkbox
              v-if="exportFormat === 'pdf'"
              v-model="exportOptions.watermark"
              label="Add confidential watermark"
              hint="Mark export as 'Clinical Summary - Confidential'"
              persistent-hint
              color="primary"
              class="mb-2"
            ></v-checkbox>

            <!-- Apply Filters Option -->
            <v-checkbox
              v-model="exportOptions.apply_filters"
              label="Apply current timeline filters"
              hint="Export only concepts/documents matching active filters"
              persistent-hint
              color="primary"
            ></v-checkbox>

            <!-- Export Info -->
            <v-alert
              type="info"
              variant="tonal"
              density="compact"
              class="mt-4"
            >
              <template v-if="exportFormat === 'pdf'">
                <strong>PDF Export:</strong> Visual clinical summary for referrals and audits.
              </template>
              <template v-else-if="exportFormat === 'fhir'">
                <strong>FHIR Export:</strong> FHIR R4 Composition for EHR interoperability.
              </template>
              <template v-else>
                <strong>JSON Export:</strong> Machine-readable data for research and analysis.
              </template>
            </v-alert>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            variant="text"
            @click="dialog = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            @click="performExport"
            :loading="isExporting"
          >
            Export
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Success Snackbar -->
    <v-snackbar
      v-model="snackbar.show"
      :color="snackbar.color"
      :timeout="5000"
      location="top"
    >
      {{ snackbar.message }}

      <template v-slot:actions>
        <v-btn
          v-if="snackbar.showDownload"
          variant="text"
          @click="handleDownload"
        >
          Download
        </v-btn>
        <v-btn
          variant="text"
          @click="snackbar.show = false"
        >
          Close
        </v-btn>
      </template>
    </v-snackbar>
  </v-toolbar>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useTimelineExport } from '@/composables/useTimelineExport'

interface Props {
  patientId: string
  filters?: any
}

const props = defineProps<Props>()

const {
  isLoading,
  error,
  exportTimeline,
  downloadPDF,
  downloadJSON
} = useTimelineExport()

// Dialog state
const dialog = ref(false)
const exportFormat = ref<'pdf' | 'fhir' | 'json'>('pdf')
const isExporting = ref(false)

// Export loading states (per format)
const exportLoading = reactive({
  pdf: false,
  fhir: false,
  json: false
})

// Export options
const exportOptions = reactive({
  de_identified: false,
  watermark: true,
  apply_filters: false
})

// Snackbar state
const snackbar = reactive({
  show: false,
  message: '',
  color: 'success',
  showDownload: false
})

// Store last export result for download
const lastExportResult = ref<any>(null)

/**
 * Show export dialog for selected format
 */
const showExportDialog = (format: 'pdf' | 'fhir' | 'json') => {
  exportFormat.value = format

  // Reset options to defaults
  exportOptions.de_identified = false
  exportOptions.watermark = format === 'pdf'  // Only for PDF
  exportOptions.apply_filters = false

  dialog.value = true
}

/**
 * Perform export operation
 */
const performExport = async () => {
  if (!props.patientId) {
    snackbar.message = 'Error: No patient selected'
    snackbar.color = 'error'
    snackbar.showDownload = false
    snackbar.show = true
    return
  }

  isExporting.value = true
  exportLoading[exportFormat.value] = true
  dialog.value = false

  try {
    // Prepare filters if apply_filters is enabled
    const filtersToApply = exportOptions.apply_filters ? props.filters : null

    // Prepare options
    const options = {
      de_identified: exportOptions.de_identified,
      ...(exportFormat.value === 'pdf' && { watermark: exportOptions.watermark })
    }

    // Call export API
    const result = await exportTimeline(
      props.patientId,
      exportFormat.value,
      filtersToApply,
      options
    )

    // Store result for download
    lastExportResult.value = result

    // Show success message
    snackbar.message = `${exportFormat.value.toUpperCase()} export completed successfully!`
    snackbar.color = 'success'
    snackbar.showDownload = true
    snackbar.show = true

  } catch (err: any) {
    // Show error message
    snackbar.message = `Export failed: ${err.message || 'Unknown error'}`
    snackbar.color = 'error'
    snackbar.showDownload = false
    snackbar.show = true
  } finally {
    isExporting.value = false
    exportLoading[exportFormat.value] = false
  }
}

/**
 * Handle download action from snackbar
 */
const handleDownload = () => {
  if (!lastExportResult.value) {
    return
  }

  const result = lastExportResult.value
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
  const patientIdShort = props.patientId.substring(0, 8)

  try {
    if (result.format === 'pdf' && result.data) {
      // Download PDF (base64 decode)
      const filename = `timeline-${patientIdShort}-${timestamp}.pdf`
      downloadPDF(result.data, filename)
    } else if (result.format === 'json' && result.data) {
      // Download JSON
      const filename = `timeline-${patientIdShort}-${timestamp}.json`
      downloadJSON(result.data, filename)
    } else if (result.format === 'fhir' && result.data) {
      // Download FHIR as JSON
      const filename = `timeline-fhir-${patientIdShort}-${timestamp}.json`
      downloadJSON(result.data, filename)
    } else if (result.download_url) {
      // Fallback: Use download URL if provided (async export)
      window.open(result.download_url, '_blank')
    }

    // Close snackbar after download initiated
    snackbar.show = false
  } catch (err: any) {
    snackbar.message = `Download failed: ${err.message}`
    snackbar.color = 'error'
    snackbar.showDownload = false
    snackbar.show = true
  }
}
</script>

<style scoped>
.timeline-export-toolbar {
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}
</style>
