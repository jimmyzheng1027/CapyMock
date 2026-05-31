<script setup>
import { ref, onMounted } from 'vue'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'
import ResultsHeader from '@/components/common/ResultsHeader.vue'
import SectionCard from '@/components/common/SectionCard.vue'
import FileUploadZone from '@/components/common/FileUploadZone.vue'
import { api } from '@/api/index.js'

// State: 'list' | 'upload' | 'analyzing' | 'result'
const view = ref('list')
const resumes = ref([])
const selectedResume = ref(null)
const uploadedFile = ref(null)
const loading = ref(false)
const loadingText = ref('')
const error = ref(null)
const results = null // unused, kept for template compatibility

// Load resumes on mount
onMounted(async () => {
  await loadResumes()
})

async function loadResumes() {
  try {
    resumes.value = await api.getResumes()
    if (resumes.value.length === 0) {
      view.value = 'upload'
    }
  } catch (e) {
    error.value = e.message
  }
}

function goToUpload() {
  view.value = 'upload'
  uploadedFile.value = null
  error.value = null
}

function goToList() {
  view.value = 'list'
  selectedResume.value = null
  error.value = null
  loadResumes()
}

async function handleUpload() {
  if (!uploadedFile.value) return
  loading.value = true
  loadingText.value = '正在上传简历...'
  error.value = null
  try {
    await api.uploadResume(uploadedFile.value.raw)
    uploadedFile.value = null
    await loadResumes()
    view.value = 'list'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function analyzeResume(resume, force = false) {
  loading.value = true
  loadingText.value = '正在分析简历，Capy 在仔细阅读中...'
  error.value = null
  try {
    const data = await api.analyzeResume(resume.id, force)
    selectedResume.value = { ...resume, analysis_result: data }
    view.value = 'result'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function viewCachedResult(resume) {
  loading.value = true
  loadingText.value = '加载分析结果...'
  error.value = null
  try {
    const detail = await api.getResume(resume.id)
    selectedResume.value = detail
    view.value = 'result'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function deleteResume(resume) {
  try {
    await api.deleteResume(resume.id)
    await loadResumes()
  } catch (e) {
    error.value = e.message
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}
</script>

<template>
  <AnalysisLayout>
    <!-- Resume List View -->
    <div v-if="view === 'list'">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold">我的简历</h2>
          <p class="text-sm text-ink-muted mt-1">管理你的简历，上传后可进行分析和模拟面试</p>
        </div>
        <button class="btn btn--primary" @click="goToUpload">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M8 3v10M3 8h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          上传新简历
        </button>
      </div>

      <div v-if="error" class="mb-4 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400">
        {{ error }}
      </div>

      <!-- Resume cards -->
      <div class="space-y-4">
        <div
          v-for="resume in resumes"
          :key="resume.id"
          class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-5 flex items-center gap-4 transition-theme hover:shadow-subtle"
        >
          <!-- File icon -->
          <div class="w-12 h-12 rounded-lg bg-gradient-to-br from-[#fce4dc] to-[#f5d8cc] flex items-center justify-center shrink-0">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <rect x="4" y="3" width="14" height="16" rx="2" stroke="#E8937A" stroke-width="1.5"/>
              <line x1="7" y1="8" x2="15" y2="8" stroke="#E8937A" stroke-width="1" opacity="0.5"/>
              <line x1="7" y1="11" x2="12" y2="11" stroke="#E8937A" stroke-width="1" opacity="0.5"/>
            </svg>
          </div>

          <!-- Info -->
          <div class="flex-1 min-w-0">
            <div class="text-sm font-medium truncate">{{ resume.file_name }}</div>
            <div class="text-xs text-ink-muted mt-0.5">
              {{ resume.file_type?.toUpperCase() }} · {{ formatDate(resume.created_at) }}
              <span v-if="resume.has_analysis" class="ml-2 text-moss-green">已分析</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 shrink-0">
            <button
              v-if="resume.has_analysis"
              class="btn btn--ghost text-xs"
              @click="viewCachedResult(resume)"
            >查看结果</button>
            <button
              class="btn btn--secondary text-xs"
              @click="analyzeResume(resume, resume.has_analysis)"
            >{{ resume.has_analysis ? '重新分析' : '分析' }}</button>
            <button
              class="w-8 h-8 rounded-full flex items-center justify-center text-ink-muted hover:bg-red-500/10 hover:text-red-500 transition-theme"
              @click="deleteResume(resume)"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M3 4h8l-.7 8H3.7L3 4zM5 4V3a1 1 0 011-1h2a1 1 0 011 1v1M2 4h10" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Upload View -->
    <div v-if="view === 'upload'">
      <div class="flex items-center gap-3 mb-6">
        <button class="w-8 h-8 rounded-full flex items-center justify-center text-ink-muted hover:bg-surface-alt transition-theme" @click="goToList">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M11 4L6 9l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div>
          <h2 class="text-xl font-bold">上传简历</h2>
          <p class="text-sm text-ink-muted">支持 PDF、PNG、JPG 格式，最大 10MB</p>
        </div>
      </div>

      <div class="bg-white dark:bg-surface border-2 border-border-light dark:border-border rounded-2xl p-8 transition-theme focus-within:border-primary focus-within:shadow-glow">
        <FileUploadZone
          :file="uploadedFile"
          label="点击上传或拖拽简历文件"
          hint="支持 PDF、PNG、JPG 格式"
          :formats="['.pdf', '.png', '.jpg', '.jpeg']"
          accept=".pdf,.png,.jpg,.jpeg"
          @select="uploadedFile = $event"
          @remove="uploadedFile = null"
        />

        <div v-if="error" class="mt-3 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400">
          {{ error }}
        </div>

        <div class="flex items-center justify-between mt-5">
          <span class="text-xs text-ink-muted">上传后可进行简历分析和模拟面试</span>
          <button class="btn btn--primary" :disabled="!uploadedFile || loading" @click="handleUpload">
            上传并保存
          </button>
        </div>
      </div>
    </div>

    <!-- Analysis Result View -->
    <div v-if="view === 'result' && selectedResume">
      <div class="flex items-center gap-3 mb-6">
        <button class="w-8 h-8 rounded-full flex items-center justify-center text-ink-muted hover:bg-surface-alt transition-theme" @click="goToList">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none"><path d="M11 4L6 9l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div>
          <h2 class="text-xl font-bold">简历分析报告</h2>
          <p class="text-sm text-ink-muted">{{ selectedResume.file_name }}</p>
        </div>
      </div>

      <div v-if="error" class="mb-4 px-4 py-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400">
        {{ error }}
      </div>

      <div v-if="selectedResume.analysis_result" class="animate-fade-in">
        <!-- Strengths -->
        <SectionCard icon="check" title="优点">
          <div v-for="(s, i) in selectedResume.analysis_result.strengths" :key="i" class="mb-4 last:mb-0">
            <div class="text-sm font-medium text-ink">{{ s.text }}</div>
            <div class="text-sm text-ink-light mt-1">{{ s.detail }}</div>
          </div>
        </SectionCard>

        <!-- Weaknesses -->
        <SectionCard icon="info" title="待改进项" class="mt-4">
          <div v-for="(w, i) in selectedResume.analysis_result.weaknesses" :key="i" class="mb-4 last:mb-0">
            <div class="text-sm font-medium text-ink">{{ w.text }}</div>
            <div class="mt-1 px-3 py-2 bg-oat dark:bg-surface-alt rounded-lg text-sm text-ink-light">
              <span class="text-xs font-medium text-primary mr-1">建议：</span>{{ w.suggestion }}
            </div>
          </div>
        </SectionCard>

        <!-- Suggestions -->
        <SectionCard icon="plus" title="整体建议" class="mt-4">
          <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
            <li v-for="(s, i) in selectedResume.analysis_result.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
          </ul>
        </SectionCard>
      </div>
    </div>

    <LoadingOverlay
      :active="loading"
      :text="loadingText"
      subtext="请稍候..."
    />
  </AnalysisLayout>
</template>
