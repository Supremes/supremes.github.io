# agentscope-java 中的 Mono 设计详解

## 一句话结论

`agentscope-java` 里确实有一套明确的 **Mono 设计**，但它不是“全仓库只用 Mono”，而是更准确地说成：**单值异步边界统一用 `Mono`，多值/流式边界统一用 `Flux`**。真正的设计中心在 `agentscope-core`；扩展模块更多是在把外部 SDK、HTTP、向量库、MCP 等能力适配进这套 Reactor 协议。

## 从第一性原理看，这个设计到底在解决什么问题

这个框架要处理两类完全不同的返回语义：

1. 一次调用最终只产出一个结果，比如 agent 最终回复、tool 执行结果、memory 检索结果。
2. 一次调用会持续产出事件或 token，比如模型 streaming、事件流、WebSocket 接收。

所以它没有粗暴地“全部统一成一个类型”，而是先把语义分清：

- **单值异步**：`Mono<T>`
- **多值/流式**：`Flux<T>`

这不是编码风格问题，而是接口语义问题。

## 架构层：Mono 在框架里的位置

### 1. Agent 层：Mono 表达“最终答复”

核心接口和实现：

- `agentscope-core/src/main/java/io/agentscope/core/agent/CallableAgent.java`
  - `call(...) -> Mono<Msg>`
- `agentscope-core/src/main/java/io/agentscope/core/agent/ObservableAgent.java`
  - `observe(...) -> Mono<Void>`
- `agentscope-core/src/main/java/io/agentscope/core/agent/StreamableAgent.java`
  - `stream(...) -> Flux<Event>`
- `agentscope-core/src/main/java/io/agentscope/core/agent/AgentBase.java`

这里的分工非常清楚：

- `call()`：返回最终结果
- `stream()`：返回执行过程事件

`AgentBase.call(...)` 用 `Mono.using(...)` 管理完整生命周期，包括：

- 运行状态保护
- pre/post hook
- tracing 接入
- 错误恢复

这说明 Mono 在 agent 层不是随手包一下，而是生命周期协议的一部分。

### 2. Model 层：主接口其实是 Flux

最关键的顶层接口：

- `agentscope-core/src/main/java/io/agentscope/core/model/Model.java`
  - `stream(List<Msg>, List<ToolSchema>, GenerateOptions) -> Flux<ChatResponse>`

这点很重要：**模型层把 streaming 当作一等公民**。

例如：

- `agentscope-core/src/main/java/io/agentscope/core/model/OpenAIChatModel.java`

即使底层是非流式调用，它也会把单次结果包装成单元素 `Flux` 返回，而不是额外定义一套 `Mono<ChatResponse>` 主接口。

所以框架的真实结构是：

- **Agent / Tool / Hook / Memory**：Mono 主导
- **Model / Event / Audio / Transport stream**：Flux 主导

## API 层：哪些抽象返回 Mono，语义分别是什么

### Agent 相关

- `CallableAgent.call(...) -> Mono<Msg>`
  - 一次 agent 调用的最终回复
- `ObservableAgent.observe(...) -> Mono<Void>`
  - 观察/写入上下文，没有业务结果返回

### Tool 相关

- `agentscope-core/src/main/java/io/agentscope/core/tool/AgentTool.java`
  - `callAsync(...) -> Mono<ToolResultBlock>`
- `agentscope-core/src/main/java/io/agentscope/core/tool/Toolkit.java`
  - `callTool(...) -> Mono<ToolResultBlock>`
  - `callTools(...) -> Mono<List<ToolResultBlock>>`

这里 Mono 表达的是：**一次工具执行最终产出一个结果块**。

### Hook 相关

- `agentscope-core/src/main/java/io/agentscope/core/hook/Hook.java`
  - `onEvent(T event) -> Mono<T>`

含义是：hook 可以异步处理事件，并且可以返回修改后的事件对象。

### Memory / RAG / Plan

- `agentscope-core/src/main/java/io/agentscope/core/memory/LongTermMemory.java`
  - `record(...) -> Mono<Void>`
  - `retrieve(...) -> Mono<String>`
