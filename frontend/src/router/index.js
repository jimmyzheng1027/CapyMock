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
    name: 'interview',
    component: () => import('@/pages/InterviewPage.vue'),
    meta: { title: '模拟面试 — CapyMock' },
  },
  {
    path: '/analysis/github',
    name: 'github',
    component: () => import('@/pages/GitHubPage.vue'),
    meta: { title: 'GitHub 源码分析 — CapyMock' },
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
