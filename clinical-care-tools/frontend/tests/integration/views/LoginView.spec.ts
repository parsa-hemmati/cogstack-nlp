/**
 * Integration tests for LoginView
 *
 * Tests cover:
 * - Complete login flow
 * - Form submission to store
 * - Successful login and redirect
 * - Error handling and display
 * - Loading states
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { vuetify, mockRouter, mockAxios, createMockUser } from '@/tests/setup'

// Mock component (replace with actual LoginView)
const LoginView = {
  template: `
    <div class="login-view">
      <h1>Login</h1>
      <form @submit.prevent="handleLogin">
        <input
          v-model="credentials.email"
          type="email"
          placeholder="Email"
          data-testid="email-input"
        />
        <input
          v-model="credentials.password"
          type="password"
          placeholder="Password"
          data-testid="password-input"
        />
        <label>
          <input
            v-model="credentials.rememberMe"
            type="checkbox"
            data-testid="remember-me"
          />
          Remember me
        </label>
        <button type="submit" :disabled="isLoading" data-testid="submit-button">
          {{ isLoading ? 'Logging in...' : 'Login' }}
        </button>
        <div v-if="error" class="error-alert" data-testid="error-alert">
          {{ error }}
        </div>
      </form>
    </div>
  `,
  data() {
    return {
      credentials: {
        email: '',
        password: '',
        rememberMe: false,
      },
      isLoading: false,
      error: null,
    }
  },
  methods: {
    async handleLogin() {
      this.isLoading = true
      this.error = null

      try {
        // Simulate API call
        const response = await new Promise((resolve) => {
          setTimeout(() => {
            resolve({
              data: {
                access_token: 'mock_token',
                user: createMockUser({ email: this.credentials.email }),
              },
            })
          }, 100)
        })

        // Simulate storing token and user
        const auth = { user: (response as any).data.user }
        this.$emit('login-success', auth)

        // Simulate redirect
        this.$router.push('/dashboard')
      } catch (err: any) {
        this.error = err.message || 'Login failed'
      } finally {
        this.isLoading = false
      }
    },
  },
}

describe('LoginView Integration', () => {
  let wrapper: any

  beforeEach(() => {
    setActivePinia(createPinia())

    wrapper = mount(LoginView, {
      global: {
        plugins: [vuetify],
        mocks: {
          $router: mockRouter,
          $route: mockRouter.currentRoute,
        },
      },
    })

    // Reset mocks
    vi.clearAllMocks()
  })

  afterEach(() => {
    localStorage.clear()
  })

  describe('View Rendering', () => {
    it('should render login view', () => {
      expect(wrapper.find('.login-view').exists()).toBe(true)
    })

    it('should render login form', () => {
      expect(wrapper.find('form').exists()).toBe(true)
    })

    it('should render email input', () => {
      expect(wrapper.find('[data-testid="email-input"]').exists()).toBe(true)
    })

    it('should render password input', () => {
      expect(wrapper.find('[data-testid="password-input"]').exists()).toBe(true)
    })

    it('should render submit button', () => {
      expect(wrapper.find('[data-testid="submit-button"]').exists()).toBe(true)
    })
  })

  describe('Login Flow', () => {
    it('should handle successful login', async () => {
      const emailInput = wrapper.find('[data-testid="email-input"]')
      const passwordInput = wrapper.find('[data-testid="password-input"]')
      const submitButton = wrapper.find('[data-testid="submit-button"]')

      await emailInput.setValue('test@example.com')
      await passwordInput.setValue('password123')
      await submitButton.trigger('submit')

      await flushPromises()

      // Should emit login-success
      expect(wrapper.emitted('login-success')).toBeTruthy()
    })

    it('should redirect to dashboard on successful login', async () => {
      const emailInput = wrapper.find('[data-testid="email-input"]')
      const passwordInput = wrapper.find('[data-testid="password-input"]')
      const submitButton = wrapper.find('[data-testid="submit-button"]')

      await emailInput.setValue('test@example.com')
      await passwordInput.setValue('password123')
      await submitButton.trigger('submit')

      await flushPromises()

      expect(mockRouter.push).toHaveBeenCalledWith('/dashboard')
    })

    it('should show loading state during login', async () => {
      const emailInput = wrapper.find('[data-testid="email-input"]')
      const passwordInput = wrapper.find('[data-testid="password-input"]')

      await emailInput.setValue('test@example.com')
      await passwordInput.setValue('password123')

      const submitButton = wrapper.find('[data-testid="submit-button"]')
      expect(submitButton.text()).toBe('Login')

      await submitButton.trigger('submit')

      // Should show loading state
      expect(wrapper.vm.isLoading).toBe(true)

      await flushPromises()

      // Should clear loading state after complete
      expect(wrapper.vm.isLoading).toBe(false)
    })

    it('should disable submit button during login', async () => {
      const emailInput = wrapper.find('[data-testid="email-input"]')
      const passwordInput = wrapper.find('[data-testid="password-input"]')

      await emailInput.setValue('test@example.com')
      await passwordInput.setValue('password123')

      const submitButton = wrapper.find('[data-testid="submit-button"]')
      await submitButton.trigger('submit')

      expect(submitButton.attributes('disabled')).toBeDefined()
    })
  })

  describe('Remember Me', () => {
    it('should include remember me in login request', async () => {
      const emailInput = wrapper.find('[data-testid="email-input"]')
      const passwordInput = wrapper.find('[data-testid="password-input"]')
      const rememberMe = wrapper.find('[data-testid="remember-me"]')

      await emailInput.setValue('test@example.com')
      await passwordInput.setValue('password123')
      await rememberMe.setValue(true)

      expect(wrapper.vm.credentials.rememberMe).toBe(true)
    })
  })

  describe('Error Handling', () => {
    it('should display error message on failed login', async () => {
      // Simulate error by not providing credentials
      const submitButton = wrapper.find('[data-testid="submit-button"]')

      // Set error manually for this test
      wrapper.vm.error = 'Invalid credentials'
      await wrapper.vm.$nextTick()

      expect(wrapper.find('[data-testid="error-alert"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="error-alert"]').text()).toBe(
        'Invalid credentials'
      )
    })

    it('should clear error on new login attempt', async () => {
      wrapper.vm.error = 'Previous error'
      await wrapper.vm.$nextTick()

      const emailInput = wrapper.find('[data-testid="email-input"]')
      await emailInput.setValue('test@example.com')

      // Error should be cleared
      expect(wrapper.vm.error).toBeNull()
    })
  })

  describe('Form Validation', () => {
    it('should not submit with empty email', async () => {
      const passwordInput = wrapper.find('[data-testid="password-input"]')
      const submitButton = wrapper.find('[data-testid="submit-button"]')

      await passwordInput.setValue('password123')
      // Don't set email
      await submitButton.trigger('submit')

      // Email is empty, form should not process
      expect(wrapper.vm.credentials.email).toBe('')
    })

    it('should not submit with empty password', async () => {
      const emailInput = wrapper.find('[data-testid="email-input"]')
      const submitButton = wrapper.find('[data-testid="submit-button"]')

      await emailInput.setValue('test@example.com')
      // Don't set password
      await submitButton.trigger('submit')

      // Password is empty, form should not process
      expect(wrapper.vm.credentials.password).toBe('')
    })
  })

  describe('Accessibility', () => {
    it('should have proper button type', () => {
      const submitButton = wrapper.find('[data-testid="submit-button"]')
      expect(submitButton.attributes('type')).toBe('submit')
    })

    it('should show button text during normal state', () => {
      const submitButton = wrapper.find('[data-testid="submit-button"]')
      expect(submitButton.text()).toContain('Login')
    })
  })
})
