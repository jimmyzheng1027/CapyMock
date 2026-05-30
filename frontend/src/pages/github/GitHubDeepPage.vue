<script setup>
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useGithubAnalysis } from '@/composables/useGithubAnalysis.js'
import ReportSection from '@/components/github/ReportSection.vue'
import CodeSnippet from '@/components/github/CodeSnippet.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

const route = useRoute()
const { currentRepo, loading, phase, progressMessage, fetchDeepAnalysis } = useGithubAnalysis()

const activeSection = ref('')
let observer = null

onMounted(() => {
  fetchDeepAnalysis(route.params.id)
})

const repo = computed(() => currentRepo.value)
const sections = computed(() => repo.value?.sections || [])
const codeSnippets = computed(() => repo.value?.codeSnippets || [])

function setupObserver() {
  if (observer) observer.disconnect()

  const sectionIds = sections.value.map((s) => s.id)
  if (sectionIds.length === 0) return

  activeSection.value = sectionIds[0]

  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          activeSection.value = entry.target.id
        }
      }
    },
    { rootMargin: '-20% 0px -70% 0px' }
  )

  for (const id of sectionIds) {
    const el = document.getElementById(id)
    if (el) observer.observe(el)
  }
}

// Watch for data to be loaded, then setup observer
import { watch } from 'vue'
watch(
  () => repo.value?.sections,
  (val) => {
    if (val?.length) {
      // Wait for DOM to render
      setTimeout(setupObserver, 100)
    }
  }
)

onUnmounted(() => {
  if (observer) observer.disconnect()
})

function scrollToSection(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}
</script>

<template>
  <div>
    <!-- Back button -->
    <router-link
      :to="`/analysis/github/${route.params.id}`"
      class="inline-flex items-center gap-2 text-sm text-ink-muted hover:text-primary transition-colors mb-6 no-underline"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M10 3L5 8l5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
      返回概览
    </router-link>

    <div v-if="repo && repo.status !== 'failed'" class="animate-fade-in">
      <!-- Repo header (compact) -->
      <div class="flex items-center gap-3 mb-6">
        <h2 class="text-xl font-bold text-ink">{{ repo.fullName }}</h2>
        <div
          v-if="repo.score"
          class="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white"
          :style="{
            background: repo.score >= 80 ? 'var(--color-secondary)' : repo.score >= 60 ? 'var(--color-primary)' : 'var(--color-accent)',
          }"
        >
          {{ repo.score }}
        </div>
      </div>

      <!-- Sticky section nav -->
      <nav
        class="sticky z-30 -mx-2 px-2 py-2 mb-6 flex gap-1 overflow-x-auto"
        style="top: var(--nav-height); background: var(--color-base)"
      >
        <button
          v-for="section in sections"
          :key="section.id"
          class="shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-all whitespace-nowrap"
          :class="activeSection === section.id
            ? 'bg-primary text-white'
            : 'text-ink-muted hover:text-ink hover:bg-surface-alt'"
          @click="scrollToSection(section.id)"
        >
          {{ section.title }}
        </button>
      </nav>

      <!-- Report sections -->
      <div class="flex flex-col gap-4">
        <ReportSection
          v-for="section in sections"
          :key="section.id"
          :section="section"
        />
      </div>

      <!-- Code snippets -->
      <div v-if="codeSnippets.length > 0" class="mt-6">
        <h3 class="text-lg font-bold text-ink mb-4">核心代码解析</h3>
        <div class="flex flex-col gap-4">
          <CodeSnippet
            v-for="snippet in codeSnippets"
            :key="snippet.id"
            :code="snippet.code"
            :language="snippet.language"
            :title="snippet.title"
            :description="snippet.description"
          />
        </div>
      </div>
    </div>

    <LoadingOverlay
      :active="loading || phase === 'analyzing' || phase === 'submitting' || phase === 'fetching'"
      :text="phase === 'analyzing' ? '正在分析代码仓库' : '正在生成深度分析报告'"
      :subtext="progressMessage || 'Capy 正在深入阅读代码、生成分析...'"
    />
  </div>
</template>
