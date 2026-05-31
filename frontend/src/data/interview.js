export const INTERVIEW_TYPES = {
  technical: '技术面试',
  behavioral: '行为面试',
  hr: 'HR 面试',
  comprehensive: '综合面试'
}

export const PROFILE_TO_TYPE = {
  'interviewer-technical': 'technical',
  'interviewer-behavior': 'behavioral',
  'interviewer-comprehensive': 'comprehensive',
}

export const TYPE_TO_PROFILE = Object.fromEntries(
  Object.entries(PROFILE_TO_TYPE).map(([k, v]) => [v, k])
)

export const INTERVIEW_STATUS = {
  completed: '已完成',
  paused: '已暂停'
}

export const STATUS_COLORS = {
  completed: 'bg-green-100 text-green-700',
  paused: 'bg-yellow-100 text-yellow-700'
}
