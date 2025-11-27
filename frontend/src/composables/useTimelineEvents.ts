/**
 * useTimelineEvents composable for API calls.
 *
 * Handles HTTP requests to timeline API endpoints.
 *
 * Task #005: Timeline Composables & State Management
 */
import axios from 'axios'
import type { TimelineEvent, TimelineFilters } from '@/types/timeline'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export function useTimelineEvents() {
  /**
   * Fetch patient timeline from API
   */
  const getPatientTimeline = async (
    patientId: string,
    filters: TimelineFilters
  ): Promise<{ events: TimelineEvent[]; total_events: number }> => {
    const response = await axios.post(
      `${API_BASE_URL}/timeline/patient/${patientId}`,
      {
        date_range: {
          start: filters.dateRange?.start.toISOString() || '',
          end: filters.dateRange?.end.toISOString() || ''
        },
        event_types: filters.eventTypes || [],
        specialty_filter: null,
        page: 1,
        page_size: 1000
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )

    return {
      events: response.data.events || [],
      total_events: response.data.total_events || 0
    }
  }

  /**
   * Get detailed event information
   */
  const getEventDetails = async (eventId: string): Promise<TimelineEvent> => {
    const response = await axios.get(`${API_BASE_URL}/timeline/events/${eventId}`)
    return response.data
  }

  return {
    getPatientTimeline,
    getEventDetails
  }
}
