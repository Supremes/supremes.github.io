
老大，**TLDR：Spring AI 最大的亮点不是“帮你写 Agent”，而是把模型调用、Tool Calling、流式处理、Spring Bean、可观测性等基础设施做成统一且可组合的运行时。** 相比手搓 Agent，最值得深读的是那些看起来简单、实际隐藏大量边界条件的部分：**Tool Calling 闭环、Advisor 链、流式工具调用、上下文传播和自动配置**。

```text
你仍要负责                         Spring AI 值得复用
┌──────────────────────┐          ┌────────────────────────┐
│ 任务规划、策略、权限   │          │ 模型与 Provider 抽象     │
│ maxSteps、重规划       │   ───▶   │ Tool Schema 与执行闭环   │
│ 多 Agent、持久化状态   │          │ 流式解析与消息回填       │
│ 业务记忆、评估、安全   │          │ Advisor、Observation     │
└──────────────────────┘          └────────────────────────┘
```

## Spring AI 的核心亮点

|亮点|相比手搓解决了什么|评价|
|---|---|---|
|统一 Model API|屏蔽 OpenAI、Anthropic、Ollama 等 Provider 差异|有价值，但只是基础层|
| `ChatClient` Fluent API|统一 Prompt、Options、Advisor、Tool 和输出转换|Spring 风格的组合入口|
|Tool Calling Runtime|Schema 生成、参数反序列化、Bean 定位、结果回填、再次调用模型|**最有含金量**|
| `call()` / `stream()` 双路径|同时处理完整响应与增量 chunk，且都支持 Tool Calling|**最容易手搓出错**|
|Advisor Chain|用责任链实现日志、Memory、RAG、Guardrail 等横切增强|**扩展设计最值得学习**|
|Spring Boot 自动配置|由配置生成 Model、API、Retry、Tool Resolver 等 Bean|工程落地效率高|
|Observation|将 Chat、Advisor、Tool、VectorStore 纳入 Micrometer|生产环境价值高|
|VectorStore 抽象|统一 `Document / SearchRequest / similaritySearch` |做 RAG 时值得读|

## 最值得深读的 5 个部分

### 1. Tool Calling 闭环：第一优先级

这是 Spring AI 最接近 Agent Runtime 的核心：

```text
模型产生 Tool Call
  → 定位 ToolCallback
  → JSON 参数转 Java 对象
  → 调用 Function Bean
  → 结果转 ToolResponseMessage
  → 追加 conversationHistory
  → 再次请求模型
```

按顺序阅读：

1. `DefaultToolExecutionEligibilityPredicate`：什么条件下执行工具。
2. `DefaultToolCallingManager.resolveToolDefinitions()`：工具如何进入模型请求。
3. `DefaultToolCallingManager.executeToolCalls()`：Action 如何变成 Observation。
4. `SpringBeanToolCallbackResolver`：如何通过 Bean 名定位 `Function`。
5. `FunctionToolCallback.call()`：JSON → Request → `Function.apply()` → String。
6. `ToolExecutionExceptionProcessor`：工具异常如何反馈给模型。

读完必须能解释：**为什么工具返回值不是最终答案，而要作为 `ToolResponseMessage` 再喂给模型。**

### 2. `OpenAiChatModel` 的递归循环：第二优先级

重点不是 HTTP，而是 ReAct 循环如何被隐藏在 Model 实现里：

- 非流式：`call() → internalCall() → executeToolCalls() → internalCall(...)`
- 流式：`stream() → internalStream() → executeToolCalls() → internalStream(...)`

重点阅读：

- `buildRequestPrompt()`：运行时 Options 与默认 Options 如何合并。
- `createRequest()`：Message、Tool Definition 如何转换为 Provider DTO。
- `internalCall()`：同步递归与 Usage 累积。
- `internalStream()`：响应式递归、`boundedElastic` 和消息聚合。

这是理解“**Spring AI 的 Agent 循环其实位于 ChatModel 层**”的关键。

### 3. 流式 Tool Calling：第三优先级

普通文本 chunk 拼接并不难，难点是模型会把工具调用拆成多段：

