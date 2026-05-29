---
title: Agent Development Guide
date: 2026-03-16
tags: []
---
> 面向：有 Java 后端经验 → 目标：AI Agent 架构师
> 技术栈：Java 17+ · Spring Boot 3 · Spring AI · LangChain4j

---

## 📅 总体时间线

| 阶段 | 时长 | 核心目标 |
|------|------|----------|
| Phase 0：地基补强 | 第 1 月 | LLM 基础认知 + Prompt Engineering |
| Phase 1：Tool Calling | 第 2 月 | Agent 手脚：工具设计与调用 |
| Phase 2：Memory | 第 3 月 | Agent 记忆：短期/长期/语义记忆 |
| Phase 3：RAG | 第 4-5 月 | Agent 知识：检索增强生成架构 |
| Phase 4：Planner | 第 6 月 | Agent 大脑：规划与推理范式 |
| Phase 5：多 Agent 协作 | 第 7 月 | Agent 组织：编排与协作框架 |
| Phase 6：工程化 | 第 8 月 | Agent 血肉：可观测/安全/CI/CD |
| Phase 7：综合实战 | 第 9-10 月 | 完整 Agent 系统落地 |

---

## Phase 0：地基补强 — LLM 认知与 Prompt Engineering

### 🎯 学习目标
理解大模型的能力边界，掌握与 LLM 有效"沟通"的工程化方法。

### 📚 核心知识点

#### 0.1 大模型基础认知
- Transformer 架构直觉理解（不需要推导，但要懂 Attention 的本质）
- Token 机制：什么是 context window，为什么它是 Agent 设计的核心约束
- 温度（Temperature）/ Top-P：概率采样对输出确定性的影响
- **后端类比：** Token 限制 ≈ JVM 堆内存上限；超出 context window ≈ OOM，需要主动做"内存管理"（消息裁剪/压缩）

#### 0.2 Prompt Engineering
- Zero-shot / Few-shot / Chain-of-Thought (CoT)
- System Prompt 的架构设计（角色设定、约束、输出格式）
- Prompt 模板工程化：变量注入、版本管理
- 结构化输出：JSON Mode / Function Calling 输出约束

#### 0.3 主流模型 API 接入

```java
// Spring AI 接入 OpenAI 示例
@Bean
public ChatClient chatClient(ChatClient.Builder builder) {
    return builder
        .defaultSystem("你是一个专业的 Java 技术助手")
        .build();
}

// 调用
String response = chatClient.prompt()
    .user("解释 AQS 的核心原理")
    .call()
    .content();
```

### 🛠️ 推荐实践
- [ ] 搭建 Spring AI + OpenAI/Ollama 本地环境
- [ ] 手写 Prompt 模板管理器（支持版本化）
- [ ] 实现结构化 JSON 输出解析器

