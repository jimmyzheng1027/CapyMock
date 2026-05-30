<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGithubAnalysis } from '@/composables/useGithubAnalysis.js'
import RepoCard from '@/components/github/RepoCard.vue'
import AddRepoCard from '@/components/github/AddRepoCard.vue'
import EmptyState from '@/components/github/EmptyState.vue'
import LoadingOverlay from '@/components/common/LoadingOverlay.vue'

const router = useRouter()
const { repos, loading, activeTaskId, fetchRepos, analyzeNewRepo, reconnectTask } = useGithubAnalysis()
const addRepoRef = ref(null)

onMounted(async () => {
  await fetchRepos()
  if (activeTaskId.value) {
    reconnectTask(activeTaskId.value)
  }
})

async function handleAnalyzed(url) {
  const result = await analyzeNewRepo(url)
  if (result?.id) {
    router.push(`/analysis/github/${result.id}`)
  }
}

function triggerAdd() {
  addRepoRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <div>
    <!-- Header -->
    <div class="mb-6">
      <h2 class="text-xl font-bold text-ink">GitHub 源码分析</h2>
      <p class="text-sm text-ink-muted mt-1">管理你分析过的代码仓库，随时回顾和深入研究</p>
    </div>

    <!-- Empty state -->
    <EmptyState v-if="repos.length === 0 && !loading" @add="triggerAdd" />

    <!-- Repo grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <RepoCard v-for="repo in repos" :key="repo.id" :repo="repo" @retry="handleAnalyzed" />
    </div>

    <!-- Add repo card (always visible) -->
    <div ref="addRepoRef" :class="repos.length > 0 ? 'mt-4' : 'mt-0'">
      <AddRepoCard @analyzed="handleAnalyzed" />
    </div>

    <LoadingOverlay
      :active="loading"
      text="正在加载"
      subtext="Capy 正在获取数据..."
    />
  </div>
</template>