```text
chunk 1: tool.name = "knowledge"
chunk 2: tool.name = "SearchTool"
chunk 3: arguments = "{\"query\":"
chunk 4: arguments = "\"Spring AI\"}"
```

重点阅读：

- `OpenAiApi.chatCompletionStream()`
- `[DONE]` 过滤
- `windowUntil()`
- `reduce()` 与 `chunkMerger`
- `OpenAiChatModel.internalStream()`
- `MessageAggregator`
- `ToolCallReactiveContextHolder`

手搓时最容易犯的错误是：**参数还没聚合完整就执行工具、重复下发工具调用 chunk、跨线程丢失上下文。**

### 4. Advisor Chain：第四优先级

Advisor 是 Spring AI 区别于直接封装 SDK 的重要设计：

```text
ChatClientRequest
  → Logging Advisor
  → Memory Advisor
  → RAG Advisor
  → Guardrail Advisor
  → ChatModelCallAdvisor / ChatModelStreamAdvisor
```

重点阅读：

- `DefaultChatClient.buildAdvisorChain()`
- `DefaultAroundAdvisorChain.nextCall()`
- `DefaultAroundAdvisorChain.nextStream()`
- `ChatModelCallAdvisor`
- `ChatModelStreamAdvisor`

关注三个问题：

1. Advisor 如何修改 Prompt 和 Context？
2. 同步 Advisor 与流式 Advisor 为什么必须分开？
3. 为什么 Model Advisor 必须位于责任链末端？

这部分非常适合迁移到你自己的中间件、审计、权限和 Guardrail 设计中。

### 5. Reactor 上下文与生产可观测性：第五优先级

在同步代码里依赖 `ThreadLocal` 很自然，但流式调用会切换线程。你当前项目中的：

```java
.contextCapture()
Hooks.enableAutomaticContextPropagation()
StepCollectorContextAccessor
AiInteractionContextAccessor
```

正是在补足这个边界。建议结合 Spring AI 的 Observation 一起读：

- ChatClient Observation
- ChatModel Observation
- Advisor Observation
- Tool Calling Observation
- `ObservationThreadLocalAccessor`

这部分决定 Agent 在生产环境里能否正确关联：**session、trace、tool call、token usage 和错误链路**。

## 第二梯队：按业务需要阅读

- **RAG：** `Document → EmbeddingModel → VectorStore → SearchRequest`；重点理解抽象边界，具体 PGVector SQL 不必先深挖。
- **Structured Output：** `BeanOutputConverter`、原生 JSON Schema 输出；适合规划器和分类器。
- **AutoConfiguration：** 阅读 Bean 创建条件、配置属性、默认组件如何覆盖；如果要自定义 Provider，优先级会上升。
- **Retry 与 Observation Convention：** 做生产治理时再深入。

## 可以先略读的部分

- 各 Provider 大量 DTO 与字段映射。
- 每个 Starter 重复的配置属性代码。
- 简单的 `content()`、Builder 委托方法。
- 不准备使用的向量数据库实现。
- Provider 特有的图片、音频等能力。

## Spring AI 不替你解决什么

它不是完整的 Agent 编排框架，默认不会替你提供：

- 可靠的任务规划与计划校验。
- 严格的 `maxSteps`、成本预算和循环检测。
- Durable Execution、暂停恢复和事件溯源。
- 多 Agent 调度与上下文隔离。
- 工具权限、沙箱和人工审批。
- 业务记忆治理、评估体系与安全策略。

这些正是 dawn-ai 中 `AgentOrchestrator`、`TaskPlanner`、`StepCollector`、`ToolExecutionAspect`、Sub-Agent 和 Memory 模块存在的原因。

**推荐投入比例：** 40% 读 Tool Calling，25% 读 `internalCall/internalStream`，20% 读 Advisor，10% 读上下文传播与 Observation，5% 浏览自动配置和 Provider DTO。掌握前四项后，你既能正确使用 Spring AI，也能判断哪些能力应该继续使用框架、哪些必须由自己的 Agent Runtime 承担。




# Tool Calling Runtime



# Advisor Chain

