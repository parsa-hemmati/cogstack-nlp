import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  timeout: parseInt(import.meta.env.VITE_API_TIMEOUT) || 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem(import.meta.env.VITE_AUTH_TOKEN_KEY || 'cct_auth_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add request ID for tracking
    config.headers['X-Request-ID'] = generateRequestId()

    // Log request in development
    if (import.meta.env.DEV) {
    }

    return config
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.DEV) {
    }
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // Handle 401 Unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const authStore = useAuthStore()
        await authStore.refreshToken()

        // Retry original request with new token
        const token = localStorage.getItem(import.meta.env.VITE_AUTH_TOKEN_KEY || 'cct_auth_token')
        if (token && originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${token}`
        }

        return api(originalRequest)
      } catch (refreshError) {

        // Logout and redirect to login
        const authStore = useAuthStore()
        await authStore.logout()
        window.location.href = '/login'

        return Promise.reject(refreshError)
      }
    }

    // Handle other errors
    if (error.response) {
      // Server responded with error
      const message = error.response.data?.detail || error.response.data?.message || error.message

      // Create user-friendly error messages
      switch (error.response.status) {
        case 400:
          error.message = `Bad Request: ${message}`
          break
        case 403:
          error.message = 'You do not have permission to perform this action'
          break
        case 404:
          error.message = 'The requested resource was not found'
          break
        case 422:
          error.message = `Validation Error: ${message}`
          break
        case 500:
          error.message = 'An internal server error occurred. Please try again later.'
          break
        case 502:
        case 503:
          error.message = 'Service temporarily unavailable. Please try again later.'
          break
        default:
          error.message = message || 'An unexpected error occurred'
      }
    } else if (error.request) {
      // Request made but no response
      error.message = 'Unable to connect to the server. Please check your connection.'
    } else {
      // Something else happened
    }

    return Promise.reject(error)
  }
)

/**
 * Generate a unique request ID for tracking
 */
function generateRequestId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
}

/**
 * API Service class for organized endpoint calls
 */
export class ApiService {
  // Authentication
  static auth = {
    login: (credentials: { username: string; password: string }) =>
      api.post('/auth/login', credentials),

    logout: () => api.post('/auth/logout'),

    refresh: (refreshToken: string) =>
      api.post('/auth/refresh', { refresh_token: refreshToken }),

    me: () => api.get('/auth/me'),

    changePassword: (data: { current_password: string; new_password: string }) =>
      api.post('/auth/change-password', data)
  }

  // Patients
  static patients = {
    list: (params?: { skip?: number; limit?: number; search?: string }) =>
      api.get('/api/v1/patients', { params }),

    get: (id: string) => api.get(`/api/v1/patients/${id}`),

    create: (data: any) => api.post('/api/v1/patients', data),

    update: (id: string, data: any) => api.put(`/api/v1/patients/${id}`, data),

    delete: (id: string) => api.delete(`/api/v1/patients/${id}`),

    search: (query: any) => api.post('/api/v1/patients/search', query),

    timeline: (id: string) => api.get(`/api/v1/patients/${id}/timeline`)
  }

  // Documents
  static documents = {
    upload: (formData: FormData) =>
      api.post('/api/v1/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }),

    list: (patientId?: string) =>
      api.get('/api/v1/documents', { params: { patient_id: patientId } }),

    get: (id: string) => api.get(`/api/v1/documents/${id}`),

    delete: (id: string) => api.delete(`/api/v1/documents/${id}`),

    process: (id: string) => api.post(`/api/v1/documents/${id}/process`),

    annotations: (id: string) => api.get(`/api/v1/documents/${id}/annotations`)
  }

  // MedCAT
  static medcat = {
    process: (text: string) => api.post('/api/v1/medcat/process', { text }),

    entities: (text: string) => api.post('/api/v1/medcat/entities', { text }),

    models: () => api.get('/api/v1/medcat/models'),

    loadModel: (modelId: string) => api.post(`/api/v1/medcat/models/${modelId}/load`)
  }

  // Reports
  static reports = {
    generate: (params: any) => api.post('/api/v1/reports/generate', params),

    list: () => api.get('/api/v1/reports'),

    get: (id: string) => api.get(`/api/v1/reports/${id}`),

    download: (id: string) => api.get(`/api/v1/reports/${id}/download`, {
      responseType: 'blob'
    })
  }

  // FHIR
  static fhir = {
    export: (patientIds: string[]) =>
      api.post('/api/v1/fhir/export', { patient_ids: patientIds }),

    import: (bundle: any) => api.post('/api/v1/fhir/import', bundle),

    validate: (resource: any) => api.post('/api/v1/fhir/validate', resource)
  }

  // Admin
  static admin = {
    users: {
      list: () => api.get('/api/v1/admin/users'),
      create: (data: any) => api.post('/api/v1/admin/users', data),
      update: (id: string, data: any) => api.put(`/api/v1/admin/users/${id}`, data),
      delete: (id: string) => api.delete(`/api/v1/admin/users/${id}`)
    },

    audit: {
      logs: (params?: { user_id?: string; start_date?: string; end_date?: string }) =>
        api.get('/api/v1/admin/audit/logs', { params })
    },

    system: {
      health: () => api.get('/health'),
      metrics: () => api.get('/api/v1/admin/system/metrics'),
      config: () => api.get('/api/v1/admin/system/config')
    }
  }

  // Users (extended for user management)
  static users = {
    list: (params?: { skip?: number; limit?: number; search?: string; role?: string }) =>
      api.get('/api/v1/users', { params }),

    get: (id: string) => api.get(`/api/v1/users/${id}`),

    create: (data: any) => api.post('/api/v1/users', data),

    update: (id: string, data: any) => api.put(`/api/v1/users/${id}`, data),

    delete: (id: string) => api.delete(`/api/v1/users/${id}`),

    resetPassword: (id: string, newPassword: string) =>
      api.post(`/api/v1/users/${id}/reset-password`, { new_password: newPassword }),

    toggleStatus: (id: string, isActive: boolean) =>
      api.patch(`/api/v1/users/${id}/status`, { is_active: isActive }),

    getRoles: () => api.get('/api/v1/users/roles'),

    getPermissions: () => api.get('/api/v1/users/permissions')
  }

  // Projects
  static projects = {
    list: (params?: { skip?: number; limit?: number; status?: string; search?: string }) =>
      api.get('/api/v1/projects', { params }),

    get: (id: string) => api.get(`/api/v1/projects/${id}`),

    create: (data: any) => api.post('/api/v1/projects', data),

    update: (id: string, data: any) => api.put(`/api/v1/projects/${id}`, data),

    delete: (id: string) => api.delete(`/api/v1/projects/${id}`),

    getMembers: (id: string) => api.get(`/api/v1/projects/${id}/members`),

    addMember: (id: string, userId: string, role: string) =>
      api.post(`/api/v1/projects/${id}/members`, { user_id: userId, role }),

    updateMember: (id: string, userId: string, role: string) =>
      api.put(`/api/v1/projects/${id}/members/${userId}`, { role }),

    removeMember: (id: string, userId: string) =>
      api.delete(`/api/v1/projects/${id}/members/${userId}`),

    getTasks: (id: string, params?: { status?: string; assignee?: string }) =>
      api.get(`/api/v1/projects/${id}/tasks`, { params }),

    getStats: (id: string) => api.get(`/api/v1/projects/${id}/stats`)
  }

  // Tasks
  static tasks = {
    list: (params?: {
      skip?: number;
      limit?: number;
      project_id?: string;
      status?: string;
      assignee?: string;
      priority?: string;
      search?: string
    }) => api.get('/api/v1/tasks', { params }),

    get: (id: string) => api.get(`/api/v1/tasks/${id}`),

    create: (data: any) => api.post('/api/v1/tasks', data),

    update: (id: string, data: any) => api.put(`/api/v1/tasks/${id}`, data),

    delete: (id: string) => api.delete(`/api/v1/tasks/${id}`),

    updateStatus: (id: string, status: string) =>
      api.patch(`/api/v1/tasks/${id}/status`, { status }),

    assign: (id: string, userId: string) =>
      api.patch(`/api/v1/tasks/${id}/assign`, { assignee_id: userId }),

    addComment: (id: string, content: string) =>
      api.post(`/api/v1/tasks/${id}/comments`, { content }),

    getComments: (id: string) => api.get(`/api/v1/tasks/${id}/comments`),

    addAttachment: (id: string, file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return api.post(`/api/v1/tasks/${id}/attachments`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    },

    getAttachments: (id: string) => api.get(`/api/v1/tasks/${id}/attachments`)
  }
}

export default api