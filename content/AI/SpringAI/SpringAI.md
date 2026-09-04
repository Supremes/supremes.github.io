
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



---

# 核心机制拆解（源码对照笔记）

> 对照版本 **Spring AI 1.1.4**（dawn-ai 当前依赖）。下面所有代码片段都是从 `-sources.jar` 里摘的真实源码，为了突出主干做了裁剪。
> 用法：平时只看「时序图 + 类职责表 + 自测题」；某个自测题答不上来，再回去看那一段源码。

## 怎么学：别通读，只定点看 4 个方法

| 亮点 | 要不要打开源码 | 定点看什么 | 预计 |
|---|---|---|---|
| ① Tool Calling 闭环 | **要** | `DefaultToolCallingManager.executeToolCall()` 一个方法 | 20 分钟 |
| ② ChatModel 递归 | 不用 | 看本文那 12 行伪代码就够，剩下全是 DTO 噪音 | 5 分钟 |
| ③ 流式 Tool Calling | **要** | `OpenAiApi.chatCompletionStream()` 那段 Reactor 管线 | 30 分钟 |
| ④ Advisor Chain | 不用 | 就是 Servlet Filter，记住三条约束即可 | 10 分钟 |
| ⑤ Reactor 上下文 | 不用 | 记踩坑清单，比记实现有用 | 10 分钟 |

跟读源码效率低，是因为大部分时间花在 DTO 转换和 Builder 样板上。真正有信息量的代码不超过 300 行，全在下面了。

---

## 1. Tool Calling 闭环

**本质：** 模型只会「说」要调什么工具，执行、异常兜底、结果回填全是框架干的。整套是同步的、无状态的，一轮推一轮。

### 数据流

```text
ChatModel.internalCall(prompt)
   │
   ├─ ToolExecutionEligibilityPredicate 判定
   │     两个条件同时满足才执行：
   │     internalToolExecutionEnabled == true  &&  response.hasToolCalls()
   ▼ 是
ToolCallingManager.executeToolCalls(prompt, response)
   │
   ├─ 挑出第一个带 toolCalls 的 Generation
   ├─ buildToolContext()      ← 你没配 toolContext，就不会注入 TOOL_CALL_HISTORY
   │
   ├─ for (每个 toolCall)：
   │     ├─ 先在 options.toolCallbacks 里按名字找
   │     ├─ 找不到再走 ToolCallbackResolver（Spring Bean / MCP）
   │     ├─ arguments 为空 → 兜底成 "{}"
   │     ├─ toolCallback.call(args, ctx)
   │     │     └─ 抛 ToolExecutionException → ExceptionProcessor 转成文本
   │     └─ 包成 ToolResponse(id, name, result)
   │
   └─ 返回 conversationHistory = 原 messages + AssistantMessage + ToolResponseMessage
   ▼
returnDirect ? ──是──▶ 工具结果直接当答案返回，不再问模型
   │ 否
   ▼
internalCall(new Prompt(conversationHistory, options), 本轮 response)   ← 尾递归
```

### 关键类职责

| 类 | 职责 | 真正要记的点 |
|---|---|---|
| `DefaultToolExecutionEligibilityPredicate` | 判定该不该在框架内执行 | 就 2 行：开关 ON **且** 有 toolCalls |
| `DefaultToolCallingManager` | 编排整个闭环 | ChatModel 只调它一个方法。它**只跑一轮**，不负责递归 |
| `SpringBeanToolCallbackResolver` | 按 Bean 名找 `Function` | 有 `toolCallbacksCache`，解析结果缓存；描述优先级 `@Description` > `@JsonClassDescription` > 从名字推 |
| `FunctionToolCallback` | JSON → 对象 → `apply()` → String | 非 `ToolExecutionException` 的异常会被包一层再抛 |
| `DefaultToolExecutionExceptionProcessor` | 异常怎么反馈给模型 | 默认把 message 当成正常工具结果喂回去 |
| `ToolExecutionResult.returnDirect` | 短路开关 | 多工具时是 **AND**：全都 returnDirect 才短路 |

### 源码：执行循环的核心

