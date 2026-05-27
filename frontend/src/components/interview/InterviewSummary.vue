<script setup>
import SectionCard from '@/components/common/SectionCard.vue'
import ChatBubble from '@/components/interview/ChatBubble.vue'
import { INTERVIEW_TYPES } from '@/data/interview.js'

defineProps({
  summary: { type: Object, required: true }
})

const emit = defineEmits(['download', 'new-interview', 'back-to-list'])
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-6">
      <h2 class="text-xl font-bold text-ink">面试总结</h2>
      <div class="flex items-center gap-2">
        <button
          class="px-4 py-2 text-sm rounded-lg border border-border-light dark:border-border hover:bg-surface transition-colors"
          @click="emit('back-to-list')"
        >
          返回列表
        </button>
        <button
          class="btn btn--primary px-4 py-2 text-sm"
          @click="emit('new-interview')"
        >
          再来一轮
        </button>
      </div>
    </div>

    <SectionCard icon="list" title="面试概览" class="mb-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div>
          <div class="text-xs text-ink-muted mb-1">类型</div>
          <div class="text-sm font-medium text-ink">{{ INTERVIEW_TYPES[summary.overview.type] }}</div>
        </div>
        <div>
          <div class="text-xs text-ink-muted mb-1">时长</div>
          <div class="text-sm font-medium text-ink">{{ summary.overview.duration }}分钟</div>
        </div>
        <div>
          <div class="text-xs text-ink-muted mb-1">问题数</div>
          <div class="text-sm font-medium text-ink">{{ summary.overview.questionCount }}个</div>
        </div>
        <div>
          <div class="text-xs text-ink-muted mb-1">简历</div>
          <div class="text-sm font-medium text-ink">{{ summary.overview.resume }}</div>
        </div>
      </div>
      <div v-if="summary.overview.projects?.length > 0" class="mt-4">
        <div class="text-xs text-ink-muted mb-1">项目</div>
        <div class="flex flex-wrap gap-2">
          <span
            v-for="project in summary.overview.projects"
            :key="project"
            class="px-2 py-1 rounded-full text-xs bg-primary/10 text-primary"
          >
            {{ project }}
          </span>
        </div>
      </div>
    </SectionCard>

    <SectionCard icon="check" title="回答亮点" class="mb-4">
      <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
        <li v-for="(highlight, i) in summary.highlights" :key="i" class="mb-2 marker:text-primary">
          {{ highlight }}
        </li>
      </ul>
    </SectionCard>

    <SectionCard icon="info" title="改进建议" class="mb-4">
      <ul class="pl-5 m-0 text-sm text-ink-light leading-relaxed">
        <li v-for="(improvement, i) in summary.improvements" :key="i" class="mb-2 marker:text-primary">
          {{ improvement }}
        </li>
      </ul>
    </SectionCard>

    <SectionCard icon="list" title="完整对话记录" class="mb-6">
      <details>
        <summary class="text-sm font-medium text-ink cursor-pointer">点击展开查看完整对话</summary>
        <div class="mt-4 space-y-3 max-h-96 overflow-y-auto">
          <ChatBubble v-for="msg in summary.messages" :key="msg.id" :message="msg" />
        </div>
      </details>
    </SectionCard>

    <div class="flex justify-center">
      <button class="btn btn--primary px-6 py-3" @click="emit('download')">
        下载总结
      </button>
    </div>
  </div>
</template>
