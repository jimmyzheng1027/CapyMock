import { interviewQuestions } from '@/data/interviewQuestions.js'

const techTags = ['React', 'TypeScript', 'Node.js', 'Vite', 'Tailwind CSS', 'Jest', 'REST API', 'Git']

const githubQuestions = [
  { q: '请介绍一下你在这个项目中使用的状态管理方案，为什么选择这个方案？', a: '建议从技术选型背景出发，对比 Redux/Zustand/Jotai 等方案的优劣，说明选择理由，并举一个具体使用场景。' },
  { q: '这个项目的架构设计是怎样的？如果让你重新设计，你会做哪些改动？', a: '先描述当前架构（目录结构、模块划分、数据流），再提出 2-3 个可改进的点，如：组件复用、测试覆盖、性能优化等。' },
  { q: '你在项目中遇到的最大技术挑战是什么？最终是怎么解决的？', a: '用 STAR 法则回答：Situation（背景）→ Task（任务）→ Action（你做了什么）→ Result（结果和收获）。重点突出你的思考过程。' },
  { q: '项目中有没有做过性能优化？具体用了哪些手段？', a: '可以从代码分割、懒加载、缓存策略、虚拟列表、图片优化等方面回答，配合具体数据（如加载时间减少 40%）会更有说服力。' },
  { q: '如果这个项目的用户量增长 10 倍，你会从哪些方面做架构升级？', a: '从 CDN、数据库分片、缓存层、微服务拆分、负载均衡等角度展开，展示你的系统设计思维。' },
]

// ─── GitHub Repository Mock Data ─────────────────────────────────────────

const githubRepos = [
  {
    id: 'react-todo-app',
    fullName: 'devuser/react-todo-app',
    owner: 'devuser',
    repoName: 'react-todo-app',
    description: 'A modern todo application built with React, TypeScript, and Zustand for state management',
    url: 'https://github.com/devuser/react-todo-app',
    analyzedAt: '2025-05-20T10:30:00Z',
    score: 78,
    techTags: ['React', 'TypeScript', 'Zustand', 'Vite'],
  },
  {
    id: 'vue-dashboard',
    fullName: 'alice/vue-dashboard',
    owner: 'alice',
    repoName: 'vue-dashboard',
    description: 'Admin dashboard template with Vue 3, Pinia, and ECharts data visualization',
    url: 'https://github.com/alice/vue-dashboard',
    analyzedAt: '2025-05-18T14:20:00Z',
    score: 85,
    techTags: ['Vue 3', 'Pinia', 'ECharts', 'Tailwind CSS'],
  },
  {
    id: 'rust-cli-tool',
    fullName: 'bob/rust-cli-tool',
    owner: 'bob',
    repoName: 'rust-cli-tool',
    description: 'A fast CLI tool for processing CSV files, written in Rust with clap for argument parsing',
    url: 'https://github.com/bob/rust-cli-tool',
    analyzedAt: '2025-05-15T09:00:00Z',
    score: 72,
    techTags: ['Rust', 'clap', 'serde', 'CSV'],
  },
]

