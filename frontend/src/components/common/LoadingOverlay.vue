<script setup>
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'

defineProps({
  active: { type: Boolean, default: false },
  text: { type: String, default: '正在分析中' },
  subtext: { type: String, default: 'Capy 正在处理中...' },
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
          <CapybaraLogo :size="64" :stroke-width="2.5" />
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
