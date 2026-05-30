<script setup>
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
</script>

<template>
  <footer :style="{ padding: '3rem 0 2rem', borderTop: '1px solid var(--color-border-light)' }">
    <div class="container flex items-center justify-between">
      <div class="flex items-center gap-3">
        <CapybaraLogo :size="28" class="opacity-50" />
        <span class="text-sm" style="color: var(--color-ink-muted)">&copy; 2026 CapyMock. Made with care.</span>
      </div>
      <ul class="flex gap-6 list-none m-0 p-0">
        <li><a href="#" class="text-sm transition-colors hover:text-primary" style="color: var(--color-ink-muted)">关于我们</a></li>
        <li><a href="#" class="text-sm transition-colors hover:text-primary" style="color: var(--color-ink-muted)">隐私政策</a></li>
        <li><a href="#" class="text-sm transition-colors hover:text-primary" style="color: var(--color-ink-muted)">联系方式</a></li>
      </ul>
    </div>
  </footer>
</template>
