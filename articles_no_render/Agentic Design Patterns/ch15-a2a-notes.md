---
title: '第15章：智能体间通信（A2A）/ Inter-Agent Communication (A2A)'
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

# 智能体间通信（A2A）/ Inter-Agent Communication (A2A)

> **来源**：https://adp.xindoo.xyz/chapters/Chapter%2015_%20Inter-Agent%20Communication%20(A2A)/
> **整理日期**：2026-03-23

---

## 核心概念

Agent2Agent（A2A）协议是 Google 主导的**开放标准 HTTP 协议**，旨在让不同 AI 框架（LangGraph、CrewAI、Google ADK 等）构建的智能体能够跨框架通信、协调任务和共享信息。A2A 的核心理念是：通过标准化"数字身份（Agent Card）+ 通信协议（JSON-RPC 2.0）"，让异构智能体像微服务一样互操作，构建模块化的多智能体生态系统。

---

## 解决什么问题

单个 AI 智能体在面对复杂多方面问题时存在固有局限：

- **能力边界**：单一智能体无法精通所有专业领域
- **框架孤岛**：不同框架构建的智能体缺乏通用通信语言
- **集成成本高**：为每对智能体定制集成协议耗时耗力
- **可扩展性差**：无法构建动态发现和委派任务的多智能体系统

A2A 通过开放标准消除框架壁垒，让专业化智能体能够协同工作，解决任何单一智能体无法独立完成的复杂任务。

---

## 工作原理 / 关键机制

### 核心参与者

```
用户
 ↓ 请求
A2A 客户端（Client Agent）  ←→  A2A 服务器（Remote Agent）
（代表用户发起请求的智能体）        （提供 HTTP 端点的远程智能体）
                                    （以"不透明"方式运行，客户端无需知晓内部实现）
```

### Agent 卡片（Agent Card）

Agent Card 是智能体的**数字身份 JSON 文件**，托管于标准路径（如 `/.well-known/agent.json`），包含：

```json
{
  "name": "WeatherBot",
  "description": "提供天气预报和历史数据",
  "url": "http://weather-service.example.com/a2a",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "authentication": { "schemes": ["apiKey"] },
  "skills": [
    {
      "id": "get_current_weather",
      "name": "Get Current Weather",
      "tags": ["weather", "real-time"]
    }
  ]
}
```

### Agent 发现策略

| 策略 | 适用场景 |
|------|----------|
| **标准 URI** (`/.well-known/agent.json`) | 公开服务，自动化发现 |
| **精选注册表** | 企业环境，集中管理和访问控制 |
| **直接配置** | 私有/紧密耦合系统 |

### 通信与任务模型

- 通信围绕**异步任务**结构化（唯一 ID，状态流转：已提交→工作中→已完成）
- 消息由**属性**（元数据键值对）+ **部分**（实际内容：文本/文件/JSON）组成
- 智能体产出的有形输出称为**工件（Artifact）**，支持流式输出
- 所有通信通过 **HTTP(S) + JSON-RPC 2.0** 进行
- 使用 `contextId` 跨多次交互维持上下文连续性

### 四种交互机制

| 机制 | 方法 | 适用场景 |
|------|------|----------|
| **同步请求/响应** | `sendTask` | 快速、即时操作 |
| **异步轮询** | `sendTask` + 轮询状态 | 长时间处理任务 |
| **流式更新（SSE）** | `sendTaskSubscribe` | 实时增量结果（如 LLM 逐字生成） |
| **推送通知（Webhook）** | 注册 webhook URL | 超长任务，客户端不想保持连接 |

### 安全机制

- **双向 TLS（mTLS）**：加密传输，防数据拦截
- **审计日志**：全量记录通信历史，支持问责和故障排查
- **Agent Card 声明**：集中管理身份验证需求
- **凭据处理**：OAuth 2.0 / API Key 通过 HTTP Header 传递（不暴露在 URL 或 Body 中）

### A2A vs MCP 对比

| 维度 | A2A | MCP（Anthropic） |
|------|-----|-----------------|
| **焦点** | 智能体间协调与任务委派 | 智能体与外部工具/数据的交互 |
| **关系** | 智能体 ↔ 智能体 | 智能体 ↔ 工具/资源 |
| **定位** | 互补协议，可同时使用 | 互补协议，可同时使用 |

---

## 应用场景

1. **多框架协作**：ADK 智能体委派任务给 LangChain 智能体，再委派给 CrewAI 智能体，各框架透明协作
2. **自动化工作流编排**：数据收集智能体 → 分析智能体 → 报告生成智能体，全程通过 A2A 通信串联
3. **动态信息检索**：主智能体向专属"数据获取 Agent"请求实时市场数据，后者调用外部 API 后返回结果

---

## 框架实现

### Google ADK + A2A 服务器实现

```python
from google.adk.agents import LlmAgent
from google.adk.tools.google_api_tool import CalendarToolset
from a2a.server.apps import A2AStarletteApplication
from a2a.server.agent_execution import ADKAgentExecutor

# 1. 定义智能体技能
skill = AgentSkill(
    id='check_availability',
    name='Check Availability',
    description="检查用户 Google Calendar 中的空闲时间",
    tags=['calendar'],
    examples=['Am I free from 10am to 11am tomorrow?'],
)

# 2. 定义 Agent Card（智能体数字身份）
agent_card = AgentCard(
    name='Calendar Agent',
    url=f'http://{host}:{port}/',
    version='1.0.0',
    capabilities=AgentCapabilities(streaming=True),
    skills=[skill],
)

# 3. 创建 ADK 智能体
adk_agent = LlmAgent(
    model='gemini-2.0-flash-001',
    name='calendar_agent',
    description="帮助管理用户日历的智能体",
    tools=await CalendarToolset(client_id=..., client_secret=...).get_tools(),
)

# 4. 包装为 A2A Web 服务（基于 Starlette + Uvicorn）
a2a_app = A2AStarletteApplication(agent_card=agent_card, http_handler=request_handler)
uvicorn.run(Starlette(routes=a2a_app.routes()), host=host, port=port)
```

**核心流程**：定义技能 → 创建 Agent Card → 封装为 HTTP 服务 → 自动支持 A2A 协议

**多框架示例仓库**：https://github.com/google-a2a/a2a-samples（包含 LangGraph、CrewAI、Azure AI Foundry、AG2 示例）

---

## 注意事项 / 权衡

| 考量 | 说明 |
|------|------|
| **部署复杂度** | 每个智能体独立作为 HTTP 服务运行，需要服务发现和网络管理 |
| **调试难度** | 分布式多智能体系统的问题排查比单体系统复杂得多 |
| **延迟叠加** | 多跳网络通信累积延迟，不适合对实时性要求极高的场景 |
| **安全边界** | 跨框架通信引入更大的攻击面，凭据管理和 mTLS 配置不可省略 |
| **协议成熟度** | A2A 仍在快速演进中，生产级采用需关注向后兼容性 |
| **与 MCP 互补** | 完整的多智能体系统通常同时使用 A2A（智能体协调）和 MCP（工具访问） |

---

## 一句话总结

> A2A 协议通过标准化的 Agent Card + HTTP/JSON-RPC 通信机制，打破不同 AI 框架的孤岛壁垒，让专业化智能体像微服务一样互相发现、委派任务和协作，是构建复杂模块化多智能体系统的基础设施标准。
