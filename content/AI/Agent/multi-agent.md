---
title: Multi-Agent 架构模式深度指南
date: 2026-06-17
summary: 四种 Multi-Agent 协作模式（Handoff / Agent-As-Tool / Leader-Workers / A2A）的详解、协议标准（MCP/ACP/A2A）、框架实现对比（Spring AI/LangChain/PydanticAI），以及 Dawn AI 项目的实践映射
tags:
  - AI-Agent
  - Multi-Agent
  - Spring-AI
  - LangChain
  - PydanticAI
  - MCP
  - A2A
  - ReAct
---

## 一、四种 Multi-Agent 协作模式

Multi-Agent 系统的核心差异在于**控制权归谁、Agent 之间如何协作**。

### Pattern A: Agent Handoff — 控制权移交

当前 Agent 判断"这个任务不该我做"，把控制权**移交**给另一个 Agent，自己退出，上下文随之转交。

```
Agent_A: "这个问题我处理不了，交给你了"
         → 控制权完全转移给 Agent_B
         → Agent_A 退出，上下文一起转走
         → Agent_B 独立完成剩余工作
```

**类比**：客服转接——前一位挂线，新坐席接手。

**关键特征**：
- **单向交接**：控制权一去不回（或需显式交回）
- **上下文共享转移**：对话历史、用户意图随控制权一起带走
- **同一时刻只有一个 Agent 活跃**
- 实现简单，但 Agent 之间**紧耦合**（需要在同一进程、共享状态格式）

**典型实现**：
- **OpenAI Swarm** 的 `handoff()` 函数——Agent 返回一个特殊的 `Agent` 对象而非文本，框架自动切换活跃 Agent
- 多技能客服系统（售前/售后/技术支持之间切换）

**适用场景**：
- 多步骤工作流中不同阶段由不同专家接管
- 对话分流（意图识别后路由到对应领域 Agent）
- 需要保持完整对话上下文的场景

**不适用**：需要多个 Agent 同时工作、或需要主 Agent 汇总结果的场景。

---

### Pattern B: Agent As Tool — 子 Agent 当工具调

把一个 Agent **当作工具**注册给另一个 Agent。调用时同步等返回，调用方继续保留控制权。

```
主 Agent: "我需要深度研究这个问题"
         → 调用 DispatchSubAgentTool(type="research", task="...")
         → 子 Agent 执行（主 Agent 等待）
         → 子 Agent 返回结果（Observation）
         → 主 Agent 拿到结果继续推理
```

**类比**：函数调用——子函数返回值，主函数继续执行。

**关键特征**：
- **调用方保留控制权**：子 Agent 的输出只是主 Agent 的一个 Observation
- **同步等待**：主 Agent 发起调用后阻塞等结果
- **上下文隔离**：子 Agent 通常看不到主 Agent 的完整对话历史
- 对主 Agent 来说，子 Agent 和普通 Tool（天气查询、数据库查询）**没有本质区别**

**典型实现**：
- **Claude Code 的 Agent tool**——主 Agent 派发子 Agent 执行搜索/编码任务
- **Dawn AI 的 DispatchSubAgentTool**——主 Agent 通过 ReAct 循环决定派发 research 子 Agent

**Dawn AI 中的具体实现**：

| 组件 | 角色 |
|------|------|
| `DispatchSubAgentTool` | 把子 Agent 伪装成普通 Tool，注册到主 Agent 的工具列表 |
| `SubAgentRegistry` | 子 Agent 类型注册中心（当前注册了 `research` 类型） |
| `GenericReActSubAgentExecutor` | 子 Agent 执行引擎——在独立线程池上跑独立 ReAct 循环 |
| `SubAgentDefinition` | 子 Agent 的"定义卡片"（system prompt、工具白名单、maxSteps、timeout） |
| `StepCollector.newDetachedContext()` | 隔离点——子 Agent 的步骤计数独立于主 Agent |

**隔离保障**（Dawn AI 代码中的明确约束）：
- 子 Agent **不读主对话历史**——task description 是自包含的
- 子 Agent **不读/不写主 Memory**
- 子 Agent **禁止递归派发**——system prompt 明确禁止调用 `dispatch_subagent`
- 子 Agent 有**独立 maxSteps（15）和超时（60s）**

**适用场景**：
- 主 Agent 需要"深度研究"某个子问题
- 不同子任务需要不同的工具集/system prompt
- 需要隔离上下文、防止污染的场景

---

### Pattern C: Leader & N Workers — 领导者分发

一个 **Leader** 拆解任务并分发给多个 **Worker** 并行执行，最后汇总结果。

```
Leader: "这个任务拆成 3 部分"
        → Worker_1: 子任务 A     ┐
        → Worker_2: 子任务 B     ├─ 并行执行
        → Worker_3: 子任务 C     ┘
        → Leader 汇总 3 个结果 → 最终答案
```

