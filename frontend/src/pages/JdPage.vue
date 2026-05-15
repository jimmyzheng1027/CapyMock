<script setup>
import { ref } from 'vue'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import ScoreRing from '@/components/common/ScoreRing.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { api } from '@/api/index.js'

const jdInput = ref('')
const loading = ref(false)
const results = ref(null)

async function analyze() {
  if (!jdInput.value.trim()) return
  loading.value = true
  try {
    results.value = await api.analyzeJd(jdInput.value)
  } finally {
    loading.value = false
  }
}

function retry() {
  results.value = null
  jdInput.value = ''
}
</script>

<template>
  <AnalysisLayout>
    <!-- Input Card -->
    <div v-if="!results" class="bg-white dark:bg-surface border-2 border-border-light dark:border-border rounded-2xl p-8 transition-theme focus-within:border-primary focus-within:shadow-glow">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-11 h-11 rounded-lg bg-gradient-to-br from-[#dde5da] to-[#d0dbca] flex items-center justify-center shrink-0">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="4" y="3" width="14" height="16" rx="2" stroke="#A8B5A0" stroke-width="1.8"/>
            <line x1="7" y1="7" x2="15" y2="7" stroke="#A8B5A0" stroke-width="1.3" stroke-linecap="round"/>
            <line x1="7" y1="10.5" x2="13" y2="10.5" stroke="#A8B5A0" stroke-width="1.3" stroke-linecap="round"/>
            <line x1="7" y1="14" x2="14" y2="14" stroke="#A8B5A0" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h2 class="text-xl font-bold">粘贴职位描述 (JD)</h2>
          <p class="text-sm text-ink-muted">Capy 将拆解岗位要求、匹配度评估和准备建议</p>
        </div>
      </div>

      <textarea
        v-model="jdInput"
        class="w-full min-h-[140px] px-5 py-4 bg-surface dark:bg-surface-alt border-2 border-border-light dark:border-border rounded-xl text-sm font-mono text-ink outline-none focus:border-primary focus:shadow-glow resize-y transition-theme placeholder:text-ink-muted placeholder:font-sans"
        placeholder="将 JD 内容粘贴到这里...

例如：
岗位名称：高级前端工程师
工作职责：
1. 负责公司核心产品的前端开发...
任职要求：
1. 3年以上前端开发经验..."
      ></textarea>

      <div class="flex items-center justify-between mt-5">
        <span class="text-xs text-ink-muted">建议粘贴完整的职位描述以获得更准确的分析</span>
        <button class="btn btn--primary" @click="analyze">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8z" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          开始分析
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results" class="animate-fade-in">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold">JD 分析报告</h3>
        <button class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border border-border dark:border-border bg-white dark:bg-surface text-ink-light hover:border-primary hover:text-primary transition-theme" @click="retry">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7a6 6 0 1 1 1.8 4.2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M1 11V7h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          重新分析
        </button>
      </div>

      <ScoreRing :score="results.score" label="岗位匹配难度" :summary="results.summary" />

      <!-- Requirements -->
      <div class="mt-6 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><rect x="2" y="2" width="14" height="14" rx="3" stroke="currentColor" stroke-width="1.3"/><path d="M6 8l3 3 3-3" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          核心要求拆解
        </div>
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(r, i) in results.requirements" :key="i" class="mb-2 marker:text-primary">
            <strong class="text-ink">{{ r.label }}：</strong>{{ r.text }}
          </li>
        </ul>
      </div>

      <!-- Implicit -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.3"/><path d="M9 6v4M9 12v0.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          隐含期望分析
        </div>
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(item, i) in results.implicit" :key="i" class="mb-2 marker:text-primary">
            <strong class="text-ink">{{ item.label }}：</strong>{{ item.text }}
          </li>
        </ul>
      </div>

      <!-- Suggestions -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><path d="M2 9h14M9 2v14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          针对性准备建议
        </div>
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(s, i) in results.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
        </ul>
      </div>
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在分析职位描述"
      subtext="Capy 正在拆解岗位要求..."
    />
  </AnalysisLayout>
</template>
