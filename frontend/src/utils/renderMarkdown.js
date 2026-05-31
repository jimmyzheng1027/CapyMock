/**
 * Lightweight markdown renderer for chat bubbles.
 * Escapes HTML first, then applies a small safe subset of markdown.
 */

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

function applyInline(value) {
  return escapeHtml(value)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`\n]+)`/g, '<code class="bubble-code">$1</code>')
}

export function renderMarkdown(text) {
  if (!text) return ''

  const htmlParts = []
  const blocks = text.split(/\n\n+/)

  for (const block of blocks) {
    const trimmed = block.trim()
    if (!trimmed) continue

    if (/^-{3,}$/.test(trimmed)) {
      htmlParts.push('<hr class="bubble-hr" />')
      continue
    }

    const lines = trimmed.split('\n')
    const listLines = lines.filter((line) => line.trim())
    const isOrderedList = listLines.length > 0 && listLines.every((line) => /^\d+\.\s/.test(line.trim()))

    if (isOrderedList) {
      const items = listLines
        .map((line) => `<li>${applyInline(line.replace(/^\d+\.\s*/, ''))}</li>`)
        .join('')
      htmlParts.push(`<ol class="bubble-list">${items}</ol>`)
      continue
    }

    if (lines.some((line) => /^-{3,}$/.test(line.trim()))) {
      for (const line of lines) {
        const lineTrimmed = line.trim()
        if (/^-{3,}$/.test(lineTrimmed)) {
          htmlParts.push('<hr class="bubble-hr" />')
        } else if (lineTrimmed) {
          htmlParts.push(`<p>${applyInline(lineTrimmed)}</p>`)
        }
      }
      continue
    }

    if (lines.length === 1) {
      htmlParts.push(`<p>${applyInline(lines[0])}</p>`)
    } else {
      htmlParts.push(`<p>${lines.map((line) => applyInline(line)).join('<br />')}</p>`)
    }
  }

  return htmlParts.join('')
}
