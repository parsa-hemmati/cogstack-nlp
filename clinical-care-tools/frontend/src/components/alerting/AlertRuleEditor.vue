<template>
  <v-card>
    <v-card-title>
      {{ isEditing ? 'Edit Alert Rule' : 'Create Alert Rule' }}
    </v-card-title>

    <v-card-text>
      <v-form ref="formRef" v-model="isValid" @submit.prevent="handleSubmit">
        <!-- Basic Info -->
        <v-text-field
          v-model="formData.name"
          label="Rule Name"
          :rules="[rules.required]"
          class="mb-4"
        />

        <v-textarea
          v-model="formData.description"
          label="Description"
          rows="2"
          class="mb-4"
        />

        <v-row>
          <v-col cols="12" sm="6">
            <v-select
              v-model="formData.severity"
              :items="severityOptions"
              label="Severity"
              :rules="[rules.required]"
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-text-field
              v-model.number="formData.escalationMinutes"
              label="Escalation (minutes)"
              type="number"
              hint="Time before escalating unacknowledged alert"
              persistent-hint
            />
          </v-col>
        </v-row>

        <!-- Notification Channels -->
        <div class="mb-4">
          <div class="text-subtitle-2 mb-2">Notification Channels</div>
          <v-chip-group
            v-model="formData.notificationChannels"
            multiple
            selected-class="text-primary"
          >
            <v-chip value="in_app" filter variant="outlined">
              <v-icon start>mdi-bell</v-icon>
              In-App
            </v-chip>
            <v-chip value="email" filter variant="outlined">
              <v-icon start>mdi-email</v-icon>
              Email
            </v-chip>
            <v-chip value="sms" filter variant="outlined">
              <v-icon start>mdi-message-text</v-icon>
              SMS
            </v-chip>
          </v-chip-group>
        </div>

        <!-- Conditions -->
        <div class="mb-4">
          <div class="d-flex align-center mb-2">
            <span class="text-subtitle-2">Conditions</span>
            <v-spacer />
            <v-btn-toggle
              v-model="formData.conditions.matchType"
              mandatory
              density="compact"
            >
              <v-btn value="all" size="small">All Match (AND)</v-btn>
              <v-btn value="any" size="small">Any Match (OR)</v-btn>
            </v-btn-toggle>
          </div>

          <v-card
            v-for="(condition, index) in formData.conditions.conditions"
            :key="index"
            variant="outlined"
            class="pa-3 mb-2"
          >
            <v-row dense>
              <v-col cols="12" sm="4">
                <v-text-field
                  v-model="condition.field"
                  label="Field"
                  density="compact"
                  placeholder="e.g., lab_results.potassium"
                  :rules="[rules.required]"
                />
              </v-col>
              <v-col cols="12" sm="3">
                <v-select
                  v-model="condition.operator"
                  :items="operatorOptions"
                  label="Operator"
                  density="compact"
                  :rules="[rules.required]"
                />
              </v-col>
              <v-col cols="12" sm="4">
                <v-text-field
                  v-model="condition.value"
                  label="Value"
                  density="compact"
                  :disabled="['is_null', 'is_not_null'].includes(condition.operator)"
                />
              </v-col>
              <v-col cols="12" sm="1" class="d-flex align-center">
                <v-btn
                  icon
                  size="small"
                  variant="text"
                  color="error"
                  @click="removeCondition(index)"
                  :disabled="formData.conditions.conditions.length <= 1"
                >
                  <v-icon>mdi-delete</v-icon>
                </v-btn>
              </v-col>
            </v-row>
          </v-card>

          <v-btn
            variant="text"
            color="primary"
            size="small"
            @click="addCondition"
          >
            <v-icon left>mdi-plus</v-icon>
            Add Condition
          </v-btn>
        </div>

        <!-- Enabled Toggle -->
        <v-switch
          v-model="formData.enabled"
          label="Rule Enabled"
          color="primary"
          hide-details
        />

        <!-- Change Reason (for edits) -->
        <v-textarea
          v-if="isEditing"
          v-model="changeReason"
          label="Reason for change"
          rows="2"
          class="mt-4"
          hint="Document why this rule is being changed"
        />
      </v-form>
    </v-card-text>

    <v-card-actions>
      <v-spacer />
      <v-btn text @click="$emit('cancel')">Cancel</v-btn>
      <v-btn
        v-if="isEditing && rule"
        color="secondary"
        variant="outlined"
        @click="testRule"
        :loading="testing"
      >
        Test Rule
      </v-btn>
      <v-btn
        color="primary"
        :disabled="!isValid"
        :loading="saving"
        @click="handleSubmit"
      >
        {{ isEditing ? 'Update' : 'Create' }}
      </v-btn>
    </v-card-actions>

    <!-- Test Results Dialog -->
    <v-dialog v-model="showTestResults" max-width="600">
      <v-card>
        <v-card-title>Test Results</v-card-title>
        <v-card-text>
          <v-alert
            :type="testResults?.matched ? 'success' : 'info'"
            class="mb-4"
          >
            Rule {{ testResults?.matched ? 'MATCHED' : 'did not match' }}
          </v-alert>

          <div v-if="testResults">
            <div class="text-subtitle-2 mb-2">Condition Results:</div>
            <v-list density="compact">
              <v-list-item
                v-for="(result, index) in testResults.conditionResults"
                :key="index"
              >
                <template #prepend>
                  <v-icon :color="result.matched ? 'success' : 'error'">
                    {{ result.matched ? 'mdi-check-circle' : 'mdi-close-circle' }}
                  </v-icon>
                </template>
                <v-list-item-title>
                  {{ result.condition.field }} {{ result.condition.operator }}
                  {{ result.condition.value }}
                </v-list-item-title>
                <v-list-item-subtitle>
                  Actual: {{ result.actualValue ?? 'null' }}
                </v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="showTestResults = false">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';