```java
// DefaultToolCallingManager#executeToolCall  （已裁剪）
for (AssistantMessage.ToolCall toolCall : assistantMessage.getToolCalls()) {
    String toolName = toolCall.name();

    // 流式下参数可能是 null，兜底成空对象
    final String finalArgs = StringUtils.hasText(toolCall.arguments())
            ? toolCall.arguments() : "{}";

    // 两级查找：先 options 内联，后 resolver
    ToolCallback toolCallback = toolCallbacks.stream()
        .filter(t -> toolName.equals(t.getToolDefinition().name()))
        .findFirst()
        .orElseGet(() -> this.toolCallbackResolver.resolve(toolName));

    if (toolCallback == null) {
        throw new IllegalStateException("No ToolCallback found for tool name: " + toolName);
    }

    // 多个工具全都 returnDirect 才短路 —— 注意是 AND
    returnDirect = (returnDirect == null)
            ? toolCallback.getToolMetadata().returnDirect()
            : returnDirect && toolCallback.getToolMetadata().returnDirect();

    String toolCallResult = observation.observe(() -> {
        try {
            return toolCallback.call(finalArgs, toolContext);
        }
        catch (ToolExecutionException ex) {
            return this.toolExecutionExceptionProcessor.process(ex);  // 异常转文本
        }
    });

    toolResponses.add(new ToolResponse(toolCall.id(), toolName, toolCallResult));
}
```

```java
// DefaultToolExecutionExceptionProcessor#process  （已裁剪）
Throwable cause = exception.getCause();
if (cause instanceof RuntimeException runtimeException) {
    if (this.rethrownExceptions.stream().anyMatch(r -> r.isAssignableFrom(cause.getClass()))) {
        throw runtimeException;                    // 白名单里的直接抛
    }
}
else {
    throw exception;   // ← cause 不是 RuntimeException（IOException/Error），无条件抛
}
if (this.alwaysThrow) { throw exception; }
return exception.getMessage();                     // 默认：当成工具结果喂回模型
```

### 自测

1. **为什么工具返回值不能直接当答案？**
   OpenAI 协议要求工具结果作为 `role=tool` 的消息回到对话历史里，模型看到后才决定是继续调工具还是给最终答案。只有 `returnDirect=true` 才明确跳过这一步。

2. **工具抛异常时模型看到什么？**
   默认看到异常的 `getMessage()`，且当成**正常的工具结果**。所以模型可能会道歉、可能会换参数重试。想让异常真抛出来要配 `alwaysThrow(true)` 或 `rethrowExceptions`。**但注意**：cause 不是 `RuntimeException` 时（比如 `IOException`）无论怎么配都直接抛。

3. **谁负责递归？**
   不是 `ToolCallingManager`，是 `ChatModel.internalCall/internalStream` 自己。Manager 只跑一轮就返回。

### 坑

- `internalToolExecutionEnabled=false` 时框架什么都不做，`ChatResponse` 带着 toolCalls 原样返回给你 —— 这就是「外部执行」模式。**你要自己接管 Agent 循环，就设这个。**
- `ToolContext` 里的 `TOOL_CALL_HISTORY` 只有你自己配了非空 `toolContext` 时才注入。啥都没配，工具里就拿不到对话历史。
- **递归没有 maxSteps。** 模型死循环调工具，Spring AI 不拦你。这正是 dawn-ai 里 `AgentOrchestrator` 存在的理由。

---

## 2. ChatModel 层的递归循环

**本质：** 所谓 Agent Loop，在 Spring AI 里就是 `internalCall` 尾递归调自己。12 行讲完。

```java
ChatResponse internalCall(Prompt prompt, ChatResponse previous) {
    var request  = createRequest(prompt, false);              // Message/Tool → OpenAI DTO
    var response = observe(() -> retry(() -> api.call(request)));
    response.usage = accumulate(response.usage, previous);    // ← 跨轮累加 token

    if (eligibilityPredicate.isToolExecutionRequired(prompt.getOptions(), response)) {
        var result = toolCallingManager.executeToolCalls(prompt, response);
        if (result.returnDirect()) {
            return 包装工具结果直接返回;
        }
        return internalCall(new Prompt(result.conversationHistory(), prompt.getOptions()),
                            response);                        // ← 尾递归，把自己当 previous
    }
    return response;
}
```

