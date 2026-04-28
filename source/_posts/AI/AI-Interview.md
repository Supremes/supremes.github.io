---
title: AI-Interview
tags: []
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: false
updated: '2026-03-17 17:54'
abbrlink: 6c5038c3
date: 2026-03-17 11:00:25
categories:
sticky:
---

> [!Interview]
> - 项目架构怎么设计？
> - Agent 系统怎么拆分？
> - Planner/Tool/Memory 怎么分层？
> - Memory 怎么搞？短期、长期和用户画像各自怎么处理？
> - 延迟、成本、效果如何平衡？Token 成本、推理延迟、RAG 召回策略怎么权衡？
> - RAG 效果怎么评估？召回率、准确率，线上怎么验证？
> 
> **高频：**
> - Tool Calling
> - Memory
> - RAG

## Learning

### Agent & 系统架构
- [ ] 1. 什么是 AI Agent？
- [ ] 2. Agent 和普通 ChatBot 有什么区别？
- [ ] 3. 如何实现多 Agent 协作系统？
- [ ] 4. 什么是 ReAct Agent？
- [ ] 5. AI Chat 系统的整体架构是什么？
- [ ] 6. 如何设计一个 AI 问答系统架构？
- [ ] 7. Agent 如何做任务规划（planning）？
- [ ] 8. Agent workflow 和普通 workflow 有什么区别？
- [ ] 9. Agent 为什么需要 memory？
- [ ] 10. Agent 如何避免无限循环调用工具？

### RAG
- [ ] 11. 什么是 RAG（Retrieval Augmented Generation）？
- [ ] 12. RAG 主要解决什么问题？
- [ ] 13. RAG pipeline 的完整流程是什么？
- [ ] 14. RAG 系统主要组件有哪些？
- [ ] 15. chunk size 为什么很重要？如何选择？
- [ ] 16. 文档切分有哪些策略？
- [ ] 17. RAG 如何做 rerank？
- [ ] 18. 如何实现 hybrid search（向量 + keyword）？
- [ ] 19. RAG latency 怎么优化？
- [ ] 20. 如何评估 RAG 系统效果？
- [ ] 21. RAG 如何避免检索错误？

### Memory
- [ ] 22. 什么是 ChatMemory？
- [ ] 23. Agent memory 有哪些类型？
- [ ] 24. 如何实现对话历史 memory？
- [ ] 25. 大模型上下文窗口是什么？如何突破长度限制？

### Embedding & 向量数据库
- [ ] 26. embedding 和向量相似度搜索是什么？
- [ ] 27. embedding 模型如何选择？
- [ ] 28. embedding 模型如何影响检索效果？
- [ ] 29. 向量数据库为什么适合语义检索？
- [ ] 30. 向量数据库如何进行相似度计算？

### LLM 原理
- [ ] 31. 什么是大语言模型（LLM）？
- [ ] 32. Transformer 架构核心原理是什么？
- [ ] 33. Self-Attention 的计算流程是什么？
- [ ] 34. 什么是 hallucination（幻觉）？为什么会发生？
- [ ] 35. 如何减少大模型 hallucination？
- [ ] 36. LLM 为什么推理成本高？
- [ ] 37. Temperature、Top-p、Top-k 有什么区别？

### Tool Calling & Prompt
- [ ] 38. 什么是 Tool Calling？
- [ ] 39. 什么是 Prompt Engineering？
- [ ] 40. ChatGPT 的 system / user / assistant role 有什么作用？
- [ ] 41. LangChain4j 如何实现 Tool 调用？
- [ ] 42. LangChain4j 如何返回结构化 JSON？
- [ ] 43. LangChain4j 如何实现 prompt template？
- [ ] 44. 如何设计 Prompt 管理系统？
- [ ] 45. 如何评估 Agent 的执行效果？

### Java / Spring AI / LangChain4j
- [ ] 46. 什么是 AI Service（LangChain4j）？
- [ ] 47. Spring AI 和 LangChain4j 有什么区别？
- [ ] 48. LangChain4j 和 Python LangChain 有什么区别？
- [ ] 49. 如何在 Spring Boot 中集成 LangChain4j？
- [ ] 50. Java 如何实现 streaming response？
- [ ] 51. Java 调用 OpenAI API 如何设计 SDK？
- [ ] 52. Java LLM 服务如何做连接池管理？

### 工程化 & 可观测性
- [ ] 53. 如何实现 SSE 推送？
- [ ] 54. streaming response 如何实现？
- [ ] 55. LLM 服务如何做缓存？
- [ ] 56. LLM 服务如何做限流？
- [ ] 57. LLM 服务如何做降级？
- [ ] 58. 如何做模型 fallback？
- [ ] 59. 多模型调度如何实现？
- [ ] 60. LLM 如何实现多租户？
- [ ] 61. LLM API 如何设计接口？
- [ ] 62. LLM latency 如何优化？
- [ ] 63. MCP（Model Context Protocol）是什么？
- [ ] 64. AI系统如何记录 Prompt 和 Response？
- [ ] 65. AI系统如何做监控？
- [ ] 66. AI系统如何做成本控制？
- [ ] 67. AI系统如何做权限控制？
- [ ] 68. 如何统计 token usage？
- [ ] 69. 如何设计 AI evaluation pipeline？
- [ ] 70. 如何做 A/B test 比较不同模型？

---

## 参考答案

### Agent & 系统架构

#### 1. 什么是 AI Agent？
AI Agent 是一个能够**感知环境、自主规划、调用工具并执行任务**的智能系统。与普通 LLM 一问一答不同，Agent 具备以下能力：
- **感知**：接收用户输入、工具返回结果、上下文状态
- **规划（Planning）**：利用 LLM 进行推理、任务分解、多步决策
- **执行（Action）**：调用外部工具（搜索、数据库、API、代码执行等）
- **记忆（Memory）**：维护短期对话上下文和长期知识状态
- **反馈循环**：根据工具执行结果调整下一步行动

典型框架：LangChain4j AiServices、Spring AI、AutoGen。

#### 2. Agent 和普通 ChatBot 有什么区别？

| 维度 | ChatBot | Agent |
|------|---------|-------|
| 能力 | 仅文本生成、对话 | 调用工具、执行动作、操作外部系统 |
| 规划能力 | 无 | 任务分解、多步推理、ReAct 循环 |
| 记忆 | 短期上下文窗口 | 短期 + 长期 + 外部状态 |
| 自主性 | 低，依赖用户引导 | 高，可自主决策下一步 |
| 适用场景 | 客服、FAQ、闲聊 | 复杂任务自动化、代码生成执行、数据分析 |

