/**
 * TypeScript Type Definitions
 *
 * Shared type definitions for the frontend application.
 */

// API Response Types
export interface HealthResponse {
  status: 'healthy' | 'unhealthy'
  version: string
  environment: string
  services: {
    database: {
      status: 'healthy' | 'unhealthy'
      error: string | null
    }
    redis: {
      status: 'healthy' | 'unhealthy'
    }
  }
}

// Patient Search Types (Sprint 1)
export interface PatientSearchQuery {
  concept: string
  filters?: {
    negation?: string
    temporality?: string
    experiencer?: string
  }
  limit?: number
}

export interface PatientResult {
  id: string
  mrn: string
  name: string
  concepts: MedicalConcept[]
}

export interface MedicalConcept {
  cui: string
  name: string
  types: string[]
  confidence: number
  meta_anns: {
    Negation: string
    Temporality: string
    Experiencer: string
  }
}

// Timeline Types (Sprint 2)
export interface TimelineEvent {
  id: string
  date: string
  type: string
  description: string
  concepts: MedicalConcept[]
}

// Re-export domain types
export * from './alerting'
export * from './analytics'
export * from './timeline'
export * from './user'
