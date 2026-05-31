<script setup>
import { ref } from 'vue'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import ResultsHeader from '@/components/common/ResultsHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import { api } from '@/api/index.js'

const jdInput = ref('')
const loading = ref(false)
const results = ref(null)
const error = ref(null)

async function analyze() {
  if (!jdInput.value.trim()) return
  loading.value = true
  error.value = null
  try {
    results.value = await api.analyzeJd(jdInput.value)
  } catch (e) {
    error.value = e.message || '分析失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function retry() {
  results.value = null
  error.value = null
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
          <p class="text-sm text-ink-muted">Capy 将拆解核心要求、隐含期望和潜在雷点</p>
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

      <div v-if="error" class="mt-3 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400">
        {{ error }}
      </div>

      <div class="flex items-center justify-between mt-5">
        <span class="text-xs text-ink-muted">建议粘贴完整的职位描述以获得更准确的分析</span>
        <button class="btn btn--primary" :disabled="!jdInput.trim() || loading" @click="analyze">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8z" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          开始分析
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results" class="animate-fade-in">
      <ResultsHeader title="JD 分析报告" @retry="retry" />

      <!-- Core Requirements -->
      <SectionCard icon="list" title="核心要求拆解" class="mt-6">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(r, i) in results.requirements" :key="i" class="mb-2 marker:text-primary">
            <span class="inline-block px-2 py-0.5 text-xs font-medium rounded-full mr-2"
              :class="r.type === '硬性要求' ? 'bg-coral-sand/10 text-coral-sand' : 'bg-moss-green/10 text-moss-green'"
            >{{ r.type }}</span>
            <span class="text-ink">{{ r.text }}</span>
          </li>
        </ul>
      </SectionCard>

      <!-- Implicit Expectations -->
      <SectionCard icon="info" title="隐含期望分析" class="mt-4">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(item, i) in results.implicit_expectations" :key="i" class="mb-2 marker:text-primary">
            {{ item.text }}
          </li>
        </ul>
      </SectionCard>

      <!-- Red Flags -->
      <SectionCard icon="warning" title="雷点预警" class="mt-4">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(flag, i) in results.red_flags" :key="i" class="mb-3">
            <div class="flex items-start gap-2">
              <span class="inline-block px-2 py-0.5 text-xs font-medium rounded-full shrink-0 mt-0.5"
                :class="{
                  'bg-red-100 text-red-600': flag.severity === '高',
                  'bg-amber-100 text-amber-600': flag.severity === '中',
                  'bg-gray-100 text-gray-600': flag.severity === '低',
                }"
              >{{ flag.severity }}风险</span>
              <span class="text-ink">{{ flag.text }}</span>
            </div>
          </li>
        </ul>
      </SectionCard>

      <!-- Suggestions -->
      <SectionCard icon="plus" title="针对性准备建议" class="mt-4">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(s, i) in results.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
        </ul>
      </SectionCard>
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在分析职位描述"
      subtext="Capy 正在拆解岗位要求..."
    />
  </AnalysisLayout>
</template>
