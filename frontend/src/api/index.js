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
  if (!res.ok) throw new Error(`API error: ${res.status}`)
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

  // JD analysis (mock)
  analyzeJd(text) {
    return mockRequest('/analysis/jd', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  // Resume analysis (mock)
  analyzeResume(file, position) {
    return mockRequest('/analysis/resume', {
      method: 'POST',
      body: JSON.stringify({ fileName: file.name, fileSize: file.size, position }),
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
