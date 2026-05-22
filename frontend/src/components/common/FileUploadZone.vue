<script setup>
import { ref } from 'vue'

const props = defineProps({
  accept: { type: String, default: '.pdf,.doc,.docx' },
  label: { type: String, default: '点击上传或拖拽文件' },
  hint: { type: String, default: '' },
  formats: { type: Array, default: () => ['.pdf', '.doc', '.docx'] },
  file: { type: Object, default: null },
})

const emit = defineEmits(['select', 'remove'])

const dragover = ref(false)
const fileInput = ref(null)

function onFileSelect(e) {
  const f = e.target.files?.[0]
  if (f) emit('select', formatFile(f))
}

function onDrop(e) {
  e.preventDefault()
  dragover.value = false
  const f = e.dataTransfer.files?.[0]
  if (f) emit('select', formatFile(f))
}

function formatFile(f) {
  const sizeKB = Math.round(f.size / 1024)
  return {
    name: f.name,
    size: sizeKB > 1024 ? `${(sizeKB / 1024).toFixed(1)} MB` : `${sizeKB} KB`,
    raw: f,
  }
}

function openPicker() {
  fileInput.value?.click()
}
</script>

<template>
  <!-- Upload zone (no file selected) -->
  <div v-if="!file">
    <div
      class="flex flex-col items-center gap-3 py-12 px-6 border-2 border-dashed border-border dark:border-border rounded-2xl cursor-pointer transition-theme text-center"
      :class="dragover ? 'border-primary bg-primary/5' : 'hover:border-primary hover:bg-primary/3'"
      @click="openPicker"
      @dragover.prevent="dragover = true"
      @dragleave="dragover = false"
      @drop="onDrop"
    >
      <slot name="icon">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" class="text-ink-muted">
          <path d="M20 24V8M20 8l-6 6M20 8l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M6 28v4a3 3 0 003 3h22a3 3 0 003-3v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </slot>
      <span class="text-base font-medium text-ink">{{ label }}</span>
      <span v-if="hint" class="text-sm text-ink-muted">{{ hint }}</span>
      <div v-if="formats.length" class="flex gap-2 mt-2">
        <span
          v-for="fmt in formats"
          :key="fmt"
          class="px-2 py-0.5 bg-surface dark:bg-surface-alt rounded text-xs font-mono text-ink-muted"
        >{{ fmt }}</span>
      </div>
    </div>
    <input ref="fileInput" type="file" :accept="accept" class="hidden" @change="onFileSelect" />
  </div>

  <!-- File display (file selected) -->
  <div v-else class="flex items-center gap-3 px-5 py-4 bg-surface dark:bg-surface-alt border border-border-light dark:border-border rounded-xl">
    <slot name="file-icon">
      <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-[#fce4dc] to-[#f5d8cc] flex items-center justify-center shrink-0">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="2" width="14" height="16" rx="2" stroke="#E8937A" stroke-width="1.5"/><line x1="6" y1="7" x2="14" y2="7" stroke="#E8937A" stroke-width="1" opacity="0.5"/><line x1="6" y1="10" x2="11" y2="10" stroke="#E8937A" stroke-width="1" opacity="0.5"/></svg>
      </div>
    </slot>
    <div class="flex-1 min-w-0">
      <div class="text-sm font-medium truncate">{{ file.name }}</div>
      <div class="text-xs text-ink-muted">{{ file.size }}</div>
    </div>
    <button
      class="w-7 h-7 rounded-full flex items-center justify-center text-ink-muted hover:bg-red-500/10 hover:text-red-500 transition-theme"
      @click="emit('remove')"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M5 5l6 6M11 5l-6 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
    </button>
  </div>
</template>
