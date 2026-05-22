<script setup>
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGithubAnalysis } from '@/composables/useGithubAnalysis.js'
import ScoreRing from '@/components/common/ScoreRing.vue'
import TechStackTags from '@/components/github/TechStackTags.vue'
import DirectoryTree from '@/components/github/DirectoryTree.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

const route = useRoute()
const { currentRepo: repo, loading, fetchRepo } = useGithubAnalysis()

onMounted(() => {
  fetchRepo(route.params.id)
})
</script>

<template>
  <div>
    <!-- Back button -->
    <router-link
      to="/analysis/github"
      class="inline-flex items-center gap-2 text-sm text-ink-muted hover:text-primary transition-colors mb-6 no-underline"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      返回仓库列表
    </router-link>

    <div v-if="repo" class="animate-fade-in">
      <!-- Repo header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <h2 class="text-xl font-bold text-ink">{{ repo.fullName }}</h2>
          <p class="text-sm text-ink-muted mt-1">{{ repo.description }}</p>
        </div>
        <a
          :href="repo.url"
          target="_blank"
          rel="noopener"
          class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border border-border dark:border-border bg-white dark:bg-surface text-ink-light hover:border-primary hover:text-primary transition-theme no-underline"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M5.5 8.5l3-3M4.5 5.5h-2v6h6v-2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          GitHub
        </a>
      </div>

      <!-- Score -->
      <ScoreRing
        :score="repo.score"
        label="项目综合评分"
        :summary="`仓库 ${repo.fullName} 综合评估`"
      />

      <!-- Tech Stack -->
      <div class="mt-6">
        <TechStackTags :tags="repo.techTags" />
      </div>

      <!-- Directory Tree -->
      <div v-if="repo.directoryTree" class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary">
            <path d="M3 5c0-.6.4-1 1-1h2l1.5 2h6.5c.6 0 1 .4 1 1v6c0 .6-.4 1-1 1H4c-.6 0-1-.4-1-1V5z" stroke="currentColor" stroke-width="1.3"/>
          </svg>
          项目结构
        </div>
        <DirectoryTree :node="repo.directoryTree" />
      </div>

      <!-- Highlights & Suggestions -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><path d="M9 2l2.1 4.3 4.7.7-3.4 3.3.8 4.7L9 12.8l-4.2 2.2.8-4.7L2.2 7l4.7-.7z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/></svg>
          项目亮点 & 改进建议
        </div>
        <div class="text-sm text-ink-light leading-relaxed">
          <ul class="pl-5 m-0">
            <li v-for="(h, i) in repo.highlights" :key="i" class="mb-2 marker:text-primary">
              <strong class="text-ink">{{ h.text.split('：')[0] }}：</strong>{{ h.text.split('：')[1] }}
            </li>
          </ul>
          <div class="mt-4 font-semibold text-primary">改进建议：</div>
          <ul class="pl-5 m-0 mt-2">
            <li v-for="(s, i) in repo.suggestions" :key="i" class="mb-2 marker:text-primary">{{ s }}</li>
          </ul>
        </div>
      </div>

      <!-- Interview Questions -->
      <div class="mt-4 bg-white dark:bg-surface border border-border-light dark:border-border rounded-xl p-6">
        <div class="flex items-center gap-2 mb-4 font-semibold">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="text-primary"><circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.3"/><path d="M7 7.5a2 2 0 0 1 3.3 1.3c0 1-1.3 1.2-1.3 2.2" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/><circle cx="9.2" cy="13" r="0.8" fill="currentColor"/></svg>
          面试问题
        </div>
        <div class="flex flex-col gap-4">
          <div v-for="(qa, i) in repo.questions" :key="i" class="p-5 bg-surface dark:bg-surface-alt rounded-xl border-l-[3px] border-primary">
            <div class="font-semibold text-sm text-ink mb-3">{{ qa.q }}</div>
            <div class="text-sm text-ink-light leading-relaxed pl-4 border-l-2 border-border-light dark:border-border">{{ qa.a }}</div>
          </div>
        </div>
      </div>

      <!-- Deep Analysis CTA -->
      <div class="mt-6 flex justify-center">
        <router-link
          :to="`/analysis/github/${repo.id}/deep`"
          class="btn btn--primary text-sm"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 3h12M2 8h8M2 13h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          查看深度分析报告
        </router-link>
      </div>
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在加载仓库数据"
      subtext="Capy 正在整理分析结果..."
    />
  </div>
</template>