#### 3. 如何实现多 Agent 协作系统？
多 Agent 系统常见模式：
- **Orchestrator-Worker 模式**：一个主 Agent 负责任务拆解和调度，多个子 Agent 各司其职（搜索 Agent、代码 Agent、数据库 Agent）
- **Pipeline 模式**：各 Agent 串行处理，前一个输出作为后一个输入
- **竞争/投票模式**：多个 Agent 独立执行，取最优或投票决策
- **消息总线模式**：Agent 通过消息队列（如 Redis Pub/Sub）异步通信

关键要素：
1. 清晰的 Agent 角色定义和能力边界
2. 统一的消息格式（通常是结构化 JSON）
3. 任务状态追踪（防止死循环）
4. 错误处理和超时机制

LangChain4j 可通过 AiServices 组合多个 service 实现，Spring AI 通过 Tool 注入实现子任务委派。

#### 4. 什么是 ReAct Agent？
ReAct = **Reasoning + Acting**，是一种将推理和行动交替进行的 Agent 模式：

```
Thought: 我需要查询用户的订单信息
Action: query_order(user_id=123)
Observation: 订单状态为"已发货"，快递单号为SF12345
Thought: 需要进一步查询快递状态
Action: track_express(no="SF12345")
Observation: 当前在上海转运中心
Thought: 信息已足够，可以回复用户
Answer: 您的订单已发货，快递正在上海转运中心...
```

优点：推理链路透明可解释，工具调用有明确依据。
在 LangChain4j 中通过 `@Tool` 注解 + `AiServices` 自动实现 ReAct 循环。

#### 5. AI Chat 系统的整体架构是什么？
```
用户请求
   ↓
[API Gateway / 限流]
   ↓
[Chat Service]
   ├─ Session 管理（会话 ID、用户信息）
   ├─ Memory 层（ChatMemory、短期上下文）
   ├─ RAG 层（向量检索、知识库）
   ├─ Agent/Tool 层（工具调用）
   └─ LLM 层（模型路由、Token 计费）
           ↓
      [LLM API]（OpenAI / Claude / 本地模型）
           ↓
[Streaming Response → SSE → 前端]
```
辅助组件：向量数据库（Milvus/Weaviate）、关系数据库（MySQL 存会话）、监控（Prometheus + Grafana）、日志（ELK）。

#### 6. 如何设计一个 AI 问答系统架构？
核心链路：`用户问题 → Query 改写 → RAG 检索 → Prompt 构建 → LLM 推理 → 答案后处理 → 返回`

关键设计点：
- **Query 改写**：多路查询扩展（HyDE）、意图识别
- **检索层**：向量检索 + BM25 混合检索，rerank 精排
- **Prompt 构建**：System prompt + 检索上下文 + 对话历史 + 用户问题
- **答案验证**：Faithfulness 检查（答案是否基于检索内容）
- **缓存**：语义缓存相似问题
- **降级**：RAG 无结果时 fallback 到纯 LLM 回答

#### 7. Agent 如何做任务规划（planning）？
主要规划策略：
- **ReAct**：边推理边执行，逐步决策
- **Plan-and-Execute**：先生成完整执行计划，再逐步执行（适合确定性强的任务）
- **Tree of Thought（ToT）**：树状探索多条路径，选最优路径
- **Self-Consistency**：多次采样取一致性最高的答案

在 LangChain4j 中可用 `AiServices` + 多步对话实现，或集成 LangGraph4j（Graph 状态机）做复杂规划。

#### 8. Agent workflow 和普通 workflow 有什么区别？

| 维度 | 普通 workflow | Agent workflow |
|------|--------------|----------------|
| 决策方式 | 预定义流程，硬编码条件 | LLM 动态决策，灵活路由 |
| 适应性 | 低，新情况需修改代码 | 高，LLM 可处理未见情况 |
| 可解释性 | 高 | 相对低（黑盒推理） |
| 稳定性 | 高 | 较低（非确定性） |
| 适用场景 | 固定流程审批、ETL | 复杂对话、开放式任务 |

Agent workflow 通常通过状态机（如 LangGraph）管理节点流转，结合 LLM 做路由判断。

#### 9. Agent 为什么需要 memory？
LLM 本身是**无状态**的，每次请求独立。Agent 需要 memory 的原因：
- **上下文连贯性**：多轮对话需要记住前几轮的内容
- **任务状态追踪**：多步任务中记录已完成哪些步骤
- **用户偏好**：长期记住用户习惯、个性化设置
- **工具调用结果**：保存中间工具执行结果供后续步骤使用

没有 memory，Agent 每次都从零开始，无法完成需要上下文的复杂任务。

#### 10. Agent 如何避免无限循环调用工具？
- **最大迭代次数限制**：设置 `maxIterations`（如 LangChain4j 默认10次），超过则强制终止
- **循环检测**：检测连续相同 Action + 相同参数，判定为循环，中断执行
- **Token/时间预算**：设置最大 Token 消耗或超时时间
- **工具幂等性标记**：对已执行过的工具+参数组合做去重
- **强制终止条件**：在 System Prompt 中明确说明"若无法得出结论，直接回复无法完成"

---

### RAG

#### 11. 什么是 RAG（Retrieval Augmented Generation）？
RAG = **检索增强生成**，是将**外部知识检索**与 **LLM 生成**结合的技术：
1. 用户提问 → 向量化 query
2. 在向量数据库中检索相关文档片段
3. 将检索结果拼入 Prompt
4. LLM 基于上下文生成答案

解决了 LLM 知识过时、幻觉、私有知识无法使用等问题。

#### 12. RAG 主要解决什么问题？
- **知识时效性**：LLM 训练数据有截止日期，RAG 可接入实时/私有知识库
- **幻觉（Hallucination）**：提供真实文档作为依据，减少 LLM 凭空捏造
- **私有数据**：企业内部文档、代码库不可能放入训练数据，RAG 可低成本接入
- **可溯源性**：答案来自检索文档，可提供引用来源

#### 13. RAG pipeline 的完整流程是什么？
**离线阶段（Indexing）：**
```
原始文档 → 文档解析 → 文本切分（Chunking）→ Embedding → 存入向量数据库
```

**在线阶段（Retrieval & Generation）：**
```
用户 Query → Query 预处理/改写 → Embedding → 向量检索（Top-K）
    → （可选）Rerank 精排 → Prompt 构建 → LLM 生成 → 后处理 → 返回答案
```