import { useAlertStore } from '@/stores/alertStore';
import type {
  AlertRule,
  AlertRuleCreate,
  Condition,
  RuleTestResult,
} from '@/types/alerting';
import { OPERATOR_LABELS } from '@/types/alerting';

const props = defineProps<{
  rule?: AlertRule;
}>();

const emit = defineEmits<{
  cancel: [];
  saved: [rule: AlertRule];
}>();

const alertStore = useAlertStore();

const formRef = ref();
const isValid = ref(false);
const saving = ref(false);
const testing = ref(false);
const changeReason = ref('');
const showTestResults = ref(false);
const testResults = ref<RuleTestResult | null>(null);

const isEditing = computed(() => !!props.rule);

const formData = ref<{
  name: string;
  description: string;
  severity: string;
  notificationChannels: string[];
  escalationMinutes: number | null;
  enabled: boolean;
  conditions: {
    matchType: 'all' | 'any';
    conditions: Condition[];
  };
}>({
  name: '',
  description: '',
  severity: 'medium',
  notificationChannels: ['in_app'],
  escalationMinutes: null,
  enabled: true,
  conditions: {
    matchType: 'all',
    conditions: [{ field: '', operator: 'equals', value: '' }],
  },
});

const rules = {
  required: (v: unknown) => !!v || 'Required',
};

const severityOptions = [
  { title: 'Critical', value: 'critical' },
  { title: 'High', value: 'high' },
  { title: 'Medium', value: 'medium' },
  { title: 'Low', value: 'low' },
];

const operatorOptions = Object.entries(OPERATOR_LABELS).map(([value, title]) => ({
  title,
  value,
}));

onMounted(() => {
  if (props.rule) {
    formData.value = {
      name: props.rule.name,
      description: props.rule.description || '',
      severity: props.rule.severity,
      notificationChannels: [...props.rule.notificationChannels],
      escalationMinutes: props.rule.escalationMinutes || null,
      enabled: props.rule.enabled,
      conditions: {
        matchType: props.rule.conditions.match_type,
        conditions: props.rule.conditions.conditions.map((c) => ({ ...c })),
      },
    };
  }
});

function addCondition() {
  formData.value.conditions.conditions.push({
    field: '',
    operator: 'equals',
    value: '',
  });
}

function removeCondition(index: number) {
  formData.value.conditions.conditions.splice(index, 1);
}

async function handleSubmit() {
  const { valid } = await formRef.value.validate();
  if (!valid) return;

  saving.value = true;
  try {
    const data: AlertRuleCreate = {
      name: formData.value.name,
      description: formData.value.description || undefined,
      severity: formData.value.severity as 'critical' | 'high' | 'medium' | 'low',
      notificationChannels: formData.value.notificationChannels as ('email' | 'sms' | 'in_app')[],
      escalationMinutes: formData.value.escalationMinutes || undefined,
      enabled: formData.value.enabled,
      conditions: {
        match_type: formData.value.conditions.matchType,
        conditions: formData.value.conditions.conditions,
      },
    };

    let result: AlertRule | null;
    if (isEditing.value && props.rule) {
      result = await alertStore.updateRule(props.rule.id, {
        ...data,
        changeReason: changeReason.value || undefined,
      });
    } else {
      result = await alertStore.createRule(data);
    }

    if (result) {
      emit('saved', result);
    }
  } finally {
    saving.value = false;
  }
}

async function testRule() {
  if (!props.rule) return;

  testing.value = true;
  try {
    // Use sample test data
    const testData = {
      lab_results: {
        potassium: 5.8,
        sodium: 140,
      },
      medications: ['lisinopril', 'aspirin'],
    };

    testResults.value = await alertStore.testRule(props.rule.id, testData);
    if (testResults.value) {
      showTestResults.value = true;
    }
  } finally {
    testing.value = false;
  }
}
</script>
