/**
 * useTimelineCache composable for client-side caching.
 *
 * Caches timeline data in localStorage with TTL.
 *
 * Task #005: Timeline Composables & State Management
 */
import { createHash } from 'crypto'
import type { TimelineEvent, TimelineFilters } from '@/types/timeline'

const CACHE_PREFIX = 'timeline'
const CACHE_TTL_MS = 5 * 60 * 1000 // 5 minutes

interface CachedTimeline {
  events: TimelineEvent[]
  total_events: number
  timestamp: number
}

export function useTimelineCache() {
  /**
   * Generate cache key from patient ID and filters
   */
  const generateCacheKey = (patientId: string, filters: TimelineFilters): string => {
    const filtersStr = JSON.stringify(filters, Object.keys(filters).sort())
    const hash = createHash('md5').update(filtersStr).digest('hex').substring(0, 16)
    return `${CACHE_PREFIX}:${patientId}:${hash}`
  }

  /**
   * Get cached timeline if available and not expired
   */
  const getCachedTimeline = (
    patientId: string,
    filters: TimelineFilters,
    ignoreExpiry: boolean = false
  ): CachedTimeline | null => {
    try {
      const cacheKey = generateCacheKey(patientId, filters)
      const cachedStr = localStorage.getItem(cacheKey)

      if (!cachedStr) {
        return null
      }

      const cached: CachedTimeline = JSON.parse(cachedStr)

      // Check if cache is expired
      if (!ignoreExpiry && Date.now() - cached.timestamp > CACHE_TTL_MS) {
        localStorage.removeItem(cacheKey)
        return null
      }

      return cached
    } catch (error) {
      console.error('Failed to get cached timeline:', error)
      return null
    }
  }

  /**
   * Cache timeline data
   */
  const setCachedTimeline = (
    patientId: string,
    filters: TimelineFilters,
    data: { events: TimelineEvent[]; total_events: number }
  ): void => {
    try {
      const cacheKey = generateCacheKey(patientId, filters)
      const cached: CachedTimeline = {
        ...data,
        timestamp: Date.now()
      }

      localStorage.setItem(cacheKey, JSON.stringify(cached))
    } catch (error) {
      console.error('Failed to cache timeline:', error)
    }
  }

  /**
   * Clear cached timeline
   */
  const clearCache = (patientId: string, filters: TimelineFilters): void => {
    try {
      const cacheKey = generateCacheKey(patientId, filters)
      localStorage.removeItem(cacheKey)
    } catch (error) {
      console.error('Failed to clear cache:', error)
    }
  }

  /**
   * Clear all timeline caches
   */
  const clearAllCaches = (): void => {
    try {
      const keys = Object.keys(localStorage)
      keys.forEach(key => {
        if (key.startsWith(CACHE_PREFIX)) {
          localStorage.removeItem(key)
        }
      })
    } catch (error) {
      console.error('Failed to clear all caches:', error)
    }
  }

  return {
    getCachedTimeline,
    setCachedTimeline,
    clearCache,
    clearAllCaches
  }
}
