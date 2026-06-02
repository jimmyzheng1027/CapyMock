<script setup>
import { ref, nextTick, onMounted, watch } from 'vue'
import { api } from '@/api/index.js'
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import { renderMarkdown } from '@/utils/renderMarkdown.js'
import { eventsToMessages } from '@/utils/interviewHelpers.js'

const props = defineProps({
  sessionId: { type: String, required: true },
  interviewType: { type: String, default: 'technical' },
  autoStart: { type: Boolean, default: false },
  hasHistory: { type: Boolean, default: false },
  paused: { type: Boolean, default: false }
})

const emit = defineEmits(['update:messages', 'interview-started', 'interview-ended'])

const messages = ref([])
const started = ref(false)
const inputText = ref('')
const chatContainer = ref(null)
const textareaRef = ref(null)
const aiTyping = ref(false)
const historyLoading = ref(false)
let currentEventSource = null

function hasAssistantMessages() {
  return messages.value.some((msg) => msg.role === 'ai')
}

async function loadHistory() {
  historyLoading.value = true
  try {
    const data = await api.getSessionEvents(props.sessionId)
    const loaded = eventsToMessages(data.events || []).map((msg) => ({
      ...msg,
      html: msg.role === 'ai' ? renderMarkdown(msg.content) : null,
    }))
    messages.value = loaded
    if (loaded.length > 0) {
      started.value = true
    }
  } catch (e) {
    console.error('Failed to load session history:', e)
  } finally {
    historyLoading.value = false
    if (messages.value.length > 0) {
      await nextTick()
      scrollToTop()
    }
  }
}

async function initializeSession() {
  closeSSE()
  aiTyping.value = false
  messages.value = []
  started.value = false

  await loadHistory()

  if (hasAssistantMessages() || props.hasHistory) {
    started.value = true
    return
  }

  if (props.autoStart) {
    startInterview()
  }
}

function startInterview() {
  started.value = true
  messages.value = []
  emit('interview-started')
  // Send initial empty message to trigger agent's opening question
  triggerAgent('')
}

function patchStreamingAiMessage(aiIndex, patch) {
  const msg = messages.value[aiIndex]
  if (!msg || msg.role !== 'ai') return
  messages.value[aiIndex] = { ...msg, ...patch }
}

function appendAiStreamDelta(aiIndex, delta) {
  if (!delta) return
  const msg = messages.value[aiIndex]
  if (!msg || msg.role !== 'ai') return
  const content = msg.content + delta
  patchStreamingAiMessage(aiIndex, {
    content,
    html: renderMarkdown(content),
  })
  if (aiTyping.value) aiTyping.value = false
  scrollToBottom()
}

async function triggerAgent(text) {
  aiTyping.value = true

  try {
    closeSSE()

    const aiIndex = messages.value.length
    messages.value.push({ role: 'ai', content: '', html: '' })

    const eventSource = api.streamEvents(props.sessionId)
    currentEventSource = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'assistant.text.delta') {
          const delta = data.payload?.delta ?? data.payload?.text ?? ''
          appendAiStreamDelta(aiIndex, delta)
        } else if (data.type === 'assistant.text.done') {
          const finalText = data.payload?.text
          if (finalText) {
            patchStreamingAiMessage(aiIndex, {
              content: finalText,
              html: renderMarkdown(finalText),
            })
          }
          scrollToBottom()
        } else if (data.type === 'turn.done') {
          closeSSE()
          aiTyping.value = false
          emit('update:messages', messages.value)
        } else if (data.type === 'error') {
          console.error('Agent error:', data.payload)
          const msg = messages.value[aiIndex]
          if (msg && !msg.content) {
            patchStreamingAiMessage(aiIndex, {
              content: '抱歉，遇到了一些问题，请重试。',
              html: renderMarkdown('抱歉，遇到了一些问题，请重试。'),
            })
          }
          closeSSE()
          aiTyping.value = false
          emit('update:messages', messages.value)
        }
      } catch (e) {
        // Keepalive or non-JSON, ignore
      }
    }

    eventSource.onerror = () => {
      closeSSE()
      aiTyping.value = false
      const msg = messages.value[aiIndex]
      if (msg && !msg.content) {
        patchStreamingAiMessage(aiIndex, {
          content: '连接中断，请重试。',
          html: renderMarkdown('连接中断，请重试。'),
        })
      }
      emit('update:messages', messages.value)
    }

    // Trigger agent after SSE is listening so deltas are not missed
    await api.sendSSEMessage(props.sessionId, text)
  } catch (e) {
    console.error('Failed to trigger agent:', e)
    aiTyping.value = false
    messages.value.push({ role: 'ai', content: '发送失败，请重试。' })
    scrollToBottom()
    emit('update:messages', messages.value)
  }
}

function closeSSE() {
  if (currentEventSource) {
    currentEventSource.close()
    currentEventSource = null
  }
}

