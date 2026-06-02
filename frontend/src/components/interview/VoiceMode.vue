<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import { useVoiceInterview } from '@/composables/useVoiceInterview.js'
import { isVoiceSupported } from '@/utils/voiceAudio.js'

const props = defineProps({
  sessionId: { type: String, required: true },
  profileId: { type: String, required: true },
  autoStart: { type: Boolean, default: false },
  paused: { type: Boolean, default: false },
})

const emit = defineEmits(['update:transcript', 'voice-started', 'voice-stopped'])

const supported = isVoiceSupported()
const voiceRunning = ref(false)
const isMuted = ref(false)
const elapsed = ref(0)
const statusText = ref('等待开始')
const transcriptContainer = ref(null)

let timer = null

const voice = useVoiceInterview({
  sessionId: props.sessionId,
  profileId: props.profileId,
})

const formattedTime = computed(() => {
  const m = Math.floor(elapsed.value / 60)
  const s = elapsed.value % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

/** 仅展示会话中最新一条对话（面试官提问或用户回答） */
const displayTranscript = computed(() => {
  if (voice.liveAiText) {
    return {
      label: 'Capy（回复中...）',
      text: voice.liveAiText,
      isUser: false,
    }
  }
  const entries = voice.transcriptEntries
  if (!entries.length) return null
  const last = entries[entries.length - 1]
  return {
    label: last.label,
    text: last.text,
    isUser: last.label === '你',
  }
})

function scrollTranscript() {
  nextTick(() => {
    if (transcriptContainer.value) {
      transcriptContainer.value.scrollTop = transcriptContainer.value.scrollHeight
    }
  })
}

watch(() => voice.transcriptEntries, (entries) => {
  scrollTranscript()
  emit('update:transcript', entries)
}, { deep: true })

watch(() => voice.liveAiText, scrollTranscript)

watch(() => voice.connected, (isConnected) => {
  if (isConnected) {
    statusText.value = '面试进行中'
  } else if (voiceRunning.value && !voice.connecting) {
    statusText.value = '连接已断开'
    if (!voice.error) {
      voice.hintText = '连接已断开，请点击麦克风重新开始'
    }
  }
})

async function startVoice() {
  if (!supported || voiceRunning.value) return

  voiceRunning.value = true
  isMuted.value = false
  elapsed.value = 0
  statusText.value = '面试进行中'
  timer = setInterval(() => elapsed.value++, 1000)

  await voice.connect()
  if (voice.connected) {
    emit('voice-started')
  } else {
    stopVoice()
  }
}

function stopVoice() {
  voiceRunning.value = false
  statusText.value = '面试已结束'
  voice.hintText = voice.error || `面试时长 ${formattedTime.value}`
  clearInterval(timer)
  timer = null
  voice.disconnect()
  emit('voice-stopped', voice.transcriptEntries)
}

function toggleMute() {
  isMuted.value = !isMuted.value
  voice.setMuted(isMuted.value)
}

async function toggleVoice() {
  if (!voiceRunning.value) {
    await startVoice()
  } else {
    stopVoice()
  }
}

defineExpose({
  getTranscript: () => voice.transcriptEntries,
  clearTranscript: voice.clearTranscript,
})

watch(() => props.paused, (paused) => {
  voice.setPaused(paused)
})

onMounted(() => {
  if (!supported) {
    voice.hintText = '当前浏览器不支持语音面试，请使用 Chrome 并允许麦克风权限'
    return
  }
  if (props.autoStart) {
    startVoice()
  }
})

onUnmounted(() => {
  clearInterval(timer)
  voice.disconnect()
})
</script>

<template>
  <div class="voice-page">
    <div class="voice-container">
      <div class="voice-status" :class="voiceRunning && voice.connected ? 'active' : ''">
        <span class="voice-status__dot"></span>
        <span>{{ voice.connecting ? '连接中...' : statusText }}</span>
      </div>

      <div class="voice-avatar" :class="voice.avatarSpeaking ? 'speaking' : ''">
        <div class="voice-avatar__ring"></div>
        <div class="voice-avatar__ring voice-avatar__ring--2"></div>
        <div class="voice-avatar__face">
          <CapybaraLogo :size="64" :stroke-width="2.5" />
        </div>
      </div>

      <h2 class="voice-name" style="font-family: var(--font-heading)">Capy</h2>
      <p class="voice-hint">{{ voice.hintText }}</p>

      <div class="voice-waveform" :class="voice.waveformActive || voice.isListening ? 'active' : ''">
        <span v-for="n in 20" :key="n"></span>
      </div>

      <div ref="transcriptContainer" class="voice-transcript">
        <div
          v-if="displayTranscript"
          class="voice-transcript__entry"
          :class="displayTranscript.isUser ? 'voice-transcript__entry--user' : 'voice-transcript__entry--ai'"
        >
          <span class="transcript-label">{{ displayTranscript.label }}</span>
          <p>{{ displayTranscript.text }}</p>
        </div>
        <p v-else class="voice-transcript__placeholder">当前问答将显示在这里...</p>
      </div>

      <div class="voice-controls">
        <button
          v-if="!voiceRunning"
          class="voice-ctrl voice-ctrl--primary"
          :class="{ 'opacity-50 cursor-not-allowed': !supported || voice.connecting }"
          :disabled="!supported || voice.connecting"
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
          :disabled="!voiceRunning"
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
  min-height: 72px;
  max-height: 240px;
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

.voice-ctrl--secondary:hover:not(:disabled) {
  background: var(--color-surface-alt);
  color: var(--color-primary);
  transform: scale(1.06);
}

.voice-ctrl--secondary.muted {
  color: #EF4444;
  border-color: #EF4444;
}

.voice-ctrl--secondary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
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
