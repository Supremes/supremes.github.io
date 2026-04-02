---
title: dawn-ai
date: 2026-04-01 22:57:03
tags: []
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-04-02 23:53
---
## **Propmt Engineering**
- Output Structure：限制LLM 的输出结果符合结构化的格式，适应非概率型的业务场景

## **ReAct**
- max-steps: 单次对话 tool 最多调用次数，避免 LLM <-> AGENT 陷入死循环
- plan-and-resovle: 
- llm params optimization:
	- temperature
	- ...

## **RAG**
- Query 重写
- Agentic RAG (LLM 驱动), Max-rag-calls (每次请求，RAG 工具最多调用次数)
- Embedding、Chunk、Overlap
- 召回率
- HYDE - Hypothetical Document Embeddings

## **向量检索算法**
- IVF (Inverted File System) - 缩小搜索范围
- PQ (Product Quantization) - 压缩向量体积
- HNSW (Hierarchical navigable small world) - 分层可导航小世界算法
- HNSW_PQ / HNSW_SQ
- DiskANN (Vamana 图)

## **Memory Management**
- 核心记忆 - 用户画像、核心指令等信息，每次都会携带在 System Prompt 里
- 短期记忆 - 对话历史
	> - **存储内容**：当前 Session（会话）中最近发生的 N 轮对话历史。
	> - **管理策略与痛点**： 随着对话进行，Token 会迅速逼近大模型的上限（同时导致 KV Cache 暴增，拖慢生成速度）。必须引入**截断与压缩机制**：
	>     - **Sliding Window (滑动窗口)**：最粗暴的方法，只保留最近的 N 条消息（如 LangChain4j 中的 `MessageWindowChatMemory`）。
	>     - **Token Bounding (Token 限制)**：实时计算历史记录的 Token 数，超过阈值（如 4000 tokens）就丢弃最老的记录。
	>     - **Summary Buffer (摘要缓冲)**：当对话达到一定长度时，触发一个后台的小模型或低成本 API（如 Gemini Flash），将旧的对话“浓缩”成一段简短的摘要（Summary），然后替换掉原有的完整对话。
	> - **技术选型**：通常存在后端内存中，或者为了分布式无状态化，存储在 Redis 中（如 `RedisChatMemoryStore`）。
- 长期记忆 - 向量数据库
- 记忆流转与管理
	- **记忆固化 (Consolidation)** 类似于人类的“睡眠”。当用户离线或当前 Task 结束后，后台调度任务（如使用 Spring 的 `@Async` 或定时任务）会对短期记忆进行盘点。提取关键信息、生成摘要、调用 Embedding API，然后持久化到长期记忆（向量/图数据库）中，最后清空或截断 Redis 中的短期记忆。
	- **记忆反思 (Reflection)** 借鉴斯坦福 Generative Agents 论文：当 Agent 积累了足够多的散碎情景记忆后，系统会主动触发 LLM 进行“高维思考”。
	    - _底层数据_：“用户昨天问了多线程，今天问了 JUC，刚才问了线程池”。
	    - _反思生成_：“用户是一个关注高并发和底层原理的后端开发”。
	    - 这个反思结果会被提升（Promote）到核心工作记忆或作为高权重的长期记忆。
	- **遗忘机制 (Decay / Eviction)** 并不是所有检索出来的长期记忆都有价值。在进行向量检索时，工业界通常不仅看“相似度得分”，还会结合以下公式进行 Rerank（重排序）：
	    - `最终相关性 = 向量相似度权重 * a + 时间衰减权重 * b + 重要性评分权重 * c`
	    - 这意味着：越近发生的事、以及被 LLM 判定为越“重要”的事（比如用户的医疗过敏史 vs 用户昨天中午吃了什么），越容易被回忆起来。

## **Reflection**

## **Agent 评估系统**
