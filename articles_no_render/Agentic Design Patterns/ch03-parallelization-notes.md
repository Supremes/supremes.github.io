---
title: '第3章：Parallelization（并行化模式）学习笔记'
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

# Parallelization（并行化模式）学习笔记

> 来源：https://adp.xindoo.xyz/chapters/Chapter%203_%20Parallelization/
> 整理日期：2026-03-23

---

## 一、什么是 Parallelization

**并行化（Parallelization）** = 并发执行多个**相互独立**的子任务（LLM 调用、工具调用、子 Agent），而非顺序等待，从而显著缩短总执行时间。

与前两章的关系：
- **Prompt Chaining**：顺序依赖，解决"怎么做"
- **Routing**：条件分支，解决"做哪个"
- **Parallelization**：并发执行，解决"怎么更快"

三者结合，构成完整的 Agent 控制流工具箱。

---

## 二、核心原则

**识别工作流中不依赖彼此即时输出的环节，并将它们并行执行。**

典型对比（研究 Agent）：

| 顺序执行 | 并行执行 |
|---------|---------|
| 搜索 A → 总结 A → 搜索 B → 总结 B → 合成 | 搜索 A + 搜索 B（同时）→ 总结 A + 总结 B（同时）→ 合成 |
| 总时间 = 各步骤之和 | 总时间 ≈ 最慢单步 + 合成 |

> 关键：合成步骤通常仍需顺序执行（依赖所有并行结果）。

---

## 三、7 大应用场景

| 场景 | 并行任务示例 | 优势 |
|------|------------|------|
| **信息收集** | 同时查新闻、股票、社交媒体、数据库 | 更快获得全面视图 |
| **数据分析** | 同时做情感分析、关键词提取、分类、紧急识别 | 快速多维度结果 |
| **多 API 调用** | 同时查航班、酒店、活动、餐厅 | 更快呈现完整方案 |
| **内容生成** | 同时生成标题、正文、图片查找、CTA 文案 | 高效组装最终内容 |
| **验证核实** | 同时验证邮箱、手机、地址、不当内容 | 更快给出有效性反馈 |
| **多模态处理** | 同时分析文本情感、识别图像对象 | 快速整合跨模态洞察 |
| **A/B 测试生成** | 同时生成多个标题/方案变体 | 快速比较选最优 |

---

## 四、注意事项

- **asyncio ≠ 真并行**：Python asyncio 是单线程并发（事件循环），在 I/O 等待时切换任务，受 GIL 限制。对于 API 调用（网络 I/O）非常有效，对于 CPU 密集型任务需用多进程。
- **复杂性代价**：并发架构会增加设计、调试、日志追踪的复杂度。
- **适用前提**：子任务之间真正无依赖关系才能并行，有依赖的部分仍需顺序执行。

---

## 五、框架实现对比

### LangChain（显式 RunnableParallel）
```python
# 定义三个独立链
summarize_chain = prompt_summarize | llm | StrOutputParser()
questions_chain = prompt_questions | llm | StrOutputParser()
terms_chain     = prompt_terms     | llm | StrOutputParser()

# 并行执行
map_chain = RunnableParallel({
    "summary":    summarize_chain,
    "questions":  questions_chain,
    "key_terms":  terms_chain,
    "topic":      RunnablePassthrough(),
})

# 顺序合并
full_chain = map_chain | synthesis_prompt | llm | StrOutputParser()
```
- 开发者**显式定义**哪些链并行
- 清晰可控，适合复杂自定义工作流

### Google ADK（声明式 ParallelAgent + SequentialAgent）
```python
# 3 个并行研究 Agent
parallel_agent = ParallelAgent(
    sub_agents=[researcher_1, researcher_2, researcher_3]
)

# 顺序编排：先并行研究，再合并
pipeline = SequentialAgent(
    sub_agents=[parallel_agent, merger_agent]
)
```
- **声明式**：用 `ParallelAgent` 包裹子 Agent，框架自动并发执行
- 结合 `SequentialAgent` 实现"并行 → 汇总"的经典模式
- 每个 Agent 用 `output_key` 将结果写入共享状态，供后续 Agent 读取

| 维度 | LangChain LCEL | Google ADK |
|------|---------------|-----------|
| 并行方式 | `RunnableParallel` 显式定义 | `ParallelAgent` 声明式 |
| 状态传递 | 字典直接传递 | 通过 `output_key` 写入会话状态 |
| 适用场景 | 精细控制的链式工作流 | 多 Agent 协作系统 |

---

## 六、经典模式：Scatter-Gather

```
输入
  ├── Agent/Chain A ──┐
  ├── Agent/Chain B ──┤ (并行)
  └── Agent/Chain C ──┘
              ↓
         汇总 Agent（顺序）
              ↓
           最终输出
```

这是并行化的最典型结构：**分散执行 → 聚合合并**。

---

## 七、一句话总结

> **并行化通过识别工作流中的独立子任务并发执行，将总时间从"各步之和"压缩为"最慢单步"，是构建高性能 Agent 系统的核心优化手段。**

---

## 参考资料

- [原文章](https://adp.xindoo.xyz/chapters/Chapter%203_%20Parallelization/)
- [LangChain LCEL 文档](https://python.langchain.com/docs/concepts/lcel/)
- [Google ADK 多智能体文档](https://google.github.io/adk-docs/agents/multi-agents/)
- [Python asyncio 文档](https://docs.python.org/3/library/asyncio.html)
