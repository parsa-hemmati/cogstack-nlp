<template>
  <v-card max-width="600">
    <v-card-title>Notification Preferences</v-card-title>
    <v-card-subtitle>
      Configure how you want to receive alert notifications
    </v-card-subtitle>

    <v-card-text>
      <v-form ref="formRef">
        <!-- Notification Channels -->
        <div class="mb-6">
          <div class="text-subtitle-2 mb-3">Notification Channels</div>

          <v-list>
            <v-list-item>
              <template #prepend>
                <v-icon>mdi-bell</v-icon>
              </template>
              <v-list-item-title>In-App Notifications</v-list-item-title>
              <v-list-item-subtitle>
                Show notifications within the application
              </v-list-item-subtitle>
              <template #append>
                <v-switch
                  v-model="formData.inAppEnabled"
                  color="primary"
                  hide-details
                />
              </template>
            </v-list-item>

            <v-list-item>
              <template #prepend>
                <v-icon>mdi-email</v-icon>
              </template>
              <v-list-item-title>Email Notifications</v-list-item-title>
              <v-list-item-subtitle>
                Receive alerts via email
              </v-list-item-subtitle>
              <template #append>
                <v-switch
                  v-model="formData.emailEnabled"
                  color="primary"
                  hide-details
                />
              </template>
            </v-list-item>

            <v-list-item>
              <template #prepend>
                <v-icon>mdi-message-text</v-icon>
              </template>
              <v-list-item-title>SMS Notifications</v-list-item-title>
              <v-list-item-subtitle>
                Receive alerts via text message
              </v-list-item-subtitle>
              <template #append>
                <v-switch
                  v-model="formData.smsEnabled"
                  color="primary"
                  hide-details
                />
              </template>
            </v-list-item>
          </v-list>

          <!-- Phone Number (for SMS) -->
          <v-expand-transition>
            <div v-if="formData.smsEnabled" class="mt-2 pl-12">
              <v-text-field
                v-model="formData.phoneNumber"
                label="Phone Number"
                placeholder="+447123456789"
                :rules="[phoneRule]"
                hint="Enter phone number in international format"
                persistent-hint
              />
            </div>
          </v-expand-transition>
        </div>

        <!-- Minimum Severity -->
        <div class="mb-6">
          <div class="text-subtitle-2 mb-3">Minimum Severity</div>
          <p class="text-body-2 text-grey mb-3">
            Only receive notifications for alerts at or above this severity level
          </p>

          <v-btn-toggle
            v-model="formData.minSeverity"
            mandatory
            color="primary"
            variant="outlined"
          >
            <v-btn value="low" color="success">Low</v-btn>
            <v-btn value="medium" color="info">Medium</v-btn>
            <v-btn value="high" color="warning">High</v-btn>
            <v-btn value="critical" color="error">Critical</v-btn>
          </v-btn-toggle>
        </div>

        <!-- Quiet Hours -->
        <div class="mb-6">
          <div class="text-subtitle-2 mb-3">Quiet Hours</div>
          <p class="text-body-2 text-grey mb-3">
            Suppress non-critical notifications during these hours
          </p>

          <v-row>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.quietHoursStart"
                label="Start Time"
                type="time"
                hint="e.g., 22:00"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formData.quietHoursEnd"
                label="End Time"
                type="time"
                hint="e.g., 07:00"
                persistent-hint
              />
            </v-col>
          </v-row>

          <v-alert
            type="info"
            variant="tonal"
            density="compact"
            class="mt-2"
          >
            Critical alerts will still be delivered during quiet hours
          </v-alert>
        </div>
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn
        color="primary"
        :loading="saving"
        @click="savePreferences"
      >
        Save Preferences
      </v-btn>
    </v-card-actions>

    <v-snackbar v-model="showSuccess" color="success" timeout="3000">
      Preferences saved successfully
    </v-snackbar>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { useAlertStore } from '@/stores/alertStore';
import { storeToRefs } from 'pinia';
import type { NotificationPreferencesUpdate } from '@/types/alerting';

const alertStore = useAlertStore();
const { preferences } = storeToRefs(alertStore);

const formRef = ref();
const saving = ref(false);
const showSuccess = ref(false);

const formData = ref<NotificationPreferencesUpdate>({
  emailEnabled: true,
  smsEnabled: false,
  inAppEnabled: true,
  quietHoursStart: undefined,
  quietHoursEnd: undefined,
  minSeverity: 'medium',
  phoneNumber: undefined,
});

const phoneRule = (v: string | undefined) => {
  if (!formData.value.smsEnabled) return true;
  if (!v) return 'Phone number required for SMS notifications';
  if (!/^\+?[1-9]\d{1,14}$/.test(v)) return 'Enter valid phone number (e.g., +447123456789)';
  return true;
};

onMounted(async () => {
  await alertStore.fetchPreferences();
  if (preferences.value) {
    formData.value = {
      emailEnabled: preferences.value.emailEnabled,
      smsEnabled: preferences.value.smsEnabled,
      inAppEnabled: preferences.value.inAppEnabled,
      quietHoursStart: preferences.value.quietHoursStart || undefined,
      quietHoursEnd: preferences.value.quietHoursEnd || undefined,
      minSeverity: preferences.value.minSeverity as 'critical' | 'high' | 'medium' | 'low',
      phoneNumber: preferences.value.phoneNumber || undefined,
    };
  }
});

async function savePreferences() {
  const { valid } = await formRef.value.validate();
  if (!valid) return;

  saving.value = true;
  try {
    await alertStore.updatePreferences(formData.value);
    showSuccess.value = true;
  } finally {
    saving.value = false;
  }
}
</script>