#### 14. RAG 系统主要组件有哪些？
| 组件 | 作用 | 常用工具 |
|------|------|---------|
| 文档解析 | PDF/Word/HTML 转文本 | Apache Tika, PDFBox |
| 文本切分 | 按语义/固定大小切块 | LangChain4j TextSplitter |
| Embedding 模型 | 文本向量化 | OpenAI Ada, BGE, M3E |
| 向量数据库 | 存储和检索向量 | Milvus, Weaviate, Qdrant |
| Reranker | 精排检索结果 | Cohere Rerank, BGE-Reranker |
| LLM | 基于上下文生成答案 | GPT-4, Claude, Qwen |
| 缓存层 | 相似问题缓存 | Redis + 语义相似度 |

#### 15. chunk size 为什么很重要？如何选择？
chunk size 影响检索精度和上下文完整性：
- **太小**（< 128 tokens）：语义不完整，检索准确但缺乏上下文，答案不完整
- **太大**（> 1024 tokens）：噪音多，相关性被稀释，检索质量下降
- **推荐策略**：
  - 通用文档：256-512 tokens，overlap 50-100 tokens
  - FAQ/问答对：一问一答为一个 chunk
  - 代码：按函数/类切分
  - 长文档：先按段落/标题切分，再细分

建议通过评估（召回率 + 答案质量）来确定最佳 chunk size。

#### 16. 文档切分有哪些策略？
- **固定长度切分**：按 token 数量固定切分，简单但可能截断语义
- **递归字符切分（RecursiveCharacter）**：优先按段落→句子→词切分，LangChain4j 推荐
- **语义切分（Semantic）**：通过 embedding 相似度检测语义边界，质量最高但最慢
- **句子切分**：按句号/换行切分，适合新闻、评论类文本
- **结构化切分**：按 Markdown 标题、HTML 标签、代码块边界切分
- **父子切分（Parent-Child）**：存储大 chunk，检索小 chunk，返回时扩展为父 chunk

#### 17. RAG 如何做 rerank？
Rerank 是对向量检索 Top-K 结果进行二次精排，提升相关性：

**方式一：Cross-Encoder Reranker**（质量最好）
```
每个 (query, chunk) 对送入 rerank 模型，输出相关性分数
常用模型：Cohere Rerank, BGE-Reranker-v2, bce-reranker-base
```

**方式二：LLM Rerank**
```
让 LLM 对检索结果排序（成本高，速度慢）
```

**方式三：RRF（Reciprocal Rank Fusion）**
```
合并多路检索结果的排名，公式：score = Σ 1/(k + rank_i)
适合 hybrid search 结果融合
```

LangChain4j 中通过 `ContentAggregator` + `ReRankingContentInjector` 实现。

#### 18. 如何实现 hybrid search（向量 + keyword）？
Hybrid Search = **向量语义检索** + **BM25/全文关键词检索**，互补优势：

```java
// 向量检索 - 语义相似
List<TextSegment> vectorResults = vectorStore.search(query, topK=20);

// BM25/全文检索 - 关键词精确匹配
List<TextSegment> keywordResults = bm25Index.search(query, topK=20);

// 融合排序（RRF）
List<TextSegment> merged = rrfMerge(vectorResults, keywordResults);

// 可选 Rerank
return reranker.rerank(query, merged.subList(0, 10));
```

支持 hybrid search 的向量数据库：Weaviate、Qdrant（native hybrid）、Elasticsearch（dense_vector + BM25）。

#### 19. RAG latency 怎么优化？
| 优化点 | 方法 |
|--------|------|
| 向量检索 | ANN 近似检索（HNSW）替代精确检索，topK 控制在 5-10 |
| Embedding | 本地部署小模型，或 batch 请求 |
| Rerank | 只对 Top-K 做 rerank，减少候选数量 |
| 缓存 | 语义缓存（相似问题直接返回缓存答案） |
| 并行化 | 多路检索并行，embedding + 检索 pipeline 化 |
| Prompt 压缩 | 对检索内容做摘要压缩，减少 LLM 输入 |
| 流式返回 | SSE/Streaming 让用户先看到部分答案 |

#### 20. 如何评估 RAG 系统效果？
**检索评估：**
- **Recall@K**：相关文档在 Top-K 中的召回比例
- **MRR（Mean Reciprocal Rank）**：最相关文档排名的倒数均值
- **NDCG**：归一化折扣累计增益

**生成评估：**
- **Faithfulness（忠实度）**：答案是否有检索内容支撑（防幻觉）
- **Answer Relevance**：答案是否回答了用户问题
- **Context Precision/Recall**：检索上下文是否恰当

**工具：** RAGAS 框架（自动化评估）、人工标注金标集对比。

#### 21. RAG 如何避免检索错误？
- **Query 改写/扩展**：HyDE（生成假设文档再检索）、多 Query 扩展增加召回
- **提高 Chunk 质量**：合理切分、去重、清洗噪音数据
- **Hybrid Search**：向量 + 关键词双路检索，避免单一召回失败
- **Rerank**：精排过滤低相关结果
- **No-answer 判断**：检索结果相似度低于阈值时，直接回复"知识库无相关信息"而非强行生成
- **Faithfulness 检查**：生成答案后验证是否有对应原文依据

---

### Memory

#### 22. 什么是 ChatMemory？
ChatMemory 是维护**对话历史**的组件，让 LLM 在多轮对话中保持上下文。

LangChain4j 提供两种实现：
- **MessageWindowChatMemory**：保留最近 N 条消息（滑动窗口），超出则截断最旧消息
- **TokenWindowChatMemory**：按 Token 数量限制，超出则从最旧消息开始删除

```java
ChatMemory memory = MessageWindowChatMemory.withMaxMessages(20);
// 或
ChatMemory memory = TokenWindowChatMemory.withMaxTokens(4096, tokenizer);
```

多用户场景需为每个 userId 维护独立的 ChatMemory 实例（通常存 Redis/DB）。

#### 23. Agent memory 有哪些类型？
| 类型 | 描述 | 存储方式 |
|------|------|---------|
| **短期记忆（Working Memory）** | 当前对话上下文，Token 窗口内 | 内存/Context Window |
| **长期记忆（Long-term Memory）** | 跨会话持久化信息，用户历史偏好 | 数据库 / 向量库 |
| **情节记忆（Episodic Memory）** | 历史对话的摘要/关键事件 | 向量数据库（可语义检索） |
| **语义记忆（Semantic Memory）** | 结构化知识、用户画像、事实 | KV 存储 / 图数据库 |
| **程序记忆（Procedural Memory）** | Agent 如何使用工具的策略 | 内嵌于 System Prompt |