| 位置 | 干什么 | 容易忽略的点 |
|---|---|---|
| `call()` | 只做 `buildRequestPrompt()` 然后转 `internalCall` | 入口和递归体拆开，就是为了 options **只 merge 一次** |
| `buildRequestPrompt()` | 运行时 options + 默认 options 合并 | `@JsonIgnore` 的字段 Jackson merge 不到，得手工逐个补 |
| `internalCall()` | 递归主体 | `previousChatResponse` 唯一作用是累加 usage |
| `UsageCalculator.getCumulativeUsage` | token 累加 | 你最后拿到的 usage 是**整个 loop 的总和**，不是最后一轮 |
| `internalStream()` | 响应式版本 | 外面裹 `Flux.deferContextual`，保证每次订阅都是新的冷流 |

### 源码：手工 merge 的那几个字段

```java
// OpenAiChatModel#buildRequestPrompt  （已裁剪）
OpenAiChatOptions requestOptions = ModelOptionsUtils.merge(runtimeOptions, this.defaultOptions,
        OpenAiChatOptions.class);

// 下面这几个字段带 @JsonIgnore，上面那行 merge 不到，必须手工来
requestOptions.setInternalToolExecutionEnabled(ModelOptionsUtils.mergeOption(
        runtimeOptions.getInternalToolExecutionEnabled(),
        this.defaultOptions.getInternalToolExecutionEnabled()));
requestOptions.setToolNames(    ToolCallingChatOptions.mergeToolNames(...));
requestOptions.setToolCallbacks(ToolCallingChatOptions.mergeToolCallbacks(...));
requestOptions.setToolContext(  ToolCallingChatOptions.mergeToolContext(...));
```

### 自测

1. **为什么 `call()` 和 `internalCall()` 要拆成两个方法？** options merge 只能做一次，递归里再 merge 会重复叠加 toolCallbacks。
2. **响应里的 promptTokens 是这一轮的还是全程的？** 全程累加。想看单轮得自己在 Observation 里拆。
3. **流式为什么要 `Flux.deferContextual` 而不是直接返回 Flux？** 一是要拿订阅时的 `contextView` 去接父 Observation，二是保证是冷流、可重订阅。

---

## 3. 流式 Tool Calling 聚合

**本质：** SSE 里一个 tool call 会被拆成好几个 chunk，参数是逐字符流过来的。攒完整这件事在 `OpenAiApi.chatCompletionStream()` 里就干完了 —— `OpenAiChatModel` 拿到的已经是**完整 chunk**。

### 真实 chunk 序列

```text
chunk1  delta.toolCalls=[{id:"call_x", name:"getWeather", arguments:""}]
chunk2  delta.toolCalls=[{id:null,     name:null,        arguments:"{\"ci"}]
chunk3  delta.toolCalls=[{id:null,     name:null,        arguments:"ty\":\"北京\"}"}]
chunk4  delta={}   finishReason=TOOL_CALLS         ← 窗口在这里关闭
```

### Reactor 管线

```java
// OpenAiApi#chatCompletionStream  （已裁剪，注释为原文）
AtomicBoolean isInsideTool = new AtomicBoolean(false);   // 每次调用新建一个，别提成字段

return webClient.post()...bodyToFlux(String.class)
    .takeUntil(SSE_DONE_PREDICATE)          // 收到 [DONE] 断流
    .filter(SSE_DONE_PREDICATE.negate())    // 但 [DONE] 自己不往下传
    .map(content -> jsonToObject(content, ChatCompletionChunk.class))

    // 看到 delta.toolCalls 非空就进入「工具模式」
    .map(chunk -> {
        if (chunkMerger.isStreamingToolFunctionCall(chunk)) { isInsideTool.set(true); }
        return chunk;
    })

    // Flux<Chunk> → Flux<Flux<Chunk>>：返回 true = 当前元素是本窗最后一个
    .windowUntil(chunk -> {
        if (isInsideTool.get() && chunkMerger.isStreamingToolFunctionCallFinish(chunk)) {
            isInsideTool.set(false);
            return true;                    // finishReason==TOOL_CALLS → 切窗
        }
        return !isInsideTool.get();         // 不在工具模式 → 每个 chunk 自成一窗
    })

    // 把窗口内所有 chunk reduce 成一个完整 chunk
    .concatMapIterable(window -> List.of(
        window.reduce(new ChatCompletionChunk(null,null,null,null,null,null,null,null),
                      (prev, cur) -> chunkMerger.merge(prev, cur))))
    .flatMap(mono -> mono);
```

