---
title: RAG
date: 2026-04-12 15:15:51
tags: []
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-04-13 00:31
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

**Sparse recall:**
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

**Fusion:**

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

## Eveluation

```
我先补两项你需要的内容：一是适配你当前 Ubuntu 24.04 的 `nvidia-container-toolkit` 安装命令，二是安装完成后的逐步验证链路。

Ran terminal command:  source /etc/os-release && printf 'ID=%s\nVERSION_ID=%s\n' "$ID" "$VERSION_ID" && printf '\n' && (systemctl is-active docker || true)

Ran terminal command:  cd /mnt/f/work/code/dawn-ai && docker compose -f docker-compose.yml -f docker-compose.gpu.yml config | sed -n '1,120p'

我已经确认你的系统是 Ubuntu 24.04，`systemd` 管理 Docker 也正常，所以可以直接按原生 Docker Engine 的方式安装 `nvidia-container-toolkit`，然后再验证 `bge-m3` 的 GPU 启动链路。

Ran terminal command:  cd /mnt/f/work/code/dawn-ai && printf 'ready-for-user-steps\n'

已整理出适配你当前环境的安装与验证步骤：先给 `nvidia-container-toolkit` 的命令，再给 GPU 容器和 `bge-m3` 服务的验证命令。

Inserted into memory file [](file:///root/.vscode-server/data/User/workspaceStorage/551e815fccfbaf9609d2288cfd090274/GitHub.copilot-chat/memory-tool/memories/repo/dawn-ai-notes.md)

按你当前环境，直接做这两步就行。

**2. 安装 `nvidia-container-toolkit`**
你现在是 Ubuntu 24.04，Docker 由 `systemd` 管理，这套命令可以直接用：

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
  | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -fsSL https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
  | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
  | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list > /dev/null

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

装完先做基础验证：

```bash
nvidia-ctk --version
docker info | sed -n '/Runtimes/,+8p'
docker run --rm --gpus all nvidia/cuda:12.6.3-base-ubuntu22.04 nvidia-smi
```

你要看到两件事才算通了：
- `nvidia-ctk` 不再报 `command not found`
- `docker run --gpus all ... nvidia-smi` 能在容器里打印显卡信息

如果这一步还不通，先不要启动项目里的 GPU compose，因为 `gpus: all` 还是会失败。

**3. 验证 GPU 容器和 `bge-m3`**
基础 GPU runtime 通了以后，再启动你项目里的 GPU 版 embedding：

```bash
cd /mnt/f/work/code/dawn-ai
docker compose down embedding app
docker compose -f docker-compose.yml -f docker-compose.gpu.yml up -d --force-recreate embedding app
```

先看服务状态：

```bash
docker compose ps
```

再看 embedding 日志，确认模型开始加载：

```bash
docker compose logs -f embedding
```

正常情况下你应该能看到 `BAAI/bge-m3` 下载或加载相关日志，而不是立刻退出。

然后测一下容器是不是已经能提供 embeddings 接口。等日志里显示服务 ready 后执行：

```bash
curl -s http://localhost:7997/docs | head
```

如果能返回 Swagger HTML，说明 Infinity HTTP 服务已经起来了。

再做一个实际 embedding 请求测试：

```bash
curl -s http://localhost:7997/v1/embeddings \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "BAAI/bge-m3",
    "input": "退款政策是什么？"
  }'
```

如果成功，返回里会有 embedding 向量数据。接着再看应用日志，确认 Spring Boot 连到了本地 embedding 服务：

```bash
docker compose logs --tail=100 app
```

你这个项目现在已经拆成了独立 embedding 地址配置，所以 GPU 版真正生效时，应用会继续走云端 chat，同时走本地 `bge-m3` embeddings。相关入口分别在 docker-compose.yml、docker-compose.gpu.yml 和 application.yml。

如果你执行完安装命令后，我可以继续帮你做两件事：
1. 帮你判断 `nvidia-container-toolkit` 是否已经装成功
2. 带你逐条检查 `embedding` 容器日志，确认 `bge-m3` 是否真的跑在 GPU 上
```