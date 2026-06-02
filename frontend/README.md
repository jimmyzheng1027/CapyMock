# Frontend — CapyMock

AI 求职助手前端，基于 Vue 3 + Vite + Tailwind CSS。

## Tech Stack

- **Framework:** Vue 3 (Composition API + `<script setup>`)
- **Build:** Vite 6
- **Styling:** Tailwind CSS 3 + CSS Custom Properties
- **Routing:** Vue Router 4
- **State:** Pinia + 响应式模块
- **Language:** JavaScript（无 TypeScript）

## Quick Start

```bash
npm install
npm run dev        # localhost:3000
npm run build      # production build
npm run preview    # preview production build
```

## Directory Structure

```
src/
├── pages/                      # 页面视图
│   ├── HomePage.vue                # 首页（英雄区 + 功能展示 + CTA）
│   ├── InterviewListPage.vue       # 面试记录列表
│   ├── InterviewConfigPage.vue     # 面试配置（选简历、类型、仓库）
│   ├── InterviewSessionPage.vue    # 面试进行中（文字/语音模式切换）
│   ├── InterviewSummaryPage.vue    # 面试总结与反馈
│   ├── JdPage.vue                  # JD 分析
│   ├── ResumePage.vue              # 简历上传与管理
│   └── github/
│       ├── GitHubListPage.vue      # 仓库分析列表
│       ├── GitHubOverviewPage.vue  # 仓库概览（评分、标签、亮点）
│       └── GitHubDeepPage.vue      # 深度分析（代码片段、目录树）
├── components/
│   ├── common/                 # 通用组件
│   │   ├── CapybaraLogo.vue        # 水豚 Logo
│   │   ├── FileUploadZone.vue      # 拖拽上传
│   │   ├── LoadingOverlay.vue      # 全屏加载
│   │   ├── ResultsHeader.vue       # 结果页头部
│   │   ├── ScoreRing.vue           # 环形评分
│   │   ├── SectionCard.vue         # 卡片容器
│   │   ├── ThemeToggle.vue         # 深色/浅色切换
│   │   └── TweaksPanel.vue         # 设计系统微调面板
│   ├── interview/              # 面试组件
│   │   ├── TextMode.vue            # 文字模式（SSE 流式 + Markdown 渲染）
│   │   ├── VoiceMode.vue           # 语音模式（WebSocket + 音频录制/播放）
│   │   ├── VoiceMonitor.vue        # 音频波形监控
│   │   ├── ChatBubble.vue          # 聊天气泡
│   │   ├── InterviewCard.vue       # 面试记录卡片
│   │   ├── InterviewSummary.vue    # 总结展示组件
│   │   ├── FollowUpTag.vue         # 追问标签
│   │   ├── SettingsPanel.vue       # 面试设置面板
│   │   ├── InterviewConfigModal.vue
│   │   └── InterviewConfigStep.vue
│   ├── github/                 # GitHub 分析组件
│   │   ├── RepoCard.vue            # 仓库卡片
│   │   ├── AddRepoCard.vue         # 添加仓库
│   │   ├── CodeSnippet.vue         # 代码片段（语法高亮）
│   │   ├── DirectoryTree.vue       # 目录树
│   │   ├── ReportSection.vue       # 报告区块
│   │   ├── TechStackTags.vue       # 技术栈标签
│   │   └── EmptyState.vue          # 空状态
│   └── landing/                # 首页区块
│       ├── HeroSection.vue         # 英雄区
│       ├── FeaturesSection.vue     # 功能展示
│       ├── InterviewSection.vue    # 面试演示
│       ├── CtaSection.vue          # 行动号召
│       ├── NavSection.vue          # 导航栏
│       └── FooterSection.vue       # 页脚
├── composables/                # 组合式函数
│   ├── useVoiceInterview.js        # 语音面试（WebSocket、音频、转写、打断）
│   ├── useInterviewConfig.js       # 面试配置（简历/仓库加载、会话创建）
│   ├── useGithubAnalysis.js        # GitHub 分析（提交、SSE 进度、缓存）
│   ├── useScrollReveal.js          # 滚动渐显动画
│   └── useScrollState.js           # 滚动状态检测
├── utils/                      # 工具函数
│   ├── voiceAudio.js               # PCM16 编解码、音频录制/播放、特性检测
│   ├── renderMarkdown.js           # Markdown → HTML 渲染器
│   └── interviewHelpers.js         # 事件 → 消息/转写条目转换
├── stores/                     # Pinia 状态
│   ├── theme.js                    # 深色/浅色主题
│   └── tweaks.js                   # 设计微调（颜色、字号、圆角、动画）
├── data/                       # 静态数据
│   ├── interview.js                # 面试类型常量、profile 映射
│   └── interviewQuestions.js       # 示例面试题
├── layouts/                    # 页面布局
│   ├── AnalysisLayout.vue          # 分析子页面布局
│   └── GitHubLayout.vue            # GitHub 分析嵌套布局
├── api/                        # 接口层
│   ├── index.js                    # API 客户端（REST + SSE + WebSocket URL）
│   └── mock.js                     # Mock 适配器
├── router/                     # 路由配置（懒加载）
├── assets/styles/              # 全局 CSS（base.css 定义所有 CSS 变量）
└── App.vue                     # 根组件
```

