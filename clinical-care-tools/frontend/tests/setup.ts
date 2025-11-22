/**
 * Frontend test setup and configuration
 *
 * This file configures:
 * - Vue Test Utils global setup
 * - Vuetify components registration
 * - Mock axios client
 * - Router mocks
 * - Global test utilities
 */

import { vi } from 'vitest'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Create Vuetify instance for tests
export const vuetify = createVuetify({
  components,
  directives,
})

/**
 * Mock axios client for API requests
 */
export const mockAxios = {
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  request: vi.fn(),
  interceptors: {
    request: { use: vi.fn(), eject: vi.fn() },
    response: { use: vi.fn(), eject: vi.fn() },
  },
}

/**
 * Mock router for navigation tests
 */
export const mockRouter = {
  push: vi.fn(),
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn(),
  currentRoute: {
    value: {
      path: '/',
      name: 'home',
      params: {},
      query: {},
    },
  },
  install: vi.fn(),
}

/**
 * Mock localStorage
 */
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

// Setup global mocks
Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

/**
 * Mock sessionStorage
 */
const sessionStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'sessionStorage', {
  value: sessionStorageMock,
})

/**
 * Mock window.matchMedia for media query tests
 */
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

/**
 * Mock IntersectionObserver
 */
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

/**
 * Test utilities
 */
export const createMockAuthToken = (): string => {
  return 'test_jwt_token_' + Math.random().toString(36).substr(2, 9)
}

export const createMockUser = (overrides = {}) => {
  return {
    id: '1',
    email: 'test@example.com',
    full_name: 'Test User',
    is_active: true,
    role: 'clinician',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export const createMockPatient = (overrides = {}) => {
  return {
    id: '1',
    mrn: 'MRN123456',
    first_name: 'John',
    last_name: 'Doe',
    date_of_birth: '1960-01-01',
    age: 65,
    gender: 'M',
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

export const createMockResponse = (data: any, status = 200) => {
  return {
    status,
    statusText: status === 200 ? 'OK' : 'Created',
    headers: {},
    config: {},
    data,
  }
}
