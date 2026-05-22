<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    title: 'GitHub 源码分析',
    desc: '粘贴你的 GitHub 仓库链接，Capy 会深入分析代码结构、技术栈和项目亮点，自动生成针对性的面试问题和回答话术。',
    tag: '支持主流语言和框架',
    route: '/analysis/github',
    iconWrapBg: 'linear-gradient(135deg, #f0e6dc, #e8ddd1)',
    iconStroke: '#C4956A',
  },
  {
    title: 'JD 智能分析',
    desc: '粘贴职位描述，Capy 会拆解岗位核心要求、隐含期望和匹配度评估，帮你判断是否值得投递，以及如何针对性准备。',
    tag: '关键词匹配 + 评估报告',
    route: '/analysis/jd',
    iconWrapBg: 'linear-gradient(135deg, #dde5da, #d0dbca)',
    iconStroke: '#A8B5A0',
  },
  {
    title: '简历匹配分析',
    desc: '上传简历并指定目标岗位，Capy 会评估你的经历与岗位的相关性，指出亮点和不足，并给出具体的修改建议。',
    tag: 'PDF / Word 格式支持',
    route: '/analysis/resume',
    iconWrapBg: 'linear-gradient(135deg, #fce4dc, #f5d8cc)',
    iconStroke: '#E8937A',
  },
]
</script>

<template>
  <section id="features" :style="{ padding: '6rem 0', background: 'var(--color-surface)' }">
    <div class="container">
      <!-- Section header -->
      <div class="text-center mb-16 reveal">
        <div
          class="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-wider mb-4"
          style="color: var(--color-primary); letter-spacing: 0.1em"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.2"/><path d="M5 8h6M8 5v6" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
          智能分析
        </div>
        <h2 class="text-3xl lg:text-5xl font-bold mb-4" style="font-family: var(--font-heading)">三个维度，全面准备</h2>
        <p class="text-lg mx-auto" style="color: var(--color-ink-light); max-width: 560px; line-height: var(--leading-relaxed)">
          从技术能力到岗位匹配，再到简历优化，每个环节都有 Capy 帮你梳理
        </p>
      </div>

      <!-- Cards grid -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          v-for="(f, i) in features"
          :key="i"
          class="reveal relative cursor-pointer overflow-hidden transition-all border border-border-light hover:-translate-y-1.5 hover:shadow-lg hover:border-primary-light"
          :style="{
            transitionDelay: `${i * 0.1}s`,
            background: 'var(--color-white)',
            borderRadius: 'var(--radius-xl)',
            padding: '2rem',
            transitionDuration: 'var(--duration-slow)',
            transitionTimingFunction: 'var(--ease-out)',
          }"
          @click="router.push(f.route)"
        >
          <!-- Icon -->
          <div
            class="w-16 h-16 flex items-center justify-center mb-6"
            :style="{ borderRadius: 'var(--radius-lg)', background: f.iconWrapBg }"
          >
            <svg v-if="i === 0" width="32" height="32" viewBox="0 0 32 32" fill="none">
              <path d="M6 10 L12 16 L6 22" :stroke="f.iconStroke" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M15 22 L25 22" :stroke="f.iconStroke" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <svg v-if="i === 1" width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect x="6" y="4" width="20" height="24" rx="3" :stroke="f.iconStroke" stroke-width="2" fill="none"/>
              <line x1="10" y1="10" x2="22" y2="10" :stroke="f.iconStroke" stroke-width="1.5" stroke-linecap="round"/>
              <line x1="10" y1="15" x2="18" y2="15" :stroke="f.iconStroke" stroke-width="1.5" stroke-linecap="round"/>
              <line x1="10" y1="20" x2="20" y2="20" :stroke="f.iconStroke" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <svg v-if="i === 2" width="32" height="32" viewBox="0 0 32 32" fill="none">
              <rect x="6" y="3" width="20" height="26" rx="3" :stroke="f.iconStroke" stroke-width="2" fill="none"/>
              <circle cx="16" cy="12" r="4" :stroke="f.iconStroke" stroke-width="1.5" fill="none"/>
              <path d="M10 24 C10 20, 13 18, 16 18 C19 18, 22 20, 22 24" :stroke="f.iconStroke" stroke-width="1.5" stroke-linecap="round" fill="none"/>
            </svg>
          </div>

          <!-- Content -->
          <h3 class="text-xl font-bold mb-3" style="font-family: var(--font-heading)">{{ f.title }}</h3>
          <p class="text-sm mb-6" style="color: var(--color-ink-light); line-height: var(--leading-relaxed)">{{ f.desc }}</p>

          <!-- Tag -->
          <span class="inline-flex items-center gap-1.5 text-xs font-medium rounded-full" style="padding: 0.25rem 0.75rem; background: var(--color-surface); color: var(--color-ink-muted)">
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 6h8M6 2v8" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            {{ f.tag }}
          </span>

          <!-- Deco capybara -->
          <svg v-if="i === 0" class="absolute bottom-2.5 right-2.5 opacity-[0.06] hover:opacity-[0.12] transition-opacity" width="120" height="120" viewBox="0 0 140 120" fill="none">
            <path d="M55 75 C30 75, 15 58, 20 42 C23 32, 35 22, 55 18 C72 14, 90 18, 100 30 C110 42, 108 65, 90 75 C78 82, 68 80, 55 75 Z" stroke="#C4956A" stroke-width="2" stroke-linecap="round" fill="none"/>
            <circle cx="50" cy="42" r="2" fill="#C4956A"/>
            <circle cx="68" cy="38" r="2" fill="#C4956A"/>
            <path d="M58 50 L58 56" stroke="#C4956A" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M52 56 Q58 62 64 56" stroke="#C4956A" stroke-width="1.5" stroke-linecap="round" fill="none"/>
          </svg>
        </div>
      </div>
    </div>
  </section>
</template>