function addUserMessage(content) {
  messages.value.push({ role: 'user', content })
  scrollToBottom()
  emit('update:messages', messages.value)
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || aiTyping.value || props.paused) return
  inputText.value = ''
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  addUserMessage(text)
  triggerAgent(text)
}

function scrollToBottom() {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

function autoResize() {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 120) + 'px'
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
  }
}

function getMessages() {
  return messages.value
}

function clearMessages() {
  messages.value = []
  emit('update:messages', messages.value)
}

defineExpose({ getMessages, clearMessages })

onMounted(async () => {
  if (!props.autoStart) return
  await initializeSession()
})
</script>

<template>
  <div v-if="!started && !autoStart" class="interview-page">
    <div class="chat-welcome">
      <svg width="80" height="80" viewBox="0 0 120 120" fill="none" style="margin-bottom: var(--space-6)">
        <path d="M60 95 C25 95, 8 75, 12 55 C15 40, 30 25, 60 22 C90 25, 105 40, 108 55 C112 75, 95 95, 60 95 Z" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        <path d="M35 28 C32 18, 42 15, 44 24" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <path d="M76 24 C74 14, 84 12, 85 22" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <path d="M42 52 Q48 46 54 52" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <path d="M66 49 Q72 43 78 49" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <path d="M58 60 L58 72" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round"/>
        <path d="M48 72 Q58 85 68 72" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <ellipse cx="58" cy="78" rx="6" ry="5" fill="var(--color-accent)" opacity="0.4"/>
        <path d="M18 65 C8 55, 2 42, 10 32" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
        <path d="M102 65 C112 55, 118 42, 110 32" stroke="var(--color-primary)" stroke-width="2.5" stroke-linecap="round" fill="none"/>
      </svg>

      <h2 class="chat-welcome__title" style="font-family: var(--font-heading)">准备好了吗？</h2>
      <p class="chat-welcome__desc">
        Capy会根据你的简历和目标岗位进行个性化提问。<br>
        选择下方的面试类型开始吧。
      </p>

      <div class="chat-welcome__options">
        <button
          v-for="opt in welcomeOptions"
          :key="opt.type"
          class="welcome-option"
          @click="startInterview(opt.type)"
        >
          <div class="welcome-option__icon">
            <svg v-if="opt.icon === 'code'" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M8 6l-6 6 6 6M16 6l6 6-6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-if="opt.icon === 'people'" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="8" r="4" stroke="currentColor" stroke-width="1.8"/>
              <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            </svg>
            <svg v-if="opt.icon === 'briefcase'" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <rect x="3" y="4" width="18" height="16" rx="3" stroke="currentColor" stroke-width="1.8"/>
              <line x1="7" y1="9" x2="17" y2="9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <line x1="7" y1="13" x2="13" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </div>
          <div class="welcome-option__text">
            <strong>{{ opt.label }}</strong>
            <span>{{ opt.desc }}</span>
          </div>
        </button>
      </div>
    </div>
  </div>

  <div v-else class="interview-page">
    <div v-if="historyLoading" class="flex items-center justify-center flex-1">
      <p class="text-ink-muted text-sm">加载聊天记录...</p>
    </div>

    <div v-else ref="chatContainer" class="chat-area">
      <div class="chat-messages">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="chat-bubble"
          :class="msg.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--ai'"
        >
          <div v-if="msg.role === 'ai'" class="bubble-header">
            <CapybaraLogo :size="16" :stroke-width="2" />
            Capy
          </div>
          <template v-if="msg.role === 'ai'">
            <div v-html="msg.html || renderMarkdown(msg.content)"></div>
          </template>
          <template v-else>
            {{ msg.content }}
          </template>
        </div>

        <div v-if="aiTyping" class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <div class="chat-input-wrap">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          class="chat-input"
          :placeholder="paused ? '面试已暂停...' : '输入你的回答...'"
          rows="1"
          :disabled="paused"
          @input="autoResize"
          @keydown="onKeydown"
        ></textarea>
        <button
          class="chat-send"
          :class="{ 'opacity-50 cursor-not-allowed': !inputText.trim() || aiTyping || paused }"
          :disabled="!inputText.trim() || aiTyping || paused"
          @click="sendMessage"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M18 2L9 11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <path d="M18 2l-6 16-3-7-7-3z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
      <p class="chat-input-hint">按 Enter 发送，Shift + Enter 换行</p>
    </div>
  </div>
</template>

