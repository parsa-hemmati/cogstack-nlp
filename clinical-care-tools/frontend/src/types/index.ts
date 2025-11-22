// Authentication Types
export interface User {
  id: string
  username: string
  email: string
  firstName?: string
  lastName?: string
  displayName?: string
  roles: string[]
  permissions: string[]
  isActive: boolean
  createdAt: string
  updatedAt: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthTokens {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: User
}

// Patient Types
export interface Patient {
  id: string
  mrn?: string
  firstName: string
  lastName: string
  dateOfBirth: string
  gender: 'male' | 'female' | 'other'
  email?: string
  phone?: string
  address?: Address
  conditions: Condition[]
  medications: Medication[]
  documents: Document[]
  createdAt: string
  updatedAt: string
}

export interface Address {
  street?: string
  city?: string
  state?: string
  postalCode?: string
  country?: string
}

export interface Condition {
  id: string
  cui: string
  name: string
  status: 'active' | 'resolved' | 'inactive'
  onsetDate?: string
  resolutionDate?: string
  severity?: 'mild' | 'moderate' | 'severe'
  confidence: number
}

export interface Medication {
  id: string
  cui?: string
  name: string
  dosage?: string
  frequency?: string
  route?: string
  startDate?: string
  endDate?: string
  status: 'active' | 'stopped' | 'paused'
}

// Document Types
export interface Document {
  id: string
  patientId: string
  title: string
  type: DocumentType
  content?: string
  mimeType: string
  size: number
  uploadedBy: string
  processedAt?: string
  status: DocumentStatus
  annotations?: Annotation[]
  createdAt: string
  updatedAt: string
}

export enum DocumentType {
  ClinicalNote = 'clinical_note',
  DischargeSummary = 'discharge_summary',
  LabReport = 'lab_report',
  RadiologyReport = 'radiology_report',
  Prescription = 'prescription',
  Other = 'other'
}

export enum DocumentStatus {
  Pending = 'pending',
  Processing = 'processing',
  Processed = 'processed',
  Failed = 'failed'
}

// Annotation Types
export interface Annotation {
  id: string
  documentId: string
  cui: string
  prettyName: string
  types: string[]
  startChar: number
  endChar: number
  contextString: string
  confidence: number
  metaAnnotations: MetaAnnotations
  createdAt: string
}

export interface MetaAnnotations {
  Negation?: 'Affirmed' | 'Negated' | 'Other'
  Temporality?: 'Current' | 'Past' | 'Future' | 'Hypothetical'
  Experiencer?: 'Patient' | 'Family' | 'Other'
  Certainty?: 'Certain' | 'Uncertain' | 'Hypothetical'
}

// Search Types
export interface SearchQuery {
  query: string
  filters?: SearchFilters
  pagination?: Pagination
  sort?: SortOptions
}

export interface SearchFilters {
  negation?: string[]
  temporality?: string[]
  experiencer?: string[]
  certainty?: string[]
  dateFrom?: string
  dateTo?: string
  documentTypes?: string[]
  minConfidence?: number
}

export interface SearchResult<T = any> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasNext: boolean
  hasPrevious: boolean
  aggregations?: Record<string, any>
}

// Timeline Types
export interface TimelineEvent {
  id: string
  patientId: string
  date: string
  type: 'diagnosis' | 'medication' | 'procedure' | 'lab' | 'note' | 'appointment'
  title: string
  description?: string
  severity?: 'low' | 'medium' | 'high'
  source?: string
  metadata?: Record<string, any>
}

// Report Types
export interface Report {
  id: string
  title: string
  type: ReportType
  status: ReportStatus
  parameters?: Record<string, any>
  generatedBy: string
  generatedAt: string
  expiresAt?: string
  downloadUrl?: string
}

export enum ReportType {
  PatientSummary = 'patient_summary',
  CohortAnalysis = 'cohort_analysis',
  QualityMetrics = 'quality_metrics',
  ComplianceAudit = 'compliance_audit'
}

