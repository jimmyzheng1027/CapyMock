# CapyMock

1. **温暖优先于效率** — 情感舒适是第一位的
2. **支持而非施压** — 鼓励进步，不制造焦虑
3. **人性化而非企业化** — 对话式语气，自然流畅
4. **清晰而不冰冷** — 干净的布局，温暖的色彩与动效

![CapyMock 首页](homepage.png)

## 简介

CapyMock 是一间面试前的练习室 —— 温暖、包容、不带评判。不同于冷冰冰的企业 HR 平台和令人焦虑的刷题网站，CapyMock 让你按自己的节奏练习，获得真诚的反馈，逐步建立信心。

线条水豚吉祥物体现了产品气质：沉稳、亲切、不急不躁。

### 功能

- **模拟面试** — 支持文字和语音两种模式的 AI 模拟面试，覆盖技术、行为、综合三类面试官，并且支持一键在两个模式间无缝切换
- **GitHub 仓库分析** — 克隆仓库、扫描代码结构、生成项目分析报告，为技术面试做准备
- **岗位描述分析** — 粘贴 JD 文本，获得结构化的岗位要求分析
- **简历管理** — 上传 PDF/图片简历，AI 多模态分析并给出改进建议
- **面试总结** — 面试结束后自动生成总结报告，含亮点、建议和技术/行为评估
- **记忆系统** — 跨会话的分层记忆（用户画像、简历笔记、真实面试题），让面试官越练越懂你

## 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + Vite + Tailwind CSS |
| **后端** | FastAPI + 自研 ReAct Agent Loop + Realtime Voice Agent |
| **数据库** | SQLite (aiosqlite) + SQLAlchemy 2.0 + JSONL 事件日志 |
| **LLM** | MiMo / DashScope / DeepSeek（文本）；DashScope Qwen-Omni / OpenAI Realtime（语音） |
| **可观测性** | Langfuse（OpenTelemetry SDK v4） |
| **设计系统** | 大地色系（蜂蜜橡木、苔藓绿、珊瑚沙）+ Plus Jakarta Sans / Outfit |

### Agent 架构

仿照 Claude Code 的 ReAct 循环设计：

- **ReActAgent** — Reason → Act → Observe 循环，支持迭代推理、工具调用、上下文压缩
- **RealtimeAgent** — 双泵架构，桥接客户端 WebSocket 与实时语音 LLM，支持打断、中注入摘要、不活跃检测
- **AgentProfile** — YAML 配置驱动，定义 LLM、工具、提示词、策略、语音参数
- **MemoryStore** — 分层 Markdown 记忆（用户画像 / 简历笔记 / 真实面试题），跨会话持久化
- **状态机** - 7 个状态通过有限状态机严格管控转换（IDLE → THINKING → STREAMING_TEXT → EXECUTING_TOOLS → AGGREGATING），任意状态可被中断至 INTERRUPTED；语音模式另设 LISTENING / AI_SPEAKING / THINKING / CLOSED 四态。
- **其他** - 上下文管理、容错与降级策略等

## 核心架构

### 文字面试（SSE 流式）

```
前端 TextMode → POST /api/sessions/{id}/messages
             → ReActAgent.run()
             → LLM 流式输出 + 工具调用
             → SSE 事件推送到前端
```

![文字面试模式](text_mode_interview.png)

### 语音面试（WebSocket 实时）

```
前端 VoiceMode → WebSocket /ws/voice/{session_id}
              → RealtimeAgent（双泵架构）
              → 客户端音频 ↔ 实时 LLM（DashScope Qwen-Omni / OpenAI）
              → 支持 VAD、打断（barge-in）、实时转写
```

![语音面试模式](voice-mode-interview.png)

### GitHub 仓库分析

![GitHub 仓库分析](github_repo_analysis_1.png)
![GitHub 仓库分析详情](github_repo_analysis_2.png)

### 岗位描述分析

![JD 分析](JD_analysis.png)

## 快速开始

### 后端

```bash
cd backend
uv sync
cp .env.example .env   # 填入 LLM API Key
uv run uvicorn api.app:app --reload
```

API 默认运行在 `http://localhost:8000`。

### 前端

```bash
cd frontend
npm install
npm run dev
```

开发服务器默认运行在 `http://localhost:3000`。

### Langfuse 追踪（可选）

```bash
# 在 .env 中设置 TRACER=langfuse 并配置 Langfuse 密钥
# 或使用 Docker Compose 启动 Langfuse 服务
docker compose --profile langfuse up -d
```

![Langfuse 追踪](langfuse_tracer.png)

## 项目结构

```
job-seeker-assistant/
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── pages/              # 页面（首页、面试、分析、简历）
│       ├── components/         # 可复用组件（面试、GitHub、通用）
│       ├── composables/        # 组合式函数（语音、配置、分析）
│       ├── utils/              # 工具函数（音频、Markdown、事件转换）
│       ├── stores/             # Pinia 状态管理
│       ├── layouts/            # 页面布局
│       ├── router/             # 路由配置
│       ├── data/               # 静态数据（面试类型、示例问题）
│       └── api/                # 接口层
├── backend/                # FastAPI 后端
│   ├── agent/                  # Agent 核心
│   │   ├── loop.py                 # ReActAgent（文字模式）
│   │   ├── realtime_agent.py       # RealtimeAgent（语音模式）
│   │   ├── factory.py              # AgentFactory
│   │   ├── context/                # 上下文构建与压缩
│   │   └── llm/                    # LLM 抽象与 provider
│   │       ├── providers/              # 文本 LLM（MiMo、DeepSeek、DashScope）
│   │       └── realtime/               # 实时语音 LLM（OpenAI、DashScope）
│   ├── api/                    # FastAPI 路由（REST / SSE / WebSocket）
│   ├── config/                 # 配置与 Agent Profile YAML
│   ├── tool/                   # 工具系统（9 个内建工具）
│   ├── service/                # 业务逻辑（会话、简历、任务）
│   ├── storage/                # 数据存储（SQLite、JSONL、Markdown 记忆）
│   ├── trace/                  # Langfuse 可观测性集成
│   ├── data/                   # 系统提示词与技能定义
│   └── tests/                  # 测试
├── DESIGN.md               # 设计系统规范
├── PRODUCT.md              # 产品定位和用户画像
├── CLAUDE.md               # Claude Code 项目指令
└── README.md               # 本文件
```

## License

MIT
