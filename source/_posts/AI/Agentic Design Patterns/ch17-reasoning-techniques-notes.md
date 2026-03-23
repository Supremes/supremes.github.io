---
title: '第17章：推理技术 / Reasoning Techniques'
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

# 第17章：推理技术 / Reasoning Techniques

**来源 URL**: https://adp.xindoo.xyz/chapters/Chapter%2017_%20Reasoning%20Techniques/  
**整理日期**: 2026-03-23

---

## 核心概念

推理技术（Reasoning Techniques）是一套使 AI 智能体能够进行**多步骤逻辑推理和复杂问题解决**的高级方法。核心原则是：**在推理过程中分配更多的计算资源**——给予 LLM 更多处理时间或推理步骤，使其进行迭代改进、探索多种解决方案或利用外部工具。

这些技术使智能体的内部推理过程变得透明可见，将复杂问题分解为可管理的子问题，显著提升准确性、连贯性和鲁棒性。

---

## 解决什么问题

面对复杂问题时，简单的单次 LLM 调用存在以下缺陷：

- 无法处理需要多步推理的复杂问题（多跳查询、逻辑推导）
- 推理过程不透明，难以调试和验证
- 容易在中间步骤出错，且无法自我纠正
- 缺乏与外部工具、实时数据的交互能力
- 对于需要精确计算或代码执行的任务，纯语言模型不足

---

## 工作原理/关键机制

### 1. 思维链（Chain-of-Thought，CoT）

引导 LLM 生成**一系列中间推理步骤**，而非直接给出答案。

```
系统提示词（定义五步推理流程）
    ↓
Thought 1（分析查询）
    ↓
Thought 2（制定搜索方案）
    ↓
Thought 3（模拟信息检索）
    ↓
Thought 4（综合信息）
    ↓
Thought 5（审查和精炼）
    ↓
最终答案
```

实现方式：提供"逐步思考"的少样本示例，或直接指示模型"一步步地思考"。

### 2. 思维树（Tree-of-Thought，ToT）

建立在 CoT 之上，允许 LLM **探索多个推理路径**，形成树状结构。支持回溯、自我纠正和探索替代解决方案，在最终确定答案前评估各种推理轨迹。

### 3. 自我纠正（Self-Correction）

智能体对生成内容进行**内部批判性审查**：
- 起草初稿 → 对照原始要求审查 → 识别弱点 → 提出改进建议 → 生成修订版本
- 这种迭代循环确保输出的准确性和完整性

### 4. 程序辅助语言模型（PALMs）

将 LLM 与符号推理能力结合，允许在推理过程中**生成并执行代码**（如 Python），将精确计算卸载到确定性编程环境。

### 5. ReAct（Reasoning + Acting）

将推理与行动交错执行：

```
思考 → 行动（调用工具）→ 观察（获取结果）→ 思考 → ...（循环）
```

允许智能体与外部工具和环境交互，根据实时反馈调整计划。

### 6. 辩论链（CoD）/ 辩论图（GoD）

**CoD（Chain of Debates）**：多个不同模型协作争辩，类似 AI 委员会，通过集体智慧减少偏见。

**GoD（Graph of Debates）**：将讨论重构为动态非线性网络，论点作为节点，通过识别最稳健的论点集群得出结论。

### 7. 推理扩展定律（Inference Scaling Law）

关键原则：通过增加推理时间的计算投资，可以从相对较小的 LLM 获得优越结果。核心要素：

- **模型大小** vs **推理时间** vs **运营成本**的三角平衡
- 较小模型 + 更多推理步骤，有时优于更大模型 + 简单生成
- "思考预算"：推理期间应用的额外计算步骤

---

## 应用场景

1. **复杂问答（多跳查询）**：需要整合不同来源数据并进行逻辑推理，CoT 引导多步综合

2. **数学问题解决**：将复杂数学问题分解为可解决的组件，结合代码执行进行精确计算（PALMs）

3. **代码调试和生成**：ReAct 模式下自动执行代码、观察错误、迭代修复；自我纠正确保代码质量

4. **战略规划**：ToT 探索多方案后果，ReAct 根据反馈动态调整策略

5. **医疗诊断**：CoT 分步推理症状和检查结果，ReAct 检索外部医学数据库，自我纠正消除逻辑矛盾

6. **法律分析**：分析法律文件和先例，CoD/GoD 通过多模型辩论确保论证严谨性

7. **Deep Research**：自主执行多轮搜索 + 推理 + 知识差距识别 + 再搜索，输出综合研究报告

---

## 框架实现

### Google ADK（PALMs / 工具使用）

```python
from google.adk.code_executors import BuiltInCodeExecutor

coding_agent = Agent(
    model='gemini-2.0-flash',
    name='CodeAgent',
    instruction="您是代码执行专家",
    code_executor=[BuiltInCodeExecutor],
)
```

### LangGraph（DeepSearch 实现）

```python
builder = StateGraph(OverallState)
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)        # 推理 + 知识差距分析
builder.add_node("finalize_answer", finalize_answer)

builder.add_edge(START, "generate_query")
builder.add_conditional_edges("generate_query", continue_to_web_research, ["web_research"])
builder.add_edge("web_research", "reflection")
builder.add_conditional_edges("reflection", evaluate_research, ["web_research", "finalize_answer"])
```

### MASS（多智能体系统搜索，进阶）

自动优化多智能体设计的框架，三阶段优化：
1. 块级提示词优化（各智能体独立）
2. 工作流拓扑优化（影响加权方法）
3. 工作流级联合提示词优化

---

## 注意事项或权衡

| 权衡点 | 说明 |
|--------|------|
| 延迟增加 | 多步推理消耗更多时间，不适合对延迟极其敏感的场景 |
| 成本提升 | 更多推理步骤 = 更多 token = 更高费用 |
| 过度推理风险 | 简单问题套用复杂推理框架会浪费资源 |
| 错误累积 | 链式推理中前期错误可能级联传播 |
| 提示词设计难度 | CoT/ToT 的效果高度依赖提示词质量 |
| ToT 状态空间爆炸 | 树的宽度和深度需要合理控制，否则计算成本极高 |

---

## 一句话总结

> 推理技术通过 CoT、ToT、ReAct 等模式让智能体"慢下来深入思考"，以更多的推理时间换取更高的准确性和可靠性，核心是"推理扩展定律"——适当增加推理计算比单纯增大模型更经济有效。
