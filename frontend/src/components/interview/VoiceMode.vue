<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { interviewQuestions } from '@/data/interviewQuestions.js'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import { INTERVIEW_TYPES } from '@/constants/interview.js'

const props = defineProps({
  interviewType: { type: String, default: 'technical' },
  autoStart: { type: Boolean, default: false },
  paused: { type: Boolean, default: false }
})

const emit = defineEmits(['update:transcript', 'voice-started', 'voice-stopped'])

const voiceRunning = ref(false)
const isMuted = ref(false)
const isListening = ref(false)
const elapsed = ref(0)
const supported = typeof window !== 'undefined'
  ? !!(window.SpeechRecognition || window.webkitSpeechRecognition)
  : false
const statusText = ref('等待开始')
const hintText = ref(supported ? '选择面试类型后点击开始' : '当前浏览器不支持语音识别，请使用 Chrome')
const avatarSpeaking = ref(false)
const transcriptEntries = ref([])
const liveText = ref('')
const liveIsFinal = ref(false)
const waveformActive = ref(false)
const transcriptContainer = ref(null)

let recognition = null
let timer = null
let questionIndex = 0
let conversationHistory = []
let pendingTimeouts = []

const SpeechRecognition = typeof window !== 'undefined'
  ? window.SpeechRecognition || window.webkitSpeechRecognition
  : null

const formattedTime = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

function addTimeout(fn, delay) {
  const id = setTimeout(() => {
    pendingTimeouts = pendingTimeouts.filter(t => t !== id)
    fn()
  }, delay)
  pendingTimeouts.push(id)
  return id
}

function clearAllTimeouts() {
  pendingTimeouts.forEach(id => clearTimeout(id))
  pendingTimeouts = []
}

function addTranscript(label, text) {
  transcriptEntries.value.push({ label, text })
  nextTick(() => {
    if (transcriptContainer.value) {
      transcriptContainer.value.scrollTop = transcriptContainer.value.scrollHeight
    }
  })
  emit('update:transcript', transcriptEntries.value)
}

function startVoice() {
  if (!SpeechRecognition) return

  voiceRunning.value = true
  isMuted.value = false
  isListening.value = false
  elapsed.value = 0
  questionIndex = 0
  conversationHistory = []
  transcriptEntries.value = []
  liveText.value = ''
  statusText.value = '面试进行中'

  timer = setInterval(() => elapsed.value++, 1000)

  const firstQ = getFirstQuestion()
  avatarSpeaking.value = true
  hintText.value = 'Capy正在提问...'
  addTimeout(() => {
    addTranscript('Capy', firstQ)
    conversationHistory.push({ role: 'assistant', content: firstQ })
    avatarSpeaking.value = false
    hintText.value = '请回答...'
    startListening()
  }, 1200)

  emit('voice-started')
}

function getFirstQuestion() {
  const qs = interviewQuestions[props.interviewType] || interviewQuestions.technical
  return qs[0]
}

function getNextAIResponse() {
  const qs = interviewQuestions[props.interviewType] || interviewQuestions.technical
  questionIndex = (questionIndex + 1) % qs.length
  return qs[questionIndex]
}

