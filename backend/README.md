# Backend — CapyMock API

AI 求职助手后端，基于 FastAPI + ReAct Agent Loop 架构。

## Tech Stack

- **Runtime:** Python 3.13+
- **Framework:** FastAPI
- **Database:** SQLite (aiosqlite)
- **Package Manager:** uv
- **ORM:** SQLAlchemy 2.0
- **LLM Providers:** DashScope, DeepSeek, MiMo (OpenAI-compatible)

## Project Structure

```
backend/
├── agent/              # Agent Loop 核心实现
│   ├── loop.py         # ReActAgent (Reason-Act-Observe)
│   ├── state.py        # AgentState 状态机
│   ├── factory.py      # AgentFactory 创建 agent 实例
│   ├── profile.py      # AgentProfile Pydantic 模型
│   ├── profile_loader.py # 从 YAML 加载 profile
│   ├── context/        # Context 构建与压缩
│   │   ├── builder.py  # ContextBuilder 拼装消息
│   │   ├── compactor.py # ContextCompactor 压缩历史
│   │   └── skill_loader.py # 加载 SKILL.md
│   └── llm/            # LLM 抽象与 provider
│       ├── base.py     # BaseLLM 抽象类
│       ├── events.py   # LLMEvent 事件类型
│       ├── factory.py  # LLMFactory 注册表
│       └── providers/  # 具体 provider 实现
│           ├── openai_compatible.py # OpenAI 兼容基类
│           ├── deepseek.py         # DeepSeek 适配器
│           ├── dashscope_compat.py # DashScope 适配器
│           └── mimo.py             # MiMo (小米) 适配器
├── api/                # FastAPI 路由
│   ├── app.py          # FastAPI app + lifespan
│   ├── sessions.py     # REST API (会话 CRUD)
│   ├── chat.py         # SSE 端点 (Chat + Stream)
│   ├── tasks.py        # 异步任务 API
│   ├── github_analysis.py # GitHub 分析任务
│   ├── ws.py           # WebSocket (语音模式预留)
│   ├── schemas.py      # FrontendEvent + 请求/响应模型
│   └── deps.py         # 依赖注入函数
├── config/             # 配置文件
│   ├── settings.py     # pydantic-settings 读 .env
│   └── agents/         # AgentProfile YAML 文件
│       ├── interviewer-behavior.yaml
│       ├── interviewer-comprehensive.yaml
│       ├── interviewer-technical.yaml
│       ├── repo-analyzer.yaml
│       └── summary-generator.yaml
├── data/               # 数据文件
│   ├── prompt/         # 系统提示词
│   │   ├── interviewer_behavior.md
│   │   ├── interviewer_comprehensive.md
│   │   ├── interviewer_technical.md
│   │   ├── repo_analyzer_system_prompt.md
│   │   └── summary_generator.md
│   └── skill/          # 技能定义 (SKILL.md)
│       └── repo-analyzer/SKILL.md
├── service/            # 业务逻辑
│   ├── session_service.py # 会话管理服务
│   └── task_service.py # 异步任务服务
├── storage/            # 数据存储层
│   ├── db/             # SQLAlchemy
│   │   ├── models.py   # ORM 模型
│   │   └── engine.py   # 异步 engine + session 工厂
│   ├── session/        # JSONL 会话存储
│   │   └── store.py    # SessionStore
│   └── memory/         # 分层 Markdown 记忆存储
│       └── store.py    # MemoryStore (user/resume 分层)
├── tool/               # 工具系统
│   ├── base.py         # @tool 装饰器、ToolContext、ToolResult
│   ├── registry.py     # ToolRegistry 显式注册
│   ├── executor.py     # ToolExecutor 并发执行
│   ├── sandbox.py      # 沙箱路径校验
│   └── builtins/       # 内建工具
│       ├── read_resume.py
│       ├── query_github_analysis.py
│       ├── take_note.py
│       ├── read_skill.py
│       ├── remember.py          # 记忆读写
│       ├── clone_repo.py        # Git 仓库克隆
│       ├── list_directory.py    # 目录列表
│       ├── read_file.py         # 文件读取
│       ├── search_code.py       # 代码搜索 (ripgrep)
│       └── save_repo_analysis.py # 保存分析结果
├── trace/              # 可观测性
│   └── observability.py # Langfuse 集成 (SDK v4)
├── docs/               # 设计文档
├── tests/              # 测试
└── docker/             # Docker 配置
```

## API 设计

### 通信模式

| 模式 | 协议 | 用途 | 端点 |
|------|------|------|------|
| **Chat** | HTTP POST | 同步请求-响应，等完整回复 | `POST /api/sessions/{id}/chat` |
| **Stream** | SSE | 异步流式，实时推送事件 | `POST /api/sessions/{id}/messages` + `GET /api/sessions/{id}/stream` |
| **Task** | HTTP + SSE | 长时间任务，进度追踪 | `POST /api/analysis` + `GET /api/tasks/{id}/stream` |
| **Voice** | WebSocket | 语音模式（预留） | `WS /ws/voice/{session_id}` |

### 会话 API

```
POST   /api/sessions                    # 创建会话
GET    /api/sessions                    # 列表 + 筛选 + 排序
GET    /api/sessions/{id}               # 单条详情
GET    /api/sessions/{id}/events        # 事件回放
POST   /api/sessions/{id}/finalize      # 生成总结
```

### Chat API（面试对话）

```
POST   /api/sessions/{id}/chat          # 同步聊天，返回完整回复
POST   /api/sessions/{id}/messages      # 发送消息（触发 agent）
GET    /api/sessions/{id}/stream        # SSE 流式接收事件
POST   /api/sessions/{id}/interrupt     # 中断 agent
```

