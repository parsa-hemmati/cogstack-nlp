/**
 * HTML Sanitization Utilities
 *
 * Purpose: Prevent XSS attacks by sanitizing HTML before rendering
 * Used for: Search result highlights from Elasticsearch
 *
 * HIPAA Compliance: Prevents session hijacking and PHI theft via XSS
 * GDPR Compliance: Protects personal data from unauthorized access
 */

import DOMPurify from 'dompurify'

/**
 * Sanitize HTML content allowing only safe tags
 *
 * For search highlights, we only allow <mark> tags for highlighting
 * All other HTML is stripped to prevent XSS attacks
 *
 * @param html - Raw HTML string from Elasticsearch
 * @returns Sanitized HTML safe for v-html rendering
 *
 * @example
 * ```typescript
 * const unsafe = 'Patient <script>alert("XSS")</script> discharged'
 * const safe = sanitizeHtml(unsafe)
 * // Returns: 'Patient  discharged'
 * ```
 *
 * @example
 * ```typescript
 * const highlight = 'Patient <mark>discharged</mark> on 2024-01-15'
 * const safe = sanitizeHtml(highlight)
 * // Returns: 'Patient <mark>discharged</mark> on 2024-01-15'
 * ```
 */
export function sanitizeHtml(html: string): string {
  if (!html) return ''

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['mark'],
    ALLOWED_ATTR: [],
    KEEP_CONTENT: true, // Keep text content even if tags are stripped
    RETURN_TRUSTED_TYPE: false
  })
}

/**
 * Sanitize search result highlights
 *
 * Handles the highlight object structure from Elasticsearch
 * with multiple arrays of highlight snippets
 *
 * @param highlights - Highlight object from Elasticsearch
 * @returns Sanitized highlights object
 *
 * @example
 * ```typescript
 * const highlights = {
 *   title: ['Patient <mark>discharged</mark>'],
 *   content: ['<script>alert("XSS")</script><mark>diabetes</mark>']
 * }
 * const safe = sanitizeHighlights(highlights)
 * // Returns: {
 * //   title: ['Patient <mark>discharged</mark>'],
 * //   content: ['<mark>diabetes</mark>']
 * // }
 * ```
 */
export function sanitizeHighlights(highlights: Record<string, string[]>): Record<string, string[]> {
  if (!highlights) return {}

  const sanitized: Record<string, string[]> = {}

  for (const [field, snippets] of Object.entries(highlights)) {
    sanitized[field] = snippets.map(snippet => sanitizeHtml(snippet))
  }

  return sanitized
}

/**
 * Check if content contains potentially malicious HTML
 *
 * Used for logging/monitoring suspicious content
 * Does NOT prevent XSS (use sanitizeHtml for that)
 *
 * @param html - HTML string to check
 * @returns true if suspicious patterns found
 */
export function containsSuspiciousHtml(html: string): boolean {
  if (!html) return false

  const suspiciousPatterns = [
    /<script/i,
    /javascript:/i,
    /on\w+\s*=/i, // Event handlers like onclick, onerror
    /<iframe/i,
    /<object/i,
    /<embed/i,
    /data:text\/html/i
  ]

  return suspiciousPatterns.some(pattern => pattern.test(html))
}
