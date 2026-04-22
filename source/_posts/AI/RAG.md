---
title: RAG
date: 2026-04-12 15:15:51
tags: []
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-04-21 23:30
---
Retrieval Argument Generation - 检索增强生成

## Embedding

Chunking:
- 语义切分
- 段落切分
- ...

## Retrieval

### 混合检索 (Sparse/BM25 + Dense)

> [!important]
> Dense retrieval 向量检索依赖 embedding，擅长做**语义相近**查询，但遇到这些场景会吃亏：
> - 专有名词
> - 精确术语
> - 编号、关键词
> - 用户 query 很短，只有1-3个 token 左右
> 
> 因此需要搭配 lexical/sparse 通道，做混合检索。

- Dense recall:   把 query 和文档都编码成**稠密向量（dense vector）**，再用向量相似度做召回；
- Sparse recall:  **BM25 属于 Sparse recall**，因为它依赖的是**词项空间里的稀疏表示**，大多数维度都是 0，只在出现过的词上有权重。
- Fusion: dense 和 sparse 结果融合，由于其检索的体系不同（dense 依赖 cosine similarity, sparse 依赖 bm25或 pgvector 的 ts_rank_td）, 依赖 fusion 算法进行融合。

#### 项目实践

##### Sparse recall
> PostgreSQL 做向量库，FTS 做匹配

```sql
SELECT id, content, metadata
FROM vector_store
WHERE to_tsvector('simple', content) @@ websearch_to_tsquery('simple', ?)
ORDER BY ts_rank_cd(
    to_tsvector('simple', content),
    websearch_to_tsquery('simple', ?)
) DESC
LIMIT ?
```

- `to_tsvector('simple', content)`：把正文转成检索向量
- `websearch_to_tsquery('simple', ?)`：把用户 query 转成 tsquery
- `@@`：判断是否命中
- `simple` 配置意味着它不做太激进的词形还原，比较偏“原词匹配”。
- **`ts_rank_cd` 排序** : 这一步不是严格意义的 BM25，而是 PostgreSQL 自己的 ranking 函数.这是个工程上可接受的近似实现，但不是学术定义 BM25。

###### 详细解析 
**`to_tsvector('simple', content)`**  
将文档转为词位（lexeme）集合。`'simple'` 词典意味着：

- 只做小写化（lowercase）
- **不做词干提取（stemming）**，不做停用词过滤
- `"Running Docker containers"` → `{'running', 'docker', 'containers'}`

**`websearch_to_tsquery('simple', query)`**  
将查询解析为布尔匹配表达式，支持 `AND` / `OR` / `NOT` /短语：

- `"GPU docker"` → `'gpu' & 'docker'`（隐式 AND）
- `"docker OR kubernetes"` → `'docker' | 'kubernetes'`
- `"\"vector search\""` → `'vector' <-> 'search'`（相邻匹配）

**`ts_rank_cd`**  
基于词频和文档覆盖度（cover density）打分，是 PostgreSQL 内置的近似 BM25 排名函数。

---
是否属于"原词匹配"？

**是，但有一步预处理**：用的是 `'simple'` 词典，只做小写化，不做词干提取。

|场景|结果|
|---|---|
|query= `"Docker"`, doc 含 `"docker"` |✅ 匹配（大小写不敏感）|
|query= `"running"`, doc 含 `"run"` |❌ 不匹配（`simple` 不做词干还原）|
|query= `"GPU containers"`, doc 含两词|✅ 匹配（AND 语义）|
|query= `"如何语义搜索"`, doc 为英文|❌ 不匹配（中文词无法被 simple 正确分词）|

`'simple'` 是刻意选择，避免英文词干提取干扰中英混合场景，但代价是英文词形变化（run/running/ran）无法召回。

###### TODO

与真正 BM25 的差异

