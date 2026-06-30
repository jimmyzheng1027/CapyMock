# AGENTS.md

CapyMock — AI 求职助手，帮助用户温暖自信地准备面试。

## Behavioral Guidelines

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:

- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:

```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

## Project Structure

```
job-seeker-assistant/
├── frontend/       # Vue 3 前端 (see frontend/README.md)
├── backend/        # FastAPI 后端 (see backend/README.md)
├── DESIGN.md       # 设计系统规范
├── PRODUCT.md      # 产品定位和用户画像
└── README.md       # 项目说明
```

## Architecture Overview

### 后端

- **ReAct Agent** (`agent/loop.py`) — 文字模式面试，Reason-Act-Observe 循环
- **RealtimeAgent** (`agent/realtime_agent.py`) — 语音模式面试，双泵架构桥接 WebSocket 与实时 LLM
- **AgentFactory** (`agent/factory.py`) — 创建文本/语音 Agent，从 YAML profile 读取配置
- **LLM Providers** — 文本：MiMo / DeepSeek / DashScope；语音：DashScope Qwen-Omni / OpenAI Realtime
- **工具系统** — 9 个内建工具，沙箱路径校验
- **记忆系统** — 分层 Markdown（user.md / CAPY_NOTE.md / REAL_QUES.md）
- **存储** — SQLite（元数据）+ JSONL（事件日志）+ 文件系统（记忆）
- **可观测性** — Langfuse 全链路追踪

### 前端

- **文字面试** — SSE 流式对话，Markdown 渲染
- **语音面试** — WebSocket + PCM16 音频流，实时转写，Barge-in
- **分析系统** — GitHub 仓库分析、JD 分析、简历管理
- **设计系统** — CSS 变量驱动，深色/浅色主题，TweaksPanel 实时微调

## Key Conventions

### Backend

- Python 3.13+, uv 管理依赖
- FastAPI + async/await
- SQLAlchemy 2.0 (async) + SQLite
- Pydantic v2 数据模型
- YAML 配置驱动 Agent Profile
- 测试用 pytest + pytest-asyncio

### Frontend

- Vue 3 Composition API (`<script setup>`)
- JavaScript（无 TypeScript）
- Tailwind CSS + CSS 变量
- 组合式函数（composables）封装业务逻辑
- `api/index.js` 统一接口层

## Environment

- Platform: Windows 11
- Shell: PowerShell
