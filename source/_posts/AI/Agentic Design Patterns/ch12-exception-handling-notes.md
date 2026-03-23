---
title: '第12章：异常处理与恢复 / Exception Handling and Recovery'
tags:
  - Agentic Design Patterns
categories:
  - AI
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: true
updated: '2026-03-23 23:30'
date: '2026-03-23 23:30'
sticky:
---

# 异常处理与恢复 / Exception Handling and Recovery

> **来源**：https://adp.xindoo.xyz/chapters/Chapter%2012_%20Exception%20Handling%20and%20Recovery/
> **整理日期**：2026-03-23

---

## 核心概念

异常处理与恢复模式（Exception Handling and Recovery Pattern）是一种专注于构建**高韧性 AI 智能体**的设计模式。它要求智能体能够主动预测潜在故障（工具调用失败、API 错误、网络中断等），并在故障发生时执行结构化的检测→处理→恢复三阶段响应，从而在不可预测的真实环境中维持操作完整性，而不是直接崩溃或挂起。

---

## 解决什么问题

在真实环境中，工具错误、服务不可用、格式错误的输出、超时等问题无处不在。没有异常处理能力的智能体一旦遇到意外状况就会彻底失败，导致：

- 整个任务流程中断，用户体验极差
- 产生不可预知的副作用（如重复执行有害操作）
- 缺乏可调试性，无法快速定位问题根因

该模式将智能体从脆弱的单点失败系统转变为可靠的生产级组件。

---

## 工作原理 / 关键机制

### 三阶段框架

```
[错误检测] → [错误处理] → [恢复]
```

### 1. 错误检测（Detection）
- 验证工具输出格式是否合法
- 检查 API 错误码（404、500 等）
- 监控响应超时
- 识别无意义/不连贯的输出
- 部署监控智能体或专用监控系统主动巡检

### 2. 错误处理（Handling）
| 策略 | 说明 |
|------|------|
| **日志记录** | 详细记录错误信息，支持后续调试 |
| **重试** | 针对瞬态错误，可用略微调整的参数重试 |
| **回退（Fallback）** | 切换到替代策略或备用工具 |
| **优雅降级** | 无法完全恢复时保持部分功能可用 |
| **通知** | 向人类操作员或其他智能体发出警报 |

### 3. 恢复（Recovery）
| 策略 | 说明 |
|------|------|
| **状态回滚** | 撤销最近变更，还原到上一稳定状态 |
| **诊断分析** | 深入分析错误根因，防止复发 |
| **自我纠正** | 调整计划、参数或推理逻辑后重试 |
| **升级** | 复杂/严重问题委托给人类操作员处理 |

---

## 应用场景

1. **客户服务聊天机器人**：数据库临时宕机时，不崩溃而是提示用户稍后重试或转接人工，同时记录错误
2. **自动金融交易机器人**：遇到"资金不足"或"市场关闭"错误时，记录错误、避免重复无效交易，并通知用户
3. **智能家居自动化**：灯控失败时，重试 → 仍失败 → 通知用户手动干预
4. **批量数据处理智能体**：遇到损坏文件时跳过并记录，继续处理其余文件，最终汇报跳过列表
5. **网络爬虫智能体**：遭遇验证码/404/503 时暂停、切换代理或报告失败 URL
6. **工业机械臂**：拾取失败时重新调整位置重试，持续失败则警告操作员

---

## 框架实现

### Google ADK 实现

使用 `SequentialAgent` 组合三个子智能体实现主备 + 降级逻辑：

```python
from google.adk.agents import Agent, SequentialAgent

# 1. 主处理器：尝试精确工具
primary_handler = Agent(
    name="primary_handler",
    model="gemini-2.0-flash-exp",
    instruction="使用 get_precise_location_info 获取精确位置信息",
    tools=[get_precise_location_info]
)

# 2. 回退处理器：检查主处理器是否失败
fallback_handler = Agent(
    name="fallback_handler",
    model="gemini-2.0-flash-exp",
    instruction="""检查 state["primary_location_failed"]。
    若为 True，提取城市并使用 get_general_area_info。""",
    tools=[get_general_area_info]
)

# 3. 响应智能体：从 state 中读取最终结果
response_agent = Agent(
    name="response_agent",
    model="gemini-2.0-flash-exp",
    instruction="从 state['location_result'] 读取并向用户展示位置信息",
    tools=[]
)

# SequentialAgent 保证执行顺序
robust_location_agent = SequentialAgent(
    name="robust_location_agent",
    sub_agents=[primary_handler, fallback_handler, response_agent]
)
```

**核心思路**：通过共享 state 在子智能体间传递失败标志，实现主备切换。

### LangChain / LangGraph
- 可通过 `try/except` + 条件分支节点实现类似的错误检测和回退逻辑
- LangGraph 的图结构天然支持基于状态的条件跳转（错误边）

---

## 注意事项 / 权衡

| 考量 | 说明 |
|------|------|
| **与反思模式结合** | 失败后可触发反思，分析原因并用优化提示重试 |
| **重试风暴风险** | 不加限制的重试可能导致级联故障，需设置最大重试次数和退避策略 |
| **状态管理复杂度** | 引入回滚机制需要维护状态快照，增加系统复杂度 |
| **升级代价** | 频繁升级人工处理会降低系统自动化价值，需权衡升级阈值 |
| **日志存储成本** | 详细错误日志能提升可调试性，但会增加存储和处理开销 |

---

## 一句话总结

> 异常处理与恢复模式通过「检测→处理→恢复」三阶段机制，赋予 AI 智能体在工具故障、API 错误和网络问题等真实挑战中依然稳定运行的能力，是生产环境中构建可靠智能体的必备模式。
