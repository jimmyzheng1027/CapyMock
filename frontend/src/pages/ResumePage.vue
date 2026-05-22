<script setup>
import { ref } from 'vue'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import ScoreRing from '@/components/common/ScoreRing.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import ResultsHeader from '@/components/common/ResultsHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import FileUploadZone from '@/components/common/FileUploadZone.vue'
import { api } from '@/api/index.js'

const targetPosition = ref('')
const uploadedFile = ref(null)
const loading = ref(false)
const results = ref(null)

async function analyze() {
  if (!uploadedFile.value || !targetPosition.value.trim()) return
  loading.value = true
  try {
    results.value = await api.analyzeResume(uploadedFile.value.raw, targetPosition.value)
  } finally {
    loading.value = false
  }
}

function retry() {
  results.value = null
  uploadedFile.value = null
  targetPosition.value = ''
}
</script>

<template>
  <AnalysisLayout>
    <!-- Input Card -->
    <div v-if="!results" class="bg-white dark:bg-surface border-2 border-border-light dark:border-border rounded-2xl p-8 transition-theme focus-within:border-primary focus-within:shadow-glow">
      <div class="flex items-center gap-3 mb-5">
        <div class="w-11 h-11 rounded-lg bg-gradient-to-br from-[#fce4dc] to-[#f5d8cc] flex items-center justify-center shrink-0">
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="4" y="3" width="14" height="16" rx="2" stroke="#E8937A" stroke-width="1.8"/>
            <circle cx="11" cy="9" r="3" stroke="#E8937A" stroke-width="1.3"/>
            <path d="M6 17c0-3 2.2-5 5-5s5 2 5 5" stroke="#E8937A" stroke-width="1.3" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <h2 class="text-xl font-bold">上传简历并指定目标岗位</h2>
          <p class="text-sm text-ink-muted">Capy 将评估你的简历与目标岗位的相关性</p>
        </div>
      </div>

      <!-- Upload zone -->
      <FileUploadZone
        :file="uploadedFile"
        label="点击上传或拖拽简历文件"
        hint="支持 PDF、Word 格式，最大 10MB"
        :formats="['.pdf', '.doc', '.docx']"
        @select="uploadedFile = $event"
        @remove="uploadedFile = null"
      />

      <!-- Position input -->
      <div class="mt-4">
        <input
          v-model="targetPosition"
          type="text"
          class="w-full px-5 py-3 bg-surface dark:bg-surface-alt border-2 border-border-light dark:border-border rounded-xl text-sm font-mono text-ink outline-none focus:border-primary focus:shadow-glow transition-theme placeholder:text-ink-muted placeholder:font-sans"
          placeholder="目标岗位，例：前端工程师 / 产品经理 / 数据分析师"
        />
      </div>

      <div class="flex items-center justify-between mt-5">
        <span class="text-xs text-ink-muted">上传简历并填写目标岗位后开始分析</span>
        <button class="btn btn--primary" @click="analyze">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8a6 6 0 1 1 12 0A6 6 0 0 1 2 8z" stroke="currentColor" stroke-width="1.5"/><path d="M8 5v3l2 1.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          开始分析
        </button>
      </div>
    </div>

    <!-- Results -->
    <div v-if="results" class="animate-fade-in">
      <ResultsHeader title="简历分析报告" @retry="retry" />

      <ScoreRing
        :score="results.score"
        label="岗位匹配度"
        :summary="'与「' + targetPosition + '」的匹配度评估'"
      />

      <SectionCard icon="check" title="匹配亮点" class="mt-6">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(h, i) in results.highlights" :key="i" class="mb-2 marker:text-primary">
            <strong class="text-ink">{{ h.text.split('：')[0] }}：</strong>{{ h.text.split('：')[1] }}
          </li>
        </ul>
      </SectionCard>

      <SectionCard icon="info" title="待改进项" class="mt-4">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(item, i) in results.improvements" :key="i" class="mb-2 marker:text-primary">
            <strong class="text-ink">{{ item.label }}：</strong>{{ item.text }}
          </li>
        </ul>
      </SectionCard>

      <SectionCard icon="plus" title="简历修改建议" class="mt-4">
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(s, i) in results.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
        </ul>
      </SectionCard>
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在分析简历"
      subtext="Capy 正在评估简历与岗位的匹配度..."
    />
  </AnalysisLayout>
</template>
