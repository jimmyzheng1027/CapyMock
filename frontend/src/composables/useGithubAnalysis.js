import { ref } from 'vue'
import { api } from '@/api/index.js'

const repos = ref([])
const currentRepo = ref(null)
const loading = ref(false)
const error = ref(null)

async function withLoading(fn) {
  loading.value = true
  error.value = null
  try {
    return await fn()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

export function useGithubAnalysis() {
  function fetchRepos() {
    return withLoading(async () => {
      repos.value = await api.getGithubRepos()
    })
  }

  function fetchRepo(id) {
    return withLoading(async () => {
      currentRepo.value = await api.getGithubRepo(id)
    })
  }

  function fetchDeepAnalysis(id) {
    return withLoading(async () => {
      currentRepo.value = await api.getGithubDeep(id)
    })
  }

  function analyzeNewRepo(url) {
    return withLoading(async () => {
      const result = await api.analyzeGithub(url)
      await fetchRepos()
      return result
    })
  }

  return {
    repos,
    currentRepo,
    loading,
    error,
    fetchRepos,
    fetchRepo,
    fetchDeepAnalysis,
    analyzeNewRepo,
  }
}
