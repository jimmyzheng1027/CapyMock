<script setup>
import AnalysisLayout from '@/layouts/AnalysisLayout.vue'
import { useInterviewConfig } from '@/composables/useInterviewConfig.js'

const {
  resumes,
  interviewTypes,
  selectedResume,
  selectedProjects,
  selectedType,
  isConfigValid,
  analyzedProjects,
  toggleProject,
  handleStartInterview,
  handleGoToUpload,
  handleGoToAnalysis
} = useInterviewConfig()
</script>

<template>
  <AnalysisLayout>
    <div class="mb-6">
      <div class="flex items-center gap-3 mb-2">
        <router-link
          to="/interview"
          class="flex items-center justify-center w-9 h-9 rounded-full hover:bg-surface transition-colors"
          style="color: var(--color-ink-light)"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M12 4l-6 6 6 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </router-link>
        <h2 class="text-xl font-bold text-ink">面试配置</h2>
      </div>
      <p class="text-sm text-ink-muted ml-12">选择简历和项目，开始你的模拟面试</p>
    </div>

    <div class="space-y-6">
      <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold text-ink">
          <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold">1</div>
          <span>选择简历（必选）</span>
        </div>

        <div v-if="resumes.length > 0" class="space-y-3">
          <label
            v-for="resume in resumes"
            :key="resume.id"
            class="flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all"
            :class="selectedResume === resume.id ? 'border-primary bg-primary/5' : 'border-border-light dark:border-border hover:border-primary/50'"
          >
            <input type="radio" :value="resume.id" v-model="selectedResume" class="w-4 h-4 text-primary" />
            <div class="flex-1">
              <div class="font-medium text-ink">{{ resume.name }}</div>
              <div class="text-xs text-ink-muted">上传于 {{ resume.date }}</div>
            </div>
          </label>
        </div>

        <div v-else class="text-center py-6">
          <p class="text-sm text-ink-muted mb-3">暂无已上传的简历</p>
          <button class="text-sm text-primary hover:underline" @click="handleGoToUpload">去上传 →</button>
        </div>
      </div>

      <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold text-ink">
          <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold">2</div>
          <span>选择GitHub项目（可选，可多选）</span>
        </div>

        <div v-if="analyzedProjects.length > 0" class="space-y-3">
          <label
            v-for="project in analyzedProjects"
            :key="project.id"
            class="flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all"
            :class="selectedProjects.includes(project.id) ? 'border-primary bg-primary/5' : 'border-border-light dark:border-border hover:border-primary/50'"
          >
            <input
              type="checkbox"
              :value="project.id"
              :checked="selectedProjects.includes(project.id)"
              @change="toggleProject(project.id)"
              class="w-4 h-4 text-primary"
            />
            <div class="flex-1">
              <div class="font-medium text-ink">{{ project.name }}</div>
              <div class="text-xs text-ink-muted">{{ project.tech }} · 已分析</div>
            </div>
          </label>
        </div>

        <div v-else class="text-center py-6">
          <p class="text-sm text-ink-muted mb-3">暂无已分析的GitHub项目</p>
          <button class="text-sm text-primary hover:underline" @click="handleGoToAnalysis">去分析 →</button>
        </div>

        <p v-if="analyzedProjects.length > 0" class="text-xs text-ink-muted mt-3">
          不选择项目时，面试将仅基于简历进行
        </p>
      </div>

      <div class="bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold text-ink">
          <div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-bold">3</div>
          <span>面试类型</span>
        </div>

        <div class="space-y-3">
          <label
            v-for="type in interviewTypes"
            :key="type.id"
            class="flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-all"
            :class="selectedType === type.id ? 'border-primary bg-primary/5' : 'border-border-light dark:border-border hover:border-primary/50'"
          >
            <input type="radio" :value="type.id" v-model="selectedType" class="w-4 h-4 text-primary" />
            <div>
              <div class="font-medium text-ink">{{ type.label }}</div>
              <div class="text-sm text-ink-muted">{{ type.description }}</div>
            </div>
          </label>
        </div>
      </div>

      <div class="flex justify-end pt-4">
        <button
          class="btn btn--primary px-8 py-3 text-base"
          :disabled="!isConfigValid"
          :class="{ 'opacity-50 cursor-not-allowed': !isConfigValid }"
          @click="handleStartInterview"
        >
          开始面试 →
        </button>
      </div>

      <p v-if="!isConfigValid" class="text-sm text-ink-muted text-center">
        请选择简历和面试类型后开始面试
      </p>
    </div>
  </AnalysisLayout>
</template>
