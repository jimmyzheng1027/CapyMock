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
        <img src="@/assets/放大镜capy.png" alt="Hero Illustration" class="w-full max-w-md">
        
      </div>
    </div>
  </section>
</template>