<style scoped>
.interview-page {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Welcome */
.chat-welcome {
  max-width: 520px;
  margin: auto;
  text-align: center;
  animation: welcomeFadeIn 0.6s var(--ease-out) both;
  padding: 0 var(--space-6);
}

@keyframes welcomeFadeIn {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}

.chat-welcome svg {
  display: inline-block;
}

.chat-welcome__title {
  font-size: var(--text-3xl);
  margin-bottom: var(--space-3);
}

.chat-welcome__desc {
  font-size: var(--text-base);
  color: var(--color-ink-light);
  line-height: var(--leading-relaxed);
  margin-bottom: var(--space-8);
}

.chat-welcome__options {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.welcome-option {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-5);
  background: var(--color-white);
  border: 1.5px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  text-align: left;
  cursor: pointer;
  transition: all var(--duration-normal) var(--ease-out);
  width: 100%;
  font-family: inherit;
}

.welcome-option:hover {
  border-color: var(--color-primary-light);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.welcome-option__icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--color-primary);
}

.welcome-option__text strong {
  display: block;
  font-size: var(--text-base);
  font-weight: 600;
  margin-bottom: 2px;
  color: var(--color-ink);
}

.welcome-option__text span {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
}

.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-8) var(--space-6);
  display: flex;
  flex-direction: column;
  scroll-behavior: smooth;
}

.chat-area::-webkit-scrollbar {
  width: 4px;
}

.chat-area::-webkit-scrollbar-track {
  background: transparent;
}

.chat-area::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}

.chat-messages {
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  padding: var(--space-4) 0;
}

.chat-bubble {
  max-width: 85%;
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  animation: bubbleIn 0.35s var(--ease-out) both;
}

@keyframes bubbleIn {
  from { opacity: 0; transform: translateY(10px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

.chat-bubble--ai {
  align-self: flex-start;
  background: var(--color-white);
  border: 1px solid var(--color-border-light);
  border-bottom-left-radius: var(--space-1);
  color: var(--color-ink);
}

.chat-bubble--user {
  align-self: flex-end;
  background: var(--color-primary);
  color: var(--color-white);
  border-bottom-right-radius: var(--space-1);
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-primary);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: var(--space-4) var(--space-5);
  align-self: flex-start;
  background: var(--color-white);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  border-bottom-left-radius: var(--space-1);
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-ink-muted);
  animation: typingBounce 1.2s ease-in-out infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }

@keyframes typingBounce {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-6px); opacity: 1; }
}

.chat-input-area {
  flex-shrink: 0;
  padding: var(--space-4) var(--space-6) var(--space-6);
  background: linear-gradient(to top, var(--color-base) 60%, transparent);
}

.chat-input-wrap {
  max-width: 720px;
  margin: 0 auto;
  display: flex;
  align-items: flex-end;
  gap: var(--space-3);
  background: var(--color-white);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: var(--space-3) var(--space-3) var(--space-3) var(--space-5);
  transition: border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);
}

.chat-input-wrap:focus-within {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.chat-input {
  flex: 1;
  border: none;
  outline: none;
  background: none;
  font-size: var(--text-sm);
  line-height: var(--leading-normal);
  color: var(--color-ink);
  resize: none;
  max-height: 120px;
  font-family: inherit;
}

.chat-input::placeholder {
  color: var(--color-ink-muted);
}

.chat-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.chat-send {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-white);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all var(--duration-fast) var(--ease-out);
}

.chat-send:hover:not(:disabled) {
  background: var(--color-primary-dark);
  transform: scale(1.05);
}

.chat-send:active:not(:disabled) {
  transform: scale(0.95);
}

.chat-input-hint {
  max-width: 720px;
  margin: var(--space-2) auto 0;
  text-align: center;
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  opacity: 0.6;
}

:global(.dark) .welcome-option {
  background: var(--color-surface);
  border-color: var(--color-border);
}

:global(.dark) .chat-bubble--ai {
  background: var(--color-surface);
  border-color: var(--color-border);
}

:global(.dark) .typing-indicator {
  background: var(--color-surface);
  border-color: var(--color-border);
}

:global(.dark) .chat-input-wrap {
  background: var(--color-surface);
}

/* Markdown rendered content inside AI bubbles */
:deep(.bubble-code) {
  background: var(--color-surface);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.875em;
  font-family: var(--font-mono, monospace);
}

:deep(.bubble-list) {
  margin: var(--space-2) 0;
  padding-left: var(--space-5);
}

:deep(.bubble-list li) {
  margin-bottom: var(--space-1);
  line-height: var(--leading-relaxed);
}

:deep(.bubble-hr) {
  border: none;
  border-top: 1px solid var(--color-border-light);
  margin: var(--space-3) 0;
}

:deep(.chat-bubble--ai p) {
  margin: 0 0 var(--space-2);
}

:deep(.chat-bubble--ai p:last-child) {
  margin-bottom: 0;
}

:deep(.chat-bubble--ai strong) {
  font-weight: 600;
}

@media (max-width: 768px) {
  .chat-welcome__options {
    gap: var(--space-2);
  }

  .welcome-option {
    padding: var(--space-3) var(--space-4);
  }
}
</style>
