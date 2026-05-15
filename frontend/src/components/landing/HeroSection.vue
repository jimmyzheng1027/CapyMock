<template>
  <section :style="{ paddingTop: 'calc(var(--nav-height) + 5rem)', paddingBottom: '5rem', overflow: 'hidden' }">
    <div class="container grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
      <!-- Content -->
      <div class="text-center lg:text-left">
        <!-- Badge -->
        <div
          class="inline-flex items-center gap-2 rounded-full text-xs font-medium mb-6 animate-hero-fade-up"
          style="padding: 0.25rem 1rem; background: var(--color-surface); border: 1px solid var(--color-border); color: var(--color-ink-muted); animation-delay: 0.1s"
        >
          <span class="w-1.5 h-1.5 rounded-full" style="background: var(--color-secondary)"></span>
          AI 驱动的求职辅助平台
        </div>

        <!-- Title -->
        <h1
          class="font-bold mb-6 animate-hero-fade-up leading-[1.1] tracking-tight"
          style="font-family: var(--font-heading); font-size: var(--text-hero); margin-bottom: 1.5rem; animation-delay: 0.2s"
        >
          让求职变得<br>
          <span style="color: var(--color-primary)">更有把握</span>
        </h1>

        <!-- Description -->
        <p
          class="mb-8 max-w-[480px] mx-auto lg:mx-0 animate-hero-fade-up"
          style="font-size: var(--text-lg); color: var(--color-ink-light); line-height: var(--leading-relaxed); animation-delay: 0.35s"
        >
          从源码分析到模拟面试，CapyMock 用 AI 帮你拆解每一个求职环节。
          像有位耐心的朋友陪你准备，而不是冰冷的工具。
        </p>

        <!-- Actions -->
        <div class="flex gap-4 justify-center lg:justify-start animate-hero-fade-up" style="animation-delay: 0.5s">
          <router-link to="/interview" class="btn btn--primary no-underline" style="font-size: var(--text-base)">
            <svg class="btn__icon" viewBox="0 0 18 18" fill="none"><path d="M9 3v12M3 9l6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
            免费开始
          </router-link>
          <button class="btn btn--secondary" style="font-size: var(--text-base)">了解更多</button>
        </div>
      </div>

      <!-- Illustration -->
      <div class="flex justify-center items-center animate-hero-fade-scale" style="animation-delay: 0.3s">
        <svg viewBox="0 0 460 360" fill="none" class="w-full max-w-[420px]">
          <!-- Ground line -->
          <path d="M20 310 Q230 320 440 310" stroke="#C4956A" stroke-width="1" stroke-dasharray="4 6" opacity="0.3"/>
          <!-- Body -->
          <path d="M100 200 C60 200, 40 170, 50 140 C55 120, 70 100, 100 90 C130 80, 180 75, 220 80 C270 86, 310 100, 330 130 C350 160, 345 200, 310 220 C290 232, 250 240, 200 240 C160 240, 130 228, 100 200 Z" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <!-- Ears -->
          <path d="M130 90 C125 75, 135 68, 142 80" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M200 78 C195 63, 210 58, 215 73" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <!-- Eyes -->
          <circle cx="155" cy="135" r="4" fill="#C4956A"/>
          <circle cx="195" cy="130" r="4" fill="#C4956A"/>
          <!-- Nose/mouth -->
          <path d="M175 148 L175 162" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M165 162 Q175 175 185 162" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <ellipse cx="175" cy="168" rx="5" ry="4" fill="#E8937A" opacity="0.6"/>
          <!-- Legs -->
          <path d="M110 210 C95 225, 80 240, 75 255" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M68 258 C72 265, 82 265, 86 258" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M170 235 C165 255, 158 270, 155 280" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M148 282 C153 288, 163 288, 168 282" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M260 235 C265 255, 272 270, 278 280" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M272 282 C278 288, 288 288, 292 282" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <path d="M310 210 C325 225, 340 240, 348 250" stroke="#C4956A" stroke-width="2.8" stroke-linecap="round" fill="none"/>
          <path d="M342 252 C348 258, 358 255, 355 248" stroke="#C4956A" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          <!-- Laptop -->
          <rect x="310" y="115" width="100" height="65" rx="5" stroke="#C4956A" stroke-width="1.8" fill="none"/>
          <line x1="320" y1="128" x2="355" y2="128" stroke="#C4956A" stroke-width="1" opacity="0.4"/>
          <line x1="320" y1="136" x2="370" y2="136" stroke="#C4956A" stroke-width="1" opacity="0.4"/>
          <line x1="320" y1="144" x2="348" y2="144" stroke="#C4956A" stroke-width="1" opacity="0.4"/>
          <line x1="320" y1="152" x2="365" y2="152" stroke="#C4956A" stroke-width="1" opacity="0.3"/>
          <path d="M305 180 L302 192 L422 192 L419 180 Z" stroke="#C4956A" stroke-width="1.8" fill="none"/>
          <!-- Decorative -->
          <text x="390" y="105" font-family="JetBrains Mono, monospace" font-size="13" fill="#C4956A" opacity="0.2">&gt;</text>
          <text x="80" y="70" font-family="JetBrains Mono, monospace" font-size="11" fill="#C4956A" opacity="0.15">{ }</text>
          <circle cx="400" cy="260" r="3" stroke="#C4956A" stroke-width="1" fill="none" opacity="0.15"/>
          <circle cx="55" cy="240" r="2" stroke="#C4956A" stroke-width="1" fill="none" opacity="0.12"/>
        </svg>
      </div>
    </div>
  </section>
</template>