function startListening() {
  if (!SpeechRecognition || !voiceRunning.value || isMuted.value || props.paused) return

  try {
    recognition = new SpeechRecognition()
    recognition.continuous = false
    recognition.interimResults = true
    recognition.lang = 'zh-CN'

    let finalTranscript = ''

    recognition.onstart = () => {
      isListening.value = true
      waveformActive.value = true
      hintText.value = '请说话...'
    }

    recognition.onresult = (event) => {
      let interim = ''
      finalTranscript = ''
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const t = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += t
        } else {
          interim += t
        }
      }
      const displayText = finalTranscript || interim
      if (displayText) {
        liveText.value = displayText
        liveIsFinal.value = !!finalTranscript
      }
    }

    recognition.onend = () => {
      isListening.value = false
      waveformActive.value = false

      if (finalTranscript.trim() && voiceRunning.value) {
        addTranscript('你', finalTranscript.trim())
        conversationHistory.push({ role: 'user', content: finalTranscript.trim() })
        liveText.value = ''

        hintText.value = 'Capy正在思考...'
        avatarSpeaking.value = true

        addTimeout(() => {
          const aiResponse = getNextAIResponse()
          addTranscript('Capy', aiResponse)
          conversationHistory.push({ role: 'assistant', content: aiResponse })
          avatarSpeaking.value = false
          hintText.value = '请回答...'

          if (voiceRunning.value && !isMuted.value && !props.paused) {
            addTimeout(() => startListening(), 500)
          }
        }, 1500)
      } else if (voiceRunning.value && !isMuted.value && !props.paused) {
        addTimeout(() => startListening(), 300)
      }
    }

    recognition.onerror = (event) => {
      isListening.value = false
      waveformActive.value = false

      const errorMessages = {
        'not-allowed': '请允许麦克风权限后重试',
        'no-speech': '未检测到语音，请再试一次',
      }

      if (errorMessages[event.error]) {
        hintText.value = errorMessages[event.error]
        if (event.error === 'no-speech' && voiceRunning.value && !isMuted.value && !props.paused) {
          addTimeout(() => startListening(), 1000)
        }
      } else if (event.error !== 'aborted') {
        hintText.value = `识别出错: ${event.error}`
      }
    }

    recognition.start()
  } catch (e) {
    // Already started
  }
}

function stopVoice() {
  voiceRunning.value = false
  statusText.value = '面试已结束'
  hintText.value = `面试时长 ${formattedTime.value}`
  avatarSpeaking.value = false
  waveformActive.value = false
  isListening.value = false

  clearInterval(timer)

  if (recognition) {
    try { recognition.abort() } catch {}
    recognition = null
  }

  emit('voice-stopped', transcriptEntries.value)
}

function toggleMute() {
  isMuted.value = !isMuted.value
  if (isMuted.value) {
    if (recognition) {
      try { recognition.abort() } catch {}
      recognition = null
    }
    isListening.value = false
    waveformActive.value = false
    avatarSpeaking.value = false
    hintText.value = '已静音'
  } else {
    if (voiceRunning.value && !props.paused) {
      hintText.value = '取消静音，正在监听...'
      startListening()
    }
  }
}

function toggleVoice() {
  if (!voiceRunning.value) {
    startVoice()
  } else {
    stopVoice()
  }
}

function getTranscript() {
  return transcriptEntries.value
}

function clearTranscript() {
  transcriptEntries.value = []
  emit('update:transcript', transcriptEntries.value)
}

defineExpose({ getTranscript, clearTranscript })

watch(() => props.paused, (paused) => {
  if (paused && voiceRunning.value) {
    if (recognition) {
      try { recognition.abort() } catch {}
      recognition = null
    }
    isListening.value = false
    waveformActive.value = false
    avatarSpeaking.value = false
    hintText.value = '面试已暂停'
  } else if (!paused && voiceRunning.value) {
    hintText.value = '请回答...'
    startListening()
  }
})

onMounted(() => {
  if (props.autoStart) {
    startVoice()
  }
})

onUnmounted(() => {
  clearAllTimeouts()
  clearInterval(timer)
  if (recognition) {
    try { recognition.abort() } catch {}
  }
})
</script>

