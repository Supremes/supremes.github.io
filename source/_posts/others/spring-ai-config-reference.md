---
updated: 2026-03-19 21:36
---
# Spring AI 完整配置项参考

> 基于 Spring AI 1.1.2，聚焦 OpenAI + PGVector 组合
> 整理日期：2026-03-19

https://docs.spring.io/spring-ai/reference/index.html
---

## 一、通用连接配置（`spring.ai.openai.*`）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `spring.ai.openai.api-key` | OpenAI API Key | - |
| `spring.ai.openai.base-url` | API 地址 | `https://api.openai.com` |
| `spring.ai.openai.organization-id` | 组织 ID | - |
| `spring.ai.openai.project-id` | 项目 ID | - |

---

## 二、Chat 模型配置（`spring.ai.openai.chat.*`）

### 模型启用

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `spring.ai.model.chat` | 启用 Chat 模型（设为 `none` 禁用） | `openai` |
| `spring.ai.openai.chat.base-url` | Chat 专用地址（覆盖通用） | - |
| `spring.ai.openai.chat.api-key` | Chat 专用 Key（覆盖通用） | - |
| `spring.ai.openai.chat.completions-path` | 请求路径 | `/v1/chat/completions` |
| `spring.ai.openai.chat.organization-id` | 组织 ID | - |
| `spring.ai.openai.chat.project-id` | 项目 ID | - |

### 模型选项（`spring.ai.openai.chat.options.*`）

| 配置项                                       | 说明                                           | 默认值             |
| ----------------------------------------- | -------------------------------------------- | --------------- |
| `options.model`                           | 模型名，如 `gpt-4o`、`gpt-4-turbo`、`gpt-3.5-turbo` | `gpt-4o-mini`   |
| `options.temperature`                     | 温度（0~2，越高越随机）                                | `0.8`           |
| `options.topP`                            | 核采样（与 temperature 二选一）                       | -               |
| `options.maxTokens`                       | 最大输出 token（**非推理模型**用）                       | -               |
| `options.maxCompletionTokens`             | 最大完成 token（**推理模型**用，如 o1/o3）                | -               |
| `options.n`                               | 每次生成多少候选回答                                   | `1`             |
| `options.frequencyPenalty`                | 频率惩罚（-2.0~2.0）                               | `0.0`           |
| `options.presencePenalty`                 | 存在惩罚（-2.0~2.0）                               | -               |
| `options.stop`                            | 最多 4 个停止序列                                   | -               |
| `options.seed`                            | 随机种子（确定性输出，Beta）                             | -               |
| `options.logitBias`                       | 调整特定 token 出现概率                              | -               |
| `options.store`                           | 是否存储请求结果                                     | `false`         |
| `options.metadata`                        | 自定义过滤标签                                      | `{}`            |
| `options.user`                            | 终端用户标识（监控滥用用）                                | -               |
| `options.prompt-cache-key`                | 缓存 Key，降低延迟和费用                               | -               |
| `options.safety-identifier`               | 安全追踪标识（哈希值）                                  | -               |
| `options.stream-usage`                    | 流式时附加 token 用量统计                             | `false`         |
| `options.parallel-tool-calls`             | 是否允许并行 Function Calling                      | `true`          |
| `options.tools`                           | 可调用的工具列表                                     | -               |
| `options.toolChoice`                      | 工具调用策略（`none`/`auto`/指定函数）                   | -               |
| `options.tool-names`                      | 按名称启用的工具列表                                   | -               |
| `options.tool-callbacks`                  | 注册到 ChatModel 的 ToolCallback                 | -               |
| `options.internal-tool-execution-enabled` | 由 Spring AI 内部处理工具调用（false 则代理给客户端）          | `true`          |
| `options.output-modalities`               | 输出模态，如 `text`、`audio`                        | -               |
| `options.output-audio`                    | 音频生成参数（配合 `gpt-4o-audio-preview`）            | -               |
| `options.responseFormat.type`             | 响应格式：`JSON_OBJECT` 或 `JSON_SCHEMA`           | -               |
| `options.responseFormat.name`             | JSON Schema 名称                               | `custom_schema` |
| `options.responseFormat.schema`           | JSON Schema 内容                               | -               |
| `options.responseFormat.strict`           | Schema 严格模式                                  | -               |
| `options.service-tier`                    | 处理类型（速度/质量级别）                                | -               |
| `options.http-headers`                    | 附加 HTTP 请求头                                  | -               |
| `options.extra-body`                      | 额外请求体参数（兼容 vLLM/Ollama 等）                    | -               |

