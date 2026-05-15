<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <section id="interview" :style="{ padding: '6rem 0', position: 'relative' }">
    <div class="container">
      <!-- Section header -->
      <div class="text-center mb-16 reveal">
        <div
          class="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider mb-4"
          style="color: var(--color-primary); letter-spacing: 0.1em"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 2 C4 2, 2 5, 2 8 C2 11, 4 14, 8 14 C12 14, 14 11, 14 8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" fill="none"/><circle cx="8" cy="8" r="2" fill="currentColor"/></svg>
          模拟面试
        </div>
        <h2 class="text-3xl lg:text-5xl font-bold mb-4" style="font-family: var(--font-heading)">两种模式，随时开练</h2>
        <p class="text-lg mx-auto" style="color: var(--color-ink-light); max-width: 560px; line-height: var(--leading-relaxed)">
          Capy 会结合你的简历和目标岗位进行个性化提问，像真实面试一样自然
        </p>
      </div>

      <!-- Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-[1000px] mx-auto">
        <!-- Text mode card -->
        <div
          class="reveal relative overflow-hidden cursor-pointer transition-all"
          :style="{
            background: 'var(--color-white)',
            borderRadius: 'var(--radius-xl)',
            padding: '2.5rem',
            border: '1px solid var(--color-border-light)',
            transitionDuration: 'var(--duration-slow)',
            transitionTimingFunction: 'var(--ease-out)',
          }"
          @mouseenter="$event.currentTarget.style.transform='translateY(-4px)'; $event.currentTarget.style.boxShadow='var(--shadow-lg)'"
          @mouseleave="$event.currentTarget.style.transform=''; $event.currentTarget.style.boxShadow=''"
          @click="router.push('/interview')"
        >
          <!-- Mode badge -->
          <div class="inline-flex items-center gap-2 text-xs font-semibold rounded-full mb-6" style="padding: 0.25rem 0.75rem; background: #EDE9F5; color: #6B5B95">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="2" y="2" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.2"/><line x1="5" y1="5" x2="9" y2="5" stroke="currentColor" stroke-width="1" stroke-linecap="round"/><line x1="5" y1="7.5" x2="8" y2="7.5" stroke="currentColor" stroke-width="1" stroke-linecap="round"/></svg>
            文字对话模式
          </div>

          <h3 class="text-2xl font-bold mb-3" style="font-family: var(--font-heading)">文字模拟面试</h3>
          <p class="text-sm mb-8" style="color: var(--color-ink-light); line-height: var(--leading-relaxed)">
            以对话形式进行，Capy 面试官会根据你的回答深入追问。
            适合喜欢思考后再回答的候选人，可以反复推敲每个回答。
          </p>

          <!-- Chat preview -->
          <div class="p-6 rounded-xl" style="background: var(--color-surface); border: 1px solid var(--color-border-light); border-radius: var(--radius-lg)">
            <div class="text-xs font-semibold uppercase tracking-wider mb-4" style="color: var(--color-ink-muted); letter-spacing: 0.08em">对话预览</div>
            <div class="flex flex-col gap-3">
              <div class="max-w-[85%] rounded-xl text-sm" style="padding: 0.75rem 1rem; background: var(--color-white); color: var(--color-ink); border: 1px solid var(--color-border-light); border-bottom-left-radius: 0.25rem; line-height: var(--leading-normal)">
                你好！我看到你简历上有 React 项目经验，能介绍一下你在项目中遇到的最大技术挑战吗？
              </div>
              <div class="max-w-[85%] self-end rounded-xl text-sm" style="padding: 0.75rem 1rem; background: var(--color-primary); color: var(--color-white); border-bottom-right-radius: 0.25rem; line-height: var(--leading-normal)">
                主要是性能优化方面，列表渲染卡顿问题...
              </div>
              <div class="max-w-[85%] rounded-xl text-sm" style="padding: 0.75rem 1rem; background: var(--color-white); color: var(--color-ink); border: 1px solid var(--color-border-light); border-bottom-left-radius: 0.25rem; line-height: var(--leading-normal)">
                很好，你具体用了哪些优化手段？虚拟列表还是其他方案？
              </div>
              <div class="max-w-[85%] self-end rounded-xl text-sm" style="padding: 0.75rem 1rem; background: var(--color-primary); color: var(--color-white); border-bottom-right-radius: 0.25rem; line-height: var(--leading-normal)">
                用了虚拟列表 + React.memo + useMemo 缓存计算结果
              </div>
            </div>
          </div>
        </div>

        <!-- Voice mode card -->
        <div
          class="reveal relative overflow-hidden cursor-pointer transition-all"
          style="transition-delay: 0.1s"
          :style="{
            background: 'var(--color-white)',
            borderRadius: 'var(--radius-xl)',
            padding: '2.5rem',
            border: '1px solid var(--color-border-light)',
            transitionDuration: 'var(--duration-slow)',
            transitionTimingFunction: 'var(--ease-out)',
          }"
          @mouseenter="$event.currentTarget.style.transform='translateY(-4px)'; $event.currentTarget.style.boxShadow='var(--shadow-lg)'"
          @mouseleave="$event.currentTarget.style.transform=''; $event.currentTarget.style.boxShadow=''"
          @click="router.push('/interview')"
        >
          <!-- Mode badge -->
          <div class="inline-flex items-center gap-2 text-xs font-semibold rounded-full mb-6" style="padding: 0.25rem 0.75rem; background: #DCF0E4; color: #3D7A54">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="5" y="1" width="4" height="8" rx="2" stroke="currentColor" stroke-width="1.2"/><path d="M3 7 C3 10, 5 12, 7 12 C9 12, 11 10, 11 7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" fill="none"/><line x1="7" y1="12" x2="7" y2="14" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            语音通话模式
          </div>

          <h3 class="text-2xl font-bold mb-3" style="font-family: var(--font-heading)">语音模拟面试</h3>
          <p class="text-sm mb-8" style="color: var(--color-ink-light); line-height: var(--leading-relaxed)">
            用语音实时对话，更接近真实面试场景。
            Capy 面试官会分析你的语速、表达流畅度，训练临场应变能力。
          </p>

          <!-- Voice preview -->
          <div class="p-6 rounded-xl text-center" style="background: var(--color-surface); border: 1px solid var(--color-border-light); border-radius: var(--radius-lg)">
            <div class="text-xs font-semibold uppercase tracking-wider mb-4" style="color: var(--color-ink-muted); letter-spacing: 0.08em">语音交互</div>
            <div class="flex flex-col items-center gap-4">
              <!-- Avatar -->
              <div class="w-14 h-14 rounded-full flex items-center justify-center relative" style="background: linear-gradient(135deg, var(--color-primary-light), var(--color-primary))">
                <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                  <path d="M14 3 C7 3, 3 8, 3 14 C3 20, 7 25, 14 25 C21 25, 25 20, 25 14 C25 8, 21 3, 14 3 Z" stroke="white" stroke-width="2" stroke-linecap="round" fill="none"/>
                  <path d="M8 5 C7 2, 10 1, 11 4" stroke="white" stroke-width="2" stroke-linecap="round" fill="none"/>
                  <path d="M17 4 C16 1, 19 0, 20 3" stroke="white" stroke-width="2" stroke-linecap="round" fill="none"/>
                  <circle cx="10" cy="12" r="1.8" fill="white"/>
                  <circle cx="18" cy="12" r="1.8" fill="white"/>
                  <path d="M14 15 L14 18" stroke="white" stroke-width="1.8" stroke-linecap="round"/>
                  <path d="M11 18 Q14 21 17 18" stroke="white" stroke-width="1.8" stroke-linecap="round" fill="none"/>
                </svg>
              </div>

              <!-- Wave bars -->
              <div class="flex items-center gap-[3px] h-8">
                <span v-for="n in 7" :key="n" class="rounded-sm animate-wave-bar" :style="{ width: '3px', background: 'var(--color-primary)', animationDelay: `${(n-1) * 0.1}s`, height: [8, 16, 24, 16, 8, 20, 12][n-1] + 'px' }"></span>
              </div>

              <p class="text-sm" style="color: var(--color-ink-muted)">Capy 面试官正在聆听...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
