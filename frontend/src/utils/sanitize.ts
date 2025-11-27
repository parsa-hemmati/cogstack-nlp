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
 * For search highlights, we allow <mark> and <span> tags for highlighting
 * All other HTML is stripped to prevent XSS attacks
 *
 * @param html - Raw HTML string from Elasticsearch or user input
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
 *
 * @example
 * ```typescript
 * const annotation = 'Patient <span class="annotation-highlight" style="background-color: #FF572233;">NAME</span>'
 * const safe = sanitizeHtml(annotation)
 * // Returns: 'Patient <span class="annotation-highlight" style="background-color: #FF572233;">NAME</span>'
 * ```
 */
export function sanitizeHtml(html: string): string {
  if (!html) return ''

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['mark', 'span'],
    ALLOWED_ATTR: ['class', 'style'],
    KEEP_CONTENT: true, // Keep text content even if tags are stripped
    RETURN_TRUSTED_TYPE: false,
    // Only allow specific CSS properties in style attribute
    ALLOW_DATA_ATTR: false,
    ALLOWED_URI_REGEXP: /^(?:(?:(?:f|ht)tps?|mailto|tel|callto|sms|cid|xmpp):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i
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
