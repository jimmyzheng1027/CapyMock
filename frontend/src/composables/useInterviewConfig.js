import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '@/api/index.js'

export function useInterviewConfig() {
  const router = useRouter()

  const resumes = ref([])
  const resumesLoading = ref(false)

  const projects = ref([
    { id: 1, name: 'job-seeker-assistant', tech: 'Vue', analyzed: true },
    { id: 2, name: 'my-portfolio', tech: 'HTML', analyzed: true },
    { id: 3, name: 'data-pipeline', tech: 'Python', analyzed: false }
  ])

  const interviewTypes = [
    { id: 'technical', label: '技术面试', description: '深入技术细节和项目实现' },
    { id: 'behavioral', label: '行为面试', description: '软技能、团队协作、问题解决' },
    { id: 'comprehensive', label: '综合面试', description: '两者结合' }
  ]

  const selectedResume = ref(null)
  const selectedProjects = ref([])
  const selectedType = ref('comprehensive')

  const isConfigValid = computed(() => {
    return selectedResume.value !== null && selectedType.value !== null
  })

  const analyzedProjects = computed(() => {
    return projects.value.filter(p => p.analyzed)
  })

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
  })

  function toggleProject(projectId) {
    const index = selectedProjects.value.indexOf(projectId)
    if (index === -1) {
      selectedProjects.value.push(projectId)
    } else {
      selectedProjects.value.splice(index, 1)
    }
  }

  function handleStartInterview() {
    if (!isConfigValid.value) return

    const interviewId = Date.now()
    router.push(`/interview/${interviewId}?type=${selectedType.value}&resume=${encodeURIComponent(selectedResume.value)}&projects=${selectedProjects.value.join(',')}`)
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
    projects,
    interviewTypes,
    selectedResume,
    selectedProjects,
    selectedType,
    isConfigValid,
    analyzedProjects,
    toggleProject,
    handleStartInterview,
    handleGoToUpload,
    handleGoToAnalysis,
    loadResumes,
  }
}
