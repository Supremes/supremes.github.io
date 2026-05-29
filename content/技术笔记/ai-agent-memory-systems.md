---
title: "AI Agent 记忆系统：从短期记忆到长期知识"
date: "2026-05-27"
tags: "AI Agent,记忆系统,RAG,向量数据库,Mem0"
summary: "记忆是 AI Agent 的核心能力之一。本文系统梳理短期记忆、长期记忆和工作记忆的实现方案，以及 RAG 和向量数据库的最佳实践。"
---

## 为什么 Agent 需要记忆？

LLM 的上下文窗口是有限的（通常 128K-200K tokens）。但 Agent 需要：

- 记住之前的对话内容（短期记忆）
- 跨会话保留知识（长期记忆）
- 在当前任务中跟踪状态（工作记忆）

没有记忆的 Agent 就像一个每天失忆的人——每次对话都从零开始。

## 记忆的三种类型

```
┌─────────────────────────────────────────┐
│              Agent 记忆系统               │
├─────────────┬─────────────┬─────────────┤
│  短期记忆    │  工作记忆    │  长期记忆    │
│  (Short-term)│ (Working)   │ (Long-term) │
├─────────────┼─────────────┼─────────────┤
│ 当前对话上下文│ 当前任务状态 │ 跨会话知识   │
│ 会话历史     │ 中间结果     │ 用户偏好     │
│ 上下文窗口内 │ 任务栈       │ 学习到的模式 │
└─────────────┴─────────────┴─────────────┘
```

### 短期记忆

**实现方式：** 对话历史（Message History）

```python
messages = [
    {"role": "system", "content": "你是一个助手"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么我能帮你的？"},
    # ... 对话继续
]
```

**挑战：** 上下文窗口有限，需要管理策略：

| 策略 | 说明 | 适用场景 |
|------|------|---------|
| 滑动窗口 | 保留最近 N 条消息 | 对话不太长 |
| 摘要压缩 | 用 LLM 压缩历史 | 长对话 |
| 重要性筛选 | 只保留重要消息 | 信息密度高的对话 |

### 工作记忆

**实现方式：** 结构化状态对象

```python
class AgentState:
    task: str                    # 当前任务
    plan: list[str]             # 执行计划
    current_step: int           # 当前步骤
    intermediate_results: dict  # 中间结果
    context: dict               # 任务上下文
```

工作记忆是 Agent 在执行任务时的「便签纸」，存储当前任务的进度和中间结果。

### 长期记忆

**实现方式：** 向量数据库 + 嵌入模型

```
用户输入
   ↓
[嵌入模型] → 向量
   ↓
[向量数据库] → 相似记忆检索
   ↓
注入上下文 → LLM 推理
```

## RAG：检索增强生成

RAG（Retrieval-Augmented Generation）是实现长期记忆的核心模式：

### 基本流程

```
1. 文档分块（Chunking）
   ↓
2. 向量化（Embedding）
   ↓
3. 存储到向量数据库
   ↓
4. 查询时：用户问题 → 向量化 → 相似度搜索 → 检索相关块
   ↓
5. 将检索结果注入 LLM 上下文 → 生成回答
```

### 分块策略

```python
# 按固定大小分块
chunks = split_by_size(text, chunk_size=512, overlap=50)

# 按语义分块（推荐）
chunks = split_by_semantic(text, similarity_threshold=0.8)

# 按结构分块（文档有明确结构时）
chunks = split_by_heading(text, level=2)
```

**最佳实践：**
- 块大小：256-1024 tokens（太大丢失精度，太小丢失上下文）
- 重叠：10-20%（避免在块边界丢失信息）
- 元数据：保留来源、时间、标题等信息

### 向量数据库选型

| 数据库 | 特点 | 适用场景 |
|--------|------|---------|
| **Qdrant** | 高性能、Rust 实现 | 生产环境 |
| **Pinecone** | 全托管、易用 | 快速上线 |
| **Weaviate** | 支持混合搜索 | 复杂查询 |
| **ChromaDB** | 轻量、嵌入式 | 原型开发 |
| **pgvector** | PostgreSQL 扩展 | 已有 PG 的团队 |

## Mem0：AI 记忆层的代表方案

Mem0 是一个专门的 AI 记忆基础设施：

```python
from mem0 import Memory

memory = Memory()

# 添加记忆
memory.add(
    "我喜欢用 Python 写后端，React 写前端",
    user_id="user_123"
)

# 搜索记忆
results = memory.search(
    "这个用户喜欢什么技术栈？",
    user_id="user_123"
)
```

**核心特性：**
- **跨会话持久化** — 记忆在不同会话间保持一致
- **跨 Agent 共享** — 多个 Agent 可共享记忆
- **记忆压缩** — 自动将聊天历史压缩为紧凑记忆
- **用户隔离** — 按用户维度隔离记忆数据

## 实战建议

### 1. 分层记忆架构

```python
class AgentMemory:
    def __init__(self):
        self.short_term = MessageHistory(max_messages=50)
        self.working = AgentState()
        self.long_term = VectorDB(collection="agent_memory")
```

### 2. 记忆检索优化

```python
# 混合检索：向量 + 关键词
results = hybrid_search(
    query="用户的项目进度",
    vector_weight=0.7,
    keyword_weight=0.3,
    top_k=5
)
```

### 3. 记忆生命周期管理

```
新增 → 验证 → 存储 → 定期清理 → 归档
```

不是所有信息都值得记住。建立记忆的「遗忘机制」同样重要。

## 总结

| 记忆类型 | 实现方式 | 关键技术 |
|---------|---------|---------|
| 短期记忆 | 对话历史 | 滑动窗口、摘要压缩 |
| 工作记忆 | 状态对象 | 结构化数据、任务栈 |
| 长期记忆 | 向量数据库 | RAG、嵌入模型、Mem0 |

> **记忆让 Agent 从「一次性工具」变成「持续学习的伙伴」。**

选择合适的记忆方案，是构建生产级 Agent 的关键一步。