const directoryTrees = {
  'react-todo-app': {
    name: 'react-todo-app',
    type: 'folder',
    expanded: true,
    children: [
      {
        name: 'src',
        type: 'folder',
        children: [
          {
            name: 'components',
            type: 'folder',
            children: [
              { name: 'TodoList.tsx', type: 'file', language: 'tsx' },
              { name: 'TodoItem.tsx', type: 'file', language: 'tsx' },
              { name: 'AddTodo.tsx', type: 'file', language: 'tsx' },
            ],
          },
          {
            name: 'hooks',
            type: 'folder',
            children: [
              { name: 'useTodos.ts', type: 'file', language: 'ts' },
            ],
          },
          {
            name: 'store',
            type: 'folder',
            children: [
              { name: 'todoStore.ts', type: 'file', language: 'ts' },
            ],
          },
          { name: 'App.tsx', type: 'file', language: 'tsx' },
          { name: 'main.tsx', type: 'file', language: 'tsx' },
          { name: 'index.css', type: 'file', language: 'css' },
        ],
      },
      {
        name: 'public',
        type: 'folder',
        children: [
          { name: 'index.html', type: 'file', language: 'html' },
        ],
      },
      { name: 'package.json', type: 'file', language: 'json' },
      { name: 'tsconfig.json', type: 'file', language: 'json' },
      { name: 'vite.config.ts', type: 'file', language: 'ts' },
      { name: 'README.md', type: 'file', language: 'md' },
    ],
  },
  'vue-dashboard': {
    name: 'vue-dashboard',
    type: 'folder',
    expanded: true,
    children: [
      {
        name: 'src',
        type: 'folder',
        children: [
          {
            name: 'views',
            type: 'folder',
            children: [
              { name: 'Dashboard.vue', type: 'file', language: 'vue' },
              { name: 'Analytics.vue', type: 'file', language: 'vue' },
              { name: 'Settings.vue', type: 'file', language: 'vue' },
            ],
          },
          {
            name: 'components',
            type: 'folder',
            children: [
              { name: 'ChartCard.vue', type: 'file', language: 'vue' },
              { name: 'StatCard.vue', type: 'file', language: 'vue' },
              { name: 'Sidebar.vue', type: 'file', language: 'vue' },
            ],
          },
          {
            name: 'stores',
            type: 'folder',
            children: [
              { name: 'dashboard.ts', type: 'file', language: 'ts' },
              { name: 'user.ts', type: 'file', language: 'ts' },
            ],
          },
          {
            name: 'router',
            type: 'folder',
            children: [
              { name: 'index.ts', type: 'file', language: 'ts' },
            ],
          },
          { name: 'App.vue', type: 'file', language: 'vue' },
          { name: 'main.ts', type: 'file', language: 'ts' },
        ],
      },
      { name: 'package.json', type: 'file', language: 'json' },
      { name: 'vite.config.ts', type: 'file', language: 'ts' },
      { name: 'tailwind.config.js', type: 'file', language: 'js' },
      { name: 'README.md', type: 'file', language: 'md' },
    ],
  },
  'rust-cli-tool': {
    name: 'rust-cli-tool',
    type: 'folder',
    expanded: true,
    children: [
      {
        name: 'src',
        type: 'folder',
        children: [
          {
            name: 'commands',
            type: 'folder',
            children: [
              { name: 'convert.rs', type: 'file', language: 'rs' },
              { name: 'filter.rs', type: 'file', language: 'rs' },
              { name: 'stats.rs', type: 'file', language: 'rs' },
            ],
          },
          {
            name: 'utils',
            type: 'folder',
            children: [
              { name: 'csv_reader.rs', type: 'file', language: 'rs' },
              { name: 'output.rs', type: 'file', language: 'rs' },
            ],
          },
          { name: 'main.rs', type: 'file', language: 'rs' },
          { name: 'lib.rs', type: 'file', language: 'rs' },
        ],
      },
      { name: 'Cargo.toml', type: 'file', language: 'toml' },
      { name: 'Cargo.lock', type: 'file', language: 'toml' },
      { name: 'README.md', type: 'file', language: 'md' },
    ],
  },
}

