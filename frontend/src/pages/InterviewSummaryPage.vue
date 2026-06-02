<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/index.js'
import { eventsToMessages } from '@/utils/interviewHelpers.js'
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import InterviewSummary from '@/components/interview/InterviewSummary.vue'

const route = useRoute()
const router = useRouter()
const sessionId = route.params.id

const summary = ref(null)
const messages = ref([])
const loading = ref(true)
const error = ref(null)
const regenerating = ref(false)

function isFallbackSummary(data) {
  return (
    data?.overview === '面试已完成'
    && Array.isArray(data?.highlights)
    && data.highlights.length === 0
    && data?.suggestions?.length === 1
    && data.suggestions[0] === '继续练习以提升面试表现'
  )
}

async function loadSession() {
  loading.value = true
  error.value = null
  try {
    const [session, eventsResponse] = await Promise.all([
      api.getSession(sessionId),
      api.getSessionEvents(sessionId),
    ])

    if (session.summary) {
      summary.value = session.summary
    } else {
      error.value = '该面试还没有生成总结'
      return
    }

    messages.value = eventsToMessages(eventsResponse.events || [])
  } catch (e) {
    console.error('Failed to load session:', e)
    error.value = '面试会话不存在或已过期'
  } finally {
    loading.value = false
  }
}

async function handleRegenerateSummary() {
  regenerating.value = true
  try {
    const result = await api.finalizeSession(sessionId)
    summary.value = result.summary
  } catch (e) {
    console.error('Failed to regenerate summary:', e)
    alert('重新生成总结失败，请稍后重试')
  } finally {
    regenerating.value = false
  }
}

onMounted(loadSession)

function handleDownloadSummary() {
  alert('下载功能待实现')
}

function handleBackToList() {
  router.push('/interview')
}
</script>

<template>
  <AnalysisLayout>
    <div v-if="loading" class="flex items-center justify-center py-20">
      <p class="text-ink-muted">加载中...</p>
    </div>

    <div v-else-if="error" class="flex flex-col items-center justify-center py-20 gap-4">
      <p class="text-ink-muted">{{ error }}</p>
      <button class="btn btn--primary" @click="handleBackToList">返回列表</button>
    </div>

    <InterviewSummary
      v-else
      :summary="summary"
      :messages="messages"
      @download="handleDownloadSummary"
      @back-to-list="handleBackToList"
    />

    <div
      v-if="!loading && !error && isFallbackSummary(summary)"
      class="flex justify-center mt-4"
    >
      <button
        class="btn btn--primary px-5 py-2 text-sm"
        :disabled="regenerating"
        @click="handleRegenerateSummary"
      >
        {{ regenerating ? '正在重新生成...' : '重新生成总结' }}
      </button>
    </div>
  </AnalysisLayout>
</template>
