<script setup>
import { ref } from 'vue'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import ScoreRing from '@/components/common/ScoreRing.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { api } from '@/api/index.js'

const repoUrl = ref('')
const loading = ref(false)
const results = ref(null)

async function analyze() {
  if (!repoUrl.value.trim()) return
  loading.value = true
  try {
    results.value = await api.analyzeGithub(repoUrl.value)
  } finally {
    loading.value = false
  }
}

function retry() {
  results.value = null
  repoUrl.value = ''
}

function getRepoName(url) {
  const parts = url.replace(/\/$/, '').split('/')
  return parts.slice(-2).join('/')
}
</script>

<template>
  <AnalysisLayout>
    <!-- Input Card -->
    <div v-if="!results" class="bg-white dark:bg-surface border-2 border-border-light dark:border-border rounded-2xl p-8 transition-theme focus-within:border-primary focus-within:shadow-glow">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-11 h-11 rounded-lg bg-gradient-to-br from-[#f0e6dc] to-[#e8ddd1] flex items-center justify-center shrink-0">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <path d="M5 11l5 5L19 5" stroke="#C4956A" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div>
          <h2 class="text-xl font-bold">粘贴 GitHub 仓库链接</h2>
          <p class="text-sm text-ink-muted">Capy 会分析代码结构、技术栈和项目亮点</p>
        </div>
      </div>

      <input
        v-model="repoUrl"
        type="url"
        class="w-full px-5 py-3 bg-surface dark:bg-surface-alt border-2 border-border-light dark:border-border rounded-xl text-sm font-mono text-ink outline-none focus:border-primary focus:shadow-glow transition-theme placeholder:text-ink-muted placeholder:font-sans"
        placeholder="https://github.com/username/repository"
        @keydown.enter="analyze"
      />

      <div class="flex items-center justify-between mt-5">
        <span class="text-xs text-ink-muted">支持公开仓库，私有仓库需授权</span>
        <button class="btn btn--primary" @click="analyze">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8z" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          开始分析
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results" class="animate-fade-in">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold">分析结果</h3>
        <div class="flex gap-3">
          <button class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border border-border dark:border-border bg-white dark:bg-surface text-ink-light hover:border-primary hover:text-primary transition-theme" @click="retry">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7a6 6 0 1 1 1.8 4.2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M1 11V7h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
            重新分析
          </button>
        </div>
      </div>

      <!-- Score -->
      <ScoreRing
        :score="results.score"
        label="项目综合评分"
        :summary="`仓库 ${getRepoName(repoUrl)} 综合评估`"
      />

      <!-- Tech Stack -->
      <div class="mt-6 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><rect x="2" y="2" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.3"/><path d="M6 8l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          技术栈识别
        </div>
        <div class="flex flex-wrap gap-2">
          <span v-for="tag in results.techTags" :key="tag" class="px-3 py-1 rounded-full text-xs font-medium bg-primary/12 text-primary-dark">
            {{ tag }}
          </span>
        </div>
      </div>

      <!-- Interview Questions -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.3"/><path d="M7 7.5a2 2 0 0 1 3.3 1.3c0 1-1.3 1.2-1.3 2.2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><circle cx="9.2" cy="13" r="0.8" fill="currentColor"/></svg>
          面试问题
        </div>
        <div class="flex flex-col gap-4">
          <div v-for="(qa, i) in results.questions" :key="i" class="p-5 bg-surface dark:bg-surface-alt rounded-xl border-l-[3px] border-primary">
            <div class="font-semibold text-sm text-ink mb-3">{{ qa.q }}</div>
            <div class="text-sm text-ink-light leading-relaxed pl-4 border-l-2 border-border-light dark:border-border">{{ qa.a }}</div>
          </div>
        </div>
      </div>

      <!-- Highlights -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><path d="M9 2l2.1 4.3 4.7.7-3.4 3.3.8 4.7L9 12.8l-4.2 2.2.8-4.7L2.2 7l4.7-.7z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          项目亮点 & 改进建议
        </div>
        <div class="text-sm text-ink-light leading-relaxed">
          <ul class="pl-5 m-0">
            <li v-for="(h, i) in results.highlights" :key="i" class="mb-2 marker:text-primary">
              <strong class="text-ink">{{ h.text.split('：')[0] }}：</strong>{{ h.text.split('：')[1] }}
            </li>
          </ul>
          <div class="mt-4 font-semibold text-primary">改进建议：</div>
          <ul class="pl-5 m-0 mt-2">
            <li v-for="(s, i) in results.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
          </ul>
        </div>
      </div>
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在分析代码仓库"
      subtext="Capy 正在阅读代码、理解架构..."
    />
  </AnalysisLayout>
</template>
