<script setup>
import CapybaraLogo from '@/components/common/CapybaraLogo.vue'
import { renderMarkdown } from '@/utils/renderMarkdown.js'
import { INTERVIEW_TYPES } from '@/data/interview.js'

const props = defineProps({
  summary: { type: Object, required: true },
  messages: { type: Array, default: () => [] },
})

const emit = defineEmits(['download', 'back-to-list'])

const isBackendFormat = typeof props.summary.overview === 'string'
</script>

<template>
  <!-- Top bar with actions -->
  <div class="summary-topbar -mx-6 lg:-mx-10 px-6 lg:px-10 mb-4 flex items-center justify-between">
    <h2 class="text-lg font-bold text-ink" style="font-family: var(--font-heading)">面试总结</h2>
    <div class="flex items-center gap-2">
      <button
        class="px-4 py-2 text-sm rounded-lg border border-border-light dark:border-border hover:bg-surface transition-colors"
        @click="emit('download')"
      >
        下载总结
      </button>
      <button class="btn btn--primary px-5 py-2 text-sm" @click="emit('back-to-list')">
        返回列表
      </button>
    </div>
  </div>

  <!-- Negative margins to break out of AnalysisLayout's 960px container -->
  <div class="summary-content -mx-6 lg:-mx-10">
    <!-- Left: Chat history -->
    <aside class="summary-chat">
      <div class="summary-chat__header">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 3h12v8a1 1 0 01-1 1H3a1 1 0 01-1-1V3z" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"/>
          <path d="M6 7h4M6 9.5h2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <span>对话记录</span>
        <span class="summary-chat__count">{{ messages.length }} 条</span>
      </div>

      <div class="summary-chat__body">
        <div v-if="messages.length === 0" class="summary-chat__empty">
          <p>暂无对话记录</p>
        </div>

        <template v-else>
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="chat-bubble"
            :class="msg.role === 'user' ? 'chat-bubble--user' : 'chat-bubble--ai'"
          >
            <div v-if="msg.role === 'ai'" class="bubble-header">
              <CapybaraLogo :size="14" :stroke-width="2" />
              <span>Capy</span>
            </div>
            <template v-if="msg.role === 'ai'">
              <div v-html="renderMarkdown(msg.content)"></div>
            </template>
            <template v-else>
              {{ msg.content }}
            </template>
          </div>
        </template>
      </div>
    </aside>

    <!-- Right: Summary sections -->
    <section class="summary-sections">
      <div class="summary-sections__inner">
        <!-- Overview: backend vs frontend format -->
        <template v-if="isBackendFormat">
          <div class="summary-card">
            <div class="summary-card__header">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="2" width="12" height="12" rx="2.5" stroke="currentColor" stroke-width="1.3"/>
                <path d="M5 6l2.5 2.5L11 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>面试概览</span>
            </div>
            <p class="summary-card__text">{{ summary.overview }}</p>
          </div>

          <div v-if="summary.technical_assessment" class="summary-card">
            <div class="summary-card__header">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M5 4L1 8l4 4M11 4l4 4-4 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>技术评估</span>
            </div>
            <p class="summary-card__text">{{ summary.technical_assessment }}</p>
          </div>

          <div v-if="summary.behavioral_assessment" class="summary-card">
            <div class="summary-card__header">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <circle cx="8" cy="5" r="3" stroke="currentColor" stroke-width="1.3"/>
                <path d="M2 14c0-3 2.5-5 6-5s6 2 6 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
              </svg>
              <span>行为评估</span>
            </div>
            <p class="summary-card__text">{{ summary.behavioral_assessment }}</p>
          </div>
        </template>

        <template v-else>
          <div class="summary-card">
            <div class="summary-card__header">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <rect x="2" y="2" width="12" height="12" rx="2.5" stroke="currentColor" stroke-width="1.3"/>
                <path d="M5 6l2.5 2.5L11 5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>面试概览</span>
            </div>
            <div class="summary-overview-grid">
              <div class="summary-stat">
                <span class="summary-stat__label">类型</span>
                <span class="summary-stat__value">{{ INTERVIEW_TYPES[summary.overview.type] }}</span>
              </div>
              <div class="summary-stat">
                <span class="summary-stat__label">时长</span>
                <span class="summary-stat__value">{{ summary.overview.duration }}分钟</span>
              </div>
              <div class="summary-stat">
                <span class="summary-stat__label">问题数</span>
                <span class="summary-stat__value">{{ summary.overview.questionCount }}个</span>
              </div>
              <div class="summary-stat">
                <span class="summary-stat__label">简历</span>
                <span class="summary-stat__value">{{ summary.overview.resume }}</span>
              </div>
            </div>
            <div v-if="summary.overview.projects?.length > 0" class="summary-projects">
              <span class="summary-stat__label">项目</span>
              <div class="summary-projects__tags">
                <span v-for="p in summary.overview.projects" :key="p" class="tag">{{ p }}</span>
              </div>
            </div>
          </div>
        </template>

        <!-- Shared: highlights and suggestions -->
        <div class="summary-card">
          <div class="summary-card__header">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/>
              <path d="M5.5 8l2 2 3.5-4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>回答亮点</span>
          </div>
          <ul class="summary-card__list">
            <li v-for="(item, i) in summary.highlights" :key="i">{{ item }}</li>
          </ul>
        </div>

        <div class="summary-card">
          <div class="summary-card__header">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.3"/>
              <path d="M8 5v3.5M8 11v.5" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
            </svg>
            <span>改进建议</span>
          </div>
          <ul class="summary-card__list">
            <li v-for="(item, i) in (summary.improvements || summary.suggestions)" :key="i">{{ item }}</li>
          </ul>
        </div>

      </div>
    </section>
  </div>
