<script setup>
import { ref, computed } from 'vue'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import ThemeToggle from '@/components/common/ThemeToggle.vue'
import TextMode from '@/components/interview/TextMode.vue'
import VoiceMode from '@/components/interview/VoiceMode.vue'
import SettingsPanel from '@/components/interview/SettingsPanel.vue'
import { useScrollState } from '@/composables/useScrollState.js'

const mode = ref('text')
const interviewType = ref('technical')
const settingsOpen = ref(false)
const { scrolled } = useScrollState()

const sliderStyle = computed(() => ({
  transform: mode.value === 'voice' ? 'translateX(100%)' : 'translateX(0)',
}))
</script>

<template>
  <div class="h-screen overflow-hidden transition-theme" style="background: var(--color-base)">
    <!-- Topbar -->
    <header
      class="topbar-glass fixed top-0 left-0 right-0 z-[100] flex items-center transition-shadow"
      :class="scrolled ? 'shadow-sm' : ''"
      :style="{
        height: 'var(--nav-height)',
        background: 'rgba(255,252,247,0.85)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--color-border-light)',
      }"
    >
      <div class="h-full flex items-center justify-between w-full px-6" style="max-width: 1400px; margin: 0 auto">
        <!-- Left -->
        <div class="flex items-center gap-3">
          <router-link
            to="/"
            class="flex items-center justify-center transition-all hover:bg-surface hover:text-primary"
            style="width: 36px; height: 36px; border-radius: var(--radius-full); color: var(--color-ink-light)"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M12 4l-6 6 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </router-link>
          <div class="flex items-center gap-2" style="font-family: var(--font-heading); font-weight: 600; font-size: var(--text-base)">
            <CapybaraLogo :size="24" />
            <span>模拟面试</span>
          </div>
        </div>

        <!-- Center: Mode toggle -->
        <div
          class="mode-toggle relative flex"
          :style="{ background: 'var(--color-surface)', borderRadius: 'var(--radius-full)', padding: '3px', border: '1px solid var(--color-border-light)' }"
        >
          <!-- Sliding pill -->
          <div
            class="absolute rounded-full transition-transform"
            :style="{
              top: '3px',
              left: '3px',
              height: 'calc(100% - 6px)',
              width: 'calc(50% - 3px)',
              background: 'var(--color-white)',
              borderRadius: 'var(--radius-full)',
              boxShadow: 'var(--shadow-sm)',
              transform: sliderStyle.transform,
              transition: 'transform var(--duration-normal) var(--ease-out)',
            }"
          ></div>
          <button
            class="relative z-10 flex items-center gap-2 rounded-full text-sm font-medium transition-colors"
            :style="{
              padding: 'var(--space-2) var(--space-4)',
              borderRadius: 'var(--radius-full)',
              color: mode === 'text' ? 'var(--color-ink)' : 'var(--color-ink-muted)',
            }"
            @click="mode = 'text'"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="2" y="2" width="12" height="12" rx="2" stroke="currentColor" stroke-width="1.3"/>
              <line x1="5" y1="5.5" x2="11" y2="5.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <line x1="5" y1="8" x2="9" y2="8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <line x1="5" y1="10.5" x2="10" y2="10.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
            <span>文字模式</span>
          </button>
          <button
            class="relative z-10 flex items-center gap-2 rounded-full text-sm font-medium transition-colors"
            :style="{
              padding: 'var(--space-2) var(--space-4)',
              borderRadius: 'var(--radius-full)',
              color: mode === 'voice' ? 'var(--color-ink)' : 'var(--color-ink-muted)',
            }"
            @click="mode = 'voice'"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <rect x="6" y="1.5" width="4" height="8" rx="2" stroke="currentColor" stroke-width="1.3"/>
              <path d="M3.5 7.5 C3.5 10.5, 5.5 13, 8 13 C10.5 13, 12.5 10.5, 12.5 7.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" fill="none"/>
              <line x1="8" y1="13" x2="8" y2="15" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
            <span>语音模式</span>
          </button>
        </div>

        <!-- Right -->
        <div class="flex items-center gap-2">
          <button
            class="flex items-center justify-center transition-all hover:bg-surface hover:text-primary"
            style="width: 40px; height: 40px; border-radius: var(--radius-full); color: var(--color-ink-light)"
            @click="settingsOpen = true"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="3" stroke="currentColor" stroke-width="1.5"/>
              <path d="M15 9a6 6 0 0 1-.3 1.8l1.4 1-1 1.7-1.6-.6a6 6 0 0 1-1.5 1l-.3 1.7h-2l-.3-1.7a6 6 0 0 1-1.5-1l-1.6.6-1-1.7 1.4-1A6 6 0 0 1 3.3 9a6 6 0 0 1 .3-1.8L2.2 6.2l1-1.7 1.6.6a6 6 0 0 1 1.5-1L6.6 2.4h2l.3 1.7a6 6 0 0 1 1.5 1l1.6-.6 1 1.7-1.4 1A6 6 0 0 1 15 9z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <ThemeToggle />
        </div>
      </div>
    </header>

    <!-- Content -->
    <main :style="{ paddingTop: 'var(--nav-height)' }">
      <TextMode v-if="mode === 'text'" :interview-type="interviewType" @update:type="interviewType = $event" />
      <VoiceMode v-if="mode === 'voice'" :interview-type="interviewType" />
    </main>

    <!-- Settings Panel -->
    <SettingsPanel :open="settingsOpen" @close="settingsOpen = false" />
  </div>
</template>
