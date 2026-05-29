# Agent Loop 原理

## 三层事件流

```
LLM API (OpenAI 兼容)
    ↓  原始 JSON chunks
LLM Provider (openai_compatible.py)
    ↓  LLMEvent (Python 内部事件)
_process_llm_events (loop.py)
    ↓  FrontendEvent (前端 JSON 事件)
前端 (SSE / WebSocket)
```

为什么要分两层：LLM 返回的数据格式（TextDelta、ToolCallStart 等）和前端需要的数据格式（assistant.text.delta、tool.call.start 等）不一样。中间这层 `_process_llm_events` 做翻译 + 业务逻辑。

## 两套事件类型

### LLMEvent（agent/llm/events.py）— LLM 返回的原始事件

| 类型 | 含义 |
|------|------|
| `TextDelta` | 一小段文本（一个 token 或几个 token） |
| `ThinkingDelta` | 思维链内容（DeepSeek-R1、QwQ 等模型） |
| `ToolCallStart` | LLM 决定调用某个工具，开始声明 |
| `ToolCallArgsDelta` | 工具参数的 JSON 片段 |
| `ToolCallEnd` | 工具调用声明完成，参数已完整 |
| `Usage` | token 用量统计 |
| `Done` | LLM 回复结束，附带 `stop_reason` |
| `ProviderError` | API 报错（超时、限流等） |

### FrontendEvent（api/schemas.py）— 发给前端的事件

| 类型 | 对应的 LLMEvent |
|------|------|
| `assistant.text.delta` | `TextDelta` |
| `assistant.thinking.delta` | `ThinkingDelta` |
| `tool.call.start` | `ToolCallStart` |
| `tool.call.end` | `ToolCallEnd`（执行完工具后） |
| `tool.result` | 工具执行结果（新增的，LLM 不直接返回） |
| `assistant.text.done` | `Done`（非 tool_use 时） |
| `turn.done` | 一轮对话结束 |
| `state.changed` | 状态切换（thinking/streaming/executing） |
| `error` | `ProviderError` 或其他错误 |

## isinstance 的判断原理

`isinstance(event, TextDelta)` 不是直接判断 LLM 传来的原始数据，而是判断经过转换后的 Python 对象。完整的数据变换链：

```
LLM API 服务器
    ↓  返回原始 JSON
OpenAI SDK (openai Python 包)
    ↓  解析成 ChatCompletionChunk 对象
openai_compatible.py 的 stream() 方法
    ↓  转换成我们的 LLMEvent 数据类
_process_llm_events
    ↓  这时候才能 isinstance 判断
```

LLM 返回的原始数据：

```json
{"choices": [{"delta": {"content": "你好"}, "finish_reason": null}]}
```

OpenAI SDK 解析后，`stream()` 方法做转换：

```python
async for chunk in response:
    delta = chunk.choices[0].delta
    if delta.content:
        yield TextDelta(delta=delta.content)     # ← 这里转换
```

`_process_llm_events` 收到的 `event` 已经是 `TextDelta` 实例，因为 `stream()` 在 yield 时就构造好了。

为什么自己定义类型而不是直接用 SDK 的对象：不同 LLM provider（DeepSeek、DashScope、MiMo）返回的原始格式有细微差异。通过在 provider 层统一转换成 `TextDelta`、`ThinkingDelta` 等，上层代码不关心底层用的是哪个 provider。

## yield 的原理

`yield` 把函数变成生成器。普通函数执行完才返回，生成器可以"暂停-恢复"：

```python
def count():
    yield 1    # 暂停，把 1 交给调用方
    yield 2    # 调用方要下一个，恢复执行
    yield 3

for num in count():
    print(num)  # 1, 2, 3
```

`async def` + `yield` 是异步生成器，每 yield 一个值就暂停，等调用方要下一个时再恢复。

### 在 agent loop 里的执行流

调用方是 SSE 端点（api/sse.py），大致逻辑：

```python
async def stream_events(request, session_id):
    agent = create_agent(session_id)
    async for event in agent.run(user_input):
        await sse_send(event)  # 通过 SSE 推送给前端
```

执行流：

```
agent.run("你好")
  → yield STATE_CHANGED(THINKING)   → SSE 推送 → 前端显示"思考中..."
  → 暂停...等调用方处理完...
  → 恢复，调 LLM
  → yield ASSISTANT_TEXT_DELTA("你") → SSE 推送 → 前端逐字显示
  → 暂停...
  → 恢复
  → yield ASSISTANT_TEXT_DELTA("好") → SSE 推送
  → ...直到 TURN_DONE
```

`run()` 出口统一是 FrontendEvent。内部两层：

```
_stream_llm()           → yield LLMEvent（原始 LLM 事件）
    ↓ 传给
_process_llm_events()   → 翻译成 FrontendEvent，yield 出去
    ↓ 传给
run()                   → 原样 yield 给调用方
```

`run()` 自己也直接 yield（比如状态变化），但对调用方来说只看到 FrontendEvent，内部的 LLMEvent 转换是透明的。

## ReAct 循环流程

ReAct = Reason → Act → Observe，循环执行：

```
用户输入
  ↓
[准备] 读历史 → 构建 messages → 检查是否需要压缩
  ↓
┌─── ReAct 循环（最多 max_steps 轮）──────────┐
│                                              │
│  Step 1: Reason — 调 LLM，拿到流式回复       │
│  ↓                                           │
│  Step 2: _process_llm_events 处理事件流       │
│    ├─ 文本 → 缓存 + 推送给前端               │
│    ├─ 工具调用 → 收集到 _current_tool_calls   │
│    ├─ Done(tool_use) → 执行工具 → 把结果      │
│    │   加回 messages → 继续循环               │
│    └─ Done(其他) → 结束                       │
│                                              │
└──────────────────────────────────────────────┘
  ↓
返回 IDLE
```

## 消息流转示意

一轮包含工具调用的完整对话：

```
messages = [system, user_input]

── 第 1 轮 ──
LLM: "我来查一下你的简历" + ToolCallStart(read_resume)
     → _current_tool_calls = [read_resume]
LLM: Done(stop_reason="tool_use")
     → 执行 read_resume → 得到简历内容
     → messages.append({role: "tool", content: 简历})
     → _react_should_continue = True → 继续循环

── 第 2 轮 ──
messages 现在包含工具结果
LLM: "根据你的简历，我看到你有 3 年 Python 经验..."
     → _text_buffer 逐步积累
LLM: Done(stop_reason="end_turn")
     → yield ASSISTANT_TEXT_DONE + TURN_DONE
     → done = True → 退出循环
```

## Fallback 机制

当主 LLM 返回 ProviderError 且 retryable=True 时，递归调用 `_process_llm_events`，用 fallback LLM 的事件流。因为走的是同一个方法，fallback 的文本、工具调用、结束逻辑和主路径完全一样。