export enum ReportStatus {
  Pending = 'pending',
  Generating = 'generating',
  Completed = 'completed',
  Failed = 'failed'
}

// FHIR Types
export interface FHIRResource {
  resourceType: string
  id?: string
  meta?: {
    versionId?: string
    lastUpdated?: string
    profile?: string[]
  }
  [key: string]: any
}

export interface FHIRBundle {
  resourceType: 'Bundle'
  type: 'document' | 'message' | 'transaction' | 'collection'
  timestamp?: string
  total?: number
  entry?: Array<{
    resource: FHIRResource
    fullUrl?: string
  }>
}

// Common Types
export interface Pagination {
  page: number
  pageSize: number
}

export interface SortOptions {
  field: string
  direction: 'asc' | 'desc'
}

export interface ApiError {
  code: string
  message: string
  details?: Record<string, any>
  timestamp?: string
}

export interface AuditLog {
  id: string
  userId: string
  username: string
  action: string
  resource: string
  resourceId?: string
  ipAddress: string
  userAgent?: string
  timestamp: string
  details?: Record<string, any>
}

// Project Types
export interface Project {
  id: string
  name: string
  description?: string
  status: 'active' | 'archived' | 'draft'
  ownerId: string
  owner?: User
  members: ProjectMember[]
  startDate?: string
  endDate?: string
  tags?: string[]
  settings?: Record<string, any>
  createdAt: string
  updatedAt: string
}

export interface ProjectMember {
  userId: string
  user?: User
  role: 'owner' | 'admin' | 'member' | 'viewer'
  permissions: string[]
  joinedAt: string
}

export interface CreateProjectRequest {
  name: string
  description?: string
  startDate?: string
  endDate?: string
  tags?: string[]
}

export interface UpdateProjectRequest {
  name?: string
  description?: string
  status?: 'active' | 'archived' | 'draft'
  startDate?: string
  endDate?: string
  tags?: string[]
}

// Task Types
export interface Task {
  id: string
  projectId: string
  project?: Project
  title: string
  description?: string
  status: TaskStatus
  priority: TaskPriority
  assigneeId?: string
  assignee?: User
  reporterId: string
  reporter?: User
  dueDate?: string
  completedAt?: string
  tags?: string[]
  attachments?: TaskAttachment[]
  comments?: TaskComment[]
  estimatedHours?: number
  actualHours?: number
  createdAt: string
  updatedAt: string
}

export enum TaskStatus {
  Pending = 'pending',
  InProgress = 'in_progress',
  Completed = 'completed',
  Blocked = 'blocked',
  Cancelled = 'cancelled'
}

export enum TaskPriority {
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Urgent = 'urgent'
}

export interface TaskAttachment {
  id: string
  filename: string
  size: number
  mimeType: string
  uploadedBy: string
  uploadedAt: string
  url: string
}

export interface TaskComment {
  id: string
  taskId: string
  userId: string
  user?: User
  content: string
  createdAt: string
  updatedAt: string
}

export interface CreateTaskRequest {
  projectId: string
  title: string
  description?: string
  priority?: TaskPriority
  assigneeId?: string
  dueDate?: string
  tags?: string[]
  estimatedHours?: number
}

export interface UpdateTaskRequest {
  title?: string
  description?: string
  status?: TaskStatus
  priority?: TaskPriority
  assigneeId?: string
  dueDate?: string
  tags?: string[]
  estimatedHours?: number
  actualHours?: number
}

// User Management Types
export interface CreateUserRequest {
  username: string
  email: string
  password: string
  firstName?: string
  lastName?: string
  roles: string[]
}

export interface UpdateUserRequest {
  email?: string
  firstName?: string
  lastName?: string
  roles?: string[]
  isActive?: boolean
}

export interface ResetPasswordRequest {
  userId: string
  newPassword: string
}