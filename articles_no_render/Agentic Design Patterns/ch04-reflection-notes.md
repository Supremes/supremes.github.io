---
title: '第4章：反思模式 (Reflection)'
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

# 第4章：反思模式 (Reflection)

**来源 URL：** https://adp.xindoo.xyz/chapters/Chapter%204_%20Reflection/  
**整理日期：** 2026-03-23

---

## 核心概念

反思（Reflection）模式是指智能体在完成初始输出后，对自身工作、输出或内部状态进行评估，并利用该评估迭代改进结果的自我纠正机制。它引入了"生成 → 评估 → 优化"的反馈循环，使智能体从单纯执行指令转向更高层次的问题解决与内容生成。反思可由智能体自我完成（自我反思），也可由专门的评审者智能体辅助完成（生产者-评审者模型），后者因分离关注点而更客观高效。

---

## 解决什么问题

即便采用了提示词链、路由、并行化等复杂工作流，智能体的初始输出依然可能不准确、不完整或未能满足复杂约束。基础工作流缺乏内置的错误识别与修复机制，导致系统直接将次优结果传递给下一步。反思模式通过建立自我纠正反馈回路，让初始响应不再成为最终结果，从而显著提升输出质量。

---

## 工作原理 / 关键机制

反思过程的标准步骤：

```
执行（Generate） → 评估/评审（Evaluate） → 反思/优化（Refine） → [迭代，直到满足停止条件]
```

### 关键架构：生产者-评审者模型

| 角色 | 职责 |
|------|------|
| **生产者智能体（Producer）** | 执行任务，生成初始输出（代码、文章、计划等） |
| **评审者智能体（Reviewer）** | 以独立视角根据预定标准评审产出，提供结构化反馈 |

- 评审者以不同系统提示运行，承担"高级软件工程师"、"事实核查员"等专业角色
- 反馈传回生产者，指导下一轮优化
- 循环重复直到：评审通过（如返回 `CODE_IS_PERFECT`）或达到最大迭代次数

### 反思增强因素
- **对话记忆（第8章）**：保留对话历史，使反思具有上下文连续性，避免重复错误
- **目标监控（第11章）**：目标提供评估基准，监控反馈驱动自适应调整

---

## 应用场景

1. **代码生成与调试**：编写初始代码 → 运行测试/静态分析 → 识别错误 → 修改优化。产出更健壮实用的代码。

2. **创意写作与内容生成**：生成草稿 → 评审流畅性、语气、清晰度 → 重写完善。适用于博客文章、营销文案、诗歌创作。

3. **复杂问题求解**：逻辑谜题/多步推理中，每步评估是否更接近解决方案或引入矛盾，必要时回溯。

4. **摘要与信息综合**：生成摘要 → 与原文关键点比对 → 补充缺失信息或修正不准确之处。

5. **规划与策略**：生成行动计划 → 评估可行性与约束满足 → 修订计划，制定更现实有效的方案。

6. **对话智能体**：审查对话历史，确保响应连贯性，修正误解，提升客服机器人的对话质量。

---

## 框架实现

### LangChain / LangGraph

```python
# 核心模式：使用不同系统提示创建"反思者"角色
reflector_prompt = [
    SystemMessage(content="你是高级软件工程师，评审代码。如果完美回复 'CODE_IS_PERFECT'，否则列出改进点。"),
    HumanMessage(content=f"原始任务：{task}\n代码：{current_code}")
]
critique = llm.invoke(reflector_prompt)

# 迭代循环（max_iterations 控制上限）
# 完整迭代反思需 LangGraph 的状态管理和条件转换
```

- LCEL 适合单次反思周期（生成→评审→优化）
- LangGraph 适合多轮迭代反思（有状态的循环工作流）

### Google ADK

```python
# 生成器-评审者管道
generator = LlmAgent(name="DraftWriter", output_key="draft_text")
reviewer = LlmAgent(name="FactChecker",
    instruction="读取 state['draft_text']，验证事实，返回 {status, reasoning}",
    output_key="review_output")
pipeline = SequentialAgent(sub_agents=[generator, reviewer])

# 迭代反思可使用 LoopAgent + 自定义 ConditionChecker
poller = LoopAgent(max_iterations=10, sub_agents=[process_step, ConditionChecker()])
```

- `SequentialAgent`：实现单轮生成-评审管道
- `LoopAgent`：实现多轮迭代反思，通过 `escalate=True` 退出循环

### 对比

| 维度 | LangChain/LCEL | LangGraph | Google ADK |
|------|---------------|-----------|------------|
| 单轮反思 | ✅ 简单链式调用 | ✅ | ✅ SequentialAgent |
| 多轮迭代 | ❌ 需自定义代码 | ✅ 原生支持 | ✅ LoopAgent |
| 状态管理 | 需手动维护 message_history | 内置 StateGraph | 内置 session.state |
| 停止条件 | 代码中判断 | 图中条件边 | ConditionChecker 事件 |

---

## 注意事项与权衡

- **延迟与成本增加**：每次迭代都可能需要新的 LLM 调用，不适合时间敏感型应用
- **上下文窗口压力**：对话历史随迭代扩展（初始输出+评审+优化），可能超出模型上下文限制
- **API 速率限制风险**：多次迭代可能触发速率限制
- **收益递减**：多轮反思后改进边际效益递减，需合理设置 `max_iterations`
- **评审质量依赖**：反思效果取决于评审者提示质量，提示工程至关重要
- **自我反思偏差**：单智能体自我评审存在"认知盲区"，生产者-评审者分离模型更客观

---

## 一句话总结

> 反思模式通过"生成→评审→优化"的反馈循环，让智能体具备自我纠错能力，在代码生成、内容创作、规划等高质量输出场景中以更高延迟和成本换取显著更优的结果。
