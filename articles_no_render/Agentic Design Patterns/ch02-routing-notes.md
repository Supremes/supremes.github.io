---
title: '第2章：Routing（路由模式）学习笔记'
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

# Routing（路由模式）学习笔记

> 来源：https://adp.xindoo.xyz/chapters/Chapter%202_%20Routing/
> 整理日期：2026-03-23

---

## 一、什么是 Routing

**路由（Routing）** = 在 Agent 系统中引入**条件逻辑**，让系统根据输入或状态，动态决定走哪条执行路径，而不是固定的线性流程。

与 Prompt Chaining 的关系：
- Prompt Chaining 解决"**怎么做**"（顺序执行）
- Routing 解决"**做哪个**"（条件分支）

两者结合，才能构建真正灵活的 Agent 系统。

---

## 二、4 种路由实现方式

| 方式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **LLM 路由** | 提示模型输出分类标签（如 `booker/info/unclear`） | 灵活，理解自然语言 | 有不确定性，延迟较高 |
| **嵌入路由** | 将输入转为向量，与候选路由做语义相似度比较 | 理解语义，适合模糊匹配 | 需要维护嵌入库 |
| **规则路由** | if-else / 关键词匹配 / switch-case | 快速、确定性强 | 灵活性差，难处理模糊输入 |
| **ML 分类器路由** | 监督微调的小模型，路由逻辑固化在权重中 | 低延迟，实时推理不依赖 LLM | 需要标注训练数据 |

> 实际系统常混用多种方式：简单场景用规则，复杂语义用 LLM 或嵌入。

---

## 三、路由在 Agent 系统中的位置

路由可在操作周期的多个节点实现：
- **开头**：对主任务进行分类
- **中间**：处理链中根据中间结果决定下一步
- **子流程中**：从工具集中选择最合适的工具

---

## 四、3 大应用场景

### 1. 人机对话（虚拟助手）
识别用户意图 → 路由到不同处理器：
- 查订单 → 订单数据库子 Agent
- 产品咨询 → 产品目录搜索
- 技术支持 → 故障排查指南或升级人工
- 意图不清 → 澄清子链

### 2. 数据处理管道
传入邮件 / 支持工单 / API 请求 → 按内容/格式分发：
- 销售线索 → 摄入流程
- JSON/CSV → 对应数据转换函数
- 紧急问题 → 升级路径

### 3. 多智能体系统（中央调度器）
研究系统中：路由器决定将任务分配给搜索 Agent / 总结 Agent / 分析 Agent。
AI 编码助手中：识别编程语言和意图（调试/解释/翻译）→ 路由到对应专门工具。

---

## 五、框架实现对比

### LangChain / LangGraph
```python
# 用 RunnableBranch 显式定义分支
delegation_branch = RunnableBranch(
    (lambda x: x['decision'].strip() == 'booker', booking_branch),
    (lambda x: x['decision'].strip() == 'info', info_branch),
    unclear_branch  # 默认分支
)

coordinator_agent = {
    "decision": coordinator_router_chain,  # LLM 输出分类标签
    "request": RunnablePassthrough()
} | delegation_branch
```
- 开发者**手动定义**所有分支条件
- 图结构清晰，适合复杂多步路由

### Google ADK
```python
coordinator = Agent(
    name="Coordinator",
    instruction="分析请求，委托给 Booker 或 Info 智能体。",
    sub_agents=[booking_agent, info_agent]  # 框架自动路由
)
```
- **声明式**：只需定义子 Agent，框架自动用 LLM 决策委托给谁
- 简洁，适合有明确工具集的场景

| 维度 | LangChain/LangGraph | Google ADK |
|------|--------------------|-----------| 
| 路由控制 | 开发者显式定义 | 框架自动处理 |
| 适用场景 | 复杂多步、状态化路由 | 工具集明确、快速开发 |
| 可视化 | 图结构，直观 | 声明式，简洁 |

---

## 六、一句话总结

> **路由让 Agent 从"只会按顺序执行"升级为"能根据上下文智能决策走哪条路"，是构建真正自适应 Agent 系统的关键机制。**

---

## 参考资料

- [原文章](https://adp.xindoo.xyz/chapters/Chapter%202_%20Routing/)
- [LangGraph 文档](https://www.langchain.com/)
- [Google ADK 文档](https://google.github.io/adk-docs/)
