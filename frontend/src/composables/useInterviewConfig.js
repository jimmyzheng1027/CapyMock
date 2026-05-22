import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

export function useInterviewConfig() {
  const router = useRouter()

  const resumes = ref([
    { id: 1, name: '前端工程师_简历.pdf', date: '2026-05-20' },
    { id: 2, name: '我的简历_v2.pdf', date: '2026-05-18' }
  ])

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
    handleGoToAnalysis
  }
}
