<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'

const route = useRoute()
const scrolled = ref(false)
const sidebarOpen = ref(false)

function onScroll() {
  scrolled.value = window.scrollY > 10
}

onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))

const links = [
  { to: '/analysis/github', label: 'GitHub 源码分析', icon: 'github' },
  { to: '/analysis/jd', label: 'JD 智能分析', icon: 'jd' },
  { to: '/analysis/resume', label: '简历匹配分析', icon: 'resume' },
]

const bottomLinks = [
  { to: '/interview', label: '模拟面试', icon: 'interview' },
]
</script>

<template>
  <div class="min-h-screen transition-theme" style="background: var(--color-base)">
    <!-- Topbar -->
    <header
      class="nav-glass fixed top-0 left-0 right-0 z-[100] flex items-center transition-shadow"
      :class="scrolled ? 'shadow-sm' : ''"
      :style="{
        height: 'var(--nav-height)',
        background: 'rgba(255,252,247,0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--color-border-light)',
      }"
    >
      <div class="h-full flex items-center justify-between w-full px-6">
        <div class="flex items-center gap-3">
          <button
            class="lg:hidden w-9 h-9 rounded-full flex items-center justify-center"
            style="color: var(--color-ink-light)"
            @click="sidebarOpen = !sidebarOpen"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
          <router-link to="/" style="color: var(--color-ink-light)">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12 4l-6 6 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </router-link>
          <div class="flex items-center gap-2">
            <CapybaraLogo :size="24" />
            <span class="font-semibold text-sm">
              {{ route.meta.title?.replace(' — CapyMock', '') || '分析' }}
            </span>
          </div>
        </div>
        <ThemeToggle />
      </div>
    </header>

    <!-- Sidebar overlay (mobile) -->
    <div
      v-if="sidebarOpen"
      class="fixed inset-0 z-40 bg-black/30 lg:hidden"
      @click="sidebarOpen = false"
    ></div>

    <!-- Sidebar -->
    <aside
      class="fixed left-0 bottom-0 w-[280px] z-40 p-6 flex flex-col gap-4 overflow-y-auto transition-transform lg:translate-x-0"
      :class="sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      :style="{
        top: 'var(--nav-height)',
        background: 'var(--color-white)',
        borderRight: '1px solid var(--color-border-light)',
      }"
    >
      <div class="mb-1">
        <div
          class="text-xs font-semibold uppercase mb-3"
          style="color: var(--color-ink-muted); letter-spacing: 0.08em"
        >分析模块</div>
      </div>

      <router-link
        v-for="link in links"
        :key="link.to"
        :to="link.to"
        class="flex items-center gap-3 rounded-xl text-sm font-medium no-underline transition-all"
        :style="{
          padding: '0.75rem 1rem',
          borderRadius: 'var(--radius-lg)',
          color: route.path === link.to ? 'var(--color-primary)' : 'var(--color-ink-light)',
          background: route.path === link.to ? 'rgba(196,149,106,0.1)' : 'transparent',
          fontWeight: route.path === link.to ? '600' : '500',
        }"
        @mouseenter="route.path !== link.to && ($event.currentTarget.style.background='var(--color-surface-alt)')"
        @mouseleave="route.path !== link.to && ($event.currentTarget.style.background='transparent')"
        @click="sidebarOpen = false"
      >
        <svg v-if="link.icon === 'github'" width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M5 8l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          <rect x="2" y="2" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.5"/>
        </svg>
        <svg v-if="link.icon === 'jd'" width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="3" y="2" width="12" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <line x1="6" y1="6" x2="12" y2="6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          <line x1="6" y1="9" x2="10" y2="9" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
          <line x1="6" y1="12" x2="11" y2="12" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <svg v-if="link.icon === 'resume'" width="18" height="18" viewBox="0 0 18 18" fill="none">
          <rect x="3" y="2" width="12" height="14" rx="2" stroke="currentColor" stroke-width="1.5"/>
          <circle cx="9" cy="7" r="2.5" stroke="currentColor" stroke-width="1.2"/>
          <path d="M5 14c0-2.5 1.8-4 4-4s4 1.5 4 4" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        {{ link.label }}
      </router-link>

      <!-- Bottom links -->
      <div class="mt-auto pt-4" style="border-top: 1px solid var(--color-border-light)">
        <router-link
          v-for="link in bottomLinks"
          :key="link.to"
          :to="link.to"
          class="flex items-center gap-3 rounded-xl text-sm font-medium no-underline transition-all"
          style="padding: 0.75rem 1rem; color: var(--color-ink-light)"
          @mouseenter="$event.currentTarget.style.background='var(--color-surface-alt)'"
          @mouseleave="$event.currentTarget.style.background='transparent'"
          @click="sidebarOpen = false"
        >
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <rect x="4" y="2" width="10" height="10" rx="5" stroke="currentColor" stroke-width="1.5"/>
            <path d="M4 11v2a2 2 0 002 2h6a2 2 0 002-2v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          {{ link.label }}
        </router-link>
      </div>
    </aside>

    <!-- Main content -->
    <main class="lg:ml-[280px] py-8" :style="{ paddingTop: 'calc(var(--nav-height) + 2rem)' }">
      <div class="mx-auto px-6 lg:px-10" style="max-width: 960px">
        <slot />
      </div>
    </main>
  </div>
</template>

<style>
.dark .nav-glass {
  background: rgba(15, 14, 12, 0.85) !important;
}
</style>