#### 24. 如何实现对话历史 memory？
```java
// LangChain4j 实现多用户对话 Memory
@Bean
public ChatMemoryStore chatMemoryStore() {
    return new RedisChatMemoryStore(); // 自定义实现
}

interface MyAiService {
    @SystemMessage("你是一个助手")
    String chat(@MemoryId String userId, @UserMessage String message);
}

// LangChain4j 自动按 userId 隔离 Memory
MyAiService service = AiServices.builder(MyAiService.class)
    .chatLanguageModel(model)
    .chatMemoryProvider(userId -> 
        MessageWindowChatMemory.builder()
            .id(userId)
            .maxMessages(20)
            .chatMemoryStore(store)
            .build())
    .build();
```

#### 25. 大模型上下文窗口是什么？如何突破长度限制？
**上下文窗口**：LLM 单次推理能处理的最大 Token 数（如 GPT-4 128K、Claude 200K）。

**突破长度限制的方法：**
- **滑动窗口**：保留最近 N 轮对话，丢弃最旧
- **对话摘要压缩（Summary Memory）**：定期将旧对话总结为摘要，只保留摘要
- **RAG 化 Memory**：将历史存入向量库，按需检索相关片段注入上下文
- **分层 Memory**：近期对话保留原文，远期对话保留摘要
- **文档分块处理**：长文档切分多次处理，用 Map-Reduce 模式合并结果

---

### Embedding & 向量数据库

#### 26. embedding 和向量相似度搜索是什么？
**Embedding**：将文本（或图片）映射为一个高维实数向量，语义相近的文本在向量空间中距离较近。

```
"苹果手机" → [0.23, -0.15, 0.87, ...]  (1536维)
"iPhone"    → [0.21, -0.13, 0.85, ...]  ← 距离很近
"香蕉"      → [-0.52, 0.34, -0.11, ...] ← 距离较远
```

**向量相似度搜索**：在海量向量中找出与 query 向量最相近的 Top-K 向量，常用算法：
- **余弦相似度（Cosine Similarity）**：最常用，衡量方向夹角
- **内积（Dot Product）**：效率更高，适合归一化向量
- **欧氏距离（L2）**：衡量绝对距离

#### 27. embedding 模型如何选择？
| 维度 | 选择建议 |
|------|---------|
| **语言** | 中文优先：BGE（BAAI）、M3E、text2vec；多语言：multilingual-e5 |
| **精度 vs 速度** | 高精度：bge-large；高速度：bge-small、bce-embedding-base |
| **向量维度** | OpenAI Ada: 1536维；BGE-large: 1024维；BGE-small: 512维 |
| **私有化部署** | 优先 BGE 系列（开源），可本地部署 |
| **通用场景** | OpenAI text-embedding-3-large 效果最好但有成本 |

评估方法：在业务数据上跑 MTEB 基准或自定义检索评估集。

#### 28. embedding 模型如何影响检索效果？
- **语义理解能力**：好的 embedding 模型能理解近义词、上下位关系，差的模型只能匹配字面
- **领域适配**：通用 embedding 在垂直领域（医疗/法律/代码）效果差，需领域微调
- **语言适配**：中文 embedding 用中文训练的模型，避免用英文模型强行处理中文
- **向量维度**：维度越高表达能力越强，但检索速度越慢（存储和计算开销↑）
- **相似度函数匹配**：不同模型可能优化不同的相似度函数（Cosine vs Dot Product），需配套使用

#### 29. 向量数据库为什么适合语义检索？
传统数据库（MySQL）是精确匹配（WHERE name = 'xxx'），无法做语义相似搜索。向量数据库的优势：
- **ANN（近似最近邻）算法**：HNSW、IVF 等索引支持毫秒级亿级向量检索
- **语义相似度**：基于 embedding 的距离，捕捉语义而非字面匹配
- **过滤能力**：支持 metadata 过滤（如只检索某部门的文档）
- **可扩展性**：Milvus、Qdrant 支持分布式水平扩展

常用向量数据库：**Milvus**（大规模）、**Qdrant**（轻量高性能）、**Weaviate**（自带 embedding）、**pgvector**（PostgreSQL 插件，适合小规模）。

#### 30. 向量数据库如何进行相似度计算？
**精确计算（Exact Search）：** 暴力遍历所有向量，计算余弦相似度，准确但 O(n) 慢。

**近似最近邻（ANN）：**
- **HNSW（Hierarchical Navigable Small World）**：图索引，查询速度极快（微秒级），内存占用大，Qdrant/Milvus 默认使用
- **IVF（Inverted File）**：聚类倒排索引，将向量分组，只搜索相近的簇
- **PQ（Product Quantization）**：向量量化压缩，减少内存，牺牲一点精度

主流选择：**HNSW** 用于高性能场景，**IVF_PQ** 用于大规模内存受限场景。

---

### LLM 原理

#### 31. 什么是大语言模型（LLM）？
LLM（Large Language Model）是基于 **Transformer 架构**、在海量文本数据上预训练的神经网络模型。
- 参数规模：数十亿到数千亿（GPT-3 1750亿）
- 能力：文本生成、理解、翻译、推理、代码生成等
- 原理：自回归（Autoregressive）预测下一个 Token
- 训练阶段：预训练 → 指令微调（SFT）→ RLHF（人类反馈强化学习）

代表模型：GPT-4（OpenAI）、Claude（Anthropic）、Qwen（阿里）、Llama（Meta）。

#### 32. Transformer 架构核心原理是什么？
Transformer 核心是 **Self-Attention 机制**，彻底摒弃了 RNN 的序列依赖。

```
输入 → Embedding + Positional Encoding
      ↓
[Transformer Block × N]
  ├─ Multi-Head Self-Attention（捕捉全局依赖）
  ├─ Add & Norm（残差连接 + LayerNorm）
  ├─ Feed-Forward Network（两层全连接，引入非线性）
  └─ Add & Norm
      ↓
输出层（语言模型头：预测下一 Token 概率）
```

关键创新：
- **并行计算**：不同 Token 可并行计算 Attention，训练速度远超 RNN
- **长程依赖**：任意两个位置直接计算 Attention，O(1) 路径长度
- **多头注意力**：不同 Head 关注不同语义关系

#### 33. Self-Attention 的计算流程是什么？
```
输入 X → 三个线性变换 → Q（Query）、K（Key）、V（Value）

Attention(Q, K, V) = softmax(QKᵀ / √d_k) × V
```

步骤：
1. 输入向量乘以 Wq、Wk、Wv 得到 Q、K、V 矩阵
2. Q × Kᵀ 计算注意力得分矩阵（每对 Token 间的相关性）
3. 除以 √d_k 缩放（防止 softmax 梯度消失）
4. Softmax 归一化得到注意力权重
5. 权重 × V 加权求和得到输出

