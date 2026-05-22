<script setup>
defineProps({
  isListening: { type: Boolean, default: false },
  transcript: { type: String, default: '' }
})
</script>

<template>
  <div class="text-center">
    <!-- AI Avatar -->
    <div class="w-24 h-24 mx-auto rounded-full bg-primary/10 flex items-center justify-center mb-4">
      <span class="text-4xl">🤖</span>
    </div>
    <h3 class="text-lg font-semibold text-ink mb-2">AI面试官</h3>

    <!-- Listening Status -->
    <div
      class="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-4"
      :class="isListening ? 'bg-red-100 text-red-700' : 'bg-surface text-ink-muted'"
    >
      <span
        class="w-2 h-2 rounded-full"
        :class="isListening ? 'bg-red-500 animate-pulse' : 'bg-ink-muted'"
      />
      <span class="text-sm font-medium">
        {{ isListening ? '监听中...' : '等待开始' }}
      </span>
    </div>

    <!-- Real-time Transcript -->
    <div
      v-if="transcript"
      class="max-w-md mx-auto p-4 bg-surface rounded-xl"
    >
      <p class="text-sm text-ink leading-relaxed">
        实时转写: "{{ transcript }}"
      </p>
    </div>
  </div>
</template>
