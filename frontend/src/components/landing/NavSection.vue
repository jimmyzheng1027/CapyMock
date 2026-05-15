<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const scrolled = ref(false)

function onScroll() {
  scrolled.value = window.scrollY > 10
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<template>
  <nav
    class="nav-glass fixed top-0 left-0 right-0 z-[100] flex items-center transition-shadow"
    :class="scrolled ? 'shadow-sm' : ''"
    :style="{ height: 'var(--nav-height)', background: 'rgba(255,252,247,0.85)', backdropFilter: 'blur(16px)', borderBottom: '1px solid var(--color-border-light)' }"
  >
    <div class="w-full flex items-center justify-between mx-auto px-6" style="max-width: var(--max-width)">
      <!-- Logo -->
      <router-link to="/" class="flex items-center gap-3 text-xl font-bold" style="font-family: var(--font-heading); color: var(--color-ink);">
        <CapybaraLogo :size="36" />
        CapyMock
      </router-link>

      <!-- Nav links -->
      <ul class="hidden md:flex items-center gap-8 list-none m-0 p-0">
        <li>
          <a href="#features" class="text-sm font-medium transition-colors relative" style="color: var(--color-ink-light)" @mouseenter="$event.target.style.color='var(--color-primary)'" @mouseleave="$event.target.style.color='var(--color-ink-light)'">智能分析</a>
        </li>
        <li>
          <a href="#interview" class="text-sm font-medium transition-colors relative" style="color: var(--color-ink-light)" @mouseenter="$event.target.style.color='var(--color-primary)'" @mouseleave="$event.target.style.color='var(--color-ink-light)'">模拟面试</a>
        </li>
      </ul>

      <!-- Right actions -->
      <div class="flex items-center gap-3">
        <ThemeToggle />
        <router-link
          to="/interview"
          class="inline-flex items-center text-sm font-medium rounded-full transition-all hover:-translate-y-px no-underline"
          style="padding: 0.5rem 1.25rem; background: var(--color-ink); color: var(--color-white);"
        >
          开始使用
        </router-link>
      </div>
    </div>
  </nav>
</template>

<style>
.dark .nav-glass {
  background: rgba(15, 14, 12, 0.85) !important;
}
</style>
