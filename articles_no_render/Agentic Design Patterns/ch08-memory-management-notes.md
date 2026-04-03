---
title: '第8章：记忆管理 | Memory Management'
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

# 记忆管理 | Memory Management

- **来源 URL**：https://adp.xindoo.xyz/chapters/Chapter%208_%20Memory%20Management/
- **整理日期**：2026-03-23
- **所属系列**：AI Agent Design Patterns（第8章）

---

## 1. 核心概念

记忆管理（Memory Management）是 AI 智能体维持对话上下文、跨会话保留知识和提供个性化交互的基础能力。与人类记忆类似，智能体记忆分为两大层次：**短期记忆（上下文记忆）**保存当前交互中的即时信息，存在于 LLM 上下文窗口内；**长期记忆（持久记忆）**则通过外部数据库（如向量数据库）跨会话保存持久知识，支持语义检索。有效的记忆管理使智能体能够做决策、维护连贯对话并持续改进，而不仅是孤立地回答一次性问题。

---

## 2. 解决什么问题

没有记忆机制的智能体存在以下局限：

- 无法维护多轮对话上下文，每次响应都"失忆"
- 无法跨会话记住用户偏好、历史操作
- 无法从过去的成功/失败经验中学习和适应
- 被限制在简单的一次性交互，无法处理多步骤复杂任务

**核心矛盾**：LLM 上下文窗口有限且临时（会话结束即丢失），而真正有用的智能体需要跨时间积累和调用知识。

---

## 3. 工作原理 / 关键机制

### 双层记忆架构

```
┌─────────────────────────────────────────────────────────────┐
│                     智能体记忆体系                           │
├──────────────────────────┬──────────────────────────────────┤
│     短期记忆（临时）      │       长期记忆（持久）           │
│  LLM 上下文窗口内        │  外部数据库 / 向量存储           │
│  - 最近消息              │  - 语义记忆（事实/偏好）         │
│  - 工具调用结果           │  - 情景记忆（过去经历）          │
│  - 智能体反思             │  - 程序记忆（操作规则）          │
│  会话结束即丢失           │  可跨会话持久化、语义检索         │
└──────────────────────────┴──────────────────────────────────┘
```

### 长期记忆的三种类型

| 类型 | 含义 | 实现方式 |
|------|------|---------|
| 语义记忆 | 记住事实（用户偏好、领域知识） | JSON 文档/用户配置文件 |
| 情景记忆 | 记住经历（如何完成任务） | 少样本示例提示 |
| 程序记忆 | 记住规则（核心指令和行为） | 系统提示 + 反思机制更新 |

### Google ADK 的三核心组件

- **Session**：代表单个聊天线程，记录消息历史（Events）和临时状态（State）
- **State（session.state）**：会话内的键值字典，支持前缀作用域：
  - `user:` — 跨所有会话的用户数据
  - `app:` — 所有用户共享的应用数据
  - `temp:` — 仅当前处理轮次有效
- **MemoryService**：管理长期知识库的存储与检索

---

## 4. 应用场景

1. **聊天机器人与对话式 AI**：短期记忆维持对话流；长期记忆让机器人记住用户习惯、历史问题，提供个性化持续体验。
2. **面向任务的多步骤智能体**：跟踪任务进度、前序步骤和总体目标；访问用户专属数据（如账户信息）。
3. **个性化推荐系统**：长期存储并检索用户偏好、行为历史，生成定制化响应和建议。
4. **学习与自我改进的智能体**：将成功策略、错误信息存入长期记忆，驱动未来行为优化；结合反思机制自动更新系统提示。
5. **知识问答（RAG）**：智能体访问知识库（即长期记忆），通过检索增强生成（RAG）检索相关文档来指导回答。
6. **机器人与自动驾驶系统**：短期记忆处理即时环境，长期记忆存储地图、路线、学习行为。

---

## 5. 框架实现对比

### LangChain — 短期对话记忆

```python
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
conversation = LLMChain(llm=llm, prompt=prompt, memory=memory)
# 自动将对话历史注入提示，无需手动管理
```

### LangGraph — 长期记忆（跨会话）

```python
from langgraph.store.memory import InMemoryStore

store = InMemoryStore(index={"embed": embed_fn, "dims": 768})
namespace = (user_id, "preferences")
# 存入记忆
store.put(namespace, "key", {"rules": ["用户偏好简洁语言"]})
# 语义检索
items = store.search(namespace, query="语言偏好")
```

LangGraph 支持三类长期记忆：语义（事实）、情景（经历）、程序（规则/指令），可通过"反思"节点自动更新智能体指令。

### Google ADK — Session / State / MemoryService

```python
from google.adk.sessions import InMemorySessionService, DatabaseSessionService, VertexAiSessionService

# 开发测试
session_service = InMemorySessionService()
# 生产持久化
session_service = DatabaseSessionService("sqlite:///agent.db")
# Google Cloud 可扩展
session_service = VertexAiSessionService(project="PROJECT_ID", location="us-central1")
```

**Vertex Memory Bank**：托管服务，用 Gemini 模型异步分析对话，提取关键事实，持久存储并支持跨会话检索，兼容 ADK、LangGraph、CrewAI。

---

## 6. 注意事项与权衡

| 方面 | 说明 |
|------|------|
| **上下文窗口限制** | 短期记忆受 LLM token 上限约束；"长上下文"模型只是扩大容量，仍是临时的 |
| **存储成本** | 长期记忆需要外部数据库维护，增加基础设施成本 |
| **检索延迟** | 向量相似度检索引入额外 I/O 开销 |
| **记忆噪声** | 存储过多无效信息会降低检索质量 |
| **一致性** | 多会话间状态合并存在冲突风险（如矛盾的用户偏好） |
| **隐私合规** | 长期存储用户数据需遵守 GDPR 等法规 |
| **状态更新方式** | 在 ADK 中应通过 `EventActions.state_delta` 或 `output_key` 更新状态，不应直接修改状态字典，以确保持久化正确性 |

---

## 7. 一句话总结

> **记忆管理让智能体从"只会回答当前问题"进化为"能积累经验、持续学习、个性化服务"的真正智能系统**——其本质是用双层记忆架构（上下文窗口 + 外部持久存储）弥合 LLM 无状态天性与有状态应用需求之间的鸿沟。