## Pages

| 路由 | 页面 | 说明 |
|------|------|------|
| `/` | HomePage | 产品首页 |
| `/interview` | InterviewListPage | 面试历史列表 |
| `/interview/config` | InterviewConfigPage | 面试配置（简历、类型、仓库） |
| `/interview/:id` | InterviewSessionPage | 面试进行中（文字/语音） |
| `/interview/:id/summary` | InterviewSummaryPage | 面试总结与反馈 |
| `/analysis/jd` | JdPage | JD 分析 |
| `/analysis/resume` | ResumePage | 简历管理 |
| `/analysis/github` | GitHubListPage | 仓库分析列表 |
| `/analysis/github/:id` | GitHubOverviewPage | 仓库概览 |
| `/analysis/github/:id/deep` | GitHubDeepPage | 深度分析 |

## 功能模块

### 文字面试 (`TextMode.vue`)

- SSE 流式对话，实时显示 AI 回复
- Markdown 渲染（代码高亮、列表、表格）
- 历史消息回放（重连时自动恢复）
- 追问标签（点击发送预设追问）

### 语音面试 (`VoiceMode.vue` + `useVoiceInterview.js`)

- WebSocket 连接，PCM16 音频流
- 麦克风采集 → 重采样 → base64 编码 → WebSocket 发送
- AI 音频播放（AudioContext 缓冲调度，无缝播放）
- 实时转写显示
- 静音/暂停、Barge-in 支持（用户说话时打断 AI）
- 连接状态管理、错误提示（缺少 API Key 等）

### GitHub 分析 (`useGithubAnalysis.js`)

- 提交仓库 URL → 异步分析
- SSE 进度追踪（自动重连）
- 结果缓存（避免重复分析）
- 概览页 + 深度页

### 简历管理

- 拖拽上传（PDF/图片，最大 10MB）
- AI 多模态分析
- 简历列表 + 删除

### 设计系统

- 大地色系配色（CSS 变量驱动）
- Plus Jakarta Sans（标题）+ Outfit（正文）+ JetBrains Mono（代码）
- 深色/浅色主题切换
- `TweaksPanel` 实时微调：主色、字号、圆角、动画开关

## API Integration

前端通过 `api/index.js` 对接 FastAPI 后端：

```javascript
// 会话管理
api.createSession({ profileId, mode, resumeId, githubRepoIds })
api.getSessions({ userId, status, profileId })
api.getSession(sessionId)
api.finalizeSession(sessionId)

// 文字面试（SSE 流式）
api.sendSSEMessage(sessionId, text)   // POST 触发 agent
api.streamEvents(sessionId)           // EventSource 接收事件

// 语音面试（WebSocket）
api.getVoiceWebSocketUrl(sessionId, { profileId, userId, mode })

// 分析
api.submitAnalysis(repoUrl)
api.uploadResume(file)
api.analyzeJd(text)
```

### SSE 事件类型

| 事件 | 说明 |
|------|------|
| `assistant.text.delta` | 流式文本片段 |
| `assistant.text.done` | 完整回复 |
| `assistant.transcript.delta` | 语音转写片段 |
| `assistant.transcript.done` | 完整语音转写 |
| `assistant.audio.delta` | 音频帧（base64 PCM16） |
| `user.text` | 用户文字输入 |
| `user.transcript` | 用户语音转写 |
| `tool.call.start` | 工具调用开始 |
| `tool.call.end` | 工具调用结束 |
| `turn.done` | 本轮结束 |
| `error` | 错误 |

## Design System

完整规范见 `DESIGN.md`，关键规则：

- **暖色调中性色**：不用纯黑 `#000` 或纯白 `#fff`
- **Primary 仅作强调**：Honey Oak `#B8845C` 用于按钮/链接/激活态
- **静止无阴影**：hover/focus 时才出现阴影
- **字体**：Plus Jakarta Sans（标题）+ Outfit（正文）+ JetBrains Mono（代码）