<template>
  <div class="voice-page">
    <div class="voice-container">
      <div class="voice-status" :class="voiceRunning ? 'active' : ''">
        <span class="voice-status__dot"></span>
        <span>{{ statusText }}</span>
      </div>

      <div class="voice-avatar" :class="avatarSpeaking ? 'speaking' : ''">
        <div class="voice-avatar__ring"></div>
        <div class="voice-avatar__ring voice-avatar__ring--2"></div>
        <div class="voice-avatar__face">
          <CapybaraLogo :size="64" :stroke-width="2.5" />
        </div>
      </div>

      <h2 class="voice-name" style="font-family: var(--font-heading)">Capy</h2>
      <p class="voice-hint">{{ hintText }}</p>

      <div class="voice-waveform" :class="waveformActive ? 'active' : ''">
        <span v-for="n in 20" :key="n"></span>
      </div>

      <div ref="transcriptContainer" class="voice-transcript">
        <template v-if="transcriptEntries.length || liveText">
          <div
            v-for="(entry, i) in transcriptEntries"
            :key="i"
            class="voice-transcript__entry"
            :class="entry.label === '你' ? 'voice-transcript__entry--user' : 'voice-transcript__entry--ai'"
          >
            <span class="transcript-label">{{ entry.label }}</span>
            <p>{{ entry.text }}</p>
          </div>
          <div v-if="liveText" class="voice-transcript__live voice-transcript__entry--user">
            <span class="transcript-label">你（识别中...）</span>
            <p :style="{ opacity: liveIsFinal ? 0.5 : 1 }">{{ liveText }}</p>
          </div>
        </template>
        <p v-else class="voice-transcript__placeholder">对话记录将显示在这里...</p>
      </div>

      <div class="voice-controls">
        <button
          v-if="!voiceRunning"
          class="voice-ctrl voice-ctrl--primary"
          :class="{ 'opacity-50 cursor-not-allowed': !supported }"
          :disabled="!supported"
          @click="toggleVoice"
        >
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="10" y="4" width="8" height="13" rx="4" stroke="currentColor" stroke-width="2"/>
            <path d="M6 15c0 5 3.6 8 8 8s8-3 8-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
            <line x1="14" y1="23" x2="14" y2="26" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
        <button
          v-else
          class="voice-ctrl voice-ctrl--primary recording"
          @click="toggleVoice"
        >
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="8" y="8" width="12" height="12" rx="2" fill="currentColor"/>
          </svg>
        </button>

        <button
          class="voice-ctrl voice-ctrl--secondary"
          :class="isMuted ? 'muted' : ''"
          @click="toggleMute"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="8" y="3" width="6" height="10" rx="3" stroke="currentColor" stroke-width="1.5"/>
            <path d="M5 11c0 4 2.7 6 6 6s6-2 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/>
            <line x1="11" y1="17" x2="11" y2="20" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="voice-timer">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<style scoped>
.voice-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  padding: var(--space-8);
}

.voice-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-6);
  padding: var(--space-8);
  animation: welcomeFadeIn 0.5s var(--ease-out) both;
  width: 100%;
  max-width: 560px;
}

@keyframes welcomeFadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.voice-status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  color: var(--color-ink-muted);
}

.voice-status__dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-ink-muted);
}

.voice-status.active .voice-status__dot {
  background: #4ADE80;
  animation: pulse 1.5s ease-in-out infinite;
}

.voice-status.active {
  color: var(--color-ink-light);
  border-color: rgba(74, 222, 128, 0.3);
  background: rgba(74, 222, 128, 0.08);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.voice-avatar {
  position: relative;
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.voice-avatar__ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1.5px solid var(--color-primary-light);
  opacity: 0;
}

.voice-avatar.speaking .voice-avatar__ring {
  animation: avatarRing 2s ease-out infinite;
}

.voice-avatar.speaking .voice-avatar__ring--2 {
  animation-delay: 0.6s;
}

@keyframes avatarRing {
  0% { transform: scale(0.85); opacity: 0.5; }
  100% { transform: scale(1.4); opacity: 0; }
}

.voice-avatar__face {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: var(--color-surface);
  border: 2px solid var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-normal) var(--ease-out);
}

.voice-avatar.speaking .voice-avatar__face {
  border-color: var(--color-primary-light);
  box-shadow: 0 0 0 4px rgba(196, 149, 106, 0.1);
}

.voice-name {
  font-size: var(--text-xl);
  font-weight: 700;
}

