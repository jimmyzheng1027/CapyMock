<script setup>
import { ref } from 'vue'
import { useTheme } from '@/stores/theme.js'
import { useTweaks } from '@/stores/tweaks.js'

const { state: themeState, toggle: toggleTheme } = useTheme()
const { state, setPrimary, setFontSize, setRadius, toggleAnimations } = useTweaks()

const open = ref(false)

function onPrimaryChange(e) {
  setPrimary(e.target.value)
}

function onFontSizeChange(e) {
  setFontSize(Number(e.target.value))
}

function onRadiusChange(e) {
  setRadius(Number(e.target.value))
}
</script>

<template>
  <!-- Toggle button — matches original: bg-ink, color-base, 44px -->
  <button
    class="fixed z-[9998] flex items-center justify-center transition-all"
    :style="{
      bottom: '20px', right: '20px',
      width: '44px', height: '44px', borderRadius: 'var(--radius-full)',
      background: 'var(--color-ink)', color: 'var(--color-base)',
      boxShadow: 'var(--shadow-lg)',
    }"
    @mouseenter="$event.currentTarget.style.transform='scale(1.08)'; $event.currentTarget.style.boxShadow='var(--shadow-xl)'"
    @mouseleave="$event.currentTarget.style.transform=''; $event.currentTarget.style.boxShadow='var(--shadow-lg)'"
    @click="open = !open"
    aria-label="Tweaks"
  >
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
      <path d="M10 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="1.5"/>
      <path d="M16.5 10a6.5 6.5 0 0 1-.4 2.1l1.6 1.2-1.5 2.6-1.8-.7a6.4 6.4 0 0 1-1.8 1.1L12 19h-3l-.6-2.3a6.4 6.4 0 0 1-1.8-1.1l-1.8.7-1.5-2.6 1.6-1.2A6.5 6.5 0 0 1 3.5 10a6.5 6.5 0 0 1 6.5-6.5A6.5 6.5 0 0 1 16.5 10z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  </button>

  <!-- Panel — dark glass style matching original -->
  <div
    v-if="open"
    class="fixed z-[9999]"
    :style="{
      bottom: '76px', right: '20px', width: '280px',
      background: 'rgba(24,24,27,0.95)',
      backdropFilter: 'blur(16px)',
      borderRadius: 'var(--radius-lg)',
      padding: '1.25rem',
      color: '#fff',
      fontSize: 'var(--text-sm)',
      boxShadow: '0 20px 60px rgba(0,0,0,0.3)',
      border: '1px solid rgba(255,255,255,0.08)',
    }"
  >
    <!-- Title -->
    <div class="flex items-center gap-2 font-semibold text-base mb-4">
      <span class="w-2 h-2 rounded-full" style="background: var(--color-accent)"></span>
      Tweaks
    </div>

    <!-- Primary color -->
    <div class="mb-4">
      <span class="block mb-2 text-xs uppercase tracking-wider opacity-50">主题色</span>
      <div class="flex items-center gap-3 justify-between">
        <input type="color" :value="state.primary" @input="onPrimaryChange" class="cursor-pointer p-0" style="width: 28px; height: 28px; border: 2px solid rgba(255,255,255,0.2); border-radius: var(--radius-sm); background: none; -webkit-appearance: none;" />
        <span class="text-xs opacity-40 font-mono text-right" style="min-width: 36px">{{ state.primary }}</span>
      </div>
    </div>

    <div class="my-3" style="height: 1px; background: rgba(255,255,255,0.08)"></div>

    <!-- Font size -->
    <div class="mb-4">
      <span class="block mb-2 text-xs uppercase tracking-wider opacity-50">字体大小</span>
      <div class="flex items-center gap-3 justify-between">
        <input type="range" min="14" max="20" :value="state.fontSize" @input="onFontSizeChange" class="flex-1 accent-primary" />
        <span class="text-xs opacity-40 font-mono text-right" style="min-width: 36px">{{ state.fontSize }}px</span>
      </div>
    </div>

    <!-- Border radius -->
    <div class="mb-4">
      <span class="block mb-2 text-xs uppercase tracking-wider opacity-50">圆角大小</span>
      <div class="flex items-center gap-3 justify-between">
        <input type="range" min="0" max="28" :value="state.radius" @input="onRadiusChange" class="flex-1 accent-primary" />
        <span class="text-xs opacity-40 font-mono text-right" style="min-width: 36px">{{ state.radius }}px</span>
      </div>
    </div>

    <div class="my-3" style="height: 1px; background: rgba(255,255,255,0.08)"></div>

    <!-- Dark mode toggle -->
    <div class="mb-4">
      <span class="block mb-2 text-xs uppercase tracking-wider opacity-50">深色模式</span>
      <div>
        <button
          class="relative cursor-pointer shrink-0"
          :style="{
            width: '36px', height: '20px', borderRadius: '10px',
            background: themeState.dark ? 'var(--color-primary)' : 'rgba(255,255,255,0.15)',
            transition: 'background var(--duration-fast) var(--ease-out)',
          }"
          @click="toggleTheme"
        >
          <span
            class="absolute bg-white rounded-full"
            :style="{
              top: '2px', left: '2px', width: '16px', height: '16px',
              transform: themeState.dark ? 'translateX(16px)' : '',
              transition: 'transform var(--duration-fast) var(--ease-out)',
            }"
          ></span>
        </button>
      </div>
    </div>

    <!-- Animations toggle -->
    <div>
      <span class="block mb-2 text-xs uppercase tracking-wider opacity-50">动画效果</span>
      <div>
        <button
          class="relative cursor-pointer shrink-0"
          :style="{
            width: '36px', height: '20px', borderRadius: '10px',
            background: state.animations ? 'var(--color-primary)' : 'rgba(255,255,255,0.15)',
            transition: 'background var(--duration-fast) var(--ease-out)',
          }"
          @click="toggleAnimations"
        >
          <span
            class="absolute bg-white rounded-full"
            :style="{
              top: '2px', left: '2px', width: '16px', height: '16px',
              transform: state.animations ? 'translateX(16px)' : '',
              transition: 'transform var(--duration-fast) var(--ease-out)',
            }"
          ></span>
        </button>
      </div>
    </div>
  </div>
</template>