const githubOverviewData = {
  'react-todo-app': {
    ...githubRepos[0],
    techTags: ['React', 'TypeScript', 'Node.js', 'Vite', 'Tailwind CSS', 'Jest', 'REST API', 'Git'],
    directoryTree: directoryTrees['react-todo-app'],
    highlights: [
      { type: 'positive', text: '代码结构清晰：模块划分合理，目录组织遵循最佳实践' },
      { type: 'positive', text: '类型覆盖完整：TypeScript 使用规范，类型定义准确' },
      { type: 'positive', text: '测试覆盖良好：核心模块有单元测试覆盖' },
    ],
    suggestions: [
      '可以增加 E2E 测试覆盖关键用户路径',
      '部分组件可以进一步抽象复用',
      '建议添加 CI/CD 配置和代码质量检查',
    ],
    questions: githubQuestions,
  },
  'vue-dashboard': {
    ...githubRepos[1],
    techTags: ['Vue 3', 'TypeScript', 'Pinia', 'ECharts', 'Tailwind CSS', 'Vite', 'Vitest'],
    directoryTree: directoryTrees['vue-dashboard'],
    highlights: [
      { type: 'positive', text: '组件设计优秀：图表组件高度可复用，Props 接口设计合理' },
      { type: 'positive', text: '状态管理规范：Pinia store 按功能模块拆分，职责清晰' },
      { type: 'positive', text: '响应式布局：完美适配桌面端和移动端' },
    ],
    suggestions: [
      '建议增加主题切换功能（深色/浅色模式）',
      '图表组件可以支持更多数据源格式',
      '考虑添加数据导出功能（PDF/Excel）',
    ],
    questions: [
      { q: '你在项目中使用了 ECharts，能说说为什么选择它而不是其他图表库吗？', a: '可以从 ECharts 的生态丰富度、中文社区支持、性能表现等角度对比 D3.js、Chart.js、Recharts 等方案。' },
      { q: 'Pinia 和 Vuex 的区别是什么？你为什么选择 Pinia？', a: '重点对比 API 设计、TypeScript 支持、模块化方式、devtools 集成等方面。Pinia 是 Vue 官方推荐的新一代状态管理方案。' },
      { q: '这个项目的组件复用策略是怎样的？', a: '描述原子组件（按钮、卡片）→ 分子组件（图表卡片）→ 页面模板的分层复用模式，以及 Props/Slots 的设计原则。' },
      { q: '如果要支持实时数据更新，你会怎么改造这个项目？', a: '考虑 WebSocket / SSE 接入、数据缓存策略、图表增量更新、组件性能优化（虚拟滚动、防抖）等方面。' },
      { q: '说说你对响应式设计的理解，这个项目是怎么做的？', a: '描述 Tailwind 断点策略、容器查询、流式布局、图表自适应等具体实现方式。' },
    ],
  },
  'rust-cli-tool': {
    ...githubRepos[2],
    techTags: ['Rust', 'clap', 'serde', 'CSV', 'tokio', 'anyhow'],
    directoryTree: directoryTrees['rust-cli-tool'],
    highlights: [
      { type: 'positive', text: '性能出色：利用 Rust 零成本抽象，处理百万行 CSV 仅需数秒' },
      { type: 'positive', text: '错误处理规范：使用 anyhow 统一错误类型，用户友好的错误提示' },
      { type: 'positive', text: 'CLI 设计专业：clap 子命令设计清晰，帮助文档完善' },
    ],
    suggestions: [
      '可以添加并行处理支持（rayon 库）进一步提升大数据集处理速度',
      '建议增加配置文件支持，减少重复的命令行参数',
      '考虑添加 Shell 补全脚本生成',
    ],
    questions: [
      { q: 'Rust 的所有权机制在这个项目中是怎么体现的？', a: '用具体的代码示例说明借用、生命周期标注在 CSV 解析和数据处理中的应用。' },
      { q: '为什么选择 clap 而不是 structopt 或手动解析参数？', a: '对比三个方案的易用性、功能丰富度、社区活跃度。clap v4 的 derive macro 已经非常简洁。' },
      { q: '这个项目的错误处理策略是什么？', a: '描述 anyhow 用于应用层错误、thiserror 用于库层错误的分层策略，以及错误传播链的设计。' },
      { q: '如果要支持 JSON、Parquet 等更多格式，你会怎么扩展？', a: '设计 trait 抽象层，用策略模式实现格式无关的数据读写接口。' },
      { q: 'Rust 和 Go 在 CLI 工具开发上各有什么优劣？', a: '从编译速度、运行时开销、内存安全、生态成熟度、学习曲线等维度对比。' },
    ],
  },
}

