<script setup>
import { ref, computed, onUnmounted, nextTick } from 'vue'
import { api } from '@/api/index.js'
import { interviewQuestions } from '@/api/mock.js'

const props = defineProps({
  interviewType: { type: String, default: 'technical' },
})

const voiceRunning = ref(false)
const isMuted = ref(false)
const isListening = ref(false)
const elapsed = ref(0)
const supported = ref(true)
const statusText = ref('等待开始')
const hintText = ref('选择面试类型后点击开始')
const avatarSpeaking = ref(false)
const transcriptEntries = ref([])
const liveText = ref('')
const liveIsFinal = ref(false)
const waveformActive = ref(false)

let recognition = null
let timer = null
let questionIndex = 0
let conversationHistory = []

const SpeechRecognition = typeof window !== 'undefined'
  ? window.SpeechRecognition || window.webkitSpeechRecognition
  : null

if (!SpeechRecognition) {
  supported.value = false
  hintText.value = '当前浏览器不支持语音识别，请使用 Chrome'
}

const voiceTypeNames = { technical: '技术面试', behavioral: '行为面试', hr: 'HR 面试' }
const voiceTypes = ['technical', 'behavioral', 'hr']
let voiceTypeIndex = 0
const currentVoiceType = ref(props.interviewType)

const formattedTime = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

function addTranscript(label, text) {
  transcriptEntries.value.push({ label, text })
  nextTick(() => {
    const el = document.querySelector('.voice-transcript')
    if (el) el.scrollTop = el.scrollHeight
  })
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

  // Show initial AI question
  const firstQ = getFirstQuestion()
  avatarSpeaking.value = true
  hintText.value = 'AI 面试官正在提问...'
  setTimeout(() => {
    addTranscript('AI 面试官', firstQ)
    conversationHistory.push({ role: 'assistant', content: firstQ })
    avatarSpeaking.value = false
    hintText.value = '请回答...'
    startListening()
  }, 1200)
}

function getFirstQuestion() {
  const qs = interviewQuestions[currentVoiceType.value] || interviewQuestions.technical
  return qs[0]
}

function getNextAIResponse() {
  const qs = interviewQuestions[currentVoiceType.value] || interviewQuestions.technical
  questionIndex = (questionIndex + 1) % qs.length
  return qs[questionIndex]
}

function startListening() {
  if (!SpeechRecognition || !voiceRunning.value || isMuted.value) return

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
        // Add user message to transcript
        addTranscript('你', finalTranscript.trim())
        conversationHistory.push({ role: 'user', content: finalTranscript.trim() })
        liveText.value = ''

        // AI thinks then responds
        hintText.value = 'AI 面试官正在思考...'
        avatarSpeaking.value = true

        setTimeout(() => {
          const aiResponse = getNextAIResponse()
          addTranscript('AI 面试官', aiResponse)
          conversationHistory.push({ role: 'assistant', content: aiResponse })
          avatarSpeaking.value = false
          hintText.value = '请回答...'

          // Continue listening
          if (voiceRunning.value && !isMuted.value) {
            setTimeout(() => startListening(), 500)
          }
        }, 1500)
      } else if (voiceRunning.value && !isMuted.value) {
        setTimeout(() => startListening(), 300)
      }
    }

    recognition.onerror = (event) => {
      isListening.value = false
      waveformActive.value = false

      if (event.error === 'not-allowed') {
        hintText.value = '请允许麦克风权限后重试'
      } else if (event.error === 'no-speech') {
        hintText.value = '未检测到语音，请再试一次'
        if (voiceRunning.value && !isMuted.value) {
          setTimeout(() => startListening(), 1000)
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
    if (voiceRunning.value) {
      hintText.value = '取消静音，正在监听...'
      startListening()
    }
  }
}

function cycleVoiceType() {
  voiceTypeIndex = (voiceTypeIndex + 1) % voiceTypes.length
  currentVoiceType.value = voiceTypes[voiceTypeIndex]
  hintText.value = `当前类型：${voiceTypeNames[currentVoiceType.value]}`
}

function toggleVoice() {
  if (!voiceRunning.value) {
    startVoice()
  } else {
    stopVoice()
  }
}

onUnmounted(() => {
  clearInterval(timer)
  if (recognition) {
    try { recognition.abort() } catch {}
  }
})
</script>

<template>
  <div class="voice-page">
    <div class="voice-container">
      <!-- Status badge -->
      <div class="voice-status" :class="voiceRunning ? 'active' : ''">
        <span class="voice-status__dot"></span>
        <span>{{ statusText }}</span>
      </div>

      <!-- Avatar -->
      <div class="voice-avatar" :class="avatarSpeaking ? 'speaking' : ''">
        <div class="voice-avatar__ring"></div>
        <div class="voice-avatar__ring voice-avatar__ring--2"></div>
        <div class="voice-avatar__face">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <path d="M32 8 C16 8, 8 18, 8 32 C8 46, 16 56, 32 56 C48 56, 56 46, 56 32 C56 18, 48 8, 32 8 Z" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M18 14 C16 6, 22 4, 24 10" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <path d="M40 10 C38 2, 44 0, 46 8" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
            <circle cx="24" cy="28" r="3" fill="var(--color-primary)"/>
            <circle cx="40" cy="28" r="3" fill="var(--color-primary)"/>
            <path d="M32 34 L32 42" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M26 42 Q32 50 38 42" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
          </svg>
        </div>
      </div>

      <!-- Name & hint -->
      <h2 class="voice-name" style="font-family: var(--font-heading)">AI 面试官</h2>
      <p class="voice-hint">{{ hintText }}</p>

      <!-- Waveform -->
      <div class="voice-waveform" :class="waveformActive ? 'active' : ''">
        <span v-for="n in 20" :key="n"></span>
      </div>

      <!-- Transcript area -->
      <div class="voice-transcript">
        <template v-if="transcriptEntries.length || liveText">
          <div
            v-for="(entry, i) in transcriptEntries"
            :key="i"
            class="voice-transcript__entry"
          >
            <span class="transcript-label">{{ entry.label }}</span>
            <p>{{ entry.text }}</p>
          </div>
          <!-- Live speech recognition -->
          <div v-if="liveText" class="voice-transcript__live">
            <span class="transcript-label">你（识别中...）</span>
            <p :style="{ opacity: liveIsFinal ? 0.5 : 1 }">{{ liveText }}</p>
          </div>
        </template>
        <p v-else class="voice-transcript__placeholder">对话记录将显示在这里...</p>
      </div>

      <!-- Controls -->
      <div class="voice-controls">
        <!-- Type switcher (left) -->
        <button
          class="voice-ctrl voice-ctrl--secondary"
          :title="'当前: ' + voiceTypeNames[currentVoiceType]"
          @click="cycleVoiceType"
        >
          <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
            <rect x="3" y="3" width="7" height="7" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <rect x="12" y="3" width="7" height="7" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <rect x="3" y="12" width="7" height="7" rx="2" stroke="currentColor" stroke-width="1.5"/>
            <rect x="12" y="12" width="7" height="7" rx="2" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>

        <!-- Primary start/stop (center) -->
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

        <!-- Mute (right) -->
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

      <!-- Timer -->
      <div class="voice-timer">{{ formattedTime }}</div>
    </div>
  </div>
</template>

<style scoped>
.voice-page {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100vh;
  padding-top: var(--nav-height);
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

/* Status badge */
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

/* Avatar */
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

/* Waveform */
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

/* Transcript */
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

/* Controls */
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

/* Timer */
.voice-timer {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  letter-spacing: 0.05em;
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
