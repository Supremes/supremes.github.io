---
updated: 2026-06-05 14:04
title: PI
---



- 定义了 AgentEvent，管理生命周期

```tsx
/**
 * Events emitted by the Agent for UI updates.
 *
 * `agent_end` is the last event emitted for a run, but awaited `Agent.subscribe()`
 * listeners for that event are still part of run settlement. The agent becomes
 * idle only after those listeners finish.
 */
export type AgentEvent =
	// Agent lifecycle
	| { type: "agent_start" }
	| { type: "agent_end"; messages: AgentMessage[] }
	// Turn lifecycle - a turn is one assistant response + any tool calls/results
	| { type: "turn_start" }
	| { type: "turn_end"; message: AgentMessage; toolResults: ToolResultMessage[] }
	// Message lifecycle - emitted for user, assistant, and toolResult messages
	| { type: "message_start"; message: AgentMessage }
	// Only emitted for assistant messages during streaming
	| { type: "message_update"; message: AgentMessage; assistantMessageEvent: AssistantMessageEvent }
	| { type: "message_end"; message: AgentMessage }
	// Tool execution lifecycle
	| { type: "tool_execution_start"; toolCallId: string; toolName: string; args: any }
	| { type: "tool_execution_update"; toolCallId: string; toolName: string; args: any; partialResult: any }
	| { type: "tool_execution_end"; toolCallId: string; toolName: string; result: any; isError: boolean };
```



- 引入 turn，方便做 hook: Turn lifecycle - a turn is one assistant response + any tool calls/results

​	no toolcall

```
prompt("Hello")
├─ agent_start
├─ turn_start
├─ message_start   { message: userMessage }      // Your prompt
├─ message_end     { message: userMessage }
├─ message_start   { message: assistantMessage } // LLM starts responding
├─ message_update  { message: partial... }       // Streaming chunks
├─ message_update  { message: partial... }
├─ message_end     { message: assistantMessage } // Complete response
├─ turn_end        { message, toolResults: [] }
└─ agent_end       { messages: [...] }
```

with toolcall

```
prompt("Read config.json")
├─ agent_start
├─ turn_start
├─ message_start/end  { userMessage }
├─ message_start      { assistantMessage with toolCall }
├─ message_update...
├─ message_end        { assistantMessage }
├─ tool_execution_start  { toolCallId, toolName, args }
├─ tool_execution_update { partialResult }           // If tool streams
├─ tool_execution_end    { toolCallId, result }
├─ message_start/end  { toolResultMessage }
├─ turn_end           { message, toolResults: [toolResult] }
│
├─ turn_start                                        // Next turn
├─ message_start      { assistantMessage }           // LLM responds to tool result
├─ message_update...
├─ message_end
├─ turn_end
└─ agent_end
```

- tool 执行方式可配置，可以并行或者串行





老大，4 份文档读完了。它们是 `pi-agent-core` 中 **AgentHarness（高层编排层）** 的设计笔记——比 README 更深一层，讲的是「在 agent-loop 之上怎么做会话持久化、运行时配置、钩子、可观测性和崩溃恢复」。下面是提炼版。

---

# pi-agent-core · AgentHarness 设计精炼版

## 0. 一句话定位

`AgentHarness` 是 agent-loop 之上的**编排层**，独占五件事：**会话持久化、运行时配置、资源解析、操作锁（phase）、面向扩展的安全变更语义**。核心目标：让钩子/监听器能在事件回调里安全调用 harness 公共 API，而**不破坏在途快照、不打乱持久化顺序、不丢挂起写入、不死锁**。

---

## 1. AgentHarness 生命周期（agent-harness.md）

**四类状态（关键心智模型）**

