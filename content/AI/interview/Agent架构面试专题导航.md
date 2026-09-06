---
title: Agent 架构面试专题导航
date: 2026-09-06
tags: [interview, agent, architecture]
---

# Agent 架构面试专题导航

这套目录按 Agent 系统的组成拆分。每个专题回答三个问题：

1. 这一层负责什么，不负责什么？
2. 工程上怎么实现，失败时怎么定位？
3. 面试时拿什么项目证据支撑？

## 专题地图

| 方向 | 要解决的问题 | 专题 |
|---|---|---|
| Harness 与运行时 | Agent Loop、状态、事件、终止、恢复 | [Agent Harness 与运行时](Agent-Harness与运行时.md) |
| Context 与 Memory | 上下文组装、短期状态、长期记忆、遗忘 | [Agent Context 与 Memory](Agent-Context与Memory.md) |
| Tool、MCP 与 Skill | 工具发现、调用协议、Registry、权限、技能加载 | [Agent Tool、MCP 与 Skill](Agent-Tool-MCP-Skill.md) |
| Planning 与 Reasoning | ReAct、计划执行、反思、预算和终止 | [Agent Planning 与 Reasoning](Agent-Planning与Reasoning.md) |
| RAG 与知识系统 | 检索、重排、证据、Agentic RAG | [Agent RAG 与知识系统](Agent-RAG与知识系统.md) |
| Multi-Agent | 委派、handoff、共享状态、冲突和成本 | [Agent Multi-Agent 协作](Agent-Multi-Agent协作.md) |
| 模型路由与多模态 | 模型选择、能力路由、降级、文本/图像切换 | [Agent 模型路由与多模态](Agent-模型路由与多模态.md) |
| 评测与可观测性 | Outcome、Trajectory、Judge、Dataset、Trace | [Agent 评测与可观测性](Agent-评测与可观测性.md) |
| 安全与权限 | Prompt Injection、最小权限、密钥、审计 | [Agent 安全与权限](Agent-安全与权限.md) |
| 性能与成本 | TTFT、轮数、缓存、并行、成功任务成本 | [Agent 性能与成本](Agent-性能与成本.md) |
| 可靠性与生产化 | Sandbox、幂等、重试、持久化、灰度和回滚 | [Agent 可靠性与生产化](Agent-可靠性与生产化.md) |
| Coding Agent | 仓库理解、编辑、测试、工作树和 PR | [Coding Agent 工程](Coding-Agent工程.md) |
| 系统设计与行为面试 | 架构题、权衡、STAR、项目复盘 | [Agent 系统设计与行为面试](Agent-系统设计与行为面试.md) |

## 建议复习顺序

### 第一轮：先讲清 Agent 怎么跑

Harness → Tool → Context/Memory → Planning → RAG。

目标是能从用户输入开始，口述一次完整 Agent Loop，并解释工具结果如何回到模型。

### 第二轮：再讲怎么上线

评测 → 安全 → 性能 → 可靠性。

目标是能设计一套带数据集、Trace、CI 门禁、权限控制和故障恢复的生产系统。

### 第三轮：准备项目追问

Coding Agent → Multi-Agent → 模型路由 → 系统设计与行为面试。

目标是准备两段有数据的项目经历。每段都要说清约束、取舍、失败和复盘。

## 每个专题的完成标准

- 能用 30 秒说出职责边界。
- 能画出核心数据流或状态机。
- 能回答 5 个高频追问。
- 能列出 3 个失败模式和定位证据。
- 有一个真实项目例子，不用假设数据。

## 现有综合资料

- [面试速答总览](00-面试速答总览.md)
- [Dawn AI Agent 架构九问速记](07-Dawn-AI-Agent-架构九问速记.md)
- [Dawn AI Agent 架构九问深挖](08-Dawn-AI-Agent-架构九问深挖.md)
- [The Anatomy of an Agent Harness](../the-anatomy-of-an-agent-harness.md)
- [Agent 评测面试复习](Agent-评测面试复习.md)