多头（Multi-Head）：用多组独立的 Q/K/V，并行计算多个 Attention，最后拼接，捕捉不同类型的语义关系。

#### 34. 什么是 hallucination（幻觉）？为什么会发生？
**幻觉**：LLM 生成看似合理但实际上**不准确或捏造**的信息（错误事实、不存在的引用等）。

原因：
- **训练数据分布**：模型学习的是统计模式，而非事实核查
- **自回归生成**：逐 Token 生成，一旦走错方向会持续编造自洽内容
- **知识截止**：训练数据有时效性，过期知识导致错误
- **过度自信**：模型无法感知自身的不确定性边界
- **Prompt 模糊**：问题歧义导致模型猜测意图并填充内容

#### 35. 如何减少大模型 hallucination？
- **RAG**：提供真实文档作为依据，要求模型只基于上下文回答
- **Prompt 设计**：明确要求"如果不确定请说不知道"，设置 No-answer 兜底
- **Temperature 降低**：减小随机性（temperature=0 最确定性）
- **CoT（Chain of Thought）**：让模型先推理再回答，减少跳跃
- **Self-Consistency**：多次采样取一致性高的答案
- **Faithfulness 验证**：生成后检查答案是否有原文支撑
- **RLHF/RLAIF**：通过人类反馈训练模型拒绝回答不确定内容

#### 36. LLM 为什么推理成本高？
- **参数量巨大**：GPT-4 估计约 1.8 万亿参数，每次前向传播需海量矩阵运算
- **自回归串行生成**：每个 Token 需要完整前向传播，无法并行（只能 batch 并行）
- **KV Cache 内存**：存储每层的 Key-Value 矩阵，长上下文时显存占用爆炸
- **Attention 复杂度**：标准 Attention 是 O(n²)（n 为 Token 数），长序列成本极高
- **GPU 依赖**：需要高端 GPU（A100/H100），硬件成本高

优化手段：量化（INT8/INT4）、FlashAttention、KV Cache 复用、推测解码（Speculative Decoding）。

#### 37. Temperature、Top-p、Top-k 有什么区别？

| 参数 | 含义 | 建议值 |
|------|------|--------|
| **Temperature** | 控制输出随机性。越高越随机发散，越低越确定保守 | 创意任务 0.7-1.0；精确任务 0-0.3 |
| **Top-k** | 每步只从概率最高的 k 个 Token 中采样 | 通常 40-100 |
| **Top-p（Nucleus Sampling）** | 从累积概率达到 p 的最小 Token 集合中采样 | 通常 0.9-0.95 |

实践中：通常 temperature + top-p 联合使用；精确问答用低 temperature（0~0.2），创意写作用高 temperature（0.7~1.0）。

---

### Tool Calling & Prompt

#### 38. 什么是 Tool Calling？
Tool Calling（也称 Function Calling）是 LLM 的能力，允许模型输出**结构化的工具调用请求**，而非纯文本：

```json
{
  "tool": "search_web",
  "arguments": {"query": "2024年北京天气"}
}
```

流程：
1. 将可用工具（工具名、参数描述）写入 System Prompt
2. LLM 判断需要工具时输出 JSON 格式的调用请求
3. 应用层解析并实际执行工具
4. 将执行结果作为 Tool Message 返回给 LLM
5. LLM 基于结果继续生成最终回答

LangChain4j 用 `@Tool` 注解自动处理整个流程。

#### 39. 什么是 Prompt Engineering？
Prompt Engineering 是通过精心设计输入提示来引导 LLM 输出期望结果的技术：

常用技巧：
- **角色设定**：`你是一个专业的 Java 架构师`
- **Few-shot 示例**：提供 2-5 个输入输出示例
- **CoT（思维链）**：`请一步步思考`
- **格式约束**：`用 JSON 格式返回，包含 name 和 score 字段`
- **约束条件**：`只基于以下文档回答，不要使用其他知识`
- **分步拆解**：将复杂任务拆成多个子任务 Prompt

#### 40. ChatGPT 的 system / user / assistant role 有什么作用？
| Role | 作用 | 示例 |
|------|------|------|
| **system** | 设置 AI 的行为规则、角色、约束，整个对话生效 | `你是一个专业客服，只回答产品相关问题` |
| **user** | 用户的输入/提问 | `我的订单什么时候发货？` |
| **assistant** | AI 的历史回复（用于多轮对话上下文） | `您好，请提供订单号...` |

System Message 权重最高，优先级 system > user > assistant。在 RAG 场景中，检索到的文档通常拼入 system 或 user message 中。

#### 41. LangChain4j 如何实现 Tool 调用？
```java
// 1. 定义 Tool
public class WeatherTools {
    @Tool("查询指定城市的天气")
    public String getWeather(@P("城市名") String city) {
        return weatherApi.query(city);
    }
}

// 2. 注册到 AiService
interface AssistantService {
    String chat(String message);
}

AssistantService service = AiServices.builder(AssistantService.class)
    .chatLanguageModel(model)
    .tools(new WeatherTools())  // 注册工具
    .chatMemory(memory)
    .build();

// 3. 调用
service.chat("北京今天天气怎么样？");
// LangChain4j 自动处理 Tool 调用 → 执行 → 结果回填
```

#### 42. LangChain4j 如何返回结构化 JSON？
**方式一：AiService 接口返回 POJO（推荐）**
```java
record ProductInfo(String name, double price, String category) {}

interface ExtractService {
    @UserMessage("从以下文本提取产品信息：{{text}}")
    ProductInfo extract(@V("text") String text);
}
// LangChain4j 自动生成 JSON Schema 并解析返回
```

**方式二：使用 JsonOutputParser**
```java
// 在 Prompt 中要求 JSON 格式 + 显式解析
```

**方式三：OpenAI JSON Mode**
```java
OpenAiChatRequestParameters.builder()
    .responseFormat(ResponseFormat.JSON)
    .build()
```

#### 43. LangChain4j 如何实现 prompt template？
```java
// 方式一：@SystemMessage + @UserMessage 注解
interface TranslateService {
    @SystemMessage("你是一个翻译专家，将文本翻译成{{language}}")
    @UserMessage("请翻译：{{text}}")
    String translate(@V("language") String language, @V("text") String text);
}

// 方式二：PromptTemplate 类
PromptTemplate template = PromptTemplate.from(
    "将以下{{language}}文本翻译成英文：
{{text}}"
);
Prompt prompt = template.apply(Map.of("language", "中文", "text", "你好世界"));
```

