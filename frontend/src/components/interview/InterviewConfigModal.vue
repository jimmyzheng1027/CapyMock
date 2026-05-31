<script setup>
import { useInterviewConfig } from '@/composables/useInterviewConfig.js'

const props = defineProps({
  show: { type: Boolean, default: false }
})

const emit = defineEmits(['close'])

const {
  resumes,
  githubRepos,
  selectedGithubRepos,
  interviewTypes,
  selectedResume,
  selectedType,
  isConfigValid,
  starting,
  handleStartInterview: startInterview,
  handleGoToUpload,
  handleGoToAnalysis,
} = useInterviewConfig()

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

async function handleStartInterview() {
  await startInterview()
  emit('close')
}

function handleClose() {
  emit('close')
}
</script>

<template>
  <div v-if="show" class="modal-overlay" @click.self="handleClose">
    <div class="modal">
      <div class="modal__header">
        <div class="modal__header-left">
          <div class="modal__icon">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
              <rect x="4" y="3" width="14" height="16" rx="2" stroke="#E8937A" stroke-width="1.8"/>
              <circle cx="11" cy="9" r="3" stroke="#E8937A" stroke-width="1.3"/>
              <path d="M6 17c0-3 2.2-5 5-5s5 2 5 5" stroke="#E8937A" stroke-width="1.3" stroke-linecap="round"/>
            </svg>
          </div>
          <div>
            <h2 class="modal__title">面试配置</h2>
            <p class="modal__subtitle">选择简历和面试类型，开始你的模拟面试</p>
          </div>
        </div>
        <button class="modal__close" @click="handleClose">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <div class="modal__content">
        <div class="config-step">
          <div class="config-step__header">
            <div class="config-step__number">1</div>
            <span class="config-step__title">选择简历（必选）</span>
          </div>

          <div v-if="resumes.length > 0" class="config-step__options">
            <label
              v-for="resume in resumes"
              :key="resume.id"
              class="config-option"
              :class="{ 'config-option--selected': selectedResume === resume.id }"
            >
              <input
                type="radio"
                :value="resume.id"
                v-model="selectedResume"
                class="config-option__radio"
              />
              <div class="config-option__content">
                <div class="config-option__name">{{ resume.file_name }}</div>
                <div class="config-option__desc">{{ resume.file_type?.toUpperCase() }} · 上传于 {{ formatDate(resume.created_at) }}</div>
              </div>
            </label>
          </div>

          <div v-else class="config-step__empty">
            <p class="text-sm text-ink-muted mb-2">暂无已上传的简历</p>
            <button class="text-sm text-primary hover:underline" @click="handleGoToUpload">去上传 →</button>
          </div>
        </div>

        <div class="config-step">
          <div class="config-step__header">
            <div class="config-step__number">2</div>
            <span class="config-step__title">面试类型</span>
          </div>

          <div class="config-step__options">
            <label
              v-for="type in interviewTypes"
              :key="type.id"
              class="config-option"
              :class="{ 'config-option--selected': selectedType === type.id }"
            >
              <input
                type="radio"
                :value="type.id"
                v-model="selectedType"
                class="config-option__radio"
              />
              <div class="config-option__content">
                <div class="config-option__name">{{ type.label }}</div>
                <div class="config-option__desc">{{ type.description }}</div>
              </div>
            </label>
          </div>
        </div>

        <div class="config-step">
          <div class="config-step__header">
            <div class="config-step__number">3</div>
            <span class="config-step__title">GitHub 仓库（可选）</span>
          </div>
          <p class="config-step__hint">选择已分析的仓库，让面试官了解你的项目经验</p>

          <div v-if="githubRepos.length > 0" class="config-step__options">
            <label
              v-for="repo in githubRepos"
              :key="repo.id"
              class="config-option"
              :class="{ 'config-option--selected': selectedGithubRepos.includes(repo.id) }"
            >
              <input
                type="checkbox"
                :value="repo.id"
                v-model="selectedGithubRepos"
                class="config-option__checkbox"
              />
              <div class="config-option__content">
                <div class="config-option__name">{{ repo.fullName }}</div>
                <div class="config-option__desc">{{ repo.description || '暂无描述' }}</div>
              </div>
            </label>
          </div>

          <div v-else class="config-step__empty">
            <p class="text-sm text-ink-muted mb-2">暂无已分析的仓库</p>
            <button class="text-sm text-primary hover:underline" @click="handleGoToAnalysis">去分析 →</button>
          </div>
        </div>
      </div>

      <div class="modal__footer">
        <p v-if="!isConfigValid" class="modal__hint">请选择简历和面试类型后开始面试</p>
        <div class="modal__actions">
          <button class="modal-btn modal-btn--secondary" @click="handleClose">取消</button>
          <button
            class="modal-btn modal-btn--primary"
            :disabled="!isConfigValid"
            :class="{ 'opacity-50 cursor-not-allowed': !isConfigValid }"
            @click="handleStartInterview"
          >
            开始面试 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  padding: var(--space-4);
}