---

## 三、Embedding 模型配置（`spring.ai.openai.embedding.*`）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `spring.ai.model.embedding` | 启用 Embedding 模型（设为 `none` 禁用） | `openai` |
| `spring.ai.openai.embedding.base-url` | Embedding 专用地址 | - |
| `spring.ai.openai.embedding.api-key` | Embedding 专用 Key | - |
| `spring.ai.openai.embedding.embeddings-path` | 请求路径 | `/v1/embeddings` |
| `spring.ai.openai.embedding.organization-id` | 组织 ID | - |
| `spring.ai.openai.embedding.project-id` | 项目 ID | - |
| `spring.ai.openai.embedding.metadata-mode` | 文档内容提取模式 | `EMBED` |
| `options.model` | 嵌入模型名 | `text-embedding-ada-002` |
| `options.encodingFormat` | 返回格式：`float` 或 `base64` | - |
| `options.dimensions` | 输出向量维度（仅 text-embedding-3 及以上支持） | - |
| `options.user` | 终端用户标识 | - |

---

## 四、PGVector 向量库配置（`spring.ai.vectorstore.pgvector.*`）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `index-type` | 索引类型：`NONE` / `IVFFlat` / `HNSW` | `HNSW` |
| `distance-type` | 距离计算：`COSINE_DISTANCE` / `EUCLIDEAN_DISTANCE` / `NEGATIVE_INNER_PRODUCT` | `COSINE_DISTANCE` |
| `dimensions` | 向量维度（需与 Embedding 模型一致） | 自动从模型获取 |
| `initialize-schema` | 启动时自动建表 | `false` |
| `remove-existing-vector-store-table` | 启动时删除旧表 | `false` |
| `schema-name` | Schema 名 | `public` |
| `table-name` | 表名 | `vector_store` |
| `schema-validation` | 校验 schema/table 名合法性（防 SQL 注入） | `false` |
| `max-document-batch-size` | 单批次最大文档数 | `10000` |

---

## 五、重试配置（`spring.ai.retry.*`）

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `max-attempts` | 最大重试次数 | `10` |
| `backoff.initial-interval` | 初始等待时间 | `2s` |
| `backoff.multiplier` | 退避倍数 | `5` |
| `backoff.max-interval` | 最大等待时间 | `3min` |
| `on-client-errors` | 4xx 错误是否重试 | `false` |
| `exclude-on-http-codes` | 不触发重试的 HTTP 状态码列表 | `[]` |
| `on-http-codes` | 强制触发重试的 HTTP 状态码列表 | `[]` |

---

## 附：dawn-ai 项目当前实际配置

```yaml
spring:
  ai:
    openai:
      api-key: ${OPENAI_API_KEY:your-api-key-here}
      chat:
        options:
          model: gpt-4o
          temperature: 0.7
          max-tokens: 2048
      embedding:
        options:
          model: text-embedding-ada-002
    vectorstore:
      pgvector:
        index-type: HNSW
        distance-type: COSINE_DISTANCE
        dimensions: 1536
        initialize-schema: true

app:
  ai:
    system-prompt: |
      You are Dawn AI, a helpful and knowledgeable assistant powered by advanced AI.
      You can help with calculations, weather queries, and answer questions based on your knowledge base.
      Always be concise, accurate, and helpful.
```
