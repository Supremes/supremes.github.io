---
title: '第1章：Prompt Chaining 学习笔记'
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

# Prompt Chaining 学习笔记

> 来源：https://adp.xindoo.xyz/chapters/Chapter%201_%20Prompt%20Chaining/
> 整理日期：2026-03-23

---

## 一、什么是 Prompt Chaining

**提示词链**（Prompt Chaining，也称 Pipeline 模式）= 将复杂任务拆分为多个小步骤顺序执行，每步的输出作为下一步的输入。

本质上是"分而治之"策略在 LLM 工程实践中的落地。

---

## 二、为什么不用单一 Prompt？

单一复杂 prompt 存在以下问题：

- **指令忽略**：LLM 的 attention 有限，任务越多越容易"偷懒"忽略部分指令
- **上下文偏离**：模型失去对初始上下文的追踪
- **错误传播**：早期错误被放大
- **幻觉增加**：认知负荷增加导致生成错误信息

---

## 三、Prompt Chaining 的真正价值

> ⚠️ 缩短每步 prompt 长度只是副产品，**真正价值在于在 LLM 调用之间插入确定性控制**。

### 1. 🔍 中间验证 / 过滤
Step 1 的输出可以被代码逻辑检查、拒绝、重试，再喂给 Step 2。  
单一 prompt 做不到这点——错误只会静默传播放大。

### 2. 🔧 外部工具调用
Step 1 输出 → 查数据库 / 调 API / 执行计算器 → 结果喂给 Step 2。  
这是 LLM 本身无法内嵌的能力。

### 3. 🎭 专业化角色切换
每一步可以用完全不同的 system prompt：  
「你是市场分析师」→「你是数据提取专家」→「你是文档撰写者」  
不同角色对同一信息的处理方式不同。

### 4. 🌿 条件分支 / 路由
基于 Step 1 的输出，**代码决定**走 Step 2a 还是 Step 2b。  
这是编排器（Orchestrator）的核心价值。

### 5. 🧠 突破 LLM 注意力瓶颈
即使 context window 够大，同时处理 10 个任务也会导致质量下降。  
强制每步只做一件事，是绕过这个弱点的工程手段。

---

## 四、关于并发与顺序的关系

顺序依赖确实牺牲了并发，但实际系统是**混合模式**：

```
用户请求
    ↓
Step 1（顺序：理解意图）
    ↓
Step 2a ──┐
Step 2b ──┤  ← 并发（独立子任务）
Step 2c ──┘
    ↓
Step 3（顺序：汇总合并）
    ↓
输出
```

**链处理有依赖关系的部分，并发处理独立部分，编排器决定哪些步骤并行。**

---

## 五、7 大应用场景

| 场景 | 示例链路 |
|------|---------|
| 信息处理 | 提取 → 总结 → 实体识别 → 报告生成 |
| 复杂问答 | 拆解子问题 → 分别检索 → 综合答案 |
| 数据提取 | OCR → 规范化 → 外部计算 → 结构化输出 |
| 内容生成 | 构思 → 大纲 → 分段起草 → 润色 |
| 对话智能体 | 多轮对话状态维护 |
| 代码生成 | 伪代码 → 初稿 → Review → 完善 → 文档 |
| 多模态推理 | 图像 / 文本 / 表格分阶段处理 |

---

## 六、结构化输出的重要性

步骤之间传递的数据质量至关重要。推荐使用 **JSON / XML** 等结构化格式，避免自然语言歧义导致下游步骤失败。

---

## 七、扩展：上下文工程（Context Engineering）

比提示工程更高级——不只优化 prompt 措辞，而是系统地为 LLM 构建完整信息环境：

- **系统提示**：定义 AI 的操作参数和角色
- **检索文档**：从知识库主动获取信息
- **工具输出**：调用外部 API 获取实时数据
- **历史状态**：用户身份、交互历史、环境状态

> 核心原则：即使是高级模型，在提供有限或构建不良的操作环境时也会表现不佳。

---

## 八、一句话总结

> **Prompt Chaining 的本质是：用确定性代码逻辑掌控非确定性 LLM 的执行流程，而不是让一个 LLM 独自扛下所有不确定性。**

---

## 参考资料

- [原文章](https://adp.xindoo.xyz/chapters/Chapter%201_%20Prompt%20Chaining/)
- [LangChain LCEL 文档](https://python.langchain.com/v0.2/docs/core_modules/expression_language/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/techniques/chaining)