#### 44. 如何设计 Prompt 管理系统？
- **版本控制**：Prompt 存数据库，带版本号和 tag（dev/prod），支持回滚
- **模板化**：参数化变量，同一 Prompt 复用于不同场景
- **A/B 测试**：不同版本 Prompt 灰度分流，对比效果
- **热更新**：不重启服务更新 Prompt（数据库/Redis 存储 + 定时刷新）
- **评估绑定**：每个 Prompt 关联评估指标（效果、成本、延迟）
- **审计日志**：记录修改人、时间、改动内容

```java
// 从数据库动态加载 Prompt
String systemPrompt = promptRepository.findByKeyAndVersion("qa_system", "prod");
```

#### 45. 如何评估 Agent 的执行效果？
- **任务完成率**：最终是否完成用户目标（人工标注 or LLM-as-Judge）
- **步骤正确率**：中间工具调用是否合理（对比 golden trace）
- **工具使用效率**：是否有冗余的工具调用、无效循环
- **延迟**：完成任务所需总时间、工具调用次数
- **成本**：消耗 Token 数量
- **幻觉率**：最终答案是否基于事实
- **工具链路追踪**：通过 LangSmith/Phoenix 等平台记录每步推理和工具调用

---

### Java / Spring AI / LangChain4j

#### 46. 什么是 AI Service（LangChain4j）？
AI Service 是 LangChain4j 的核心抽象，通过**Java 接口 + 注解**自动生成 AI 功能实现：

```java
interface CustomerSupportAgent {
    @SystemMessage("你是专业客服...")
    @UserMessage("用户问题：{{question}}")
    String answer(@V("question") String question);
}

// 一行代码注入 LLM + Memory + Tool 能力
CustomerSupportAgent agent = AiServices.builder(CustomerSupportAgent.class)
    .chatLanguageModel(model)
    .chatMemory(memory)
    .tools(tools)
    .build();
```

隐藏了 Prompt 构建、工具调用循环、Memory 管理等底层细节。

#### 47. Spring AI 和 LangChain4j 有什么区别？

| 维度 | Spring AI | LangChain4j |
|------|-----------|-------------|
| 来源 | Spring 官方生态 | 独立开源项目 |
| 集成方式 | Spring Boot Starter，自动配置 | 手动配置，更灵活 |
| 成熟度 | 较新（2023年）| 更成熟，社区活跃 |
| API 风格 | Spring 惯用风格 | 偏 Python LangChain 移植 |
| 功能 | RAG、工具、向量存储 | RAG、工具、Memory、Agent、模板 |
| 适用场景 | Spring Boot 项目快速接入 | 需要精细控制 AI 逻辑 |

#### 48. LangChain4j 和 Python LangChain 有什么区别？

| 维度 | Python LangChain | LangChain4j |
|------|-----------------|-------------|
| 语言 | Python | Java |
| 生态 | 更丰富，模型/工具支持更多 | Java 生态集成好（Spring/MyBatis） |
| 更新频率 | 极快，API 变化频繁 | 相对稳定 |
| 性能 | 解释型，高并发需 async | JVM 高并发天然优势 |
| 企业应用 | 原型/数据科学领域 | 生产级 Java 后端服务 |
| Agent | LangGraph 功能强大 | AiServices 更简洁 |

#### 49. 如何在 Spring Boot 中集成 LangChain4j？
```xml
<!-- pom.xml -->
<dependency>
    <groupId>dev.langchain4j</groupId>
    <artifactId>langchain4j-open-ai-spring-boot-starter</artifactId>
    <version>0.35.0</version>
</dependency>
```

```yaml
# application.yml
langchain4j:
  open-ai:
    chat-model:
      api-key: ${OPENAI_API_KEY}
      model-name: gpt-4o
      temperature: 0.3
```

```java
@Service
public class ChatService {
    @Autowired
    private ChatLanguageModel chatModel;  // 自动注入
    
    public String chat(String message) {
        return chatModel.generate(message);
    }
}
```

#### 50. Java 如何实现 streaming response？
```java
// LangChain4j StreamingChatLanguageModel
StreamingChatLanguageModel model = OpenAiStreamingChatLanguageModel.builder()
    .apiKey(API_KEY)
    .modelName("gpt-4o")
    .build();

// Spring MVC SSE Streaming
@GetMapping(value = "/chat/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter streamChat(@RequestParam String message) {
    SseEmitter emitter = new SseEmitter(60_000L);
    
    model.generate(message, new StreamingResponseHandler<AiMessage>() {
        @Override
        public void onNext(String token) {
            try {
                emitter.send(SseEmitter.event().data(token));
            } catch (IOException e) {
                emitter.completeWithError(e);
            }
        }
        @Override
        public void onComplete(Response<AiMessage> response) {
            emitter.complete();
        }
        @Override
        public void onError(Throwable error) {
            emitter.completeWithError(error);
        }
    });
    return emitter;
}
```

#### 51. Java 调用 OpenAI API 如何设计 SDK？
关键设计点：
- **HTTP 客户端**：OkHttp 或 Retrofit，支持同步/异步/流式
- **重试机制**：指数退避重试（429 Rate Limit、5xx 错误）
- **超时配置**：connectTimeout / readTimeout，流式需要更长 readTimeout
- **认证**：API Key 通过 Header `Authorization: Bearer xxx` 传递
- **请求/响应 POJO**：对应 OpenAI API 格式序列化/反序列化（Jackson/Gson）
- **流式解析**：SSE 格式，逐行解析 `data: {...}` JSON
- **错误处理**：按 HTTP Status 和 error code 分类异常

```java
// 基于 OkHttp 的简化实现
OkHttpClient client = new OkHttpClient.Builder()
    .addInterceptor(new AuthInterceptor(apiKey))
    .addInterceptor(new RetryInterceptor(maxRetries=3))
    .readTimeout(60, SECONDS)
    .build();
```

#### 52. Java LLM 服务如何做连接池管理？
```java
// OkHttp 连接池配置
ConnectionPool pool = new ConnectionPool(
    maxIdleConnections=20,  // 最大空闲连接数
    keepAliveDuration=5,    // 分钟
    TimeUnit.MINUTES
);

OkHttpClient client = new OkHttpClient.Builder()
    .connectionPool(pool)
    .connectTimeout(10, SECONDS)
    .readTimeout(120, SECONDS)  // LLM 推理需要更长时间
    .writeTimeout(10, SECONDS)
    .build();
```

注意事项：
- LLM API 调用延迟高（数秒），需配置足够的 readTimeout
- 流式响应不会释放连接，需控制并发流式请求数量
- 对不同模型/API 使用独立连接池（避免互相影响）
- 监控连接池使用率，超 80% 需扩容

