<script setup>
import { ref } from 'vue'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import ScoreRing from '@/components/common/ScoreRing.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import { api } from '@/api/index.js'

const targetPosition = ref('')
const uploadedFile = ref(null)
const loading = ref(false)
const results = ref(null)
const dragover = ref(false)

function onFileSelect(e) {
  const file = e.target.files?.[0]
  if (file) handleFile(file)
}

function onDrop(e) {
  e.preventDefault()
  dragover.value = false
  const file = e.dataTransfer.files?.[0]
  if (file) handleFile(file)
}

function handleFile(file) {
  const sizeKB = Math.round(file.size / 1024)
  uploadedFile.value = {
    name: file.name,
    size: sizeKB > 1024 ? `${(sizeKB / 1024).toFixed(1)} MB` : `${sizeKB} KB`,
    raw: file,
  }
}

function removeFile() {
  uploadedFile.value = null
}

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
      <div v-if="!uploadedFile">
        <div
          class="flex flex-col items-center gap-3 py-12 px-6 border-2 border-dashed border-border dark:border-border rounded-2xl cursor-pointer transition-theme text-center"
          :class="dragover ? 'border-primary bg-primary/5' : 'hover:border-primary hover:bg-primary/3'"
          @click="$refs.fileInput.click()"
          @dragover.prevent="dragover = true"
          @dragleave="dragover = false"
          @drop="onDrop"
        >
          <svg width="40" height="40" viewBox="0 0 40 40" fill="none" class="text-ink-muted">
            <path d="M20 24V8M20 8l-6 6M20 8l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M6 28v4a3 3 0 003 3h22a3 3 0 003-3v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
          <span class="text-base font-medium text-ink">点击上传或拖拽简历文件</span>
          <span class="text-sm text-ink-muted">支持 PDF、Word 格式，最大 10MB</span>
          <div class="flex gap-2 mt-2">
            <span class="px-2 py-0.5 bg-surface dark:bg-surface-alt rounded text-xs font-mono text-ink-muted">.pdf</span>
            <span class="px-2 py-0.5 bg-surface dark:bg-surface-alt rounded text-xs font-mono text-ink-muted">.doc</span>
            <span class="px-2 py-0.5 bg-surface dark:bg-surface-alt rounded text-xs font-mono text-ink-muted">.docx</span>
          </div>
        </div>
        <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileSelect" />
      </div>

      <!-- Uploaded file display -->
      <div v-else class="flex items-center gap-3 px-5 py-4 bg-surface dark:bg-surface-alt border border-border-light dark:border-border rounded-xl">
        <div class="w-10 h-10 rounded-lg bg-gradient-to-br from-[#fce4dc] to-[#f5d8cc] flex items-center justify-center shrink-0">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><rect x="3" y="2" width="14" height="16" rx="2" stroke="#E8937A" stroke-width="1.5"/><line x1="6" y1="7" x2="14" y2="7" stroke="#E8937A" stroke-width="1" opacity="0.5"/><line x1="6" y1="10" x2="11" y2="10" stroke="#E8937A" stroke-width="1" opacity="0.5"/></svg>
        </div>
        <div class="flex-1">
          <div class="text-sm font-medium">{{ uploadedFile.name }}</div>
          <div class="text-xs text-ink-muted">{{ uploadedFile.size }}</div>
        </div>
        <button class="w-7 h-7 rounded-full flex items-center justify-center text-ink-muted hover:bg-red-500/10 hover:text-red-500 transition-theme" @click="removeFile">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M5 5l6 6M11 5l-6 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
        </button>
      </div>

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
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold">简历分析报告</h3>
        <button class="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium border border-border dark:border-border bg-white dark:bg-surface text-ink-light hover:border-primary hover:text-primary transition-theme" @click="retry">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M1 7a6 6 0 1 1 1.8 4.2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/><path d="M1 11V7h4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          重新分析
        </button>
      </div>

      <ScoreRing
        :score="results.score"
        label="岗位匹配度"
        :summary="'与「' + targetPosition + '」的匹配度评估'"
      />

      <!-- Highlights -->
      <div class="mt-6 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><path d="M2 9l4 4L14 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
          匹配亮点
        </div>
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(h, i) in results.highlights" :key="i" class="mb-2 marker:text-primary">
            <strong class="text-ink">{{ h.text.split('：')[0] }}：</strong>{{ h.text.split('：')[1] }}
          </li>
        </ul>
      </div>

      <!-- Improvements -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.3"/><path d="M9 6v4M9 12v0.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          待改进项
        </div>
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(item, i) in results.improvements" :key="i" class="mb-2 marker:text-primary">
            <strong class="text-ink">{{ item.label }}：</strong>{{ item.text }}
          </li>
        </ul>
      </div>

      <!-- Suggestions -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><path d="M9 2v14M2 9h14" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
          简历修改建议
        </div>
        <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
          <li v-for="(s, i) in results.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
        </ul>
      </div>
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在分析简历"
      subtext="Capy 正在评估简历与岗位的匹配度..."
    />
  </AnalysisLayout>
</template>
