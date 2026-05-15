/**
 * API service layer
 * Currently using mock adapter. Switch to real adapter when FastAPI backend is ready.
 */

import { mockAdapter } from './mock.js'

const USE_MOCK = true

async function request(path, options = {}) {
  if (USE_MOCK) {
    await new Promise((r) => setTimeout(r, 2000))
    return mockAdapter(path, options)
  }

  // Real API call (to be implemented with FastAPI)
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json()
}

export const api = {
  // GitHub analysis
  analyzeGithub(url) {
    return request('/analysis/github', {
      method: 'POST',
      body: JSON.stringify({ url }),
    })
  },

  // JD analysis
  analyzeJd(text) {
    return request('/analysis/jd', {
      method: 'POST',
      body: JSON.stringify({ text }),
    })
  },

  // Resume analysis
  analyzeResume(file, position) {
    return request('/analysis/resume', {
      method: 'POST',
      body: JSON.stringify({ fileName: file.name, fileSize: file.size, position }),
    })
  },

  // Interview - get AI response
  getInterviewReply(messages, type) {
    return request('/interview/reply', {
      method: 'POST',
      body: JSON.stringify({ messages, type }),
    })
  },
}