</template>

<style scoped>
/* ── Layout: break out of AnalysisLayout's 960px container ── */
.summary-content {
  display:  flex;
  min-height: 0;
  height: calc(200vh - var(--nav-height) - 4rem - 560px);
  margin-left: -1.5rem;
  margin-right: -1.5rem;
  gap: 10px;
}

@media (min-width: 1024px) {
  .summary-content {
    margin-left: -2.5rem;
    margin-right: -2.5rem;
  }
}

/* ── Left: Chat ── */
.summary-chat {
  width: 50%;
  display: flex;
  flex-direction: column;
  background: var(--color-base);
  min-height: 0;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-light);
  overflow: hidden;
}

.summary-chat__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--color-ink);
  border-bottom: 1px solid var(--color-border-light);
  background: var(--color-white);
  flex-shrink: 0;
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
}

.summary-chat__count {
  margin-left: auto;
  font-weight: 400;
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
}

.summary-chat__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.summary-chat__body::-webkit-scrollbar {
  width: 4px;
}
.summary-chat__body::-webkit-scrollbar-track {
  background: transparent;
}
.summary-chat__body::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}

.summary-chat__empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-muted);
  font-size: var(--text-sm);
}

/* ── Chat bubbles (match TextMode) ── */
.chat-bubble {
  max-width: 85%;
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-lg);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  word-break: break-word;
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
  gap: var(--space-1);
  margin-bottom: var(--space-1);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-primary);
}

/* Markdown inside AI bubbles */
:deep(.chat-bubble--ai p) {
  margin: 0 0 var(--space-2);
}
:deep(.chat-bubble--ai p:last-child) {
  margin-bottom: 0;
}
:deep(.chat-bubble--ai strong) {
  font-weight: 600;
}
:deep(.chat-bubble--ai code) {
  background: var(--color-surface);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 0.875em;
  font-family: var(--font-mono, monospace);
}
:deep(.chat-bubble--ai ul),
:deep(.chat-bubble--ai ol) {
  margin: var(--space-2) 0;
  padding-left: var(--space-5);
}
:deep(.chat-bubble--ai li) {
  margin-bottom: var(--space-1);
}

/* ── Right: Summary ── */
.summary-sections {
  width: 50%;
  overflow-y: auto;
  background: var(--color-white);
  min-height: 0;
  border-radius: var(--radius-xl);
  border: 1px solid var(--color-border-light);
}

.summary-sections::-webkit-scrollbar {
  width: 4px;
}
.summary-sections::-webkit-scrollbar-track {
  background: transparent;
}
.summary-sections::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 2px;
}

.summary-sections__inner {
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

/* ── Summary cards ── */
.summary-card {
  background: var(--color-white);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
}

.summary-card__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-heading);
  font-weight: 600;
  font-size: var(--text-sm);
  color: var(--color-ink);
  margin-bottom: var(--space-4);
}

.summary-card__header svg {
  color: var(--color-primary);
  flex-shrink: 0;
}

.summary-card__text {
  font-size: var(--text-sm);
  color: var(--color-ink-light);
  line-height: var(--leading-relaxed);
  margin: 0;
}

.summary-card__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary-card__list li {
  position: relative;
  padding-left: var(--space-5);
  font-size: var(--text-sm);
  color: var(--color-ink-light);
  line-height: var(--leading-relaxed);
}

.summary-card__list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.55em;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
  opacity: 0.6;
}

/* ── Overview grid ── */
.summary-overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-3);
}

.summary-stat {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.summary-stat__label {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  font-weight: 500;
}

.summary-stat__value {
  font-size: var(--text-sm);
  color: var(--color-ink);
  font-weight: 500;
}

.summary-projects {
  margin-top: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.summary-projects__tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.tag {
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: 500;
  background: rgba(184, 132, 92, 0.1);
  color: var(--color-primary);
}

/* ── Dark mode ── */
:global(.dark) .summary-chat {
  background: var(--color-surface);
  border-color: var(--color-border);
}
:global(.dark) .summary-chat__header {
  background: var(--color-surface);
}
:global(.dark) .chat-bubble--ai {
  background: var(--color-base);
  border-color: var(--color-border);
}
:global(.dark) .summary-sections {
  background: var(--color-surface);
  border-color: var(--color-border);
}
:global(.dark) .summary-card {
  background: var(--color-base);
  border-color: var(--color-border);
}

/* ── Responsive ── */
@media (max-width: 1024px) {
  .summary-content {
    flex-direction: column;
    height: auto;
    min-height: calc(100vh - var(--nav-height) - 4rem - 56px);
  }

  .summary-chat {
    width: 100%;
    height: 45vh;
  }

  .summary-sections {
    width: 100%;
    flex: 1;
  }
}

@media (max-width: 640px) {
  .summary-chat {
    height: 40vh;
  }

  .summary-sections__inner {
    padding: var(--space-4);
  }

  .summary-card {
    padding: var(--space-4);
  }
}
</style>