---

### 工程化 & 可观测性

#### 53. 如何实现 SSE 推送？
```java
// Spring Boot SSE 实现
@RestController
public class SseController {
    
    @GetMapping(value = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter stream() {
        SseEmitter emitter = new SseEmitter(Long.MAX_VALUE);
        
        executorService.submit(() -> {
            try {
                for (String chunk : generateChunks()) {
                    emitter.send(SseEmitter.event()
                        .id(UUID.randomUUID().toString())
                        .name("message")
                        .data(chunk));
                    Thread.sleep(50);
                }
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });
        return emitter;
    }
}
```

前端用 `EventSource` 接收：`const es = new EventSource('/events'); es.onmessage = e => console.log(e.data);`

#### 54. streaming response 如何实现？
- **服务端**：使用 `StreamingChatLanguageModel`，通过 `StreamingResponseHandler` 回调逐 token 处理
- **传输协议**：SSE（Server-Sent Events）—— HTTP 长连接，服务端推送；或 WebSocket 双向通信
- **响应头**：`Content-Type: text/event-stream; Cache-Control: no-cache`
- **前端**：`EventSource` API 接收 SSE；React/Vue 监听事件更新 UI
- **中断处理**：客户端断开时服务端需感知并停止生成（监听 `emitter.onCompletion`）

#### 55. LLM 服务如何做缓存？
**精确缓存：** 相同 Prompt hash → Redis 缓存结果，TTL 按业务设置（适合固定模板问题）

**语义缓存：** 相似问题命中缓存（更智能）：
```
1. Query → Embedding 向量
2. 在缓存向量库中搜索相似问题（相似度 > 0.95）
3. 命中 → 返回缓存答案
4. 未命中 → 调用 LLM → 将 (向量, 答案) 存入缓存
```

**KV Cache 复用（Prompt Cache）：** OpenAI / Claude 支持对相同前缀 Prompt 的 KV Cache 复用，减少 Token 计算量（成本↓50%+）。

适用场景：FAQ 问答缓存、固定 System Prompt 缓存。

#### 56. LLM 服务如何做限流？
```java
// 基于 Guava RateLimiter 令牌桶
@Component
public class LlmRateLimiter {
    // 每秒最多 10 次请求
    private final RateLimiter rateLimiter = RateLimiter.create(10.0);
    
    public void acquire() {
        if (!rateLimiter.tryAcquire(100, TimeUnit.MILLISECONDS)) {
            throw new RateLimitException("请求过于频繁，请稍后重试");
        }
    }
}

// 多维度限流：用户级、API Key 级、全局级
// Resilience4j RateLimiter 支持更细粒度控制
```

**限流维度：**
- **用户级**：每用户每分钟 N 次
- **Token 级**：每用户每天 N 个 Token
- **全局级**：保护 LLM API Key 不超 Rate Limit

#### 57. LLM 服务如何做降级？
```java
// Resilience4j CircuitBreaker + Fallback
@CircuitBreaker(name = "llm-service", fallbackMethod = "fallbackResponse")
public String callLLM(String prompt) {
    return primaryLlmClient.generate(prompt);
}

// 降级策略
public String fallbackResponse(String prompt, Exception e) {
    // 策略1：切换到备用模型
    return backupLlmClient.generate(prompt);
    // 策略2：返回缓存答案
    // 策略3：返回预置兜底文案
}
```

降级触发条件：响应超时、错误率超阈值、服务不可用。降级链路：主模型 → 备用模型 → 缓存 → 兜底文案。

#### 58. 如何做模型 fallback？
```java
public class FallbackLlmService {
    private final List<ChatLanguageModel> models = List.of(
        gpt4oModel,       // 主模型
        claudeModel,      // 备用模型1
        qwenModel         // 备用模型2（本地/低成本）
    );
    
    public String generate(String prompt) {
        for (ChatLanguageModel model : models) {
            try {
                return model.generate(prompt);
            } catch (Exception e) {
                log.warn("Model {} failed: {}", model.getClass().getSimpleName(), e.getMessage());
            }
        }
        throw new AllModelsFailedException("所有模型均不可用");
    }
}
```

触发条件：API 超时、Rate Limit（429）、服务不可用（5xx）、账单不足（402）。

#### 59. 多模型调度如何实现？
策略：
- **按任务类型路由**：代码生成 → GPT-4、简单 FAQ → GPT-3.5（成本优化）
- **按成本路由**：优先低成本模型，复杂任务升级到高成本模型
- **负载均衡**：多个相同模型实例 Round-Robin
- **A/B 测试路由**：按用户 ID hash 分流不同模型

```java
public ChatLanguageModel route(TaskContext ctx) {
    if (ctx.isCodeTask()) return codexModel;
    if (ctx.estimatedTokens() > 10000) return longContextModel;
    if (ctx.isSimpleQa()) return cheapModel;
    return defaultModel;
}
```

#### 60. LLM 如何实现多租户？
- **API Key 隔离**：每个租户使用独立的 LLM API Key，实现成本和配额隔离
- **Prompt 隔离**：租户级 System Prompt（品牌、知识库、权限）
- **知识库隔离**：向量数据库按 tenant_id 过滤，每个租户只检索自己的文档
- **配额管理**：数据库记录每租户的 Token 用量，超配额降级或拒绝
- **数据安全**：租户数据加密存储，禁止跨租户数据访问

```java
// 向量检索时注入租户过滤
Filter tenantFilter = MetadataFilter.equal("tenant_id", currentTenantId);
vectorStore.search(query, topK, tenantFilter);
```

#### 61. LLM API 如何设计接口？
```java
// RESTful Chat API 设计
@PostMapping("/api/v1/chat/completions")
public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request,
                                          @RequestHeader("Authorization") String auth) {
    // 认证、限流、参数校验
}

// 推荐遵循 OpenAI 接口规范（兼容性好）
// ChatRequest: { model, messages[], temperature, max_tokens, stream }
// ChatResponse: { id, choices[{ message, finish_reason }], usage{prompt_tokens, completion_tokens} }
```

**设计原则：**
- 遵循 OpenAI 兼容接口（生态工具可直接复用）
- 支持 streaming（SSE）和 非 streaming 两种模式
- 统一错误码规范（4xx 客户端错误，5xx 服务端错误）
- 在 Response 中返回 Token 用量

