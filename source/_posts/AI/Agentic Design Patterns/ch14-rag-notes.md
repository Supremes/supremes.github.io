---
title: '第14章：知识检索（RAG）/ Knowledge Retrieval (RAG)'
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

# 知识检索（RAG）/ Knowledge Retrieval (RAG)

> **来源**：https://adp.xindoo.xyz/chapters/Chapter%2014_%20Knowledge%20Retrieval%20(RAG)/
> **整理日期**：2026-03-23

---

## 核心概念

RAG（Retrieval-Augmented Generation，检索增强生成）是一种在 LLM 生成响应**之前**，先从外部知识库检索相关信息并将其注入提示的模式。LLM 的知识库受限于训练截止日期，而 RAG 让它像人类查阅参考书一样"即时查找"最新或专有信息，从而生成更准确、可验证、减少幻觉的答案。对 AI 智能体而言，RAG 是从"对话者"跃升为"数据驱动执行者"的关键能力。

---

## 解决什么问题

| 问题 | LLM 局限 | RAG 解决方案 |
|------|----------|-------------|
| 知识过时 | 训练数据有截止日期 | 接入实时/最新外部知识库 |
| 幻觉风险 | 凭记忆生成可能出错 | 基于可验证的检索数据作答 |
| 私有数据 | 无法访问企业内部文档 | 索引公司内部知识库 |
| 可信度低 | 无法提供来源引用 | 可明确标注信息出处 |

---

## 工作原理 / 关键机制

### 标准 RAG 流程

```
用户查询
   ↓
语义搜索（向量数据库）
   ↓
检索最相关文档块（Top-K chunks）
   ↓
增强提示（原始查询 + 检索块）
   ↓
LLM 生成基于事实的响应
```

### 核心技术概念

**1. 嵌入（Embeddings）**
- 将文本转换为高维数值向量，捕捉语义含义
- 语义相近的文本在向量空间中距离近（如 "cat" 和 "kitten"）
- 使得语义搜索成为可能，而非简单关键字匹配

**2. 文档分块（Chunking）**
- 大文档拆分为较小片段（章节/段落/句子）
- 保持上下文完整性的同时提高检索精度
- 让 LLM 获得聚焦的信息而非整篇文档

**3. 向量数据库**
- 专为高效存储和查询嵌入向量而设计
- 使用 HNSW 等算法在百万向量中快速找到最相似的
- 代表产品：Pinecone、Weaviate、Chroma DB、Milvus、Qdrant
- 现有数据库的向量扩展：pgvector（Postgres）、Redis、Elasticsearch

**4. 检索策略对比**

| 策略 | 原理 | 优缺点 |
|------|------|--------|
| **向量搜索** | 语义相似度匹配 | 理解含义，但对精确词匹配弱 |
| **BM25** | 关键字频率排名 | 精确词匹配强，不理解语义 |
| **混合搜索** | 两者结合 | 兼顾精确性和语义理解，推荐使用 |

### 进阶：Graph RAG

使用**知识图谱**（节点 = 实体，边 = 关系）替代向量数据库，能够跨文档综合碎片化信息，适合复杂金融分析、科学研究等需要理解实体关系的场景。代价：构建维护成本显著更高。

### 最高级：Agentic RAG

在标准 RAG 上引入**推理智能体层**，主动担任知识的"守门人"：

```
检索 → [智能体评估] → LLM 生成
         ↑
    • 反思与来源验证（过滤过时文档）
    • 协调知识冲突（选择最可靠来源）
    • 多步推理（分解复杂问题为子查询）
    • 识别知识差距（激活外部工具补充）
```

---

## 应用场景

1. **企业内部问答**：员工提问 HR 政策、技术规范 → AI 从内部文档检索精准答案
2. **客户支持帮助台**：产品手册 + FAQ 索引，自动回答常见问题，减少人工介入
3. **个性化内容推荐**：语义匹配用户兴趣，而非简单关键字过滤
4. **新闻与时事摘要**：对接实时新闻源，基于最新信息生成事实准确的摘要

---

## 框架实现

### Google ADK 实现 1：Google Search 工具（内置 RAG）

```python
from google.adk.tools import google_search
from google.adk.agents import Agent

search_agent = Agent(
    name="research_assistant",
    model="gemini-2.0-flash-exp",
    instruction="帮助用户研究主题时，使用 Google Search 工具获取最新信息",
    tools=[google_search]
)
```

### Google ADK 实现 2：Vertex AI RAG Corpus

```python
from google.adk.memory import VertexAiRagMemoryService

memory_service = VertexAiRagMemoryService(
    rag_corpus="projects/your-project/locations/us-central1/ragCorpora/your-corpus-id",
    similarity_top_k=5,         # 返回 Top-5 最相关块
    vector_distance_threshold=0.7  # 语义距离阈值过滤
)
```

### LangChain 实现

```python
from langchain_community.vectorstores import Weaviate
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.schema.runnable import RunnablePassthrough

# 完整链：文档分块 → 嵌入 → 向量存储 → 检索 → LLM 生成
# 使用 Weaviate 作为向量数据库，OpenAI 嵌入模型
```

---

## 注意事项 / 权衡

| 挑战 | 说明 |
|------|------|
| **碎片化信息** | 答案跨多文档分散时，检索可能遗漏关键上下文 |
| **检索噪声** | 不相关的块会干扰 LLM，降低答案质量 |
| **知识库维护** | 需要定期更新索引，尤其对频繁变化的内容（如公司 Wiki） |
| **性能开销** | 检索步骤增加延迟、运营成本和 Token 消耗 |
| **矛盾来源** | 综合相互矛盾信息的能力仍是技术挑战 |
| **Agentic RAG 代价** | 引入推理层显著增加工程复杂度、延迟和成本，智能体本身也可能引入新错误 |

---

## 一句话总结

> RAG 通过在生成前检索外部知识，赋予 LLM「查阅参考书」的能力，显著减少幻觉、提升时效性；Agentic RAG 进一步引入推理层主动评估和综合信息，将 AI 从被动检索者升级为主动的知识解决问题者。
