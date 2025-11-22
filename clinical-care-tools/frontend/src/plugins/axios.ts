/**
 * Axios plugin configuration
 * This file is imported in main.ts to configure axios globally
 */

// Set default axios configuration
if (typeof window !== 'undefined') {
  // Browser-specific configuration

  // Handle network errors globally
  window.addEventListener('online', () => {
    // You could trigger a notification here
  })

  window.addEventListener('offline', () => {
    // You could trigger a notification here
  })

  // Add CSRF token if needed (for Django backend)
  const getCsrfToken = () => {
    const cookies = document.cookie.split(';')
    for (const cookie of cookies) {
      const [name, value] = cookie.trim().split('=')
      if (name === 'csrftoken') {
        return value
      }
    }
    return null
  }

  const csrfToken = getCsrfToken()
  if (csrfToken) {
    // Will be used by axios interceptor if needed
    (window as any).__CSRF_TOKEN__ = csrfToken
  }
}

// Export empty object to make this a module
export {}