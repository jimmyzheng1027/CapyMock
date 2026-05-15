<script setup>
import { ref } from 'vue'

defineProps({
  open: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])

const resumeFile = ref(null)
const targetPosition = ref('')
const company = ref('')
const language = ref('zh')
const difficulty = ref('medium')

function onFileChange(e) {
  const file = e.target.files?.[0]
  if (file) {
    resumeFile.value = { name: file.name, size: `${Math.round(file.size / 1024)} KB` }
  }
}
</script>

<template>
  <Transition name="settings">
    <div v-if="open" class="settings-overlay" @click.self="emit('close')">
      <!-- Panel -->
      <div class="settings-panel">
        <!-- Header -->
        <div class="settings-panel__header">
          <h3 class="font-bold" style="font-family: var(--font-heading)">面试设置</h3>
          <button
            class="settings-close"
            @mouseenter="$event.currentTarget.style.background='var(--color-surface-alt)'; $event.currentTarget.style.color='var(--color-ink)'"
            @mouseleave="$event.currentTarget.style.background='transparent'; $event.currentTarget.style.color='var(--color-ink-muted)'"
            @click="emit('close')"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M5 5l6 6M11 5l-6 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>
        </div>

        <!-- Body -->
        <div class="settings-panel__body">
          <!-- Resume upload -->
          <div class="settings-section">
            <label class="settings-label">简历上传</label>
            <div
              v-if="!resumeFile"
              class="settings-upload"
              @click="$refs.fileInput.click()"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" style="color: var(--color-ink-muted)">
                <path d="M12 4v12M12 4l-4 4M12 4l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M20 16v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              <span>点击上传简历</span>
              <span class="settings-upload__hint">PDF / Word</span>
            </div>
            <div v-else class="settings-file">
              <svg width="18" height="18" viewBox="0 0 18 18" fill="none" style="color: var(--color-primary)">
                <rect x="3" y="2" width="12" height="14" rx="2" stroke="currentColor" stroke-width="1.3"/>
                <path d="M7 8h4M7 11h3" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              </svg>
              <span class="flex-1 truncate">{{ resumeFile.name }}</span>
              <button
                class="settings-file__remove"
                @mouseenter="$event.currentTarget.style.background='rgba(239,68,68,0.1)'; $event.currentTarget.style.color='#EF4444'"
                @mouseleave="$event.currentTarget.style.background='transparent'; $event.currentTarget.style.color='var(--color-ink-muted)'"
                @click="resumeFile = null"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M4 4l6 6M10 4l-6 6" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/></svg>
              </button>
            </div>
            <input ref="fileInput" type="file" accept=".pdf,.doc,.docx" class="hidden" @change="onFileChange" />
          </div>

          <!-- Target position -->
          <div class="settings-section">
            <label class="settings-label">目标岗位</label>
            <input
              v-model="targetPosition"
              class="settings-input w-full"
              placeholder="例：高级前端工程师"
            />
          </div>

          <!-- Company -->
          <div class="settings-section">
            <label class="settings-label">目标公司</label>
            <input
              v-model="company"
              class="settings-input w-full"
              placeholder="例：字节跳动"
            />
          </div>

          <!-- Language -->
          <div class="settings-section">
            <label class="settings-label">面试语言</label>
            <div class="settings-radio-group">
              <label
                v-for="opt in [{ v: 'zh', l: '中文' }, { v: 'en', l: 'English' }, { v: 'both', l: '双语' }]"
                :key="opt.v"
                class="settings-radio"
              >
                <input type="radio" :value="opt.v" v-model="language" />
                <span class="settings-radio__mark"></span>
                {{ opt.l }}
              </label>
            </div>
          </div>

          <!-- Difficulty -->
          <div class="settings-section">
            <label class="settings-label">难度等级</label>
            <div class="settings-radio-group">
              <label
                v-for="opt in [{ v: 'easy', l: '简单' }, { v: 'medium', l: '中等' }, { v: 'hard', l: '困难' }]"
                :key="opt.v"
                class="settings-radio"
              >
                <input type="radio" :value="opt.v" v-model="difficulty" />
                <span class="settings-radio__mark"></span>
                {{ opt.l }}
              </label>
            </div>
          </div>

          <button class="btn btn--primary w-full justify-center" @click="emit('close')">保存设置</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  z-index: 200;
  display: flex;
  justify-content: flex-end;
}

.settings-panel {
  position: relative;
  width: 360px;
  max-width: 90vw;
  height: 100%;
  background: var(--color-base);
  border-left: 1px solid var(--color-border-light);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.settings-panel__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border-light);
}

.settings-panel__header h3 {
  font-size: var(--text-lg);
  font-weight: 700;
}

.settings-close {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-muted);
  transition: all var(--duration-fast) var(--ease-out);
}

.settings-panel__body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.settings-label {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-ink);
}

.settings-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-6) var(--space-4);
  border: 2px dashed var(--color-border);
  border-radius: var(--radius-lg);
  color: var(--color-ink-muted);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
  text-align: center;
  font-size: var(--text-sm);
}

.settings-upload:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: rgba(196, 149, 106, 0.04);
}

.settings-upload__hint {
  font-size: var(--text-xs);
  opacity: 0.6;
}

.settings-file {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-ink);
}

.settings-file__remove {
  margin-left: auto;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-muted);
  transition: all var(--duration-fast) var(--ease-out);
  flex-shrink: 0;
}

.settings-input {
  padding: var(--space-3) var(--space-4);
  background: var(--color-white);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--text-sm);
  color: var(--color-ink);
  outline: none;
  transition: border-color var(--duration-fast) var(--ease-out), box-shadow var(--duration-fast) var(--ease-out);
  font-family: inherit;
}

.settings-input:focus {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-glow);
}

.settings-input::placeholder {
  color: var(--color-ink-muted);
}

.settings-radio-group {
  display: flex;
  gap: var(--space-3);
  flex-wrap: wrap;
}

.settings-radio {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-ink-light);
  cursor: pointer;
}

.settings-radio input {
  display: none;
}

.settings-radio__mark {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 1.5px solid var(--color-border);
  position: relative;
  transition: all var(--duration-fast) var(--ease-out);
  flex-shrink: 0;
}

.settings-radio input:checked + .settings-radio__mark {
  border-color: var(--color-primary);
}

.settings-radio input:checked + .settings-radio__mark::after {
  content: '';
  position: absolute;
  top: 3px;
  left: 3px;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-primary);
}

/* Transition */
.settings-enter-active,
.settings-leave-active {
  transition: opacity 0.3s ease;
}

.settings-enter-active .settings-panel,
.settings-leave-active .settings-panel {
  transition: transform 0.3s var(--ease-out);
}

.settings-enter-from,
.settings-leave-to {
  opacity: 0;
}

.settings-enter-from .settings-panel {
  transform: translateX(100%);
}

.settings-leave-to .settings-panel {
  transform: translateX(100%);
}

/* Dark mode */
:global(.dark) .settings-panel {
  background: var(--color-surface);
}

:global(.dark) .settings-input {
  background: var(--color-surface-alt);
  border-color: var(--color-border);
}

@media (max-width: 768px) {
  .settings-panel {
    width: 100%;
    max-width: 100vw;
  }
}
</style>