const githubDeepAnalysisData = {
  'react-todo-app': {
    ...githubOverviewData['react-todo-app'],
    sections: [
      {
        id: 'architecture',
        title: '项目架构分析',
        icon: 'layers',
        content: `
          <h4>整体架构</h4>
          <p>项目采用了 <strong>组件化架构</strong>，遵循单一职责原则。目录结构清晰，按功能模块划分：components（UI 组件）、hooks（业务逻辑）、store（状态管理）。</p>
          <h4>数据流</h4>
          <p>使用 Zustand 进行全局状态管理，组件间通过 store 共享状态。异步操作统一在 hooks 层处理，保持组件的纯粹性。</p>
          <h4>路由设计</h4>
          <p>采用 React Router v6，路由按页面粒度划分，支持懒加载。嵌套路由用于布局复用。</p>
        `,
      },
      {
        id: 'code-quality',
        title: '代码质量评估',
        icon: 'check-circle',
        content: `
          <h4>类型安全</h4>
          <p>TypeScript 覆盖率约 <strong>92%</strong>，核心模块全部使用严格类型定义。存在少量 <code>any</code> 类型使用，建议逐步消除。</p>
          <h4>代码规范</h4>
          <p>配置了 ESLint + Prettier，代码风格统一。提交前有 lint-staged 检查，保证代码质量。</p>
          <h4>测试覆盖</h4>
          <p>单元测试覆盖率 <strong>68%</strong>，核心组件和 hooks 有测试覆盖。缺少 E2E 测试，建议补充 Playwright 或 Cypress 测试。</p>
        `,
      },
      {
        id: 'performance',
        title: '性能分析',
        icon: 'zap',
        content: `
          <h4>构建产物</h4>
          <p>Vite 构建，产物体积合理。首屏 JS 约 <strong>85KB (gzipped)</strong>，CSS 约 <strong>12KB</strong>。</p>
          <h4>优化措施</h4>
          <p>已使用 React.lazy 进行路由级代码分割。图片使用了 WebP 格式。列表渲染使用了 key 优化。</p>
          <h4>改进建议</h4>
          <p>建议添加虚拟列表（react-window）处理长列表渲染，考虑使用 React.memo 优化频繁渲染的组件，以及 useMemo/useCallback 减少不必要的重渲染。</p>
        `,
      },
      {
        id: 'security',
        title: '安全性分析',
        icon: 'shield',
        content: `
          <h4>依赖安全</h4>
          <p>无已知高危漏洞依赖。建议定期运行 <code>npm audit</code>，并配置 Dependabot 自动更新。</p>
          <h4>数据处理</h4>
          <p>用户输入有基本的 XSS 防护（React 默认转义）。API 请求使用了环境变量管理敏感配置，未硬编码密钥。</p>
        `,
      },
      {
        id: 'summary',
        title: '综合评价与建议',
        icon: 'star',
        content: `
          <p>这是一个 <strong>质量较高</strong> 的 React 项目，架构清晰、类型安全、有基本的测试覆盖。适合作为求职展示项目。</p>
          <h4>核心优势</h4>
          <ul>
            <li>技术栈选型合理，紧跟社区主流</li>
            <li>代码组织规范，模块划分清晰</li>
            <li>TypeScript 使用到位，类型安全有保障</li>
          </ul>
          <h4>改进方向</h4>
          <ul>
            <li>增加 E2E 测试覆盖关键用户路径</li>
            <li>优化长列表渲染性能</li>
            <li>补充 CI/CD 流水线配置</li>
            <li>考虑添加国际化支持</li>
          </ul>
        `,
      },
    ],
    codeSnippets: [
      {
        id: 'snippet-1',
        title: '全局状态管理 — Zustand Store',
        language: 'typescript',
        code: `import { create } from 'zustand'

interface TodoStore {
  todos: Todo[]
  addTodo: (text: string) => void
  toggleTodo: (id: string) => void
  removeTodo: (id: string) => void
}

export const useTodoStore = create<TodoStore>((set) => ({
  todos: [],
  addTodo: (text) =>
    set((state) => ({
      todos: [...state.todos, { id: crypto.randomUUID(), text, done: false }],
    })),
  toggleTodo: (id) =>
    set((state) => ({
      todos: state.todos.map((t) =>
        t.id === id ? { ...t, done: !t.done } : t
      ),
    })),
  removeTodo: (id) =>
    set((state) => ({
      todos: state.todos.filter((t) => t.id !== id),
    })),
}))`,
        description: '使用 Zustand 管理待办事项的全局状态，接口定义清晰，操作简洁。相比 Redux 大幅减少了样板代码。',
      },
      {
        id: 'snippet-2',
        title: '自定义 Hook — useTodos',
        language: 'typescript',
        code: `import { useEffect } from 'react'
import { useTodoStore } from '../store/todoStore'

export function useTodos() {
  const { todos, addTodo, toggleTodo, removeTodo } = useTodoStore()

  const activeTodos = todos.filter((t) => !t.done)
  const completedTodos = todos.filter((t) => t.done)

  useEffect(() => {
    localStorage.setItem('todos', JSON.stringify(todos))
  }, [todos])

  return {
    todos,
    activeTodos,
    completedTodos,
    addTodo,
    toggleTodo,
    removeTodo,
    stats: {
      total: todos.length,
      active: activeTodos.length,
      completed: completedTodos.length,
    },
  }
}`,
        description: '封装业务逻辑的自定义 Hook，提供派生数据（activeTodos、completedTodos）和本地持久化。组件只需调用 Hook 即可获得完整功能。',
      },
    ],
  },
  'vue-dashboard': {
    ...githubOverviewData['vue-dashboard'],
    sections: [
      {
        id: 'architecture',
        title: '项目架构分析',
        icon: 'layers',
        content: `
          <h4>整体架构</h4>
          <p>采用 <strong>Vue 3 + Composition API</strong> 架构，按功能模块组织代码。views 目录存放页面级组件，components 存放可复用 UI 组件，stores 管理全局状态。</p>
          <h4>数据可视化方案</h4>
          <p>使用 ECharts 作为图表库，封装了通用的 ChartCard 组件，支持折线图、柱状图、饼图等多种图表类型。</p>
          <h4>状态管理</h4>
          <p>使用 Pinia 进行状态管理，按业务域拆分 store（dashboard、user），每个 store 职责单一。</p>
        `,
      },
      {
        id: 'code-quality',
        title: '代码质量评估',
        icon: 'check-circle',
        content: `
          <h4>类型安全</h4>
          <p>TypeScript 覆盖率 <strong>95%</strong>，所有 Props 和 Store 均有类型定义。使用了 Vue 的 defineProps 泛型语法。</p>
          <h4>组件设计</h4>
          <p>组件粒度合理，StatCard、ChartCard 等通用组件支持丰富的 Props 配置。使用 Slots 实现灵活的内容分发。</p>
          <h4>测试覆盖</h4>
          <p>使用 Vitest 进行单元测试，覆盖率 <strong>72%</strong>。Store 测试覆盖完整，组件测试覆盖核心交互。</p>
        `,
      },
      {
        id: 'performance',
        title: '性能分析',
        icon: 'zap',
        content: `
          <h4>构建优化</h4>
          <p>Vite 构建 + 自动代码分割。首屏加载 <strong>1.2s</strong>（Lighthouse 评分 92）。使用了图片懒加载和组件懒加载。</p>
          <h4>图表性能</h4>
          <p>ECharts 实例按需创建，切换页面时正确销毁避免内存泄漏。大数据量图表使用了 dataZoom 进行分页加载。</p>
        `,
      },
      {
        id: 'summary',
        title: '综合评价与建议',
        icon: 'star',
        content: `
          <p>这是一个 <strong>高质量</strong> 的 Vue 3 项目，展示了扎实的前端工程化能力和数据可视化经验。</p>
          <h4>核心优势</h4>
          <ul>
            <li>Vue 3 Composition API 使用规范，逻辑复用灵活</li>
            <li>ECharts 集成方案成熟，图表配置可维护</li>
            <li>响应式设计完善，移动端体验良好</li>
          </ul>
          <h4>改进方向</h4>
          <ul>
            <li>添加深色模式支持</li>
            <li>图表支持数据导出功能</li>
            <li>增加 WebSocket 实时数据推送</li>
          </ul>
        `,
      },
    ],
    codeSnippets: [
      {
        id: 'snippet-1',
        title: 'Pinia Store — Dashboard 数据管理',
        language: 'typescript',
        code: `import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchDashboardData } from '@/api/dashboard'

export const useDashboardStore = defineStore('dashboard', () => {
  const stats = ref<DashboardStats | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const totalRevenue = computed(() =>
    stats.value?.revenue.reduce((sum, r) => sum + r.amount, 0) ?? 0
  )

  async function loadData(dateRange: DateRange) {
    loading.value = true
    error.value = null
    try {
      stats.value = await fetchDashboardData(dateRange)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载失败'
    } finally {
      loading.value = false
    }
  }

  return { stats, loading, error, totalRevenue, loadData }
})`,
        description: '使用 Pinia Setup Store 模式，结合 Composition API，逻辑清晰。computed 派生数据避免重复计算。',
      },
    ],
  },
  'rust-cli-tool': {
    ...githubOverviewData['rust-cli-tool'],
    sections: [
      {
        id: 'architecture',
        title: '项目架构分析',
        icon: 'layers',
        content: `
          <h4>整体架构</h4>
          <p>采用 <strong>Command 模式</strong> 组织 CLI 子命令，每个命令独立一个模块（convert、filter、stats）。lib.rs 导出核心逻辑，main.rs 负责 CLI 解析和调度。</p>
          <h4>错误处理</h4>
          <p>使用 <code>anyhow::Result</code> 作为应用层错误类型，自动实现错误链。用户友好的错误消息通过 <code>context()</code> 方法附加。</p>
          <h4>数据处理管线</h4>
          <p>CSV 解析 → 数据转换 → 输出格式化，三个阶段通过 trait 抽象解耦，易于扩展新的输入/输出格式。</p>
        `,
      },
      {
        id: 'code-quality',
        title: '代码质量评估',
        icon: 'check-circle',
        content: `
          <h4>代码风格</h4>
          <p>使用 <code>rustfmt</code> 统一格式，<code>clippy</code> 静态分析零警告。代码注释充分，公开 API 均有文档注释。</p>
          <h4>测试覆盖</h4>
          <p>单元测试覆盖率 <strong>85%</strong>，包含集成测试和基准测试。使用 <code>criterion</code> 进行性能基准测试。</p>
          <h4>依赖管理</h4>
          <p>依赖精简，仅引入必要 crate。使用 <code>cargo-audit</code> 定期检查安全漏洞。</p>
        `,
      },
      {
        id: 'performance',
        title: '性能分析',
        icon: 'zap',
        content: `
          <h4>运行时性能</h4>
          <p>处理 100 万行 CSV（约 300MB）耗时 <strong>2.3 秒</strong>，内存峰值 <strong>45MB</strong>。使用流式解析避免一次性加载整个文件。</p>
          <h4>优化空间</h4>
          <p>当前为单线程处理，可使用 <code>rayon</code> 库实现并行处理，预计提速 3-4 倍（取决于 CPU 核心数）。</p>
        `,
      },
      {
        id: 'summary',
        title: '综合评价与建议',
        icon: 'star',
        content: `
          <p>这是一个 <strong>专业水准</strong> 的 Rust CLI 项目，展示了对 Rust 语言特性的深入理解和良好的工程实践。</p>
          <h4>核心优势</h4>
          <ul>
            <li>Rust 语言特性运用得当，零成本抽象</li>
            <li>CLI 设计专业，子命令和帮助文档完善</li>
            <li>错误处理规范，用户体验友好</li>
          </ul>
          <h4>改进方向</h4>
          <ul>
            <li>添加并行处理支持</li>
            <li>支持更多数据格式（JSON、Parquet）</li>
            <li>添加 Shell 补全脚本生成</li>
          </ul>
        `,
      },
    ],
    codeSnippets: [
      {
        id: 'snippet-1',
        title: 'CLI 命令定义 — clap derive',
        language: 'rust',
        code: `use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "csvtool")]
#[command(about = "A fast CSV processing CLI tool")]
pub struct Cli {
    #[command(subcommand)]
    command: Commands,

    /// Enable verbose output
    #[arg(short, long, global = true)]
    verbose: bool,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Convert CSV to other formats
    Convert {
        /// Input CSV file path
        #[arg(short, long)]
        input: String,
        /// Output format (json, tsv)
        #[arg(short, long, default_value = "json")]
        format: String,
    },
    /// Filter rows by condition
    Filter {
        /// Input CSV file path
        #[arg(short, long)]
        input: String,
        /// Filter expression
        #[arg(short, long)]
        expression: String,
    },
}`,
        description: '使用 clap derive 宏定义 CLI 结构体，代码即文档。Subcommand 枚举清晰地组织了所有子命令。',
      },
    ],
  },
}