- `agentscope-core/src/main/java/io/agentscope/core/rag/Knowledge.java`
  - `addDocuments(...) -> Mono<Void>`
  - `retrieve(...) -> Mono<List<Document>>`
- `agentscope-core/src/main/java/io/agentscope/core/plan/PlanStorage.java`
  - `addPlan/getPlan/getPlans -> Mono<...>`

这些接口都表达“单次异步完成值”。

### 网络与传输

- `agentscope-core/src/main/java/io/agentscope/core/model/transport/websocket/WebSocketTransport.java`
  - `connect(...) -> Mono<WebSocketConnection<T>>`
- `agentscope-core/src/main/java/io/agentscope/core/model/transport/websocket/WebSocketConnection.java`
  - `send/close -> Mono<Void>`
  - `receive -> Flux<T>`

语义也很一致：

- 建连/发送/关闭：单次完成，用 Mono
- 持续接收：多值流，用 Flux

## 执行层：Mono 是怎么被串起来的

最关键的执行骨架主要看这几个类：

1. `agentscope-core/src/main/java/io/agentscope/core/agent/AgentBase.java`
2. `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java`
3. `agentscope-core/src/main/java/io/agentscope/core/tool/ToolExecutor.java`
4. `agentscope-core/src/main/java/io/agentscope/core/tool/ToolMethodInvoker.java`

常见组合方式：

- `flatMap`：串联单值异步步骤
- `flatMapMany`：从 Mono 进入 Flux
- `concatMap`：按顺序执行
- `then / thenReturn`：只关心完成，不关心前一步结果
- `timeout`：超时控制
- `retryWhen`：重试控制
- `onErrorResume / onErrorMap`：错误恢复与重映射

也就是说，Mono 在这里不只是“一个 future-like 容器”，而是整个 agent/tool/hook/memory 执行链的基本组合单位。

## 为什么这里用 Mono，而不是同步返回值、CompletableFuture 或全用 Flux

### 1. 为什么不是同步返回值

因为这个框架天然跨越大量 I/O 边界：

- 模型调用
- 工具调用
- RAG 检索
- Long-term memory
- WebSocket / SSE / HTTP
- MCP / Studio / Trinity / Mem0 / ReMe 等外部服务

如果全部设计成同步返回值，会导致：

- hook 链难组合
- tool 链难组合
- streaming 和 non-streaming 接口不统一
- tracing/context 传播更难一致

### 2. 为什么不是 CompletableFuture

`CompletableFuture` 在这个项目里是兼容输入，不是主协议。

最典型的是：

- `agentscope-core/src/main/java/io/agentscope/core/tool/ToolMethodInvoker.java`

它支持三类工具方法返回值：

- 普通同步值
- `CompletableFuture`
- `Mono`

但最终都会被统一收敛成 `Mono<ToolResultBlock>`：

- 同步值：`Mono.fromCallable(...)`
- Future：`Mono.fromFuture(...)`
- Mono：直接展开继续处理

所以这里的真正设计意图是：

**框架内部统一协议是 Reactor；CompletableFuture 只是兼容层。**

### 3. 为什么不是全都用 Flux

因为很多操作本质上只有一个结果：

- 一次 agent 调用最终只得到一个 `Msg`
- 一次 tool 调用最终只得到一个 `ToolResultBlock`
- 一次 retrieve 最终只得到一个 `String` 或一个列表

强行全部用 Flux 会削弱接口语义，让“单值完成”和“多值流式”不再清晰。

## 上下文传播与 tracing：这是 Mono 设计里最深的一层

如果一个项目只是零散用 Reactor，通常不会认真设计上下文传播；但 `agentscope-java` 这里是做过架构处理的。

### 1. AgentBase 中的上下文传递

在：

- `agentscope-core/src/main/java/io/agentscope/core/agent/AgentBase.java`

可以看到：

- `Flux.deferContextual(...)`
- `contextWrite(context -> context.putAll(ctxView))`

含义是：把外层 Reactor Context 显式带入内部异步链，避免 trace/session 等上下文在 streaming 场景下丢失。

