/**
 * API service layer
 * GitHub analysis uses real backend; other endpoints use mock adapter.
 */

import { mockAdapter } from './mock.js'

// Mock adapter for non-GitHub endpoints
async function mockRequest(path, options = {}) {
  await new Promise((r) => setTimeout(r, 2000))
  return mockAdapter(path, options)
}

// Real API call to FastAPI backend
async function realRequest(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail || `API error: ${res.status}`
    throw new Error(detail)
  }
  return res.json()
}

export const api = {
  // GitHub analysis (real backend)
  analyzeGithub(url) {
    return realRequest('/analysis', {
      method: 'POST',
      body: JSON.stringify({ repo_url: url }),
    })
  },

  getGithubRepos() {
    return realRequest('/analysis')
  },

  getGithubRepo(id) {
    return realRequest(`/analysis/${id}`)
  },

  getGithubDeep(id) {
    return realRequest(`/analysis/${id}`)
  },

  // Task progress (real backend)
  getTaskStatus(taskId) {
    return realRequest(`/tasks/${taskId}`)
  },

  getTaskStreamUrl(taskId) {
    return `/api/tasks/${taskId}/stream`
  },

  // JD analysis (real backend)
  analyzeJd(text) {
    return realRequest('/jd/analyze', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  // Resume CRUD (real backend)
  getResumes(userId = 'default') {
    return realRequest(`/resumes?user_id=${encodeURIComponent(userId)}`)
  },

  getResume(resumeId) {
    return realRequest(`/resumes/${resumeId}`)
  },

  async uploadResume(file, userId = 'default') {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('user_id', userId)
    const res = await fetch('/api/resumes/upload', {
      method: 'POST',
      body: formData,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: `Upload failed: ${res.status}` }))
      throw new Error(err.detail || `Upload failed: ${res.status}`)
    }
    return res.json()
  },

  deleteResume(resumeId) {
    return realRequest(`/resumes/${resumeId}`, { method: 'DELETE' })
  },

  analyzeResume(resumeId, force = false) {
    return realRequest(`/resumes/${resumeId}/analyze?force=${force}`, {
      method: 'POST',
    })
  },

  // Interview - get AI response (mock)
  getInterviewReply(messages, type) {
    return mockRequest('/interview/reply', {
      method: 'POST',
      body: JSON.stringify({ messages, type }),
    })
  },
}
