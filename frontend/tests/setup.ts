/**
 * Vitest setup file for global test configuration.
 *
 * Configures test utilities and mocks needed for composables and components.
 * Includes global Vuetify instance for component testing.
 */
import { vi } from 'vitest'
import { config } from '@vue/test-utils'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

// Create global Vuetify instance with all components and directives
const vuetify = createVuetify({
  components,
  directives,
})

// Configure Vue Test Utils to use Vuetify globally
config.global.plugins = [vuetify]

// Mock window.matchMedia (required by some components)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
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

// Mock IntersectionObserver (required by some components)
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  takeRecords() {
    return []
  }
  unobserve() {}
} as any

// Mock ResizeObserver (required by some components)
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
} as any

// Mock localStorage (required by useTimelineCache and other composables)
const localStorageMock = {
  store: new Map<string, string>(),
  getItem(key: string): string | null {
    return this.store.get(key) || null
  },
  setItem(key: string, value: string): void {
    this.store.set(key, value)
  },
  removeItem(key: string): void {
    this.store.delete(key)
  },
  clear(): void {
    this.store.clear()
  },
  key(index: number): string | null {
    return Array.from(this.store.keys())[index] || null
  },
  get length(): number {
    return this.store.size
  }
}

// Apply localStorage mock to global
global.localStorage = localStorageMock as any
