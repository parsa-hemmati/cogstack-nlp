/**
 * Vitest configuration for Clinical Care Tools frontend
 *
 * Specification: Frontend testing framework configuration
 * Framework: Vitest + Vue Test Utils + @testing-library/vue
 * Target: 85% overall coverage, 90% for auth/UI critical paths
 */

import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  test: {
    // Test environment
    environment: 'jsdom',

    // Global test setup
    setupFiles: ['./tests/setup.ts'],

    // Test globals (no need to import describe, it, expect, etc.)
    globals: true,

    // Coverage configuration
    coverage: {
      // Coverage provider
      provider: 'v8',

      // Files to include
      include: ['src/**/*.{js,ts,vue}'],

      // Files to exclude
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.spec.ts',
        '**/*.test.ts',
        '**/types/**',
        'dist/',
      ],

      // Coverage reports
      reporter: ['text', 'json', 'html', 'lcov', 'text-summary'],

      // Report directory
      reportsDirectory: './coverage',

      // Minimum coverage percentages
      lines: 85,
      functions: 85,
      branches: 85,
      statements: 85,

      // Skip empty lines in coverage
      skipFull: false,

      // Show per-line coverage
      lines: 85,
    },

    // Test patterns
    include: ['tests/**/*.spec.ts', 'tests/**/*.test.ts'],
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache'],

    // Globals
    globals: true,

    // Threads configuration
    threads: true,
    maxThreads: 4,
    minThreads: 1,

    // Isolate test environment between tests
    isolate: true,

    // Test timeout
    testTimeout: 10000,
    hookTimeout: 10000,

    // Reporters
    reporters: ['verbose'],

    // Include source maps for debugging
    sourcemap: true,

    // Bail on first failure (useful during development)
    bail: 0,

    // Mock reset/restore between tests
    mockReset: true,
    restoreMocks: true,
    clearMocks: true,

    // Snapshot configuration
    snapshotFormat: {
      printBasicPrototype: false,
    },

    // Aliases (match vite.config.ts)
    alias: {
      '@': path.resolve(__dirname, './src'),
    },

    // CSS handling
    css: true,
  },

  // Vite configuration
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      vue: 'vue/dist/vue.esm-bundler.js',
    },
  },
})