.voice-hint {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

.voice-waveform {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 48px;
  opacity: 0;
  transition: opacity var(--duration-normal) var(--ease-out);
}

.voice-waveform.active {
  opacity: 1;
}

.voice-waveform span {
  width: 3px;
  height: 8px;
  background: var(--color-primary);
  border-radius: 2px;
  transition: height 0.15s ease;
}

.voice-waveform.active span {
  animation: voiceWave 0.8s ease-in-out infinite alternate;
}

.voice-waveform.active span:nth-child(1)  { animation-delay: 0.00s; }
.voice-waveform.active span:nth-child(2)  { animation-delay: 0.05s; }
.voice-waveform.active span:nth-child(3)  { animation-delay: 0.10s; }
.voice-waveform.active span:nth-child(4)  { animation-delay: 0.15s; }
.voice-waveform.active span:nth-child(5)  { animation-delay: 0.20s; }
.voice-waveform.active span:nth-child(6)  { animation-delay: 0.25s; }
.voice-waveform.active span:nth-child(7)  { animation-delay: 0.30s; }
.voice-waveform.active span:nth-child(8)  { animation-delay: 0.35s; }
.voice-waveform.active span:nth-child(9)  { animation-delay: 0.40s; }
.voice-waveform.active span:nth-child(10) { animation-delay: 0.45s; }
.voice-waveform.active span:nth-child(11) { animation-delay: 0.05s; }
.voice-waveform.active span:nth-child(12) { animation-delay: 0.10s; }
.voice-waveform.active span:nth-child(13) { animation-delay: 0.15s; }
.voice-waveform.active span:nth-child(14) { animation-delay: 0.20s; }
.voice-waveform.active span:nth-child(15) { animation-delay: 0.25s; }
.voice-waveform.active span:nth-child(16) { animation-delay: 0.30s; }
.voice-waveform.active span:nth-child(17) { animation-delay: 0.35s; }
.voice-waveform.active span:nth-child(18) { animation-delay: 0.40s; }
.voice-waveform.active span:nth-child(19) { animation-delay: 0.45s; }
.voice-waveform.active span:nth-child(20) { animation-delay: 0.00s; }

@keyframes voiceWave {
  0% { height: 6px; }
  100% { height: 36px; }
}

.voice-transcript {
  width: 100%;
  max-width: 480px;
  max-height: 200px;
  overflow-y: auto;
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-ink-light);
}

.voice-transcript::-webkit-scrollbar {
  width: 3px;
}

.voice-transcript::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}

.voice-transcript__placeholder {
  text-align: center;
  color: var(--color-ink-muted);
  font-style: italic;
}

.voice-transcript__entry {
  margin-bottom: var(--space-3);
}

.voice-transcript__entry p {
  margin: 0;
}

.voice-transcript__entry--ai {
  text-align: left;
}

.voice-transcript__entry--user {
  text-align: right;
}

.voice-transcript__entry--user .transcript-label {
  color: var(--color-ink-muted);
}

.transcript-label {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-primary);
  margin-bottom: 2px;
  display: block;
}

.voice-transcript__live {
  padding: var(--space-2) var(--space-3);
  background: rgba(196, 149, 106, 0.08);
  border-radius: var(--radius-md);
  border-left: 2px solid var(--color-primary);
  transition: opacity 0.3s ease;
}

.voice-transcript__live p {
  margin: 0;
}

.voice-controls {
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.voice-ctrl {
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration-normal) var(--ease-out);
  cursor: pointer;
}

.voice-ctrl--primary {
  width: 72px;
  height: 72px;
  background: var(--color-primary);
  color: var(--color-white);
}

.voice-ctrl--primary:hover {
  background: var(--color-primary-dark);
  transform: scale(1.06);
}

.voice-ctrl--primary:active {
  transform: scale(0.95);
}

.voice-ctrl--primary.recording {
  background: #EF4444;
  animation: recordPulse 1.5s ease-in-out infinite;
}

@keyframes recordPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.3); }
  50% { box-shadow: 0 0 0 12px rgba(239, 68, 68, 0); }
}

.voice-ctrl--secondary {
  width: 48px;
  height: 48px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  color: var(--color-ink-light);
}

.voice-ctrl--secondary:hover {
  background: var(--color-surface-alt);
  color: var(--color-primary);
  transform: scale(1.06);
}

.voice-ctrl--secondary.muted {
  color: #EF4444;
  border-color: #EF4444;
}

.voice-timer {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  letter-spacing: 0.05em;
}

:global(.dark) .voice-avatar__face {
  background: var(--color-surface);
  border-color: var(--color-border);
}

@media (max-width: 768px) {
  .voice-controls {
    gap: var(--space-4);
  }

  .voice-ctrl--primary {
    width: 64px;
    height: 64px;
  }

  .voice-ctrl--secondary {
    width: 44px;
    height: 44px;
  }
}
</style>