**类比**：MapReduce——Map 阶段分发，Reduce 阶段汇总。

**关键特征**：
- **一对多并行**：Leader 同时派出多个 Worker
- **Leader 做规划 + 汇总**，Worker 只管执行
- **Worker 通常是短生命周期**，完成即销毁
- 吞吐量高，但需要处理并发控制、结果合并、部分失败

**典型实现**：
- **Anthropic 的多步研究系统**——并行搜索多个来源，汇总为一份报告
- **Claude Code 的 Workflow**——`parallel()` / `pipeline()` 多 Agent 并行
- **并行代码 review**——多维度（bug/性能/安全）同时审查

**Dawn AI 中的现状**：
- `TaskPlanner` 有 Leader 的雏形（拆解为 `PlanStep[]`），但步骤是**串行执行**的
- 要实现完整 Pattern C，需要：并行分发多个 Sub-Agent + 结果汇总

**适用场景**：
- 任务可拆解为独立子任务（无相互依赖）
- 需要多维度/多角度分析（如多源检索、多维审查）
- 时间敏感——并行执行显著降低总延迟

---

### Pattern D: Agent2Agent (A2A) — 对等协议通信

多个对等 Agent 通过**标准协议**直接通信，没有显式的主从关系。强调跨平台互操作。

```
Agent_X (团队A, Python)  ←── 标准协议 ──→  Agent_Y (团队B, Java)
Agent_Y (团队B, Java)    ←── 标准协议 ──→  Agent_Z (团队C, Go)
```

**类比**：邮件 / RPC 协议层——不同组织的系统通过标准协议互联互通。

**关键特征**：
- **无主从关系**：Agent 之间对等
- **标准协议**：Google A2A / ACP（已合并入 Linux Foundation）
- **跨平台跨语言**：不同框架、不同语言的 Agent 互通
- **发现机制**：Agent 能发现彼此的能力（Agent Card / Agent Manifest）
- 最灵活但**最复杂**——需要协议协商、序列化、网络通信、错误重试

**典型实现**：
- **Google A2A 协议**——Agent Card 描述能力，HTTP REST 通信
- **ACP（Agent Communication Protocol）**——IBM BeeAI 发起，已并入 A2A
- 跨组织 Agent 市场——财务 Agent + HR Agent + IT Agent 协作

**适用场景**：
- 不同团队/组织各自维护的 Agent 需要协作
- Agent 部署在不同基础设施/语言栈上
- 需要"Agent 市场"式的发现与调用

---

## 二、四种模式对比总结

| 维度 | A. Handoff | B. Agent As Tool | C. Leader & Workers | D. A2A |
|------|-----------|-----------------|-------------------|--------|
| **控制权** | 完全转移 | 调用方保留 | Leader 持有 | 对等，无主从 |
| **通信方式** | 内部状态切换 | 函数调用/同步返回 | 分发+汇总 | 标准协议(HTTP/REST) |
| **上下文** | 共享转移 | 隔离 | 隔离 | 各自独立 |
| **并发** | 串行 | 串行(等返回) | **并行** | 异步/并行 |
| **耦合度** | 高（同进程） | 中（同进程，接口隔离） | 中 | **低（跨进程/跨网络）** |
| **复杂度** | 低 | 中 | 高 | 最高 |
| **典型代表** | OpenAI Swarm | Claude Code Agent tool | Anthropic Workflow | Google A2A |

**自然演进路径**：B（Agent As Tool）→ C（加并行分发）→ D（跨平台互联）

---

## 三、Agent 通信协议标准

### 3.1 MCP（Model Context Protocol）

Anthropic 主导的协议，解决的是 **Agent ↔ 工具/数据源** 的通信，不是 Agent 之间的通信。

- **定位**：让 LLM 能访问外部工具和数据（类似 USB 接口标准）
- **架构**：Client-Server，Client 是 LLM 应用，Server 暴露工具/资源
- **传输**：stdio / SSE
- **Spring AI 支持**：原生集成，可作为 MCP Client 消费外部 MCP Server

### 3.2 ACP（Agent Communication Protocol）

IBM BeeAI 发起，已并入 Linux Foundation 的 A2A。解决 **Agent ↔ Agent** 的通信。

- **定位**：Agent 间多模态消息通信（文本、代码、文件、媒体）
- **架构**：REST API，Agent 通过 HTTP 互调
- **核心概念**：Agent Manifest（能力描述）、Run（执行生命周期）、Message/MessagePart（多模态消息）
- **SDK**：Python + TypeScript（**无 Java/Spring SDK**）
- **Spring AI 支持**：❌ 无原生集成
- **桥接方案**：ACP 官方提供 MCP Adapter → 把 ACP Agent 暴露为 MCP 工具 → Spring AI MCP Client 可用

