---
title: Agent Planning 与 Reasoning
date: 2026-09-06
tags: [interview, agent, planning, reasoning, react]
---

# Agent Planning 与 Reasoning

Planning 决定任务怎么拆、先做什么和何时调整。Reasoning 是模型在当前状态下做决策的能力。工程上关注可观察动作和计划状态，不依赖隐藏思维链。

## 复习范围

| 模式 | 适用场景 |
|---|---|
| ReAct | 边观察边行动，适合开放式工具任务 |
| Plan-and-Execute | 先拆任务再执行，适合多阶段工作 |
| Planner-Executor | 规划和执行用不同角色或模型 |
| Reflection / Critic | 对结果做检查，但要防止无效自我循环 |
| State Graph | 分支、回退和人工节点明确的业务流程 |

## 高频问题

1. ReAct 解决了什么问题？
2. 为什么计划写得很完整，执行仍可能失败？
3. 什么时候应该重规划，而不是继续重试？
4. Planner 和 Executor 应不应该使用不同模型？
5. 如何限制反思循环和 token 消耗？
6. 计划如何与工具结果、用户新消息保持一致？

## 工程约束

- 计划项要有状态：pending、running、done、blocked。
- 每一步要绑定证据和验收条件。
- 环境变化后检查计划是否仍成立。
- 高风险动作前增加确认节点。
- 用最大步骤、时间、token 和成本共同限制任务。

## 失败模式

- 计划和真实环境脱节。
- 只更新自然语言计划，没有更新执行状态。
- Planner 给出工具并不存在的步骤。
- 反思只是重复原答案，没有新证据。
- 为简单任务强制规划，延迟和成本反而上升。

## 项目证据

选一条长任务轨迹，标出首次规划、环境反馈、重规划和终止。说明哪一步由代码约束，哪一步交给模型判断。

## 已有资料

- [Agent 运行机制中的 ReAct](02-Agent-运行机制.md)
- [ReAct 笔记](../Agent/react.md)
- [Agent Book：工作流与 Agent](../ai-agent-book/chapter1.md)

## 待补

- [ ] 对比 ReAct、Plan-and-Execute 和 State Graph
- [ ] 准备一个重规划触发条件清单
- [ ] 写一套 task budget 计算方式
