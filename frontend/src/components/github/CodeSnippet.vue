<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  code: { type: String, default: '' },
  language: { type: String, default: '' },
  title: { type: String, default: '' },
  description: { type: String, default: '' },
})

const copied = ref(false)

const highlighted = computed(() => {
  const src = escapeHtml(props.code)
  const keywords = 'import|export|from|const|let|var|function|return|if|else|for|while|class|extends|new|this|async|await|try|catch|throw|interface|type|enum|struct|impl|fn|use|mod|pub|mut|self|super|crate|where|match|loop|break|continue|yield|default|switch|case|typeof|instanceof|void|null|undefined|true|false'

  // Single-pass tokenizer: match tokens in priority order
  const tokenRe = new RegExp(
    `(\\/\\/.*$|\\/\\*[\\s\\S]*?\\*\\/|#.*$)` +  // comments
    `|(&quot;.*?&quot;|&#039;.*?&#039;|` + '`' + `[^` + '`' + `]*` + '`' + `)` +  // strings
    `|\\b(${keywords})\\b` +  // keywords
    `|\\b(\\d+\\.?\\d*)\\b` +  // numbers
    `|(:\\s*)(\\w+)`,  // types after colon
    'gm'
  )

  let result = ''
  let last = 0
  let match

  while ((match = tokenRe.exec(src)) !== null) {
    // Add text before this match
    result += src.slice(last, match.index)

    if (match[1]) {
      // Comment
      result += `<span class="hl-comment">${match[1]}</span>`
    } else if (match[2]) {
      // String
      result += `<span class="hl-string">${match[2]}</span>`
    } else if (match[3]) {
      // Keyword
      result += `<span class="hl-keyword">${match[3]}</span>`
    } else if (match[4]) {
      // Number
      result += `<span class="hl-number">${match[4]}</span>`
    } else if (match[5] !== undefined) {
      // Type after colon
      result += `${match[5]}<span class="hl-type">${match[6]}</span>`
    }

    last = match.index + match[0].length
  }

  result += src.slice(last)
  return result
})

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

async function copyCode() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {}
}
</script>

<template>
  <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl overflow-hidden">
    <!-- Header -->
    <div v-if="title" class="flex items-center justify-between px-5 py-3 border-b border-border-light dark:border-border">
      <div class="flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" class="text-primary shrink-0">
          <path d="M5 4L1.5 8 5 12M11 4l3.5 4-3.5 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span class="text-sm font-medium text-ink">{{ title }}</span>
        <span v-if="language" class="text-[10px] px-1.5 py-0.5 rounded bg-surface-alt text-ink-muted font-mono">{{ language }}</span>
      </div>
      <button
        class="text-xs text-ink-muted hover:text-primary transition-colors flex items-center gap-1"
        @click="copyCode"
      >
        <svg v-if="!copied" width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="4" y="4" width="8" height="8" rx="1.5" stroke="currentColor" stroke-width="1.2"/><path d="M10 4V3a1.5 1.5 0 0 0-1.5-1.5H3A1.5 1.5 0 0 0 1.5 3v5.5A1.5 1.5 0 0 0 3 10h1" stroke="currentColor" stroke-width="1.2"/></svg>
        <svg v-else width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 7.5l3 3 5-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        {{ copied ? '已复制' : '复制' }}
      </button>
    </div>

    <!-- Code -->
    <div class="overflow-x-auto">
      <pre class="p-5 text-xs leading-relaxed font-mono m-0" style="background: var(--color-surface-alt); color: var(--color-ink)"><code v-html="highlighted"></code></pre>
    </div>

    <!-- Description -->
    <div v-if="description" class="px-5 py-3 border-t border-border-light dark:border-border text-sm text-ink-light leading-relaxed">
      {{ description }}
    </div>
  </div>
</template>

<style>
.hl-keyword { color: var(--color-primary); font-weight: 600; }
.hl-string { color: var(--color-secondary); }
.hl-comment { color: var(--color-ink-muted); font-style: italic; }
.hl-type { color: var(--color-accent); }
.hl-number { color: #E07858; }
</style>