### Task API（长时间任务）

```
POST   /api/analysis                    # 提交 GitHub 分析任务
GET    /api/tasks/{task_id}             # 查询任务状态
GET    /api/tasks/{task_id}/stream      # SSE 进度流
POST   /api/tasks/{task_id}/cancel      # 取消任务
```

## 核心设计

### ReAct Agent Loop

仿照 Claude Code 的核心架构：

| 模块 | 说明 |
|------|------|
| **ReActAgent** | Reason → Act → Observe 循环，支持迭代推理 |
| **AgentState** | 状态机：idle → thinking → streaming_text → executing_tools → aggregating |
| **ContextBuilder** | 拼装 system prompt + skill 摘要 + 历史消息 |
| **ContextCompactor** | 超过 token 阈值时用 LLM 总结老消息 |
| **ToolExecutor** | 并发执行工具，支持超时、失败隔离、cancel_token |
| **SessionStore** | JSONL append-only 持久化，支持 replay |

### Agent Profiles

通过 YAML 配置不同角色的 agent：

- **interviewer-behavior** — 行为面试官
- **interviewer-technical** — 技术面试官
- **interviewer-comprehensive** — 综合面试官
- **repo-analyzer** — GitHub 仓库分析（含 clone/read/search 工具链）
- **summary-generator** — 面试总结生成

### LLM Provider 架构

采用 Template Method 模式：

```
OpenAICompatibleLLM (基类)
    ├── DeepSeekLLM        (只设 base_url)
    ├── DashScopeCompatLLM (覆盖 _extra_request_params)
    └── MiMoLLM            (小米 MiMo，OpenAI 兼容)
```

### 工具系统

| 工具 | 说明 |
|------|------|
| `read_resume` | 读取用户简历 |
| `query_github_analysis` | 查询 GitHub 分析结果 |
| `take_note` | 记录面试笔记 |
| `read_skill` | 读取技能定义 |
| `remember` | 分层记忆读写 (MemoryStore) |
| `clone_repo` | Git 仓库克隆到沙箱 |
| `list_directory` | 列出目录结构 |
| `read_file` | 读取文件内容 |
| `search_code` | 代码搜索 (ripgrep) |
| `save_repo_analysis` | 保存仓库分析结果 |

所有文件工具通过 `sandbox.py` 进行路径校验，防止越权访问。

### MemoryStore

分层 Markdown 记忆存储：

```
<root>/<user_id>/user.md                    — 用户级（跨简历共享）
<root>/<user_id>/<resume_id>/CAPY_NOTE.md  — 简历级笔记
<root>/<user_id>/<resume_id>/REAL_QUES.md  — 简历级真题
```

### 双层事件协议

- **LLMEvent**：Python 内部 sum type（TextDelta / ToolCallStart / Done 等）
- **FrontendEvent**：前端 JSON 协议（assistant.text.delta / tool.call.start 等）

### 异步任务系统

长时间任务（如 GitHub 分析）使用异步任务模式：

```
1. POST /api/analysis → 返回 task_id（立即）
2. GET  /api/tasks/{task_id}/stream → SSE 进度流
3. GET  /api/tasks/{task_id} → 获取最终结果
```

核心组件：`TaskService`（通用任务管理），支持进度追踪、取消、超时。

## 前端集成指南

### 面试对话（Chat 模式）

```javascript
// 同步 Chat - 等待完整回复
const res = await fetch(`/api/sessions/${sessionId}/chat`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ text: '介绍一下自己' })
})
const { text, events } = await res.json()
```

### 面试对话（Stream 模式）

```javascript
// 异步 Stream - 实时流式
await fetch(`/api/sessions/${sessionId}/messages`, {
  method: 'POST',
  body: JSON.stringify({ text: '介绍一下自己' })
})

const es = new EventSource(`/api/sessions/${sessionId}/stream`)
es.onmessage = (e) => {
  const event = JSON.parse(e.data)
  // 处理 event...
}
```

### GitHub 分析（Task 模式）

```javascript
// 提交任务
const { task_id } = await fetch('/api/analysis', {
  method: 'POST',
  body: JSON.stringify({ repo_url: 'https://github.com/...' })
}).then(r => r.json())

// 监听进度
const es = new EventSource(`/api/tasks/${task_id}/stream`)
es.onmessage = (e) => {
  const { status, progress, message } = JSON.parse(e.data)
  updateUI(progress, message)  // "正在分析... 50%"
}

// 获取结果
const task = await fetch(`/api/tasks/${task_id}`).then(r => r.json())
console.log(task.result.analysis)
```

## 开发规范

- 使用 uv 管理依赖，`uv add <package>` 添加
- 类型注解必须完整
- 使用 async/await
- 测试放在 tests/ 对应模块下
- 使用 ruff 进行 lint 检查

## 常用命令

```bash
# 初始化
uv init
uv add fastapi uvicorn sqlalchemy

# 运行
uv run uvicorn api.app:app --reload

# 测试
uv run pytest

# Lint
uv run ruff check .
uv run ruff check . --fix

# 类型检查
uv run mypy backend
```

## 环境变量

参考 `.env.example` 文件：

- `DASHSCOPE_API_KEY` / `DEEPSEEK_API_KEY`：LLM API 密钥
- `TRACER`：noop 或 langfuse
- `SQLITE_PATH`：SQLite 数据库路径
- `JSONL_ROOT`：JSONL 会话文件根目录
