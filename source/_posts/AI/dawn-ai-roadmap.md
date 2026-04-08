---
title: dawn-ai 企业级 Agent 整改方案
date: 2026-04-03 16:00:00
tags: [AI, Agent, Architecture]
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-04-03 16:00
---

> 参考 [Claude Code 源码架构深度解析 V2.0](https://x.com/tvytlx) 提炼的 7 大设计原则，结合 dawn-ai 现状，制定从 prototype 到 enterprise-grade agent 的整改路线。
> 
> 详细差距分析见 [dawn-ai 增强点记录](/AI/dawn-ai-enhancement/)

---

## 一、设计原则对标（Claude Code → dawn-ai）

> 以下 7 条原则提炼自 Claude Code 4756 个源文件的架构解析，每条原则都有对应的源码实现支撑。

### 原则 1：不信任模型的自觉性

> 好行为要写成制度。你希望模型先读代码再改代码，就写进 prompt；你希望模型不要乱加功能，就写进 prompt；你希望模型遇到风险操作停下来，就在 runtime 层加权限检查。不要指望一个 LLM 每次都"想到"该怎么做。制度化的行为比临场发挥稳定得多。
>
> Claude Code 对应源码：`getSimpleDoingTasksSection()`、`getActionsSection()`

**dawn-ai 现状**：`buildSystemPrompt()` 已实现动态系统提示词，但行为规范较粗糙，缺乏 Claude Code 级别的细粒度行为约束（如逐条禁令："不要加用户没要求的功能"、"不要过度抽象"、"先读代码再改代码"等）。

**整改方向**：System Prompt 中增加结构化的行为规范 section，明确 Agent 的"能做/不能做"边界。

### 原则 2：把角色拆开

> 至少把"做事的人"和"验收的人"分开。哪怕用同一个模型，职责拆开也会有明显改善。因为同一个 Agent 既实现又验证，天然倾向于觉得自己做得没问题。
>
> Claude Code 对应源码：Verification Agent、Explore Agent、Plan Agent

**dawn-ai 现状**：单 Agent 架构，所有职责耦合在 `AgentOrchestrator` 中。

**整改方向**：拆分为至少 3 个角色 — Executor Agent（执行）、Verification Agent（对抗性验证）、Plan Agent（规划）。

### 原则 3：工具调用要有治理

> 模型说要调工具，中间还要过输入校验、权限检查、风险预判。执行完了还有后处理和失败处理。这层治理决定了系统在异常情况下的表现。
>
> Claude Code 对应源码：`toolExecution.ts` 的 14 步 pipeline

**dawn-ai 现状**：`ToolRegistry` 实现了自动扫描和注册，但缺乏执行前的校验、权限检查、风险预判。工具直接被 LLM 调用，无中间治理层。

**整改方向**：构建 Tool Execution Pipeline — Schema 校验 → 权限检查 → PreHook → 执行 → PostHook → 结果处理。

### 原则 4：上下文是预算

> 每个 token 都有成本，每条信息都占空间。能缓存的要缓存，能按需加载的不要一开始就塞进去，能压缩的要压缩。
>
> Claude Code 对应源码：`SYSTEM_PROMPT_DYNAMIC_BOUNDARY`、fork cache optimization、四道压缩机制（Snip → Micro → Context Collapse → Auto Compact）

**dawn-ai 现状**：短期记忆仅靠滑动窗口(MAX=20)粗暴截断，无压缩/摘要/按需加载机制。System Prompt 无静态/动态分区。

**整改方向**：实现 Summary Buffer 压缩 + System Prompt 静态/动态分区（利用 Prompt Cache）。

### 原则 5：安全层要互不绕过

> 三层防护（Classifier、Hook、Permission）可以互相配合，但任何一层不能绕过另一层。Hook 的 allow 不能绕过 settings 的 deny。这样即使某一层出了问题，整体安全性不会崩塌。
>
> Claude Code 对应源码：`resolveHookPermissionDecision()`

**dawn-ai 现状**：零安全层。无输入过滤、无权限模型、无 Prompt Injection 检测。

**整改方向**：建立分层安全架构 — Input Filter → Tool Permission → Output Filter，各层独立且不可绕过。

### 原则 6：生态的关键是模型感知

> 你给系统接了十个插件，但模型不知道什么时候该用哪个，那这十个插件就等于不存在。扩展机制的最后一步，是让模型看到自己的能力清单。
>
> Claude Code 对应源码：MCP instructions injection、skill discovery、session-specific guidance

**dawn-ai 现状**：工具通过 @Tool 注解注册，LLM 通过 function calling 感知。但缺乏 MCP 协议支持和动态工具发现能力。

**整改方向**：实现 MCP 集成，让 Agent 动态感知和使用外部工具生态。

### 原则 7：产品化在于处理第二天

> 第一天跑起来不难。难的是任务中断怎么续、脏状态怎么清、进程泄漏怎么办、session 怎么恢复。这些问题不解决，产品就只能是 Demo。
>
> Claude Code 对应源码：`runAgent.ts` 的 cleanup chain、transcript recording、task lifecycle

**dawn-ai 现状**：无生命周期管理，MemoryService Redis 不可用时无 Failsafe（#10），无 Transcript 记录。

**整改方向**：完善生命周期管理 — 会话恢复、资源清理、异常兜底、执行记录。

---

## 二、整改计划（按价值分级）

### P0 — 核心竞争力（直接决定 Agent 质量上限）

| 阶段   | Issue                                                              | 对标原则           | 核心交付                                                      |
| ---- | ------------------------------------------------------------------ | -------------- | --------------------------------------------------------- |
| P0-1 | [#23 Memory 增强](https://github.com/Supremes/dawn-ai/issues/23)     | 原则4：上下文是预算     | Summary Buffer 摘要压缩 + 记忆固化到向量库 + 时间衰减 Rerank              |
| P0-2 | [#13 Reflection 机制](https://github.com/Supremes/dawn-ai/issues/13) | 原则4：上下文是预算     | 情景记忆聚合 → 高维反思 → 提升为核心记忆                                   |
| P0-3 | [#24 安全与合规](https://github.com/Supremes/dawn-ai/issues/24)         | 原则5：安全层互不绕过    | Input Filter + Prompt Injection 检测 + Output Filter + 审计日志 |
| P0-4 | [#25 MCP 协议支持](https://github.com/Supremes/dawn-ai/issues/25)      | 原则6：生态的关键是模型感知 | MCP Client 实现 + 外部工具动态发现 + Instructions 注入                |

**执行顺序**：#23 → #13 → #24 → #25（Memory 和 Reflection 互相依赖，先打通记忆链路）

### P1 — 重要增强（提升可靠性与可扩展性）

| 阶段   | Issue                                                               | 对标原则         | 核心交付                                                 |
| ---- | ------------------------------------------------------------------- | ------------ | ---------------------------------------------------- |
| P1-1 | [#26 Agent 评估系统](https://github.com/Supremes/dawn-ai/issues/26)     | 原则1：不信任模型自觉性 | 评估指标定义 + 标准测试集 + CI 质量门禁                             |
| P1-2 | [#27 可观测性增强](https://github.com/Supremes/dawn-ai/issues/27)         | 原则7：产品化处理第二天 | OpenTelemetry 全链路 Tracing + Grafana Dashboard + 告警规则 |
| P1-3 | [#28 Multi-Agent 协作](https://github.com/Supremes/dawn-ai/issues/28) | 原则2：把角色拆开    | Executor/Verifier/Planner 三角色拆分 + 任务委派 + 结果聚合        |
| P1-4 | [#29 成本控制](https://github.com/Supremes/dawn-ai/issues/29)           | 原则4：上下文是预算   | Token 计量 + 模型路由（按任务选模型）+ 速率限制与重试                     |
| P1-5 | [#2 Streaming SSE](https://github.com/Supremes/dawn-ai/issues/2)    | 原则7：产品化处理第二天 | 流式输出 + Streaming Tool Execution                      |

**执行顺序**：#26 → #27 → #28 → #29 → #2（先建评估体系，才能量化后续改进效果）

### P2 — 长期演进（锦上添花）

| 阶段 | Issue | 对标原则 | 核心交付 |
|------|-------|---------|---------|
| P2-1 | [#30 推理增强](https://github.com/Supremes/dawn-ai/issues/30) | 原则1：不信任模型自觉性 | CoT / Tree-of-Thought / HYDE |
| P2-2 | [#31 Prompt Engineering 增强](https://github.com/Supremes/dawn-ai/issues/31) | 原则1：不信任模型自觉性 | Template 引擎 + Few-shot + Output Parsing 容错 |
| P2-3 | [#32 工程化与部署](https://github.com/Supremes/dawn-ai/issues/32) | 原则7：产品化处理第二天 | CI/CD + 弹性伸缩 + 熔断降级 |

### 已有 Issue 整合

| Issue | 状态 | 归属阶段 |
|-------|------|---------|
| [#22 System Prompt 动态组装](https://github.com/Supremes/dawn-ai/issues/22) | OPEN | 与 P0-4 MCP 协同（动态注入 MCP instructions） |
| [#21 项目优化](https://github.com/Supremes/dawn-ai/issues/21) | OPEN | 持续进行 |
| [#20 AgentScope 学习载体](https://github.com/Supremes/dawn-ai/issues/20) | OPEN(P0) | 贯穿全程，作为学习载体与原型验证平台 |
| [#10 MemoryService Redis Failsafe](https://github.com/Supremes/dawn-ai/issues/10) | OPEN(P2) | 并入 #23 Memory 增强一并解决 |
| [#9 simpleChat 绕过 Agent 基础设施](https://github.com/Supremes/dawn-ai/issues/9) | OPEN | 并入 #24 安全合规（工具治理） |
| [#6 补全单元测试](https://github.com/Supremes/dawn-ai/issues/6) | OPEN(P2) | 并入 #26 评估系统（测试是评估的基础） |

---

## 三、架构全景图

```
┌─────────────────────────────────────────────────┐
│           第八层：工程化与部署 [#32]               │
│  CI/CD · 弹性伸缩 · 熔断降级 · 灰度发布           │
├─────────────────────────────────────────────────┤
│         第七层：可观测性与评估 [#26 #27]            │
│  OpenTelemetry · Metrics · Agent 评估 · A/B Test  │
├─────────────────────────────────────────────────┤
│          第六层：安全与合规 [#24]                   │
│  Input Filter · Prompt Injection · Output Filter  │
│  三层互不绕过：Classifier → Hook → Permission      │
├─────────────────────────────────────────────────┤
│        第五层：多 Agent 协作 [#28]                  │
│  Executor · Verifier · Planner · 任务委派           │
├─────────────────────────────────────────────────┤
│         第四层：工具与执行 [#25]                    │
│  ToolRegistry · MCP · 14步执行Pipeline             │
│  Schema校验→权限→PreHook→执行→PostHook→结果       │
├─────────────────────────────────────────────────┤
│        第三层：知识与记忆 [#23 #13]                 │
│  短期(Redis) · Summary Buffer · 长期(向量库)        │
│  固化 · 反思(Reflection) · 遗忘(Decay)              │
│  RAG · Query重写 · HYDE · 向量检索                  │
├─────────────────────────────────────────────────┤
│        第二层：推理与规划 [#30]                      │
│  ReAct · Plan-and-Solve · CoT · ToT                │
├─────────────────────────────────────────────────┤
│        第一层：基础能力 [#31 #29]                    │
│  LLM集成 · Prompt Engineering · Output Parsing     │
│  Token计量 · 模型路由 · Prompt Cache                │
└─────────────────────────────────────────────────┘
```

---

## 四、关键决策点

### 决策 1：AgentScope 作为学习载体（[#20](https://github.com/Supremes/dawn-ai/issues/20)）

**结论：引入 AgentScope，定位为学习载体与原型验证平台。**

Spring AI 和 AgentScope 都是深度封装的框架。既然都是站在框架肩膀上，选择标准就变成了：**哪个框架在"用的过程中"能让你更直接地接触 Agent 设计决策？**

AgentScope 原生提供 ReAct Agent、Multi-Agent 编排、Memory 抽象、消息传递等 Agent 原语，且 Python 源码直观可读。学习路径更顺畅：**先用 → 遇到问题 → 带着问题读源码 → 理解设计决策 → 反哺 Java 实现**。

**重点阅读模块：**

| AgentScope 模块 | 学习目标 | 对应 dawn-ai Issue |
|-----------------|---------|-------------------|
| `agentscope/memory/` | Memory 抽象、短期/长期记忆切换 | #23 Memory 增强 |
| `agentscope/agents/react_agent.py` | ReAct Loop 实现细节 | AgentOrchestrator 优化 |
| `agentscope/msghub.py` | Multi-Agent 消息传递与编排 | #28 Multi-Agent 协作 |
| `agentscope/service/` | Tool/Service 注册与执行 | #25 MCP 协议支持 |
| `agentscope/prompt/` | Prompt 模板与组装策略 | #31 Prompt Engineering 增强 |

**实施步骤：**
1. 搭建 AgentScope 本地环境，跑通官方示例
2. 用 AgentScope 实现 dawn-ai 的核心场景（对话 + RAG + 工具调用）
3. 对比 Spring AI 实现，记录设计差异和优劣
4. 重点读源码模块（上表），提取可移植的设计模式
5. 将验证过的模式反哺到 dawn-ai Java 实现

### 决策 2：安全层实现策略

参照 Claude Code 的三层防护设计：
- **Classifier**（风险预判）→ 可用 Spring AI 的 Advisor 拦截链实现
- **Hook**（策略层）→ Spring AOP + 自定义注解
- **Permission**（权限决策）→ 工具级别的 `checkPermissions()` 方法

### 决策 3：上下文压缩策略

参照 Claude Code 的四道压缩机制，dawn-ai 可分步实现：
1. **Phase 1**：Summary Buffer（#23 中实现）
2. **Phase 2**：Token Bounding + Auto Compact
3. **Phase 3**：Context Collapse（需要 Multi-Agent 后支持）