### 2. SubAgentTool 中的上下文继承

在：

- `agentscope-core/src/main/java/io/agentscope/core/tool/subagent/SubAgentTool.java`

子 agent 的调用也会显式继承 Reactor Context。  
这说明上下文传播不是主链路偶然支持，而是设计要求的一部分。

### 3. TracerRegistry 的全局 Reactor hook

在：

- `agentscope-core/src/main/java/io/agentscope/core/tracing/TracerRegistry.java`

它通过 `Hooks.onEachOperator(...)` 为全局 Reactor operator 注册 hook，让 tracing context 能跨异步边界传播。

这也解释了为什么这个项目更偏向 Reactor 而不是裸 `CompletableFuture`：

- `CompletableFuture` 有结果
- Reactor 除了结果，还有流、组合能力、上下文、全局 hook 能力

## 错误处理模式

这个项目里比较典型的 Reactor 错误处理模式有：

- `onErrorResume(...)`
- `onErrorMap(...)`
- `timeout(...)`
- `retryWhen(...)`

关键位置包括：

- `AgentBase`：agent 调用的统一错误收敛
- `ToolExecutor`：tool 的超时、重试、失败兜底
- transport 层：把网络/协议错误转换成统一异常
- hook / memory / web controller：局部恢复或降级

这说明 Mono 在这里还有一个额外职责：  
**把错误也纳入统一的异步组合模型。**

## 工程现实：它不是“纯 reactive 到底”

这一点要说实话。

仓库里存在少量桥接点，会把 reactive 调用转回同步：

- `agentscope-core/src/main/java/io/agentscope/core/rag/KnowledgeRetrievalTools.java`
  - 使用 `.block()`
- `agentscope-core/src/main/java/io/agentscope/core/model/OllamaChatModel.java`
  - 使用 `.blockLast()`
- `agentscope-core/src/main/java/io/agentscope/core/hook/TTSHook.java`
  - 使用 `.blockLast()`

所以更准确的描述应该是：

**它是一套以 Reactor 为主协议的混合式架构，不是端到端纯 non-blocking 的 reactive 系统。**

这不是缺点本身，而是工程权衡：

- 框架内部需要统一异步协议与组合能力
- 但边界处仍然要兼容同步 API、现有 SDK 和某些 imperative 场景

## 关键文件阅读建议

建议按下面顺序看源码：

1. `agentscope-core/src/main/java/io/agentscope/core/agent/AgentBase.java`
   - 先看 Mono/Flux 生命周期骨架
2. `agentscope-core/src/main/java/io/agentscope/core/ReActAgent.java`
   - 再看 reasoning、tool、memory 如何组合
3. `agentscope-core/src/main/java/io/agentscope/core/model/Model.java`
   - 理解为什么模型主接口是 Flux
4. `agentscope-core/src/main/java/io/agentscope/core/model/OpenAIChatModel.java`
   - 看非流式如何包装成 Flux
5. `agentscope-core/src/main/java/io/agentscope/core/tool/ToolExecutor.java`
   - 看 tool 的调度、并发、超时、重试
6. `agentscope-core/src/main/java/io/agentscope/core/tool/ToolMethodInvoker.java`
   - 看 sync / Future / Mono 的统一桥接
7. `agentscope-core/src/main/java/io/agentscope/core/hook/Hook.java`
   - 看 hook 为什么返回 `Mono<T>`
8. `agentscope-core/src/main/java/io/agentscope/core/tracing/TracerRegistry.java`
   - 看 Reactor Context 与 tracing 的全局传播

## 最终总结

`agentscope-java` 的 Mono 设计，核心价值不在于“项目用了 Reactor”，而在于它把：

- agent
- tool
- hook
- memory
- tracing
- sub-agent

这些原本容易分裂成不同异步风格的部件，统一放进了一套 **可组合、可传播上下文、可统一处理错误** 的 Reactor 协议里。

其中最关键的抽象边界是：

- **单值异步 = Mono**
- **多值流式 = Flux**

这是理解整个 `agentscope-java` 执行模型的关键入口。
