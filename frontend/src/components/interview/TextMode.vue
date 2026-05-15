<script setup>
import { ref, nextTick } from 'vue'
import { api } from '@/api/index.js'

const props = defineProps({
  interviewType: { type: String, default: 'technical' },
})

const emit = defineEmits(['update:type'])

const messages = ref([])
const started = ref(false)
const inputText = ref('')
const chatContainer = ref(null)
const textareaRef = ref(null)
const aiTyping = ref(false)

const welcomeOptions = [
  { type: 'technical', label: '技术面试', desc: '算法、系统设计、技术深度', icon: 'code' },
  { type: 'behavioral', label: '行为面试', desc: 'STAR 法则、团队协作、领导力', icon: 'people' },
  { type: 'hr', label: 'HR 面试', desc: '职业规划、薪资谈判、自我介绍', icon: 'briefcase' },
]

function startInterview(type) {
  emit('update:type', type)
  started.value = true
  messages.value = []
  addAIMessage(getFirstQuestion(type))
}

function getFirstQuestion(type) {
  const questions = {
    technical: '你好！我看到你简历上有 React 项目经验，能介绍一下你在项目中遇到的最大技术挑战吗？',
    behavioral: '你好！请先做一个简短的自我介绍吧。',
    hr: '你好！请先简单介绍一下自己吧。',
  }
  return questions[type] || questions.technical
}

async function addAIMessage(content) {
  aiTyping.value = true
  await new Promise((r) => setTimeout(r, 800))
  messages.value.push({ role: 'ai', content })
  aiTyping.value = false
  scrollToBottom()
}

function addUserMessage(content) {
  messages.value.push({ role: 'user', content })
  scrollToBottom()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || aiTyping.value) return
  inputText.value = ''
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  addUserMessage(text)

  const res = await api.getInterviewReply(messages.value, props.interviewType)
  addAIMessage(res.content)
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
</script>

<template>
  <!-- Welcome Screen -->
  <div v-if="!started" class="interview-page">
    <div class="chat-welcome">
      <!-- Capybara illustration -->
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
        AI 面试官会根据你的简历和目标岗位进行个性化提问。<br>
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

  <!-- Chat Interface -->
  <div v-else class="interview-page">
    <!-- Messages -->
    <div ref="chatContainer" class="chat-area">
      <div class="chat-messages">
        <div
          v-for="(msg, i) in messages"
          :key="i"
          class="chat-bubble"
          :class="msg.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--ai'"
        >
          <div v-if="msg.role === 'ai'" class="bubble-header">
            <svg viewBox="0 0 14 14" fill="none" width="14" height="14">
              <path d="M7 2 C4 2, 2 4, 2 7 C2 10, 4 12, 7 12 C10 12, 12 10, 12 7 C12 4, 10 2, 7 2 Z" stroke="currentColor" stroke-width="1.2"/>
              <circle cx="5.5" cy="6.5" r="0.8" fill="currentColor"/>
              <circle cx="8.5" cy="6.5" r="0.8" fill="currentColor"/>
            </svg>
            AI 面试官
          </div>
          {{ msg.content }}
        </div>

        <!-- Typing indicator -->
        <div v-if="aiTyping" class="typing-indicator">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    </div>

    <!-- Input -->
    <div class="chat-input-area">
      <div class="chat-input-wrap">
        <textarea
          ref="textareaRef"
          v-model="inputText"
          class="chat-input"
          placeholder="输入你的回答..."
          rows="1"
          @input="autoResize"
          @keydown="onKeydown"
        ></textarea>
        <button
          class="chat-send"
          :class="{ 'opacity-50 cursor-not-allowed': !inputText.trim() || aiTyping }"
          :disabled="!inputText.trim() || aiTyping"
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
  height: calc(100vh - var(--nav-height));
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

/* Chat area */
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

/* Messages */
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

/* Typing indicator */
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

/* Input area */
.chat-input-area {
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

.chat-send:hover {
  background: var(--color-primary-dark);
  transform: scale(1.05);
}

.chat-send:active {
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

/* Dark mode overrides */
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

@media (max-width: 768px) {
  .chat-welcome__options {
    gap: var(--space-2);
  }

  .welcome-option {
    padding: var(--space-3) var(--space-4);
  }
}
</style>