.modal {
  background: var(--color-white);
  border-radius: var(--radius-2xl);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: var(--shadow-xl);
  animation: modalIn 0.3s var(--ease-out) both;
}

@keyframes modalIn {
  from { opacity: 0; transform: scale(0.95) translateY(10px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: var(--space-6) var(--space-6) var(--space-4);
}

.modal__header-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.modal__icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-lg);
  background: linear-gradient(135deg, #fce4dc, #f5d8cc);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.modal__title {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-ink);
  font-family: var(--font-heading);
}

.modal__subtitle {
  font-size: var(--text-sm);
  color: var(--color-ink-muted);
  margin-top: 2px;
}

.modal__close {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-ink-muted);
  transition: all var(--duration-fast) var(--ease-out);
}

.modal__close:hover {
  background: var(--color-surface);
  color: var(--color-ink);
}

.modal__content {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-6) var(--space-4);
}

.config-step {
  margin-bottom: var(--space-5);
}

.config-step:last-child {
  margin-bottom: 0;
}

.config-step__header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.config-step__number {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  background: var(--color-primary);
  color: var(--color-white);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--text-xs);
  font-weight: 700;
  flex-shrink: 0;
}

.config-step__title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-ink);
}

.config-step__options {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.config-step__empty {
  text-align: center;
  padding: var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
}

.config-step__hint {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  margin-top: var(--space-2);
}

.config-option {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border: 1.5px solid var(--color-border-light);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration-fast) var(--ease-out);
}

.config-option:hover {
  border-color: var(--color-primary-light);
}

.config-option--selected {
  border-color: var(--color-primary);
  background: rgba(196, 149, 106, 0.05);
}

.config-option__radio,
.config-option__checkbox {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
  flex-shrink: 0;
}

.config-option__content {
  flex: 1;
  min-width: 0;
}

.config-option__name {
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-ink);
}

.config-option__desc {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  margin-top: 2px;
}

.modal__footer {
  padding: var(--space-4) var(--space-6) var(--space-6);
  border-top: 1px solid var(--color-border-light);
}

.modal__hint {
  font-size: var(--text-xs);
  color: var(--color-ink-muted);
  text-align: center;
  margin-bottom: var(--space-4);
}

.modal__actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

.modal-btn {
  padding: var(--space-2) var(--space-5);
  font-size: var(--text-sm);
  font-weight: 500;
  border-radius: var(--radius-lg);
  transition: all var(--duration-fast) var(--ease-out);
}

.modal-btn--secondary {
  color: var(--color-ink-muted);
  border: 1px solid var(--color-border-light);
}

.modal-btn--secondary:hover {
  background: var(--color-surface);
  color: var(--color-ink);
}

.modal-btn--primary {
  background: var(--color-primary);
  color: var(--color-white);
}

.modal-btn--primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

:global(.dark) .modal {
  background: var(--color-surface);
}

:global(.dark) .config-option {
  border-color: var(--color-border);
}

:global(.dark) .config-option--selected {
  border-color: var(--color-primary);
  background: rgba(196, 149, 106, 0.1);
}

@media (max-width: 640px) {
  .modal {
    max-height: 95vh;
  }

  .modal__header,
  .modal__content,
  .modal__footer {
    padding-left: var(--space-4);
    padding-right: var(--space-4);
  }
}
</style>
