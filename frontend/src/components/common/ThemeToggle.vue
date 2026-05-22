<script setup>
import { useTheme } from '@/stores/theme.js'

const { state, toggle } = useTheme()
</script>

<template>
  <button
    class="flex items-center justify-center transition-all hover:bg-surface-alt hover:text-primary hover:rotate-12"
    :style="{
      width: '40px', height: '40px', borderRadius: 'var(--radius-full)',
      background: 'var(--color-surface)', border: '1px solid var(--color-border)',
      color: 'var(--color-ink-light)',
    }"
    @click="toggle"
    aria-label="切换深色模式"
  >
    <svg v-if="!state.dark" width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M15 10.5a6.5 6.5 0 0 1-8-8 6.5 6.5 0 1 0 8 8z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none">
      <circle cx="9" cy="9" r="4" stroke="currentColor" stroke-width="1.5"/>
      <path d="M9 1v2M9 15v2M1 9h2M15 9h2M3.3 3.3l1.4 1.4M13.3 13.3l1.4 1.4M3.3 14.7l1.4-1.4M13.3 4.7l1.4-1.4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
  </button>
</template>