### chunkMerger 的合并规则（精髓在这）

| 字段 | 规则 | 为什么 |
|---|---|---|
| id / model / role / finishReason | current 优先，null 才取 previous | 元数据只在首/末 chunk 出现一次 |
| `function.arguments` | **StringBuilder 拼接** | 全流程唯一真正累加的字段 |
| `function.name` | 有文本才覆盖 | name 只在第一个 chunk 给 |
| `toolCalls` 列表 | **看 `id` 有没有值**：有 id = 新工具，另起一条；无 id = 续上一条 | 区分「新工具」和「参数续传」的唯一依据 |
| `content` | current 覆盖，**不累加** | 非工具场景每个 chunk 自成一窗，reduce 只跑一次，没东西可拼 |

```java
// OpenAiStreamFunctionCallingHelper#merge(ChatCompletionMessage)  （已裁剪）
if (current.toolCalls() != null && !current.toolCalls().isEmpty()) {
    if (current.toolCalls().size() > 1) {
        throw new IllegalStateException("Currently only one tool call is supported per message!");
    }
    var currentToolCall = current.toolCalls().iterator().next();
    if (StringUtils.hasText(currentToolCall.id())) {
        if (lastPreviousTooCall != null) { toolCalls.add(lastPreviousTooCall); }
        toolCalls.add(currentToolCall);                       // 有 id → 新工具，另起一条
    }
    else {
        toolCalls.add(merge(lastPreviousTooCall, currentToolCall));  // 无 id → 续参数
    }
}

// merge(ChatCompletionFunction)：arguments 是唯一拼接的字段
StringBuilder arguments = new StringBuilder();
if (previous.arguments() != null) { arguments.append(previous.arguments()); }
if (current.arguments()  != null) { arguments.append(current.arguments()); }
```

### 自测

1. **`windowUntil` 的 predicate 返回 true 代表什么？**
   当前元素是窗口的**最后一个**，切窗。非工具场景永远返回 true，所以每个 chunk 单独一窗，等于不聚合、直接透传。
2. **拼参数的状态存在哪？**
   存在 `reduce` 的累加器里（一个临时 Chunk 对象）。外部只有一个 `AtomicBoolean isInsideTool` 做模式开关。
3. **为什么 content 用覆盖而不是拼接？**
   文本 chunk 每个自成一窗，`reduce` 只跑一次，previous 是那个空 Chunk，没什么可拼。

### 坑

- `isInsideTool` 是方法内新建的 `AtomicBoolean`，靠闭包捕获。**要是你自己实现时提成了字段，并发请求立刻串。**
- 一个 message 里 current 带多个 toolCall 会直接抛 `IllegalStateException`。并行 tool call 是靠 `id` 分条实现的，不是靠数组。
- `takeUntil([DONE])` —— 某些 OpenAI 兼容 API 不发 `[DONE]`，流会一直挂到超时。
- 手搓时最容易犯的三个错：**参数没聚合完就执行工具、重复下发工具调用 chunk、跨线程丢上下文。**

---

## 4. Advisor Chain

**本质：** 就是 Servlet Filter，但有两条独立的链（call / stream），而且**链是一次性消费的**。

```text
ChatClient.prompt()...call()
   │
   └─ buildAdvisorChain()                        ← 每次调用都重新 build
        ├─ 你的 advisors（Memory / RAG / Logging / Guardrail…）
        └─ 末尾 add ChatModelCallAdvisor + ChatModelStreamAdvisor
        └─ pushAll() 内部立刻 OrderComparator.sort() 重排
   ▼
Deque<CallAdvisor>                 Deque<StreamAdvisor>
   pop() 一个执行一个                  pop() 一个执行一个
   │  advisor.adviseCall(req, chain)  ← advisor 自己决定要不要 chain.nextCall()
   ▼                                  ▼
ChatModelCallAdvisor               ChatModelStreamAdvisor
  chatModel.call(prompt)             chatModel.stream(prompt)
  ↑ 不调 nextCall，是终结点            .publishOn(boundedElastic)
```

