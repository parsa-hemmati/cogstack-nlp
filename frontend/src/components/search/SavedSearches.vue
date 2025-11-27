<template>
  <v-card data-testid="saved-searches" class="saved-searches-card" elevation="2">
    <v-card-title class="d-flex justify-space-between align-center">
      <span>Saved Searches</span>
      <v-chip size="small" color="primary">
        {{ savedSearches.length }}
      </v-chip>
    </v-card-title>

    <v-card-text>
      <!-- Empty State -->
      <div
        v-if="savedSearches.length === 0"
        data-testid="empty-state"
        class="text-center py-8"
      >
        <v-icon size="64" color="grey-lighten-1">mdi-bookmark-outline</v-icon>
        <p class="text-h6 mt-4 text-grey">No saved searches</p>
        <p class="text-caption text-grey">Save your frequently used searches for quick access</p>
      </div>

      <!-- Saved Searches List -->
      <v-list
        v-else
        data-testid="saved-searches-list"
        role="list"
        lines="two"
        class="saved-searches-list"
      >
        <v-list-item
          v-for="savedSearch in savedSearches"
          :key="savedSearch.id"
          :data-testid="`saved-search-item`"
          class="saved-search-item"
          @click="executeSavedSearch(savedSearch)"
        >
          <template #prepend>
            <v-icon
              data-testid="execute-icon"
              color="primary"
            >
              mdi-magnify
            </v-icon>
          </template>

          <v-list-item-title>
            {{ savedSearch.name }}
          </v-list-item-title>

          <v-list-item-subtitle class="query-text">
            Query: {{ savedSearch.query }}
          </v-list-item-subtitle>

          <template #append>
            <v-btn
              icon
              size="small"
              variant="text"
              color="error"
              data-testid="delete-btn"
              :aria-label="`Delete ${savedSearch.name}`"
              @click.stop="confirmDelete(savedSearch.id)"
            >
              <v-icon>mdi-delete</v-icon>
            </v-btn>
          </template>
        </v-list-item>
      </v-list>
    </v-card-text>

    <!-- Save Current Search Button -->
    <v-card-actions>
      <v-btn
        block
        variant="elevated"
        color="primary"
        prepend-icon="mdi-content-save"
        data-testid="save-current-btn"
        @click="$emit('save')"
      >
        Save Current Search
      </v-btn>
    </v-card-actions>

    <!-- Delete Confirmation Dialog -->
    <v-dialog
      v-model="showDeleteConfirm"
      max-width="400"
    >
      <v-card>
        <v-card-title class="text-h5">
          Confirm Delete
        </v-card-title>

        <v-card-text>
          Are you sure you want to delete this saved search? This action cannot be undone.
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDeleteConfirm = false"
          >
            Cancel
          </v-btn>
          <v-btn
            color="error"
            variant="elevated"
            @click="deleteConfirmed"
          >
            Delete
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// ============================================================================
// TYPES
// ============================================================================

interface SavedSearch {
  id: string
  name: string
  query: string
  filters?: Record<string, any>
  created_at?: string
}

// ============================================================================
// PROPS & EMITS
// ============================================================================

const props = defineProps({
  savedSearches: {
    type: Array as () => SavedSearch[],
    default: () => [],
  },
})

const emit = defineEmits<{
  'execute': [savedSearch: SavedSearch]
  'delete': [id: string]
  'save': []
}>()

// ============================================================================
// STATE
// ============================================================================

const showDeleteConfirm = ref(false)
const deleteTargetId = ref<string | null>(null)

// ============================================================================
// METHODS
// ============================================================================

/**
 * Execute a saved search
 * Emits the saved search to parent for execution
 */
function executeSavedSearch(savedSearch: SavedSearch) {
  emit('execute', savedSearch)
}

/**
 * Show confirmation dialog for delete
 */
function confirmDelete(id: string) {
  deleteTargetId.value = id
  showDeleteConfirm.value = true
}

/**
 * Delete confirmed - emit delete event
 */
function deleteConfirmed() {
  if (deleteTargetId.value) {
    emit('delete', deleteTargetId.value)
    showDeleteConfirm.value = false
    deleteTargetId.value = null
  }
}
</script>

<style scoped>
.saved-searches-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.saved-searches-list {
  max-height: 400px;
  overflow-y: auto;
}

.saved-search-item {
  cursor: pointer;
  transition: background-color 0.2s;
}

.saved-search-item:hover {
  background-color: rgba(0, 0, 0, 0.04);
}

.query-text {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  color: #666;
}
</style>
