<script setup>
defineProps({
  step: { type: Number, required: true },
  title: { type: String, required: true },
  description: { type: String, default: '' }
})
</script>

<template>
  <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
    <div class="flex items-center gap-2 mb-4 font-semibold text-ink">
      <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold">
        {{ step }}
      </div>
      <span>{{ title }}</span>
    </div>
    <p v-if="description" class="text-sm text-ink-muted mb-4 ml-10">
      {{ description }}
    </p>
    <div class="ml-10">
      <slot />
    </div>
  </div>
</template>