### 3.3 Google A2A

Google 主导的 Agent-to-Agent 协议，与 ACP 在同一赛道。

- **定位**：跨平台 Agent 互操作
- **核心概念**：Agent Card（能力描述，类似 ACP 的 Agent Manifest）
- **与 ACP 关系**：ACP 已宣布并入 A2A

### 3.4 协议定位对比

| 协议 | 解决什么通信 | 类比 |
|------|------------|------|
| **MCP** | Agent ↔ 工具/数据源 | USB 接口标准 |
| **ACP/A2A** | Agent ↔ Agent | 邮件/RPC 协议 |
| **OpenAI Tool Calling** | LLM ↔ 工具（API 级） | 函数签名约定 |

---

## 四、框架中的 Multi-Agent 实现对比

### 4.1 循环机制

| 框架 | ReAct 循环模式 | Multi-Agent 模式 |
|------|--------------|-----------------|
| **Spring AI** | 尾递归（`internalCall()` 调自身） | Pattern B（ToolCallback 注册子 Agent） |
| **LangChain/LangGraph** | 图遍历（`StateGraph` 节点循环） | Pattern C（`Send` fan-out 并行）+ Pattern A（`Command` 路由） |
| **PydanticAI** | 状态机（`BaseNode` 转移） | Pattern B（Agent 嵌入 `pydantic_graph` 节点） |

### 4.2 并行能力

| 框架 | 并行工具执行 | 并行 Agent 派发 |
|------|-----------|---------------|
| **Spring AI** | ❌ 顺序执行 | ❌ 需自行实现 |
| **LangGraph** | ✅ `Send` fan-out 真并行 | ✅ 子图并行 |
| **PydanticAI** | ✅ 三种模式（sequential/parallel-ordered/parallel-unordered） | ✅ `pydantic_graph` 节点并行 |

### 4.3 Spring AI 的优势与不足

**优势**：
- 企业集成深度（DI/AOP/Micrometer/Security 零摩擦）
- `RetryTemplate` 最健壮的 API 级重试
- Reactor Flux 响应式流在递归工具调用中保持流式
- `ToolExecutionExceptionProcessor` 工具错误自愈

**不足**：
- 无内置 max-iteration 保护（Dawn AI 通过 `StepCollector.maxSteps` 弥补）
- 无并行工具执行
- 各 Provider 重复实现递归循环，无共享基类
- 工具解析失败直接抛异常，不像 LangChain/PydanticAI 能让 LLM 自我纠正

---

## 五、Dawn AI 的 Multi-Agent 架构现状与演进

### 5.1 当前架构：Pattern B（Agent As Tool）

```
用户请求
  → ChatController → ChatService → AgentOrchestrator
    → TaskPlanner.plan() → 生成 PlanStep[]
    → ChatClient.prompt().toolNames(tools).stream()
      → OpenAiChatModel.internalCall() [ReAct 递归循环]
        → LLM 决定调用 DispatchSubAgentTool
          → GenericReActSubAgentExecutor.execute()
            → 子 Agent 独立 ReAct 循环（隔离线程池、隔离 StepCollector）
            → 返回 SubAgentResult
        → 主 Agent 拿到结果继续推理
```

### 5.2 演进方向

| 阶段 | 模式 | 需要做什么 |
|------|------|----------|
| **当前** | Pattern B 串行 | 主 Agent 通过 `DispatchSubAgentTool` 串行调用子 Agent |
| **下一步** | Pattern C 并行 | `ParallelDispatchTool` 或 `TaskPlanner` 识别可并行步骤，同时派发多个 Worker |
| **远期** | Pattern D 跨平台 | 接入 ACP/A2A 协议，通过 MCP Adapter 桥接外部 Agent |

---

## 六、参考资料

| 资源 | 地址 |
|------|------|
| ReAct 论文 | https://arxiv.org/abs/2210.03629 |
| OpenAI Swarm（Handoff 参考） | https://github.com/openai/swarm |
| Google A2A 协议 | https://github.com/google/a2a |
| ACP 官方文档 | https://agentcommunicationprotocol.dev/ |
| ACP MCP Adapter | https://agentcommunicationprotocol.dev/integrations/mcp-adapter |
| MCP 官方文档 | https://modelcontextprotocol.io/ |
| Spring AI Tool Calling | https://docs.spring.io/spring-ai/reference/api/tools.html |
| LangGraph Multi-Agent | https://langchain-ai.github.io/langgraph/concepts/multi_agent/ |
| Dawn AI ReAct 循环架构图 | dawn-ai 项目 `docs/spring-ai-react-loop.svg` |
| Dawn AI ReAct 深度解析 | dawn-ai 项目 `docs/react-loop-deep-dive.md` |