| 点 | 事实 | 含义 |
|---|---|---|
| 两条链分开 | `Deque<CallAdvisor>` / `Deque<StreamAdvisor>` 各一条 | 同一个 advisor 想两边都生效，得同时实现两个接口（`BaseAdvisor` 帮你做了） |
| 链有状态 | 用 `pop()` 消费 `ConcurrentLinkedDeque` | **chain 实例用完就废**，所以每次 `call()`/`stream()` 都 `buildAdvisorChain()` |
| Model advisor 沉底 | `getOrder()` 返回 `Ordered.LOWEST_PRECEDENCE` | 它不调 `chain.nextCall()`，是终结点。你的 advisor 只要 order 不是同样最低就一定排在它前面 |
| 排序时机 | `pushAll()` 里 push 完立刻 `reOrder()` | 靠 `getOrder()`，**不是靠添加顺序** |
| Observation | 每个 advisor 一个 span | 链路里能看到每个 advisor 单独的耗时 |
| 结构化输出 | `ChatModelCallAdvisor.augmentWithFormatInstructions()` | format 指令是在**最后一刻**才拼到 user message 尾巴上的 |

```java
// DefaultChatClient#buildAdvisorChain
private BaseAdvisorChain buildAdvisorChain() {
    // At the stack bottom add the model call advisors.
    this.advisors.add(ChatModelCallAdvisor.builder().chatModel(this.chatModel).build());
    this.advisors.add(ChatModelStreamAdvisor.builder().chatModel(this.chatModel).build());
    return DefaultAroundAdvisorChain.builder(this.observationRegistry)
        .pushAll(this.advisors)      // push 完内部立刻 reOrder()
        .build();
}

// DefaultAroundAdvisorChain#nextCall  （已裁剪）
var advisor = this.callAdvisors.pop();          // ← 破坏性消费，链不可复用
return observation.observe(() -> advisor.adviseCall(chatClientRequest, this));
```

### 自测

1. **为什么 call 和 stream 必须两条链？** 返回类型不同（`ChatClientResponse` vs `Flux<ChatClientResponse>`），流式还要处理背压和 Reactor Context 传播，同步逻辑照搬会阻塞。
2. **Model advisor 为什么必须在末端？** 它是唯一不往下传的节点。放中间的话后面的 advisor 永远执行不到。
3. **一个 chain 实例能复用吗？** 不能。`pop()` 是破坏性的，第二次调用会 `No CallAdvisors available to execute`。

### 坑

- 自定义 advisor **忘了调 `chain.nextCall(req)`** → 整条链断在你这，模型压根没被调用，而且不报错。
- 流式 advisor 里做阻塞 IO → 卡住 Reactor 线程。`ChatModelStreamAdvisor` 自己都得 `publishOn(boundedElastic)`。
- 两个 advisor `order` 相同时顺序不确定，别依赖它。

---

## 5. Reactor 上下文与 Observation

**本质：** 流式路径会切线程，ThreadLocal 会丢。Spring AI 用四种手段补。

| 机制 | 解决什么 | 位置 |
|---|---|---|
| `contextWrite(ObservationThreadLocalAccessor.KEY, observation)` | 子 Flux 能找到父 Observation，trace 不断链 | `internalStream` 末尾 / `DefaultAroundAdvisorChain.nextStream` |
| `Flux.deferContextual` + `observation.parentObservation(ctx.getOrDefault(KEY))` | **订阅时**才去取父 span，而不是组装时 | `internalStream` 开头 |
| `ToolCallReactiveContextHolder` | **反向**：把 Reactor Context 塞进 ThreadLocal，让同步的工具代码读得到 | `internalStream` 执行工具那段 |
| `Schedulers.boundedElastic()` | 工具执行是阻塞的，不能占 Reactor 线程 | `subscribeOn(boundedElastic)` |
| `MessageAggregator` | 把流式 chunk 攒成完整 `ChatResponse` **喂给 Observation** | `internalStream` 返回前 |

