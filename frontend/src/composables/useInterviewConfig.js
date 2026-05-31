import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/index.js'
import { TYPE_TO_PROFILE } from '@/data/interview.js'

export function useInterviewConfig() {
  const router = useRouter()

  const resumes = ref([])
  const resumesLoading = ref(false)
  const githubRepos = ref([])
  const reposLoading = ref(false)
  const starting = ref(false)

  const interviewTypes = [
    { id: 'technical', label: '技术面试', description: '深入技术细节和项目实现' },
    { id: 'behavioral', label: '行为面试', description: '软技能、团队协作、问题解决' },
    { id: 'comprehensive', label: '综合面试', description: '两者结合' }
  ]

  const selectedResume = ref(null)
  const selectedType = ref('comprehensive')
  const selectedGithubRepos = ref([])

  const isConfigValid = computed(() => {
    return selectedResume.value !== null && selectedType.value !== null
  })

  // Load GitHub repos from API
  async function loadGithubRepos() {
    reposLoading.value = true
    try {
      const data = await api.getGithubRepos()
      githubRepos.value = data
    } catch (e) {
      console.error('Failed to load GitHub repos:', e)
      githubRepos.value = []
    } finally {
      reposLoading.value = false
    }
  }

  // Load resumes from API
  async function loadResumes() {
    resumesLoading.value = true
    try {
      const data = await api.getResumes()
      resumes.value = data
    } catch (e) {
      console.error('Failed to load resumes:', e)
      resumes.value = []
    } finally {
      resumesLoading.value = false
    }
  }

  // Load on mount
  onMounted(() => {
    loadResumes()
    loadGithubRepos()
  })

  async function handleStartInterview() {
    if (!isConfigValid.value || starting.value) return
    starting.value = true

    try {
      const profileId = TYPE_TO_PROFILE[selectedType.value]
      const result = await api.createSession({
        profileId,
        mode: 'text',
        resumeId: selectedResume.value,
        githubRepoIds: selectedGithubRepos.value,
      })
      router.push(`/interview/${result.session_id}?type=${selectedType.value}`)
    } catch (e) {
      console.error('Failed to create session:', e)
      alert('创建面试会话失败，请重试')
    } finally {
      starting.value = false
    }
  }

  function handleGoToUpload() {
    router.push('/analysis/resume')
  }

  function handleGoToAnalysis() {
    router.push('/analysis/github')
  }

  return {
    resumes,
    resumesLoading,
    githubRepos,
    reposLoading,
    selectedGithubRepos,
    interviewTypes,
    selectedResume,
    selectedType,
    isConfigValid,
    starting,
    handleStartInterview,
    handleGoToUpload,
    handleGoToAnalysis,
    loadResumes,
    loadGithubRepos,
  }
}
