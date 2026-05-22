<script setup>
defineProps({
  title: { type: String, required: true },
})
defineEmits(['retry'])
</script>

<template>
  <div class="flex items-center justify-between mb-6">
    <h3 class="text-xl font-bold">{{ title }}</h3>
    <button
      class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border border-border dark:border-border bg-white dark:bg-surface text-ink-light hover:border-primary hover:text-primary transition-theme"
      @click="$emit('retry')"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7a6 6 0 1 1 1.8 4.2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M1 11V7h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      重新分析
    </button>
  </div>
</template>