|特性|当前实现 (ts_rank_cd)|真正 BM25|
|---|---|---|
|词频归一化|部分（cover density）|完整（文档长度归一化）|
|IDF 加权|无|有（罕见词权重更高）|
|词干提取|不做（`simple`）|取决于分析器配置|
|中文支持|❌ 需要 zhparser 扩展|需要中文分词器|

如果要升级到真正的 BM25，可以引入 **`pg_bm25`（ParadeDB）** 扩展，或者在 Infinity 服务上启用 SPLADE 稀疏向量来替代传统关键词召回。

##### Fusion

项目实践中的fusion 不用 dense 和 sparse recall 中的分数，而是名词。
核心公式: 属于经典的 RRF 思路

```
private static final int RANK_CONSTANT = 60;

additionalScore = 1.0 / (RANK_CONSTANT + index + 1)
```

> [!NOTE]
> 互惠排名融合（RRF）排名器是 Milvus 混合搜索的一种重新排名策略，它根据多个向量搜索路径的排名位置而不是原始相似度得分来平衡搜索结果。就像体育比赛考虑的是球员的排名而不是个人统计数据一样，RRF Ranker 根据每个项目在不同搜索路径中的排名高低来组合搜索结果，从而创建一个公平、均衡的最终排名。
> 

这里的 `RANK_CONSTANT = 60`，作用是**平滑名次差异**，避免第一名把后面全碾压。

假设：
- dense: A, B
- sparse: B, C
那么：
- A 只在 dense 出现，加一次分
- C 只在 sparse 出现，加一次分
- B 在两边都出现，加两次分
所以 **B 会被推到前面**。
这就是 hybrid retrieval 里最常见、最稳的融合方式之一。

优点
- 不依赖不同检索器的原始 score 尺度
- 工程实现简单稳定
- 对 hybrid 场景很通用
局限
- 只看 rank，不看具体分差
- dense 第 1 和第 2 的差距再大，也只体现为 rank 差 1
- 如果其中一条召回链质量很差，也会“平等投票”

### metadata 检索

SpringAI 的 pgvector 的 DDL schema 创建的 table，会生成 content + metadata 字段，依据该字段，做 metadata 过滤，提升检索效率和准确度
```sql


CREATE TABLE vector_store(

    id uuid NOT NULL DEFAULT uuid_generate_v4(),

    content text,

    metadata json,

    embedding vector,

    PRIMARY KEY(id)

);

CREATE INDEX spring_ai_vector_index ON public.vector_store USING hnsw (embedding vector_cosine_ops);
```

### rerank 重排序

- 为什么要 rerank, RRF 融合解决的是“多路召回怎么合并”，但融合后结果仍然比较粗。
- 对这个具体 query，哪个候选更值得排前面？

#### LLM rerank - crossEncoder

#### 规则 rerank

项目中使用的是规则 rerank，而非 LLM rerank，打分公式：

```java
phraseBoost + (lexicalCoverage * 3.0) + metadataBoost + originalRankBoost
```

`phraseBoost`: 
如果文档里直接包含完整 query phrase，额外加 2 分。这会显著偏向“精确短语命中”的文档。
```java
documentText.contains(request.getQuery().toLowerCase(Locale.ROOT)) ? 2.0 : 0.0
```

好处：
- 对 FAQ、术语、标题命中特别有效
坏处：
- 对自然语言长 query 偏弱
- `contains` 很粗糙，不懂边界、不懂词序变体

`lexicalCoverage`: 表示 query token 有多少被文档 token 命中。

```java
matchedTokens / queryTokens.size ()
```

`metadataBoost`: 如果请求本身带 metadata 条件，而文档 metadata 也匹配，就给额外加分。
`orginalRnakBoost`: 保留一个“原始排序先验”。也就是说 rerank 不是完全推翻上一阶段，而是让上一阶段排名继续有影响。

## Evaluation

- Recall：关注找的全不全
- MRR: 关注第一个结果准不准
- NDCG：关注整体排序是否理想

