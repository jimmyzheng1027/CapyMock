<script setup>
defineProps({
  icon: { type: String, default: '' },
  title: { type: String, required: true },
})

const iconPaths = {
  list: 'M6 8l3 3 3-3',
  info: 'M9 6v4M9 12v0.5',
  check: 'M6 9l2 2 4-4',
  plus: 'M9 4v10M4 9h10',
  star: 'M9 2l2.1 4.3 4.7.7-3.4 3.3.8 4.7L9 12.8l-4.2 2.2.8-4.7L2.2 7l4.7-.7z',
}
</script>

<template>
  <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
    <div class="flex items-center gap-2 mb-4 font-semibold">
      <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary">
        <rect x="2" y="2" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.3" fill="none"/>
        <path v-if="icon === 'list'" d="M6 8l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
        <circle v-else-if="icon === 'info'" cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.3" fill="none"/>
        <path v-else-if="icon === 'info'" d="M9 6v4M9 12v0.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        <path v-else-if="icon === 'check'" d="M6 9l2 2 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <path v-else-if="icon === 'plus'" d="M9 4v10M4 9h10" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
        <path v-else-if="icon === 'star'" d="M9 2l2.1 4.3 4.7.7-3.4 3.3.8 4.7L9 12.8l-4.2 2.2.8-4.7L2.2 7l4.7-.7z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
      </svg>
      {{ title }}
    </div>
    <slot />
  </div>
</template>
