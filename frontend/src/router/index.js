import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/HomePage.vue'),
    meta: { title: 'CapyMock — AI 求职助手' },
  },
  {
    path: '/interview',
    name: 'interview-list',
    component: () => import('@/pages/InterviewListPage.vue'),
    meta: { title: '模拟面试 — CapyMock' },
  },
  {
    path: '/interview/config',
    name: 'interview-config',
    component: () => import('@/pages/InterviewConfigPage.vue'),
    meta: { title: '面试配置 — CapyMock' },
  },
  {
    path: '/interview/:id/summary',
    name: 'interview-summary',
    component: () => import('@/pages/InterviewSummaryPage.vue'),
    meta: { title: '面试总结 — CapyMock' },
  },
  {
    path: '/interview/:id',
    name: 'interview-session',
    component: () => import('@/pages/InterviewSessionPage.vue'),
    meta: { title: '模拟面试 — CapyMock' },
  },
  {
    path: '/analysis/github',
    component: () => import('@/layouts/GitHubLayout.vue'),
    meta: { title: 'GitHub 源码分析 — CapyMock' },
    children: [
      { path: '', name: 'github-list', component: () => import('@/pages/github/GitHubListPage.vue') },
      { path: ':id', name: 'github-overview', component: () => import('@/pages/github/GitHubOverviewPage.vue'), meta: { title: '仓库概览 — CapyMock' } },
      { path: ':id/deep', name: 'github-deep', component: () => import('@/pages/github/GitHubDeepPage.vue'), meta: { title: '深度分析 — CapyMock' } },
    ],
  },
  {
    path: '/analysis/jd',
    name: 'jd',
    component: () => import('@/pages/JdPage.vue'),
    meta: { title: 'JD 智能分析 — CapyMock' },
  },
  {
    path: '/analysis/resume',
    name: 'resume',
    component: () => import('@/pages/ResumePage.vue'),
    meta: { title: '简历匹配分析 — CapyMock' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  document.title = to.meta.title || 'CapyMock'
})

export default router