| **指标**       | **含义**                                                                                                               | **关注点** | **排序敏感度**        | **典型应用**           |
| ------------ | -------------------------------------------------------------------------------------------------------------------- | ------- | ---------------- | ------------------ |
| **Recall@K** | (召回率)，在返回的前 $K$ 个结果中，包含的相关文档数量占系统中所有相关文档总数的比例。                                                                       | 查全率     | 低（只要进了 Top-K 即可） | 向量检索、粗排阶段          |
| **MRR@K**    | (Mean Reciprocal Rank, 平均倒数排名)，衡量算法将“第一个相关结果”排在多靠前的位置。它是所有查询请求中，第一个相关结果排名倒数的平均值。                                     | 首个结果的位置 | 极高（只看第一个相关的）     | 智能客服、Fact-checking |
| **NDCG@K**   | (Normalized Discounted Cumulative Gain, 归一化折损增益)，一种综合考虑了“结果相关性得分”和“排名顺序”的指标。它通过将实际搜索结果的得分（DCG）除以理想状态下的最高得分（IDCG）来计算。 | 整体排序质量  | 高（按相关度阶梯式衰减）     | 推荐系统、精排模型          |
﻿ 项目里的 RAG 评估机制目前主要分三层：

1. 离线检索评估：核心是 RetrievalEvaluator，基于标注数据集 retrieval-eval-dataset.json 计算
  Recall@K、MRR@K、NDCG@K，用于比较 dense / hybrid 等检索策略优劣。
2. 组件级验证：通过
  RetrievalRouterTest、HeuristicRetrievalRerankerTest、CrossEncoderRetrievalRerankerTest、KnowledgeSearchToolTest
  等，分别验证路由、rerank、query rewrite、dedup、metadata filter 等关键环节是否按预期工作。
3. 线上观测指标：通过 Micrometer 暴露
  ai.rag.retrieval.total、ai.rag.retrieval.filtered_count、ai.rag.calls_per_session、ai.rag.dedup.skipped
  等指标，持续观察召回是否有效、是否有噪音、是否存在重复检索。

  结论上，这个项目当前评估的重点是 retrieval quality，也就是“能不能找对、排对文档”；还没有形成完整的 answer-level RAG 
  评估，例如 Faithfulness、Answer
  Relevance、Ragas 或 LLM-as-a-judge 这一层。

## TODO

- [ ] 多路归并：使用 completableFuture 来做并发重构，提升性能 - 将 BM25检索和向量加密锁改为并发执行
- [ ] 超时熔断设计：利用 Java 9+ 的 .completeOnTimeout() API 为外部 Rerank 模型调用加上严格的 SLA 限制（例如 800ms）。
- [ ] 降级链路实现：使用 .exceptionally() 编写优雅的 Fallback 逻辑。当 Rerank 失败或 LLM API 阻滞时，能够自动返回未重排的原始召回结果或降级话术

## 参考

### Infinity

一款**高性能、低延迟的开源推理引擎**，专门用于部署文本向量化（Text-Embeddings）、重排序（Reranking）、视觉向量化（CLIP/ColPali）等模型。是目前 RAG（检索增强生成）架构中非常流行的后端组件，其主要优势包括：
- **高性能吞吐**：采用动态批处理（Dynamic Batching）技术，能够像 NVIDIA 的 `text-embeddings-inference` (TEI) 一样高效地榨干 GPU 性能。
- **多框架支持**：后端支持 PyTorch、ONNX (Optimum) 和 CTranslate2，可在 NVIDIA GPU、AMD ROCm、Apple Silicon (MPS) 和 CPU 上运行。
- **兼容 OpenAI API**：对外提供 REST API，接口格式完全兼容 OpenAI，可以无缝集成到 LangChain、LlamaIndex 或你的自定义 RAG 流动中。
- **模型广泛**：支持 HuggingFace 上几乎所有的 Sentence-Transformers 模型。