| 状态           | 含义                                                       | 读写语义                                                     |
| -------------- | ---------------------------------------------------------- | ------------------------------------------------------------ |
| Harness config | 最新运行时配置（model/thinking/tools/resources/系统提示…） | getter 返回**最新配置**，非在途快照；setter 立即生效但只影响**下一轮** |
| Turn snapshot  | 单轮 LLM 调用冻结的具体状态，由 `createTurnState()` 创建   | 整轮逻辑共用同一快照；数组浅拷贝                             |
| Session        | **仅持久化条目**（append-only）                            | 读只返回已持久化状态，不含挂起写入                           |
| Pending writes | busy 期间请求的会话写入                                    | 排队，在 save point / 结算 / 失败清理时刷盘，**绝不丢弃**    |

**Phase 锁**：`idle | turn | compaction | branch_summary | retry`
- **结构性操作**（prompt / skill / promptFromTemplate / compact / navigateTree）要求 `idle`，否则 reject `"busy"`
- **turn 内允许**：steer / followUp / nextTurn / abort / 运行时 setter

**Save point**（核心机制）：一轮 assistant + 工具结果完成后 → ① 刷挂起写入 ② 若循环继续则建新快照 ③ 应用新 context/model/thinking 给下一轮。**让 turn 中途的配置变更影响下一轮，却永不改在途 provider 请求**。靠 `AssistantMessageStream` 解耦了 provider 传输与下游消费，所以 save-point 工作可直接 await，顺序确定。

**错误分层**：底层能力用 `Result<T,E>`（不抛）；高层编排（Session / AgentHarness）直接 throw，统一归一化为 `AgentHarnessError`（子系统错误挂 `cause`）。commit 后钩子失败不回滚，方法 reject code `"hook"`。

**Abort**：中止底层 run + 清 steer/followUp 队列；**不清** nextTurn 消息、**不丢**挂起写入。

---

## 2. Hooks 设计（hooks.md）

**核心思想：事件自带结果类型（type-only phantom），无结果映射表。**

```ts
interface HookEvent<TType, TResult = void> { type: TType; readonly [HookResult]?: TResult }
```

**双 API 分工**
- `observe()` — 看**所有**事件，只读，返回值忽略
- `on(type, handler)` — 参与该事件语义，可返回结果
- `emit(event)` — harness 唯一调用入口；harness 不存 handler、不懂扩展策略

**各事件的归约语义（reducer）**
| 事件                                 | 语义                           |
| ------------------------------------ | ------------------------------ |
| context / provider_request / payload | 顺序 transform，后者见前者输出 |
| before_agent_start                   | 收集注入消息 + 链式拼系统提示  |
| tool_call                            | 顺序，遇 `block` 早退          |
| tool_result                          | 顺序累积 patch，后者见前面补丁 |
| session_before_*                     | 顺序，遇 `cancel` 早退         |

**留的口子**：错误策略需显式（coding-agent 默认 `"continue"`）；需要 source 元数据（哪个扩展产生）→ 用 `createScope({sourceInfo})`；tools/commands/shortcuts 等是**注册表不是钩子**，不进 harness。

---

## 3. 可观测性（observability.md）

**目标：让 ai/agent 可观测，但不绑定 OTel/Sentry/Node API。**

**思路**：pi 只发**稳定结构化的生命周期事件**（start/end/error），外部 adapter 自行转成 OTel span / Sentry / 日志。

- 模型：trace（一棵因果树，如一次 turn）+ span（一次计时操作，用 ID 表示）
- 核心 API：`traceOperation(name, payload, fn)` 自动建 span、串父子、发 start/end/error
- 异步上下文：`AsyncLocalStorage`（Node 版 ThreadLocal）做**运行时 adapter**，不进核心抽象（要跑 Bun/浏览器/worker）
- **安全默认**：provider/model/token/cost/status 可发；prompt/completion/tool args/文件内容/key/headers **默认不发**
- 铁律：可观测订阅者是**被动的**，错误必须吞掉，绝不影响 pi 执行（与控制面的 hooks 区分）

