const techTags = ['React', 'TypeScript', 'Node.js', 'Vite', 'Tailwind CSS', 'Jest', 'REST API', 'Git']

const githubQuestions = [
  { q: '请介绍一下你在这个项目中使用的状态管理方案，为什么选择这个方案？', a: '建议从技术选型背景出发，对比 Redux/Zustand/Jotai 等方案的优劣，说明选择理由，并举一个具体使用场景。' },
  { q: '这个项目的架构设计是怎样的？如果让你重新设计，你会做哪些改动？', a: '先描述当前架构（目录结构、模块划分、数据流），再提出 2-3 个可改进的点，如：组件复用、测试覆盖、性能优化等。' },
  { q: '你在项目中遇到的最大技术挑战是什么？最终是怎么解决的？', a: '用 STAR 法则回答：Situation（背景）→ Task（任务）→ Action（你做了什么）→ Result（结果和收获）。重点突出你的思考过程。' },
  { q: '项目中有没有做过性能优化？具体用了哪些手段？', a: '可以从代码分割、懒加载、缓存策略、虚拟列表、图片优化等方面回答，配合具体数据（如加载时间减少 40%）会更有说服力。' },
  { q: '如果这个项目的用户量增长 10 倍，你会从哪些方面做架构升级？', a: '从 CDN、数据库分片、缓存层、微服务拆分、负载均衡等角度展开，展示你的系统设计思维。' },
]

const interviewQuestions = {
  technical: [
    '你好！我看到你简历上有 React 项目经验，能介绍一下你在项目中遇到的最大技术挑战吗？',
    '很好，你具体用了哪些优化手段？虚拟列表还是其他方案？',
    '能说说你对前端工程化的理解吗？比如 CI/CD、代码规范这些。',
    '如果让你从零搭建一个新项目，你会怎么选择技术栈？考虑哪些因素？',
    '最后一个问题：你平时是怎么保持技术学习的？最近在关注什么新技术？',
  ],
  behavioral: [
    '你好！请先做一个简短的自我介绍吧。',
    '能分享一个你在团队中解决冲突的经历吗？',
    '描述一个你需要在紧迫的 deadline 下完成任务的情况，你是怎么处理的？',
    '你有没有主动推动过某个改进或创新？结果如何？',
    '最后一个问题：你为什么想加入我们公司？你对这个岗位有什么期待？',
  ],
  hr: [
    '你好！请先简单介绍一下自己吧。',
    '你为什么想离开现在的公司？',
    '你的期望薪资是多少？能接受的最低范围是多少？',
    '你对未来 3-5 年的职业规划是怎么想的？',
    '你有什么想问我们的吗？',
  ],
}

export function mockAdapter(path) {
  if (path === '/analysis/github') {
    return {
      score: 78,
      summary: '仓库综合评估',
      techTags,
      questions: githubQuestions,
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
    const type = 'technical'
    const idx = Math.floor(Math.random() * interviewQuestions[type].length)
    return { content: interviewQuestions[type][idx] }
  }

  return {}
}

export { interviewQuestions }
