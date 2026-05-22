<script setup>
import FollowUpTag from './FollowUpTag.vue'

defineProps({
  message: { type: Object, required: true }
})
</script>

<template>
  <div
    class="flex gap-3"
    :class="message.role === 'user' ? 'flex-row-reverse' : 'flex-row'"
  >
    <!-- Avatar -->
    <div
      class="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0"
      :class="message.role === 'ai' ? 'bg-primary/10 text-primary' : 'bg-surface text-ink-muted'"
    >
      {{ message.role === 'ai' ? '🤖' : '👤' }}
    </div>

    <!-- Bubble -->
    <div
      class="max-w-[80%] rounded-xl p-4"
      :class="[
        message.role === 'ai'
          ? 'bg-white dark:bg-surface border border-border-light dark:border-border'
          : 'bg-primary text-white',
        message.isFollowUp ? 'ml-8' : ''
      ]"
    >
      <FollowUpTag v-if="message.isFollowUp" class="mb-2" />
      <p
        class="text-sm leading-relaxed"
        :class="message.role === 'ai' ? 'text-ink' : 'text-white'"
      >
        {{ message.content }}
      </p>
    </div>
  </div>
</template>
