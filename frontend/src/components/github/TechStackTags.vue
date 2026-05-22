<script setup>
defineProps({
  tags: { type: Array, default: () => [] },
})
</script>

<template>
  <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
    <div class="flex items-center gap-2 mb-4 font-semibold">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><rect x="2" y="2" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.3"/><path d="M6 8l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
      技术栈识别
    </div>
    <div class="flex flex-wrap gap-2">
      <span
        v-for="tag in tags"
        :key="tag"
        class="px-3 py-1 rounded-full text-xs font-medium bg-primary/12 text-primary-dark"
      >
        {{ tag }}
      </span>
    </div>
  </div>
</template>
