<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/index.js'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import TextMode from '@/components/interview/TextMode.vue'
import VoiceMode from '@/components/interview/VoiceMode.vue'
import { INTERVIEW_TYPES, PROFILE_TO_TYPE, TYPE_TO_PROFILE } from '@/data/interview.js'

const route = useRoute()
const router = useRouter()
const interviewId = route.params.id

const mode = ref('text')
const interviewStatus = ref('active')
const showExitDialog = ref(false)
const showResumeDialog = ref(false)
const exitOption = ref('save')
const textModeRef = ref(null)
const voiceModeRef = ref(null)

const interviewType = ref(route.query.type || 'technical')
const profileId = computed(() => TYPE_TO_PROFILE[interviewType.value] || 'interviewer-technical')
const sessionLoading = ref(true)
const sessionError = ref(null)

const summaryLoading = ref(false)

const formattedTime = ref('00:00')
let timer = null
let elapsed = 0

function startTimer() {
  timer = setInterval(() => {
    elapsed++
    const m = Math.floor(elapsed / 60)
    const s = elapsed % 60
    formattedTime.value = `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  }, 1000)
}

function stopTimer() {
  clearInterval(timer)
}

function handlePause() {
  interviewStatus.value = 'paused'
  stopTimer()
}

function handleResume() {
  showResumeDialog.value = true
}

function handleContinueInterview() {
  interviewStatus.value = 'active'
  showResumeDialog.value = false
  startTimer()
}

function handleRestartInterview() {
  if (mode.value === 'text' && textModeRef.value) {
    textModeRef.value.clearMessages()
  } else if (mode.value === 'voice' && voiceModeRef.value) {
    voiceModeRef.value.clearTranscript()
  }
  interviewStatus.value = 'active'
  showResumeDialog.value = false
  elapsed = 0
  formattedTime.value = '00:00'
  startTimer()
}

function handleEndInterview() {
  showExitDialog.value = true
}

function handleExitConfirm() {
  if (exitOption.value === 'save') {
    showExitDialog.value = false
    router.push('/interview')
  } else if (exitOption.value === 'summary') {
    handleGenerateSummary()
  } else {
    showExitDialog.value = false
    router.push('/interview')
  }
}

async function handleGenerateSummary() {
  summaryLoading.value = true
  showExitDialog.value = false
  stopTimer()

  try {
    await api.finalizeSession(interviewId)
    router.push(`/interview/${interviewId}/summary`)
  } catch (e) {
    console.error('Failed to generate summary:', e)
    alert('生成总结失败，请重试')
    startTimer()
  } finally {
    summaryLoading.value = false
  }
}

function switchMode(newMode) {
  mode.value = newMode
}

onMounted(async () => {
  // Validate session exists
  try {
    const session = await api.getSession(interviewId)
    if (session.status === 'completed' && session.summary) {
      router.replace(`/interview/${interviewId}/summary`)
      return
    }
    // Map profile_id back to interview type
    if (PROFILE_TO_TYPE[session.profile_id]) {
      interviewType.value = PROFILE_TO_TYPE[session.profile_id]
    }
  } catch (e) {
    sessionError.value = '面试会话不存在或已过期'
    console.error('Session not found:', e)
  } finally {
    sessionLoading.value = false
    if (!sessionError.value) {
      startTimer()
    }
  }
})

onUnmounted(() => {
  stopTimer()
})
</script>

<template>
  <div class="interview-page">
    <header class="interview-header">
      <div class="interview-header__left">
        <router-link to="/interview" class="back-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M12 4l-6 6 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </router-link>
        <div class="interview-header__title">
          <CapybaraLogo :size="24" />
          <span>{{ INTERVIEW_TYPES[interviewType] || '模拟面试' }}</span>
          <span v-if="mode === 'voice'" class="text-sm text-ink-muted">（语音模式）</span>
        </div>
      </div>

      <div class="interview-header__right">
        <button
          class="mode-toggle"
          @click="switchMode(mode === 'text' ? 'voice' : 'text')"
        >
          {{ mode === 'text' ? '切换语音' : '切换文字' }}
        </button>

        <button
          v-if="interviewStatus === 'active'"
          class="control-btn"
          @click="handlePause"
        >
          暂停
        </button>
        <button
          v-else-if="interviewStatus === 'paused'"
          class="control-btn"
          @click="handleResume"
        >
          继续
        </button>

        <button
          class="control-btn control-btn--danger"
          @click="handleEndInterview"
        >
          结束面试
        </button>
      </div>
    </header>

    <main class="interview-content">
      <div v-if="sessionLoading" class="flex items-center justify-center flex-1">
        <p class="text-ink-muted">加载中...</p>
      </div>

      <div v-else-if="sessionError" class="flex flex-col items-center justify-center flex-1 gap-4">
        <p class="text-ink-muted">{{ sessionError }}</p>
        <button class="btn btn--primary" @click="router.push('/interview')">返回列表</button>
      </div>

      <div v-else-if="summaryLoading" class="flex items-center justify-center flex-1">
        <p class="text-ink-muted">正在生成面试总结...</p>
      </div>

      <div v-else class="interview-mode-container">
        <TextMode
          v-if="mode === 'text'"
          ref="textModeRef"
          :session-id="interviewId"
          :interview-type="interviewType"
          :auto-start="true"
          :paused="interviewStatus === 'paused'"
        />

        <VoiceMode
          v-else
          ref="voiceModeRef"
          :session-id="interviewId"
          :profile-id="profileId"
          :auto-start="true"
          :paused="interviewStatus === 'paused'"
        />
      </div>
    </main>

    <div v-if="showExitDialog" class="dialog-overlay">
      <div class="dialog">
        <h3 class="dialog__title">确认退出？</h3>
        <p class="dialog__desc">你正在进行模拟面试，退出后进度会自动保存。</p>

        <div class="dialog__progress">
          <p class="text-sm text-ink-muted">当前进度：</p>
          <p class="text-sm text-ink">• 面试时长: {{ formattedTime }}</p>
        </div>

        <div class="dialog__options">
          <label class="dialog-option">
            <input type="radio" v-model="exitOption" value="save" />
            <span>保存进度，稍后继续</span>
          </label>
          <label class="dialog-option">
            <input type="radio" v-model="exitOption" value="summary" />
            <span>结束面试，生成总结</span>
          </label>
          <label class="dialog-option">
            <input type="radio" v-model="exitOption" value="exit" />
            <span>直接退出，不保存</span>
          </label>
        </div>

        <div class="dialog__actions">
          <button class="dialog-btn dialog-btn--secondary" @click="showExitDialog = false">取消</button>
          <button class="dialog-btn dialog-btn--primary" @click="handleExitConfirm">确认退出</button>
        </div>
      </div>
    </div>

    <div v-if="showResumeDialog" class="dialog-overlay">
      <div class="dialog">
        <h3 class="dialog__title">继续面试</h3>

        <div class="dialog__progress">
          <p class="text-sm text-ink-muted">上次进度：</p>
          <p class="text-sm text-ink">• 面试时长: {{ formattedTime }}</p>
        </div>

        <div class="dialog__actions">
          <button class="dialog-btn dialog-btn--secondary" @click="handleRestartInterview">重新开始</button>
          <button class="dialog-btn dialog-btn--primary" @click="handleContinueInterview">继续面试</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.interview-page {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--color-base);
}

.interview-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-4) var(--space-6);
  background: rgba(255, 252, 247, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border-light);
  height: var(--nav-height);
}

.interview-header__left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  color: var(--color-ink-light);
  transition: all var(--duration-fast) var(--ease-out);
}

.back-btn:hover {
  background: var(--color-surface);
  color: var(--color-primary);
}

.interview-header__title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--color-ink);
}

.interview-header__right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.mode-toggle {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-ink-muted);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-out);
}

.mode-toggle:hover {
  background: var(--color-surface);
  color: var(--color-ink);
}

.control-btn {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-ink-muted);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  transition: all var(--duration-fast) var(--ease-out);
}

.control-btn:hover {
  background: var(--color-surface);
  color: var(--color-ink);
}

.control-btn--danger {
  color: #EF4444;
  border-color: #EF4444;
}

.control-btn--danger:hover {
  background: #FEF2F2;
}

.interview-content {
  height: 100vh;
  padding-top: var(--nav-height);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.interview-mode-container {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.dialog {
  background: var(--color-white);
  border-radius: var(--radius-2xl);
  padding: var(--space-8);
  max-width: 480px;
  width: 90%;
  box-shadow: var(--shadow-xl);
  animation: dialogIn 0.3s var(--ease-out) both;
}

@keyframes dialogIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.dialog__title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-ink);
  margin-bottom: var(--space-4);
}

.dialog__desc {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  margin-bottom: var(--space-6);
}

.dialog__progress {
  padding: var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-6);
}

.dialog__options {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.dialog-option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1.5px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.dialog-option:hover {
  border-color: var(--color-primary-light);
}

.dialog-option input[type="radio"] {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
}

.dialog__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.dialog-btn {
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-lg);
  transition: all var(--duration-fast) var(--ease-out);
}

.dialog-btn--secondary {
  color: var(--color-ink-muted);
  border: 1px solid var(--color-border-light);
}

.dialog-btn--secondary:hover {
  background: var(--color-surface);
  color: var(--color-ink);
}

.dialog-btn--primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.dialog-btn--primary:hover {
  background: var(--color-primary-dark);
}

:global(.dark) .interview-header {
  background: var(--color-surface);
}

:global(.dark) .dialog {
  background: var(--color-surface);
}

@media (max-width: 768px) {
  .interview-header {
    padding: var(--space-3) var(--space-4);
  }

  .interview-header__right {
    gap: var(--space-1);
  }

  .mode-toggle,
  .control-btn {
    padding: var(--space-1) var(--space-3);
    font-size: var(--text-xs);
  }
}
</style>
