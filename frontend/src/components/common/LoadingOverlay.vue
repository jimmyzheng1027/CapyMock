<script setup>
defineProps({
  active: { type: Boolean, default: false },
  text: { type: String, default: '正在分析中' },
  subtext: { type: String, default: 'AI 正在处理中...' },
})
</script>

<template>
  <Transition name="fade">
    <div
      v-if="active"
      class="fixed inset-0 z-50 flex items-center justify-center"
      style="background: rgba(0,0,0,0.15); backdrop-filter: blur(4px)"
    >
      <div
        class="text-center animate-fade-in"
        :style="{
          background: 'var(--color-white)',
          borderRadius: 'var(--radius-xl)',
          padding: '2.5rem 3rem',
          boxShadow: 'var(--shadow-xl)',
        }"
      >
        <div class="mb-5 animate-bounce-subtle">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <path d="M32 8 C16 8, 8 18, 8 32 C8 46, 16 56, 32 56 C48 56, 56 46, 56 32 C56 18, 48 8, 32 8 Z" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M18 14 C16 6, 22 4, 24 10" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M40 10 C38 2, 44 0, 46 8" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <circle cx="24" cy="28" r="3" fill="var(--color-primary)"/>
            <circle cx="40" cy="28" r="3" fill="var(--color-primary)"/>
            <path d="M32 34 L32 42" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M26 42 Q32 50 38 42" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          </svg>
        </div>
        <p class="text-base font-medium mb-2" style="color: var(--color-ink)">
          {{ text }}<span class="loading-dots"><span></span><span></span><span></span></span>
        </p>
        <p class="text-sm" style="color: var(--color-ink-muted)">{{ subtext }}</p>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