```java
// OpenAiChatModel#internalStream  （已裁剪，FIXME 是原文注释）
Flux<ChatResponse> flux = chatResponse.flatMap(response -> {
    if (this.toolExecutionEligibilityPredicate.isToolExecutionRequired(prompt.getOptions(), response)) {
        // FIXME: bounded elastic needs to be used since tool calling
        //  is currently only synchronous
        return Flux.deferContextual(ctx -> {
            ToolExecutionResult toolExecutionResult;
            try {
                ToolCallReactiveContextHolder.setContext(ctx);   // Reactor Ctx → ThreadLocal
                toolExecutionResult = this.toolCallingManager.executeToolCalls(prompt, response);
            }
            finally {
                ToolCallReactiveContextHolder.clearContext();    // 必须清，线程会复用
            }
            if (toolExecutionResult.returnDirect()) { return Flux.just(包装结果); }
            return this.internalStream(new Prompt(toolExecutionResult.conversationHistory(),
                                                  prompt.getOptions()), response);
        }).subscribeOn(Schedulers.boundedElastic());
    }
    return Flux.just(response);
})
.doOnError(observation::error)
.doFinally(s -> observation.stop())
.contextWrite(ctx -> ctx.put(ObservationThreadLocalAccessor.KEY, observation));

return new MessageAggregator().aggregate(flux, observationContext::setResponse);
```

### 自测

1. **`ToolCallReactiveContextHolder` 的方向是什么？**
   Reactor Context → ThreadLocal。跟平常 `Hooks.enableAutomaticContextPropagation()`（ThreadLocal → Reactor Context）**方向相反**。因为工具执行是同步阻塞代码，只认 ThreadLocal。
2. **`MessageAggregator` 会改变你收到的流吗？**
   不会。全是 `doOnSubscribe`/`doOnNext`/`doOnComplete` 副作用，纯旁路，只为让 Observation 拿到一份完整响应。
3. **流式下工具执行为什么必须 `subscribeOn(boundedElastic)`？**
   源码注释直说了 —— 工具调用目前只有同步实现。阻塞代码跑在 Netty event loop 上会卡死整个连接。

### 坑（dawn-ai 正在处理的就是这些）

- 自定义 ThreadLocal（`StepCollectorContextAccessor`、`AiInteractionContextAccessor`）必须注册成 `ThreadLocalAccessor` SPI 并开 `Hooks.enableAutomaticContextPropagation()`，否则只在同步路径生效。
- `.contextCapture()` **只在订阅那一刻捕获一次**。工具执行后的递归 `internalStream` 是一次新订阅，得靠 `ToolCallReactiveContextHolder` 补。
- `boundedElastic` 默认线程上限 = CPU×10。工具慢会排队，而且**这个队列没有超时**。

---

## 一页速查

| 问题 | 答案 |
|---|---|
| Agent 循环在哪一层？ | `ChatModel.internalCall/internalStream` 的尾递归，**不在** ChatClient，也不在 ToolCallingManager |
| 怎么关掉框架的自动工具执行？ | `internalToolExecutionEnabled=false`，`ChatResponse` 会带着 toolCalls 原样返回给你 |
| 怎么让工具结果直接当答案？ | 工具标 `returnDirect=true`；多工具时必须**全都**标才生效 |
| 工具异常默认怎么处理？ | 转成文本喂回模型；cause 非 `RuntimeException` 时无条件抛出 |
| 流式参数在哪聚合？ | `OpenAiApi.chatCompletionStream()` 的 `windowUntil + reduce(chunkMerger)`，在进 ChatModel 之前 |
| 怎么区分「新工具」和「参数续传」？ | 看 chunk 里 `toolCall.id` 有没有值 |
| Advisor 链能复用吗？ | 不能，`pop()` 破坏性消费，每次调用重新 build |
| Advisor 顺序谁定？ | `getOrder()`，不是添加顺序；Model advisor 是 `LOWEST_PRECEDENCE` 沉底 |
| usage 是单轮还是全程？ | 全程累加 |
| 谁来管 maxSteps / 循环检测？ | **没人管。** 这是你自己 Agent Runtime 的活 |

