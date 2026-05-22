<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import InterviewCard from '@/components/interview/InterviewCard.vue'
import InterviewConfigModal from '@/components/interview/InterviewConfigModal.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

const router = useRouter()
const loading = ref(false)
const interviews = ref([])
const filterType = ref('all')
const filterStatus = ref('all')
const sortBy = ref('date')
const showConfigModal = ref(false)

// Mock data for development
const mockInterviews = [
  {
    id: 1,
    type: 'comprehensive',
    resume: '前端工程师_简历.pdf',
    projects: ['job-seeker-assistant'],
    duration: 15,
    status: 'completed',
    date: '2026-05-23',
    summary: {
      highlights: ['Vue组件化组织清晰', '对状态管理的理解准确'],
      improvements: ['性能优化回答可更具体', '建议深入学习Vue3响应式原理']
    }
  },
  {
    id: 2,
    type: 'technical',
    resume: '前端工程师_简历.pdf',
    projects: ['my-portfolio'],
    duration: 22,
    status: 'paused',
    date: '2026-05-22',
    progress: {
      answered: 3,
      totalQuestions: 8
    }
  },
  {
    id: 3,
    type: 'behavioral',
    resume: '我的简历_v2.pdf',
    projects: [],
    duration: 10,
    status: 'completed',
    date: '2026-05-21',
    summary: {
      highlights: ['回答有条理', '团队协作经验丰富'],
      improvements: ['可以更多举例说明', '表达可以更简洁']
    }
  }
]

const filteredInterviews = computed(() => {
  let result = [...interviews.value]

  // Filter by type
  if (filterType.value !== 'all') {
    result = result.filter(i => i.type === filterType.value)
  }

  // Filter by status
  if (filterStatus.value !== 'all') {
    result = result.filter(i => i.status === filterStatus.value)
  }

  // Sort
  if (sortBy.value === 'date') {
    result.sort((a, b) => new Date(b.date) - new Date(a.date))
  } else if (sortBy.value === 'duration') {
    result.sort((a, b) => b.duration - a.duration)
  }

  return result
})

onMounted(() => {
  // TODO: Replace with actual API call
  interviews.value = mockInterviews
})

function handleViewSummary(id) {
  router.push(`/interview/${id}`)
}

function handleContinueInterview(id) {
  router.push(`/interview/${id}`)
}

function handleStartNew() {
  showConfigModal.value = true
}

function handleCloseModal() {
  showConfigModal.value = false
}
</script>

<template>
  <AnalysisLayout>
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-bold text-ink">模拟面试</h2>
      <p class="text-sm text-ink-muted mt-1">
        {{ interviews.length > 0 ? `你已完成 ${interviews.length} 场模拟面试，继续加油！` : '开始你的第一场模拟面试' }}
      </p>
    </div>

    <!-- Filters and Sort -->
    <div v-if="interviews.length > 0" class="flex flex-wrap items-center gap-4 mb-6">
      <div class="flex items-center gap-2">
        <label class="text-sm text-ink-muted">筛选:</label>
        <select
          v-model="filterType"
          class="px-3 py-2 bg-surface dark:bg-surface-alt border border-border-light dark:border-border rounded-lg text-sm text-ink outline-none focus:border-primary transition-theme"
        >
          <option value="all">全部类型</option>
          <option value="technical">技术面试</option>
          <option value="behavioral">行为面试</option>
          <option value="comprehensive">综合面试</option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <label class="text-sm text-ink-muted">状态:</label>
        <select
          v-model="filterStatus"
          class="px-3 py-2 bg-surface dark:bg-surface-alt border border-border-light dark:border-border rounded-lg text-sm text-ink outline-none focus:border-primary transition-theme"
        >
          <option value="all">全部状态</option>
          <option value="completed">已完成</option>
          <option value="paused">已暂停</option>
        </select>
      </div>

      <div class="flex items-center gap-2">
        <label class="text-sm text-ink-muted">排序:</label>
        <select
          v-model="sortBy"
          class="px-3 py-2 bg-surface dark:bg-surface-alt border border-border-light dark:border-border rounded-lg text-sm text-ink outline-none focus:border-primary transition-theme"
        >
          <option value="date">最近日期</option>
          <option value="duration">面试时长</option>
        </select>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="interviews.length === 0 && !loading" class="text-center py-12">
      <div class="w-20 h-20 mx-auto mb-4 rounded-full bg-surface flex items-center justify-center">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" class="text-ink-muted">
          <rect x="8" y="6" width="24" height="28" rx="3" stroke="currentColor" stroke-width="2"/>
          <circle cx="20" cy="16" r="4" stroke="currentColor" stroke-width="1.5"/>
          <path d="M12 28c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
      </div>
      <h3 class="text-lg font-semibold text-ink mb-2">还没有面试记录</h3>
      <p class="text-sm text-ink-muted mb-6">上传简历并分析GitHub仓库后即可开始面试</p>
      <button
        class="btn btn--primary"
        @click="handleStartNew"
      >
        开始配置 →
      </button>
    </div>

    <!-- Interview Grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <InterviewCard
        v-for="interview in filteredInterviews"
        :key="interview.id"
        :interview="interview"
        @view-summary="handleViewSummary"
        @continue="handleContinueInterview"
      />
    </div>

    <!-- Add New Interview Card -->
    <div v-if="interviews.length > 0" class="mt-4">
      <div
        class="bg-white dark:bg-surface border-2 border-dashed border-border-light dark:border-border rounded-xl p-6 text-center cursor-pointer hover:border-primary hover:bg-primary/5 transition-all"
        @click="handleStartNew"
      >
        <div class="w-12 h-12 mx-auto mb-3 rounded-full bg-surface flex items-center justify-center">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" class="text-primary">
            <path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3 class="font-semibold text-ink mb-1">开始新面试</h3>
        <p class="text-sm text-ink-muted">上传简历并分析GitHub仓库后即可开始面试</p>
      </div>
    </div>

    <!-- Config Modal -->
    <InterviewConfigModal
      :show="showConfigModal"
      @close="handleCloseModal"
    />

    <LoadingOverlay
      :active="loading"
      text="正在加载"
      subtext="Capy 正在获取面试记录..."
    />
  </AnalysisLayout>
</template>
