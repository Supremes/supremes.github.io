---
title: dawn-ai 增强点记录
date: 2026-04-03 15:00:00
tags: [AI, Agent, Architecture]
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-04-03 15:00
---

## 代码与文档差距分析

> 对照 [dawn-ai](https://github.com/Supremes/dawn-ai) 仓库代码与规划文档，标注各模块实现状态。

| 模块 | 状态 | 关键代码 | 备注 |
|------|------|---------|------|
| Prompt Engineering | ✅ 已实现 | `BeanOutputConverter<RewriteResult>`、`buildSystemPrompt()` | 结构化输出通过 Record(PlanStep) 实现，系统提示词动态构建 |
| ReAct | ✅ 已实现 | `AgentOrchestrator`、`TaskPlanner`、`application.yml` | max-steps=10, plan-and-resolve 完整, temperature 差异化(TaskPlanner 0.3, QueryRewriter 0.1) |
| RAG | ✅ 已实现 | `RagService`、`QueryRewriter`、`KnowledgeSearchTool` | Query 重写、Agentic RAG、Chunking(500token/50overlap)、相似度阈值 0.7、max-calls=3、去重机制 |
| 向量检索算法 | 🔨 部分实现 | `application.yml`(HNSW) | 仅 HNSW 在 pgvector 中已配置；PQ/IVF/DiskANN 受限于 pgvector 版本未实现 |
| Memory Management | 🔨 部分实现 | `MemoryService` | 短期记忆 Redis List(MAX_HISTORY=20) 可用；摘要压缩/长期记忆固化/遗忘机制仅在设计文档中 |
| Reflection | ❌ 未实现 | — | 文档已规划（用户画像聚合、底层数据反思生成），代码无对应实现 |
| Agent 评估系统 | ❌ 未实现 | — | 文档中空白，代码中无评估模块 |

### 文档未覆盖但代码已有的功能

1. **可观测性**：完整的 Micrometer 指标体系（`ai.token.*`、`ai.rag.*`、`ai.planner.*`）
2. **StepTraceHook**：Agent 执行步骤的自动追踪和指标上报
3. **异常体系**：`MaxStepsExceededException`、`LLMProviderException`、`PlanGenerationException`
4. **工具注册**：自动扫描 @Tool 注解的 `ToolRegistry` 机制
5. **PDF 支持**：依赖中已引入 `spring-ai-pdf-document-reader`

---

## 企业级 Agent 架构全景（8 层）

### 第一层：基础能力层

#### 1.1 LLM 核心集成 [已有部分]
- 模型推理与参数优化 [已有]（temperature 差异化配置）
- Token 计数与成本控制 [待补充]
- 速率限制与重试策略 [待补充]

#### 1.2 Prompt Engineering [已有]
- Output Structure：限制 LLM 输出结果符合结构化格式 [已有]
- Prompt Template 与变量绑定 [待补充]
- Few-shot Learning 与示例设计 [待补充]

#### 1.3 Output Parsing [待补充]
- 结构化输出解析（JSON、XML）[待补充]
- 容错与降级机制 [待补充]

---

### 第二层：推理与规划层

#### 2.1 Chain-of-Thought [待补充]
- 标准 CoT [待补充]
- Tree-of-Thought [待补充]

#### 2.2 ReAct Framework [已有]
- Tool Calling 与 Agent Loop [已有]
- Max-steps 控制与死循环检测 [已有]
- Plan-and-Solve 策略 [已有]
- LLM 参数优化（temperature 等）[已有]

---

### 第三层：知识与记忆层

#### 3.1 Memory Management [已有]
- 核心记忆 — 用户画像、核心指令，携带在 System Prompt 中 [已有]
- 短期记忆 [已有]
    - Sliding Window（滑动窗口）[已有]
    - Token Bounding（Token 限制）[已有]
    - Summary Buffer（摘要缓冲）[待补充]
- 长期记忆 — 向量数据库 [已有架构]
- 记忆固化 (Consolidation) [待补充]
- 记忆反思 (Reflection) [待补充]
- 遗忘机制 (Decay / Eviction) [待补充]
    - `最终相关性 = 向量相似度权重 * a + 时间衰减权重 * b + 重要性评分权重 * c`

#### 3.2 RAG 系统 [已有]
- Query 重写 [已有]
- Agentic RAG（LLM 驱动），Max-rag-calls [已有]
- Embedding、Chunk、Overlap [已有]
- 召回率优化 [已有]
- HYDE - Hypothetical Document Embeddings [待补充]

#### 3.3 向量检索算法 [已有]
- IVF (Inverted File System) — 缩小搜索范围 [待补充]
- PQ (Product Quantization) — 压缩向量体积 [待补充]
- HNSW (Hierarchical Navigable Small World) [已有]
- HNSW_PQ / HNSW_SQ [待补充]
- DiskANN (Vamana 图) [待补充]

---

### 第四层：工具与执行层 [待补充]

#### 4.1 Function Calling [待补充]
- Tool 定义与 Schema [待补充]
- 执行结果处理与错误恢复 [待补充]
- ToolRegistry 自动扫描机制 [已有代码，待文档化]

#### 4.2 MCP 协议支持 [待补充]
- MCP Server 集成 [待补充]
- 外部工具接入标准化 [待补充]

---

### 第五层：多 Agent 协作层 [待补充]

#### 5.1 Multi-Agent 编排 [待补充]
- 协作模式（串行、并行、层级）[待补充]
- Agent 间通信协议 [待补充]

#### 5.2 任务委派与协调 [待补充]
- 子任务分解与分配 [待补充]
- 结果聚合与冲突解决 [待补充]

---

### 第六层：安全与合规层 [待补充]

#### 6.1 Prompt Injection 防护 [待补充]
- 输入过滤与检测 [待补充]
- 沙箱执行隔离 [待补充]

#### 6.2 Guardrails [待补充]
- Input/Output Filtering [待补充]
- 敏感信息脱敏 [待补充]
- 合规审计日志 [待补充]

---

### 第七层：可观测性与评估层 [部分已有]

#### 7.1 Tracing 与 Monitoring [已有代码，待文档化]
- Micrometer 指标体系 [已有]
- StepTraceHook 执行追踪 [已有]
- 全链路 Tracing [待补充]

#### 7.2 Agent 评估系统 [待补充]
- 评估指标与基准定义 [待补充]
- A/B Testing 框架 [待补充]
- 回归测试与质量门禁 [待补充]

---

### 第八层：工程化与部署层 [待补充]

#### 8.1 CI/CD [待补充]
- 自动化测试流水线 [待补充]
- 模型版本管理 [待补充]

#### 8.2 弹性伸缩与容错 [待补充]
- 异步处理与队列 [待补充]
- 熔断与降级策略 [待补充]
- 异常体系（MaxStepsExceeded 等）[已有代码，待文档化]

#### 8.3 成本优化 [待补充]
- Token 用量监控与预算 [待补充]
- 模型路由（按任务选模型）[待补充]