#### 62. LLM latency 如何优化？
| 优化手段 | 效果 |
|---------|------|
| **流式返回（Streaming）** | 用户感知首 token 时间大幅降低 |
| **模型选择** | GPT-4o-mini vs GPT-4，延迟差 3-5 倍 |
| **Prompt 压缩** | 减少输入 Token，降低 TTFT（Time To First Token） |
| **KV Cache 复用** | 相同前缀 Prompt 复用，减少计算 |
| **就近部署** | 选择距离用户最近的 API Region |
| **并行工具调用** | 多个工具并行执行，非串行 |
| **语义缓存** | 相似问题直接命中缓存，零 LLM 延迟 |

#### 63. MCP（Model Context Protocol）是什么？
MCP 是 Anthropic 2024年提出的**标准化 AI 与外部工具/数据源交互协议**：

```
[LLM / AI Agent]
       ↕ MCP Protocol (JSON-RPC 2.0)
[MCP Server]
  ├─ 数据库查询工具
  ├─ 文件系统访问
  ├─ 外部 API 调用
  └─ 代码执行环境
```

核心概念：
- **Resources**：暴露数据（文件、DB 记录）
- **Tools**：暴露可执行功能
- **Prompts**：预定义 Prompt 模板

意义：统一工具接入标准，MCP Server 可被任何兼容 MCP 的 AI 客户端复用，避免重复开发。

#### 64. AI系统如何记录 Prompt 和 Response？
```java
// AOP 方式统一记录
@Aspect
@Component
public class LlmAuditAspect {
    
    @Around("execution(* dev.langchain4j..ChatLanguageModel.generate(..))")
    public Object auditLlmCall(ProceedingJoinPoint pjp) throws Throwable {
        LlmAuditLog log = new LlmAuditLog();
        log.setUserId(SecurityContext.getCurrentUser());
        log.setPrompt(extractPrompt(pjp.getArgs()));
        log.setStartTime(Instant.now());
        
        Object result = pjp.proceed();
        
        log.setResponse(result.toString());
        log.setDuration(Duration.between(log.getStartTime(), Instant.now()));
        log.setTokenUsage(extractTokenUsage(result));
        auditLogRepository.save(log);
        
        return result;
    }
}
```

存储：结构化日志 → Elasticsearch / ClickHouse（便于查询分析）。

#### 65. AI系统如何做监控？
**指标维度：**
- **可用性**：LLM API 成功率、错误率
- **延迟**：P50/P95/P99 响应时间、TTFT（首 Token 时间）
- **吞吐量**：每秒请求数（RPS）
- **成本**：Token 消耗速率、每请求成本
- **业务指标**：用户满意度、任务完成率

**技术方案：**
```
应用层 → Prometheus 埋点 → Grafana 大盘
       → ELK 日志 → 异常告警（Slack/钉钉）
       → LangSmith / Phoenix（专用 LLM 追踪）
```

LangChain4j 集成 Micrometer 可自动上报延迟、Token 使用指标。

#### 66. AI系统如何做成本控制？
- **模型选型**：按任务复杂度选择模型（简单任务用 GPT-4o-mini，复杂用 GPT-4o）
- **Prompt 优化**：压缩 System Prompt、减少冗余上下文
- **缓存**：语义缓存高频相似问题（命中率 30%+ 可节省大量 Token）
- **Prompt Cache**：利用 Claude/OpenAI 的前缀缓存特性（长 System Prompt 只计算一次）
- **Token 预算**：设置 max_tokens 上限，防止超长回复
- **用量监控**：实时监控各 UserId/TenantId 的 Token 消耗，设置预算告警
- **量化模型**：自部署场景使用 INT4/INT8 量化模型

#### 67. AI系统如何做权限控制？
```java
// 多层权限控制
@PreAuthorize("hasRole('AI_USER') and @tokenBudgetService.hasBalance(authentication.name)")
@PostMapping("/chat")
public ChatResponse chat(@RequestBody ChatRequest req, Authentication auth) {
    // 1. 认证：JWT Token 验证
    // 2. 授权：角色检查（RBAC）
    // 3. 配额：Token 余额检查
    // 4. 数据权限：租户隔离，只能访问自己的知识库
    // 5. 内容安全：输入/输出内容审核（敏感词、违规检测）
    return chatService.chat(req, auth.getName());
}
```

关键控制点：API 认证（JWT/OAuth2）、功能权限（RBAC）、数据权限（租户隔离）、配额管理、内容审核。

#### 68. 如何统计 token usage？
```java
// LangChain4j 通过 TokenUsage 获取
Response<AiMessage> response = model.generate(messages);
TokenUsage usage = response.tokenUsage();

// 记录到数据库
TokenUsageRecord record = new TokenUsageRecord();
record.setUserId(userId);
record.setModel(modelName);
record.setInputTokens(usage.inputTokenCount());
record.setOutputTokens(usage.outputTokenCount());
record.setTotalTokens(usage.totalTokenCount());
record.setCost(calculateCost(usage, modelName));
record.setTimestamp(Instant.now());
tokenUsageRepository.save(record);
```

汇总分析：按用户/时间/模型维度聚合，ClickHouse 适合大规模 Token 用量 OLAP 分析。

#### 69. 如何设计 AI evaluation pipeline？
**评估架构：**
```
测试数据集（问题+标准答案）
        ↓
AI 系统批量推理
        ↓
评估指标计算：
  ├─ 自动指标：BLEU, ROUGE, Exact Match
  ├─ LLM-as-Judge：用 GPT-4 对答案打分（相关性/准确性/完整性）
  └─ 专项指标：RAG Faithfulness, Tool Calling 准确率
        ↓
结果持久化 + 趋势对比（新版本 vs 旧版本）
        ↓
回归告警：关键指标下降超阈值则阻断发布
```

工具推荐：**RAGAS**（RAG 评估）、**DeepEval**（通用 LLM 评估）、**LangSmith**（追踪+评估一体）。

#### 70. 如何做 A/B test 比较不同模型？
```java
// 基于用户 ID hash 分流
public ChatLanguageModel selectModel(String userId) {
    int bucket = Math.abs(userId.hashCode()) % 100;
    if (bucket < 50) {
        return modelA;  // GPT-4o，控制组
    } else {
        return modelB;  // Claude-3.5，实验组
    }
}
```

**关键设计：**
- **分流策略**：用户 ID hash（同用户体验一致）或随机分流
- **指标采集**：记录每次请求的模型版本、延迟、Token 数、用户反馈（点赞/踩）
- **统计显著性**：样本量足够（通常数千次）后用 t-test 判断差异是否显著
- **灰度控制**：从 5% 流量开始，逐步扩大，监控异常指标
- **实验隔离**：同一用户在实验期间保持同一组（避免体验割裂）