### 📖 推荐资料
- [Spring AI 官方文档](https://docs.spring.io/spring-ai/reference/)
- [LangChain4j 快速开始](https://docs.langchain4j.dev/)
- OpenAI Prompt Engineering Guide

---

## Phase 1：Tool Calling — Agent 的"手脚"

> **后端类比：** Tool = 你注册在 Spring 容器里的 `@Service`，LLM 是调用方；整个 Tool Calling 机制 ≈ 反射 + 动态代理 + RPC 路由

### 🎯 学习目标
设计和实现高可用、可扩展的 Agent Tool 体系，处理并发安全与降级。

### 📚 核心知识点

#### 1.1 Tool Calling 底层原理
- Function Calling 协议：LLM 如何决策调用哪个工具（JSON Schema 描述）
- 工具注册机制：Tool Description 的质量直接决定 LLM 的调用准确率
- 同步 vs 异步工具调用
- 工具调用的循环：`LLM → Tool → Result → LLM`（ReAct 的基础）

```java
// LangChain4j Tool 定义
public class DatabaseQueryTool {

    @Tool("查询用户订单列表，支持按状态和时间范围过滤")
    public List<Order> queryOrders(
        @P("用户ID") Long userId,
        @P("订单状态: PENDING/COMPLETED/CANCELLED") String status,
        @P("开始时间 yyyy-MM-dd") String startDate
    ) {
        // 实现查询逻辑
        return orderService.query(userId, status, startDate);
    }
}
```

#### 1.2 工具设计原则（Tool Design Patterns）

| 原则 | 说明 | 后端类比 |
|------|------|----------|
| 单一职责 | 一个 Tool 只做一件事 | 微服务拆分原则 |
| 幂等设计 | 重复调用结果一致 | HTTP PUT 语义 |
| 防御性编程 | 入参校验 + 类型安全 | DTO 校验 + @Valid |
| 超时控制 | 每个 Tool 必须有超时 | `@Async` + `CompletableFuture.orTimeout()` |

#### 1.3 进阶：并发工具调用

```java
// 并行工具调用 - 类比 CompletableFuture.allOf()
@Component
public class ParallelToolExecutor {

    private final ExecutorService toolExecutor =
        new ThreadPoolExecutor(
            10, 50, 60L, TimeUnit.SECONDS,
            new LinkedBlockingQueue<>(100),
            new ThreadFactory() { /* 命名线程 */ },
            new ThreadPoolExecutor.CallerRunsPolicy() // 背压策略
        );

    public Map<String, Object> executeParallel(List<ToolCall> toolCalls) {
        List<CompletableFuture<Map.Entry<String, Object>>> futures =
            toolCalls.stream()
                .map(call -> CompletableFuture
                    .supplyAsync(() -> executeOne(call), toolExecutor)
                    .orTimeout(5, TimeUnit.SECONDS)
                    .exceptionally(ex -> Map.entry(call.id(), "ERROR: " + ex.getMessage()))
                )
                .toList();

        return CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
            .thenApply(v -> futures.stream()
                .map(CompletableFuture::join)
                .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue)))
            .join();
    }
}
```

#### 1.4 高级：工具注册中心
- 动态工具注册/注销（插件化架构）
- 工具权限控制（哪个 Agent 能调用哪些工具）
- 工具调用审计日志

### 🛠️ 推荐实践
- [ ] 实现数据库查询 Tool（带超时 + 降级）
- [ ] 实现 HTTP 调用 Tool（带重试 + 熔断）
- [ ] 设计工具调用链路的 Trace 日志
- [ ] 压测：模拟 LLM 并发调用 50 个 Tool 实例

### 📖 推荐资料
- OpenAI Function Calling 官方文档
- LangChain4j Tools & Agents 文档
- Spring AI Tool/Function Calling 章节

---

## Phase 2：Memory — Agent 的"记忆"

> **后端类比：**
> - 短期记忆（Buffer Memory）≈ Redis String，快速读写，有 TTL
> - 长期记忆（Vector Memory）≈ MySQL + 倒排索引，持久化，按语义检索
> - 对话摘要 ≈ 数据库归档压缩（将历史 binlog 归档为快照）

### 🎯 学习目标
设计多层次记忆体系，解决 context window 限制，实现跨会话的持久化记忆。

### 📚 核心知识点

#### 2.1 短期记忆（Conversation Buffer）
- 消息窗口管理：滑动窗口 vs Token 预算管理
- 消息压缩策略：超出窗口后的摘要生成
- 多轮对话状态机设计

```java
// 基于 Spring AI 的对话历史管理
@Service
public class ConversationMemoryService {

    // 类比 Redis 的 List 结构存储消息
    private final ChatMemory chatMemory = MessageWindowChatMemory.builder()
        .maxMessages(20)  // 滑动窗口大小
        .build();

    public String chat(String sessionId, String userInput) {
        return chatClient.prompt()
            .user(userInput)
            .advisors(new MessageChatMemoryAdvisor(chatMemory, sessionId, 10))
            .call()
            .content();
    }
}
```

#### 2.2 Token 预算管理（核心难点）

```java
// Token 计算与裁剪 - 类比内存分页管理
public class TokenBudgetManager {

    private static final int MAX_CONTEXT_TOKENS = 8000;
    private static final int RESPONSE_RESERVE = 1000;
    private static final int AVAILABLE_TOKENS = MAX_CONTEXT_TOKENS - RESPONSE_RESERVE;

    public List<Message> trimHistory(List<Message> history) {
        int usedTokens = 0;
        Deque<Message> result = new ArrayDeque<>();

        for (int i = history.size() - 1; i >= 0; i--) {
            Message msg = history.get(i);
            int tokens = estimateTokens(msg);
            if (usedTokens + tokens > AVAILABLE_TOKENS) break;
            result.addFirst(msg);
            usedTokens += tokens;
        }
        return new ArrayList<>(result);
    }
}
```

#### 2.3 长期记忆（Vector Memory）
- Embedding 原理：文本 → 高维向量（类比将文档转换为多维索引键）
- 向量数据库选型：

| 数据库 | 特点 | 适用场景 |
|--------|------|----------|
| Milvus | 高性能，企业级 | 亿级向量，生产首选 |
| Qdrant | Rust 实现，轻量 | 中小规模 |
| PGVector | PostgreSQL 扩展 | 已有 PG 的团队 |
| Redis Vector | 低延迟 | 热数据语义搜索 |

```java
// Spring AI 向量存储操作
@Service
public class LongTermMemoryService {

    private final VectorStore vectorStore;

    // 存储记忆（类比 INSERT + 建索引）
    public void remember(String userId, String content) {
        Document doc = new Document(content,
            Map.of("userId", userId, "timestamp", Instant.now().toString()));
        vectorStore.add(List.of(doc));
    }

    // 语义检索（类比 SELECT WHERE similarity > threshold）
    public List<String> recall(String userId, String query, int topK) {
        SearchRequest request = SearchRequest.query(query)
            .withTopK(topK)
            .withFilterExpression("userId == '" + userId + "'");

        return vectorStore.similaritySearch(request)
            .stream()
            .map(Document::getContent)
            .toList();
    }
}
```

#### 2.4 记忆分层架构

```
┌─────────────────────────────────────────────┐
│              Agent Memory 分层               │
├─────────────────────────────────────────────┤
│  L1: 工作记忆 (Working Memory)               │
│      当前对话 context window                 │
│      类比: CPU L1 Cache / JVM 栈帧           │
├─────────────────────────────────────────────┤
│  L2: 会话记忆 (Session Memory)               │
│      Redis 存储，TTL=24h                     │
│      类比: CPU L2 Cache / Redis 热数据       │
├─────────────────────────────────────────────┤
│  L3: 长期记忆 (Episodic Memory)              │
│      Vector DB，永久存储                     │
│      类比: 磁盘 / MySQL 全文索引             │
├─────────────────────────────────────────────┤
│  L4: 知识记忆 (Semantic Memory)              │
│      RAG 知识库（下一章节）                  │
│      类比: 只读文档数据库                    │
└─────────────────────────────────────────────┘
```

### 🛠️ 推荐实践
- [ ] 实现基于 Redis 的会话记忆存储（带 TTL + 序列化）
- [ ] 接入 PGVector，实现用户历史行为的语义检索
- [ ] 实现对话摘要压缩（超过 10 轮自动摘要）
- [ ] 压测：1000 并发用户会话的内存隔离验证

---

## Phase 3：RAG — Agent 的"知识库"

> **后端类比：** RAG = 数据库查询增强版。`SELECT * FROM knowledge WHERE semantic_similarity(content, query) > 0.8`。Embedding 就是给文档建"语义索引"，比 MySQL LIKE 查询高维得多。

### 🎯 学习目标
构建生产级 RAG 系统，掌握从文档摄入到检索增强的完整链路。

### 📚 核心知识点

#### 3.1 RAG 基础架构（Naive RAG）

```
文档摄入流水线（离线）：
原始文档 → 解析 → 分块(Chunking) → Embedding → 向量存储

检索增强流水线（在线）：
用户问题 → Embedding → 向量检索 → 重排序 → 注入 Prompt → LLM → 回答
```

#### 3.2 文档处理流水线

```java
// Spring AI ETL Pipeline
@Service
public class DocumentIngestionPipeline {

    private final VectorStore vectorStore;
    private final EmbeddingModel embeddingModel;

    public void ingest(Resource documentResource) {
        // 1. 读取文档（支持 PDF/Word/Markdown）
        var reader = new PagePdfDocumentReader(documentResource,
            PdfDocumentReaderConfig.builder()
                .withPageTopMargin(0)
                .withPageExtractedTextFormatter(
                    ExtractedTextFormatter.builder()
                        .withNumberOfBottomTextLinesToDelete(3)
                        .build())
                .build());

        // 2. 分块策略（核心！类比数据库分区策略）
        var splitter = new TokenTextSplitter(
            512,    // chunk size（类比分区大小）
            128,    // overlap（类比分区重叠，保证语义连续性）
            5, 10000, true);

        // 3. ETL & 写入向量库
        List<Document> docs = splitter.apply(reader.get());
        vectorStore.add(docs);  // 自动 Embedding + 存储
    }
}
```

#### 3.3 分块策略（Chunking Strategy）

| 策略 | 原理 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| Fixed Size | 固定 Token 数切割 | 简单 | 语义割裂 | 快速原型 |
| Recursive | 按段落/句子递归 | 语义完整 | 实现复杂 | 通用文档 |
| Semantic | 语义相似度分割 | 最佳质量 | 计算昂贵 | 高质量知识库 |
| Hierarchical | 父子块关联 | 支持多粒度检索 | 存储翻倍 | 长文档问答 |

#### 3.4 进阶 RAG 模式

**Advanced RAG 架构：**

```
查询理解层:
  ├── Query Rewriting（查询改写，提高召回率）
  ├── Query Decomposition（复杂问题分解）
  └── HyDE（假设文档嵌入，提高检索精度）

检索层:
  ├── Dense Retrieval（向量检索）
  ├── Sparse Retrieval（BM25 关键词检索）
  └── Hybrid Search（混合检索 = 两者 + RRF 融合）

后处理层:
  ├── Re-ranking（交叉编码器重排序）
  ├── Contextual Compression（上下文压缩）
  └── Citation（来源溯源）
```

```java
// 混合检索实现
@Service
public class HybridSearchService {

    private final VectorStore vectorStore;
    private final ElasticsearchClient esClient;  // BM25 检索

    public List<Document> hybridSearch(String query, int topK) {
        CompletableFuture<List<Document>> denseFuture =
            CompletableFuture.supplyAsync(() ->
                vectorStore.similaritySearch(SearchRequest.query(query).withTopK(topK * 2)));

        CompletableFuture<List<Document>> sparseFuture =
            CompletableFuture.supplyAsync(() ->
                esClient.bm25Search(query, topK * 2));

        // RRF 融合排序（Reciprocal Rank Fusion）
        return CompletableFuture.allOf(denseFuture, sparseFuture)
            .thenApply(v -> rrfFusion(denseFuture.join(), sparseFuture.join(), topK))
            .join();
    }

    private List<Document> rrfFusion(List<Document> dense,
                                      List<Document> sparse, int topK) {
        // RRF score = Σ 1/(k + rank_i), k=60
        Map<String, Double> scores = new HashMap<>();
        IntStream.range(0, dense.size()).forEach(i ->
            scores.merge(dense.get(i).getId(), 1.0 / (60 + i + 1), Double::sum));
        IntStream.range(0, sparse.size()).forEach(i ->
            scores.merge(sparse.get(i).getId(), 1.0 / (60 + i + 1), Double::sum));

        return scores.entrySet().stream()
            .sorted(Map.Entry.<String, Double>comparingByValue().reversed())
            .limit(topK)
            .map(e -> findDocById(e.getKey(), dense, sparse))
            .toList();
    }
}
```

#### 3.5 RAG 评估体系（RAGAS 指标）

| 指标 | 含义 | 类比 |
|------|------|------|
| Faithfulness | 回答是否忠实于检索内容 | 数据一致性检验 |
| Answer Relevance | 回答与问题相关性 | 查询精度（Precision）|
| Context Recall | 检索是否覆盖必要信息 | 查询召回率（Recall）|
| Context Precision | 检索结果是否精准 | 索引选择性 |

### 🛠️ 推荐实践
- [ ] 构建企业文档问答系统（PDF 摄入 → 问答）
- [ ] 对比 4 种分块策略的效果差异
- [ ] 实现混合检索（Vector + BM25）
- [ ] 集成 RAGAS 建立评估 Pipeline
- [ ] 实现 Re-ranking（使用 Cohere Rerank API）

---

## Phase 4：Planner — Agent 的"大脑"

> **后端类比：** Planner ≈ 分布式任务调度器（类比 Quartz/XXL-Job），但决策逻辑由 LLM 驱动而非硬编码。ReAct ≈ 工作流引擎的 `决策节点 → 执行节点 → 观察节点` 循环。

### 🎯 学习目标
掌握主流 Agent 推理范式，设计可观测、可干预的规划执行引擎。

### 📚 核心知识点

#### 4.1 推理范式对比

| 范式 | 机制 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|----------|
| CoT | 思维链推理 | 提升推理质量 | 无法执行动作 | 复杂分析 |
| ReAct | 推理 + 行动交替 | 动态环境适应 | 多轮开销大 | 通用 Agent |
| Plan-and-Execute | 先完整规划再执行 | 全局最优 | 规划失败代价高 | 长任务 |
| Tree of Thoughts | 树状搜索 | 最优解探索 | 极高开销 | 复杂决策 |

#### 4.2 ReAct 实现

```java
// ReAct 循环核心实现
@Service
public class ReActAgent {

    private static final int MAX_ITERATIONS = 10;  // 防止无限循环

    public AgentResult execute(String task, List<Object> tools) {
        List<Message> trajectory = new ArrayList<>();
        trajectory.add(new SystemMessage(buildSystemPrompt(tools)));
        trajectory.add(new UserMessage(task));

        for (int iter = 0; iter < MAX_ITERATIONS; iter++) {
            // Thought: LLM 推理
            ChatResponse response = chatClient.prompt()
                .messages(trajectory)
                .call()
                .chatResponse();

            String llmOutput = response.getResult().getOutput().getContent();
            trajectory.add(new AssistantMessage(llmOutput));

            // 检测是否完成
            if (llmOutput.contains("Final Answer:")) {
                return AgentResult.success(extractFinalAnswer(llmOutput));
            }

            // Action: 解析工具调用
            ToolCall toolCall = parseToolCall(llmOutput);
            if (toolCall == null) {
                return AgentResult.failure("无法解析工具调用");
            }

            // Observation: 执行工具获取结果
            String observation = executeToolWithTimeout(toolCall, 5, TimeUnit.SECONDS);
            trajectory.add(new UserMessage("Observation: " + observation));

            // 记录追踪（可观测性）
            tracer.record(iter, toolCall, observation);
        }

        return AgentResult.failure("超过最大迭代次数");
    }
}
```

#### 4.3 Plan-and-Execute 模式

```java
public record ExecutionPlan(
    String goal,
    List<PlanStep> steps,
    Map<String, Object> context  // 步骤间共享状态
) {}

public record PlanStep(
    int stepId,
    String description,
    String toolName,
    Map<String, Object> parameters,
    List<Integer> dependsOn  // 依赖关系，支持并行执行！
) {}

@Service
public class PlanAndExecuteAgent {

    public AgentResult execute(String goal) {
        // Phase 1: Planner - 生成执行计划
        ExecutionPlan plan = plannerLlm.generatePlan(goal);

        // Phase 2: Executor - 按依赖关系并行执行
        Map<Integer, CompletableFuture<StepResult>> futures = new HashMap<>();

        for (PlanStep step : plan.steps()) {
            CompletableFuture<Void> deps = step.dependsOn().isEmpty()
                ? CompletableFuture.completedFuture(null)
                : CompletableFuture.allOf(
                    step.dependsOn().stream()
                        .map(futures::get)
                        .toArray(CompletableFuture[]::new));

            futures.put(step.stepId(), deps.thenApplyAsync(
                v -> executeStep(step, plan.context())));
        }

        // Phase 3: 汇总结果
        return aggregateResults(futures);
    }
}
```

#### 4.4 规划的核心工程问题
- **幻觉降级：** LLM 规划出不存在的工具 → 工具名称白名单校验
- **循环检测：** Agent 陷入重复调用循环 → 调用链去重 + 最大迭代限制
- **状态持久化：** 长任务中途失败后恢复 → Checkpoint 机制（类比 Saga 模式）
- **人机交互：** 关键节点需人工确认 → Human-in-the-loop 暂停点

### 🛠️ 推荐实践
- [ ] 实现 ReAct Agent，完成「研究竞品并生成报告」任务
- [ ] 实现 Plan-and-Execute，含步骤依赖并行化
- [ ] 加入 Checkpoint 机制，支持任务断点续跑
- [ ] 实现 Human-in-the-loop 的审批暂停点

---

## Phase 5：多 Agent 协作

> **后端类比：** 多 Agent 系统 ≈ 微服务架构。每个 Agent 是一个专职微服务，需要服务发现、负载均衡、消息总线和分布式追踪。

### 🎯 学习目标
设计可扩展的多 Agent 协作架构，掌握主流编排框架。

### 📚 核心知识点

#### 5.1 多 Agent 拓扑模式

```
模式一：层级式（Hierarchical）
┌─────────────────────────────┐
│      Supervisor Agent       │  ← 任务分发、结果汇总
└──────────┬──────────────────┘
    ┌──────┼──────┐
    ↓      ↓      ↓
  Agent1 Agent2 Agent3      ← 专职 Worker Agent

模式二：流水线式（Pipeline）
User → [预处理Agent] → [分析Agent] → [写作Agent] → Result

模式三：辩论式（Debate）
                ┌→ Agent-正方 ─┐
User Request ──→│              ├→ Judge Agent → Final Answer
                └→ Agent-反方 ─┘
```

#### 5.2 基于 LangGraph4j 的状态机编排

```java
// LangGraph4j 工作流定义（类比 Spring State Machine）
@Configuration
public class ResearchWorkflow {

    @Bean
    public StateGraph<ResearchState> researchGraph() {
        return StateGraph.<ResearchState>builder()
            .addNode("planner", plannerAgent::run)
            .addNode("researcher", researcherAgent::run)
            .addNode("writer", writerAgent::run)
            .addNode("reviewer", reviewerAgent::run)

            // 条件路由（类比路由表）
            .addConditionalEdges("reviewer", state ->
                state.reviewScore() >= 8 ? "END" : "writer")

            .addEdge(START, "planner")
            .addEdge("planner", "researcher")
            .addEdge("researcher", "writer")
            .addEdge("writer", "reviewer")
            .build();
    }
}
```

#### 5.3 Agent 间通信设计

```java
// 基于消息总线的 Agent 通信（类比 MQ 解耦）
@Service
public class AgentMessageBus {

    private final Map<String, BlockingQueue<AgentMessage>> queues =
        new ConcurrentHashMap<>();

    public void publish(String targetAgentId, AgentMessage message) {
        queues.computeIfAbsent(targetAgentId, k -> new LinkedBlockingQueue<>())
            .offer(message);
    }

    public AgentMessage consume(String agentId, long timeout, TimeUnit unit)
        throws InterruptedException {
        return queues.computeIfAbsent(agentId, k -> new LinkedBlockingQueue<>())
            .poll(timeout, unit);
    }
}
```

### 🛠️ 推荐实践
- [ ] 实现「研究员 + 撰写员 + 评审员」三角协作系统
- [ ] 实现 Supervisor 模式，动态分配子任务
- [ ] 基于 LangGraph4j 实现条件循环工作流

---

## Phase 6：Agent 工程化 — 生产级标准

> 这是从「能用」到「好用」的关键跨越。

### 🎯 学习目标
建立完整的 Agent 工程化体系：可观测 + 安全 + 自动化交付。

### 📚 核心知识点

#### 6.1 可观测性（Observability）

```java
// Micrometer + Prometheus 打点
@Component
public class AgentMetrics {

    private final MeterRegistry registry;
    private final Timer llmLatency;
    private final Counter tokenCounter;
    private final Counter toolSuccessCounter;
    private final Counter toolFailureCounter;

    public AgentMetrics(MeterRegistry registry) {
        this.registry = registry;
        this.llmLatency = Timer.builder("agent.llm.latency")
            .description("LLM API 调用延迟")
            .tag("model", "gpt-4o")
            .publishPercentiles(0.5, 0.95, 0.99)
            .register(registry);
    }

    public <T> T recordLlmCall(Supplier<T> llmCall, String model) {
        return llmLatency.record(() -> {
            try {
                T result = llmCall.get();
                tokenCounter.increment(extractTokenCount(result));
                return result;
            } catch (Exception e) {
                registry.counter("agent.llm.errors", "model", model).increment();
                throw e;
            }
        });
    }
}
```

**Grafana 核心监控面板：**
- LLM API P99 延迟趋势
- Token 消耗速率（成本控制）
- 工具调用成功率
- Agent 任务完成率
- 内存使用量（向量存储增长）

#### 6.2 降级策略

```java
// Resilience4j 集成 LLM 熔断
@Bean
public CircuitBreaker llmCircuitBreaker(CircuitBreakerRegistry registry) {
    return registry.circuitBreaker("llm-api", CircuitBreakerConfig.custom()
        .failureRateThreshold(50)           // 失败率超 50% 开启熔断
        .waitDurationInOpenState(Duration.ofSeconds(30))
        .slidingWindowSize(10)
        .build());
}

// 降级策略：主模型熔断时切换备用模型
@Service
public class ResilientLlmClient {

    public String chat(String prompt) {
        return Decorators.ofSupplier(() -> primaryLlm.call(prompt))
            .withCircuitBreaker(llmCircuitBreaker)
            .withRetry(Retry.ofDefaults("llm-retry"))
            .withFallback(List.of(Exception.class),
                e -> fallbackLlm.call(prompt))  // 降级到本地模型
            .decorate()
            .get();
    }
}
```

#### 6.3 安全设计

| 威胁 | 防护措施 |
|------|----------|
| Prompt Injection | 输入净化 + 系统提示隔离 |
| 数据泄露 | Tool 调用权限矩阵 + 敏感数据脱敏 |
| 资源滥用 | Token 配额限流（令牌桶算法）|
| 未授权调用 | OIDC + JWT 验证 Agent 身份 |

```java
// 基于令牌桶的 Token 限流
@Service
public class TokenRateLimiter {

    // 每用户每分钟最多 10000 tokens
    private final Cache<String, RateLimiter> userLimiters = Caffeine.newBuilder()
        .expireAfterAccess(1, TimeUnit.HOURS)
        .build();

    public boolean tryAcquire(String userId, int tokenCount) {
        RateLimiter limiter = userLimiters.get(userId,
            k -> RateLimiter.create(10000.0 / 60)); // tokens/second
        return limiter.tryAcquire(tokenCount);
    }
}
```

#### 6.4 CI/CD Pipeline

```yaml
# GitHub Actions - Agent 系统 CI/CD
name: Agent CI/CD Pipeline

on: [push]

jobs:
  test:
    steps:
      - name: 单元测试（Mock LLM）
        run: ./gradlew test

      - name: RAG 评估测试
        run: ./gradlew ragas-eval  # 自动化 RAG 质量评估

      - name: Prompt 回归测试
        run: ./gradlew prompt-regression  # 对比 Prompt 变更前后效果

  build:
    needs: test
    steps:
      - name: 构建镜像
        run: docker build -t agent-service:${{ github.sha }} .

  deploy:
    needs: build
    steps:
      - name: 金丝雀发布（5% 流量）
        run: kubectl set image deployment/agent-service ...

      - name: 监控 15min 后全量发布
        run: ./scripts/canary-promote.sh
```

### 🛠️ 推荐实践
- [ ] 搭建完整 Prometheus + Grafana 监控栈
- [ ] 实现 LLM API 熔断降级
- [ ] 实现 Prompt Injection 防护
- [ ] 搭建含 RAG 评估的 CI/CD Pipeline

---

## Phase 7：综合实战项目 🏆

### 项目：「企业级智能客服 Agent 系统」

> 将所有模块串联，覆盖完整的工程化落地。

#### 系统架构

```
┌────────────────────────────────────────────────────────┐
│                    用户接入层                           │
│         Web / WeChat / API (Spring Boot 3)             │
└──────────────────────┬─────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│                   Agent 编排层                          │
│    Supervisor Agent → [意图识别] → [路由决策]           │
│         ↓                ↓                             │
│   FAQ Agent        Order Agent      Complaint Agent    │
│  (RAG驱动)        (Tool Calling)    (Escalation)       │
└──────────────────────┬─────────────────────────────────┘
                       ↓
┌────────────────────────────────────────────────────────┐
│                   基础设施层                            │
│  Memory: Redis(短期) + Milvus(长期)                    │
│  Knowledge: PGVector + Elasticsearch (混合检索)        │
│  Tools: 订单系统/CRM/工单系统                          │
│  Observability: Prometheus + Grafana + Jaeger          │
└────────────────────────────────────────────────────────┘
```

#### 涵盖的技术模块

| 模块 | 在项目中的体现 |
|------|---------------|
| Tool Calling | 查询订单状态、创建工单、发送邮件 |
| Memory | 记住用户历史投诉记录、偏好 |
| RAG | 企业知识库问答（产品手册/FAQ）|
| Planner | 复杂投诉处理的多步骤规划 |
| 多 Agent | Supervisor 路由 + 专职 Agent |
| 工程化 | 全链路监控 + 灰度发布 + 降级 |

---

## 📊 技能成熟度自检表

| 能力维度 | 入门 ✓ | 进阶 ✓✓ | 高级 ✓✓✓ |
|----------|--------|---------|---------|
| Tool 设计与并发安全 | 能实现基本 Tool | 含超时/降级/并发 | 动态插件化 Tool 注册中心 |
| Memory 分层架构 | 实现对话历史 | 向量长期记忆 | Token 预算管理 + 压缩 |
| RAG 质量优化 | Naive RAG | 混合检索 + Rerank | 自适应 RAG + 评估体系 |
| Planner 可靠性 | ReAct 基础实现 | 带 Checkpoint 的长任务 | 多 Agent 协作编排 |
| 工程化成熟度 | 基础日志 | Prometheus 监控 | 熔断降级 + 自动化评估 CI |

---

> 💡 **导师寄语：** 你的 Java 后端底子是最大的优势。每当遇到 Agent 的「概率性」让你不安时，记住：你已经驯服了 JVM GC 的不确定性、分布式网络的抖动——大模型不过是另一个需要被工程化约束的"不确定性黑盒"。**用你驾驭系统的方式，去驾驭 AI。**