事件名：`pi.agent.prompt` / `pi.agent.turn` / `pi.ai.provider.request` / `pi.session.append_entry` …

---

## 4. 持久化与崩溃恢复（durable-harness.md）

**定位：不追求「完全持久」，只做「半持久」**——因为 tools/model providers/扩展/系统提示回调都是宿主提供的运行时 JS，无法序列化。

**核心原则**
- **Session = 全部持久化状态**（不只是 transcript），单一 append-only 日志，不加 sidecar
- harness 只持久化**可序列化配置**（如 active tool **名字**），不存具体 tool 实现
- 恢复从**持久边界重启**，不从在途 provider 流恢复（provider 流不可续）
- 每个被接受的变更，**必须在公共 API resolve 前先持久化**

**恢复策略（默认保守）**
| 中断点                     | 处理                                                      |
| -------------------------- | --------------------------------------------------------- |
| 未完成 turn                | 标记 interrupted，保留队列/挂起写入，回 idle              |
| 未完成 provider 请求       | 标记 interrupted，**不自动重试**                          |
| 未完成 tool call           | 追加 error 结果；**仅当 tool 声明幂等/retry-safe 才重试** |
| 未完成 compaction / 树导航 | 无最终条目则重跑                                          |

宿主 resume 时须重建：model 注册表、tool 注册表、扩展集与顺序、资源加载器、系统提示、auth、app 钩子。

---

## 总览图

```mermaid
graph TD
    A["应用 / 扩展"] -->|公共 API + 钩子| H["AgentHarness 编排层"]
    H -->|createTurnState 冻结快照| L["agent-loop 底层循环"]
    H -->|append-only 持久化| S["Session 日志"]
    H -->|emit 事件| K["Hooks 控制面 · 可改执行"]
    H -->|traceOperation| O["Observability 被动面 · 不可改执行"]
    S -->|reduce 日志| R["崩溃恢复 · 半持久"]
```

---

**贯穿四份文档的一条主线**：**「快照隔离 + append-only 日志 + 确定性顺序」**。在途请求用冻结快照保护，所有变更落成可归约的持久条目，钩子能改执行、观测只能旁观、恢复靠重放日志。这套设计让 harness 既可被扩展深度介入，又不会被并发/重入/崩溃搞乱状态。



它和我刚总结的那 4 份 docs 是**互补的两层**：

- **README**（你现在打开的这篇）：讲 **`Agent` 类 + 底层 `agentLoop`** 的**用法层**——事件序列、`convertToLlm`/`transformContext` 消息流、steering/follow-up、tools、`beforeToolCall`/`afterToolCall`、`terminate`、proxy、自定义消息类型。
- **docs/**（agent-harness / hooks / observability / durable）：讲 **`AgentHarness` 编排层**的**设计层**——会话持久化、phase 锁、save point、钩子归约、可观测性、崩溃恢复。

补充一个我从这篇 README 里抓到、但之前没强调的**关键细节**——它正好补全了你那个问题的边界：

> **`shouldStopAfterTurn`**：在 `turn_end` 之后、轮询 steering/follow-up 之前、启动下一次 LLM 调用之前触发。返回 `true` 就直接 `agent_end`，**但不中止 provider 流、不取消运行中的工具、不改 stop reason**。

这就是为什么「turn 切在工具之后」是有意为之——它给了一个「LLM 还没消费工具结果前就能优雅刹车」的窗口（典型用途：下一轮前发现该压缩上下文）。

还有一个 README 里值得记的对比点：

|      | 底层 `agentLoop()`                                   | `Agent` 类                                                   |
| ---- | ---------------------------------------------------- | ------------------------------------------------------------ |
| 事件 | 纯观察性，**不等**你的异步处理 settle 就继续下一阶段 | `message_end` 是 **barrier**，`beforeToolCall` 能看到已含该 assistant 消息的状态 |
| 适用 | 要极致控制                                           | 需要「消息处理先于工具预检」的顺序保证                       |