// ─── localStorage Bridge ─────────────────────────────────────────────────

const STORAGE_KEY = 'capy-github-repos'

function getStoredIds() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
  } catch {
    return []
  }
}

function addStoredId(id) {
  const ids = getStoredIds()
  if (!ids.includes(id)) {
    ids.push(id)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids))
  }
}

// ─── Mock Adapter ────────────────────────────────────────────────────────

export function mockAdapter(path, options = {}) {
  // GitHub repo list
  if (path === '/analysis/github/repos' && (!options.method || options.method === 'GET')) {
    const stored = getStoredIds()
    return githubRepos.filter((r) => stored.includes(r.id))
  }

  // GitHub deep analysis (must check before overview to avoid regex conflict)
  const deepMatch = path.match(/^\/analysis\/github\/repos\/([^/]+)\/deep$/)
  if (deepMatch) {
    const id = deepMatch[1]
    return githubDeepAnalysisData[id] || githubDeepAnalysisData['react-todo-app']
  }

  // GitHub repo overview
  const overviewMatch = path.match(/^\/analysis\/github\/repos\/([^/]+)$/)
  if (overviewMatch && (!options.method || options.method === 'GET')) {
    const id = overviewMatch[1]
    return githubOverviewData[id] || githubOverviewData['react-todo-app']
  }

  // GitHub analysis (existing - POST)
  if (path === '/analysis/github') {
    const newId = 'react-todo-app'
    addStoredId(newId)
    // Also pre-populate with other repos for demo purposes
    addStoredId('vue-dashboard')
    addStoredId('rust-cli-tool')
    return {
      id: newId,
      ...githubOverviewData[newId],
    }
  }

  if (path === '/analysis/jd') {
    return {
      score: 65,
      summary: '基于技能要求、经验门槛和竞争程度',
      requirements: [
        { label: '核心技术要求', text: 'React/Vue 等主流框架、TypeScript、性能优化经验' },
        { label: '经验门槛', text: '3 年以上前端开发经验，有大型项目经验优先' },
        { label: '软技能要求', text: '良好的沟通能力、团队协作经验、技术文档编写能力' },
        { label: '加分项', text: '开源贡献、技术博客、带团队经验' },
      ],
      implicit: [
        { label: '隐含期望', text: '该岗位可能同时需要后端基础知识（Node.js/BFF 层）' },
        { label: '团队阶段', text: '可能是新组建团队，需要能独立推动技术方案的人' },
        { label: '业务方向', text: '从 JD 描述来看，业务处于快速增长期，需要关注可扩展性' },
        { label: '薪资范围推测', text: '结合市场行情，预计在 25K-40K 之间' },
      ],
      suggestions: [
        '准备 2-3 个能体现架构设计能力的项目案例',
        '复习性能优化相关知识，准备具体数据和方案',
        '了解目标公司的技术栈和产品，准备针对性的问题',
        '准备一个"你最有成就感的技术方案"的故事',
        '如果是大厂，准备系统设计相关的面试题',
      ],
    }
  }

  if (path === '/analysis/resume') {
    return {
      score: 72,
      summary: '与目标岗位的匹配度评估',
      highlights: [
        { type: 'positive', text: '技能匹配度高：简历中的技术栈与岗位要求高度重合' },
        { type: 'positive', text: '项目经验相关：过往项目经历体现了所需的核心能力' },
        { type: 'positive', text: '学历背景达标：教育背景符合岗位基本要求' },
      ],
      improvements: [
        { label: '量化成果不足', text: '建议为每个项目添加具体数据指标（如提升 XX%、服务 XX 万用户）' },
        { label: '技术深度展示', text: '可以补充一个有深度的技术难点攻克案例' },
        { label: '关键词缺失', text: '简历中缺少部分 JD 关键词，如"性能优化"、"架构设计"' },
      ],
      suggestions: [
        '在项目描述中添加量化数据，用"提升了 XX%"代替"优化了性能"',
        '增加一个"技术亮点"板块，突出你最擅长的领域',
        '根据 JD 关键词调整简历措辞，提高 ATS 筛选通过率',
        '补充开源贡献或技术博客链接，增强技术影响力展示',
        '将简历控制在 1-2 页，突出与目标岗位最相关的经历',
      ],
    }
  }

  if (path === '/interview/reply') {
    const body = JSON.parse(options.body || '{}')
    const type = body.type || 'technical'
    const questions = interviewQuestions[type] || interviewQuestions.technical
    const idx = Math.floor(Math.random() * questions.length)
    return { content: questions[idx] }
  }

  // Interview list
  if (path === '/interviews' && (!options.method || options.method === 'GET')) {
    return [
      {
        id: 1,
        type: 'comprehensive',
        resume: '前端工程师_简历.pdf',
        projects: ['job-seeker-assistant'],
        duration: 15,
        status: 'completed',
        date: '2026-05-23',
        summary: {
          highlights: ['Vue组件化组织清晰', '对状态管理的理解准确'],
          improvements: ['性能优化回答可更具体', '建议深入学习Vue3响应式原理']
        }
      },
      {
        id: 2,
        type: 'technical',
        resume: '前端工程师_简历.pdf',
        projects: ['my-portfolio'],
        duration: 22,
        status: 'paused',
        date: '2026-05-22',
        progress: {
          answered: 3,
          totalQuestions: 8
        }
      },
      {
        id: 3,
        type: 'behavioral',
        resume: '我的简历_v2.pdf',
        projects: [],
        duration: 10,
        status: 'completed',
        date: '2026-05-21',
        summary: {
          highlights: ['回答有条理', '团队协作经验丰富'],
          improvements: ['可以更多举例说明', '表达可以更简洁']
        }
      }
    ]
  }

  // Get single interview
  const interviewMatch = path.match(/^\/interviews\/(\d+)$/)
  if (interviewMatch && (!options.method || options.method === 'GET')) {
    const id = parseInt(interviewMatch[1])
    const interviews = [
      {
        id: 1,
        type: 'comprehensive',
        resume: '前端工程师_简历.pdf',
        projects: ['job-seeker-assistant'],
        duration: 15,
        status: 'completed',
        date: '2026-05-23',
        messages: [
          { id: 1, role: 'ai', content: '你好！我看到你简历上有 React 项目经验，能介绍一下你在项目中遇到的最大技术挑战吗？', isFollowUp: false },
          { id: 2, role: 'user', content: '我在项目中遇到了性能问题，主要是长列表渲染卡顿。', isFollowUp: false },
          { id: 3, role: 'ai', content: '很好，你具体用了哪些优化手段？虚拟列表还是其他方案？', isFollowUp: false },
          { id: 4, role: 'user', content: '我使用了react-window实现虚拟列表，同时配合useMemo缓存计算结果。', isFollowUp: false },
          { id: 5, role: 'ai', content: '能具体说说你是怎么决定使用react-window的吗？有没有考虑过其他方案？', isFollowUp: true }
        ],
        summary: {
          overview: {
            type: 'comprehensive',
            duration: 15,
            questionCount: 5,
            resume: '前端工程师_简历.pdf',
            projects: ['job-seeker-assistant']
          },
          highlights: ['Vue组件化组织清晰，提到了合理的目录结构', '对状态管理的理解准确，能结合项目说明', '回答有条理，逻辑清晰'],
          improvements: ['关于性能优化的回答可以更具体，举实际例子', '建议深入学习Vue3的响应式原理', '可以多练习系统设计类问题的表达'],
          messages: [
            { id: 1, role: 'ai', content: '你好！我看到你简历上有 React 项目经验，能介绍一下你在项目中遇到的最大技术挑战吗？', isFollowUp: false },
            { id: 2, role: 'user', content: '我在项目中遇到了性能问题，主要是长列表渲染卡顿。', isFollowUp: false },
            { id: 3, role: 'ai', content: '很好，你具体用了哪些优化手段？虚拟列表还是其他方案？', isFollowUp: false },
            { id: 4, role: 'user', content: '我使用了react-window实现虚拟列表，同时配合useMemo缓存计算结果。', isFollowUp: false },
            { id: 5, role: 'ai', content: '能具体说说你是怎么决定使用react-window的吗？有没有考虑过其他方案？', isFollowUp: true }
          ]
        }
      }
    ]
    return interviews.find(i => i.id === id) || interviews[0]
  }

  return {}
}

export { interviewQuestions }
