---
title: '第16章：资源感知优化 / Resource-Aware Optimization'
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

# 第16章：资源感知优化 / Resource-Aware Optimization

**来源 URL**: https://adp.xindoo.xyz/chapters/Chapter%2016_%20Resource-Aware%20Optimization/  
**整理日期**: 2026-03-23

---

## 核心概念

资源感知优化（Resource-Aware Optimization）使 AI 智能体在运行过程中能够**动态监控和管理计算、时间和财务资源**。与简单的规划（关注动作序列安排）不同，该模式要求智能体在动作执行方面做出实时决策，以便在指定资源预算内达成目标或优化效率。

核心是在"更准确但昂贵的模型"与"更快速、成本更低的模型"之间动态权衡——根据任务复杂度、时间预算和成本约束，智能选择最合适的模型或工具路径。

---

## 解决什么问题

基于 LLM 的应用可能既昂贵又缓慢，为每项任务选择最佳模型通常效率低下：

- 简单问题用大模型 → 浪费资源和金钱
- 复杂任务用小模型 → 质量不达标
- 主模型不可用时 → 服务中断（没有回退机制）
- 静态资源分配无法适应动态负载和任务差异

---

## 工作原理/关键机制

```
用户请求
    ↓
[路由器智能体] ← 分类查询复杂度
    ├── simple（直接回答）→ 快速小模型（如 Gemini Flash / gpt-4o-mini）
    ├── reasoning（逻辑推理）→ 强大模型（如 Gemini Pro / o4-mini）
    └── internet_search（实时信息）→ 搜索 + 大模型（gpt-4o）
    ↓
[批评智能体] → 评估响应质量，反馈改进路由逻辑
    ↓
返回最终响应
```

**关键策略**：
1. **动态模型切换**：根据任务复杂度选择不同大小的 LLM
2. **回退机制（Fallback）**：主模型不可用时自动切换备用模型，确保服务连续性
3. **自适应工具使用**：智能从工具集中选择最经济高效的工具
4. **上下文修剪和摘要**：压缩历史信息，减少 token 消耗
5. **并行化与分布式计算**：将计算负载分布到多处理器
6. **优雅降级**：资源极度受限时以降低能力继续运行，而非完全失败

---

## 应用场景

1. **成本优化的 LLM 使用**：智能体根据预算约束，对复杂任务使用大模型，对简单查询使用小模型（如金融分析师场景：快速报告用 Flash，关键投资决策用 Pro）

2. **旅行规划器分层架构**：高级行程规划（理解复杂需求、逻辑推理）由 Gemini Pro 处理；具体工具调用（查航班、查酒店价格）由 Gemini Flash 执行

3. **延迟敏感操作**：实时系统中选择更快但可能不够全面的推理路径，确保及时响应（如实时客服）

4. **边缘设备部署**：在电力受限环境中优化处理过程，延长电池寿命

5. **服务可靠性回退**：当主要模型因过载或限流不可用时，自动切换到备用模型

---

## 框架实现

### Google ADK

```python
# 两个不同成本的智能体
gemini_pro_agent = Agent(
    name="GeminiProAgent",
    model="gemini-2.5-pro",  # 复杂查询
    description="高能力智能体，用于复杂问题",
)
gemini_flash_agent = Agent(
    name="GeminiFlashAgent",
    model="gemini-2.5-flash",  # 简单查询
    description="快速高效智能体，用于简单问题",
)

# 路由器智能体：按查询长度/复杂度分发
class QueryRouterAgent(BaseAgent):
    async def _run_async_impl(self, context):
        query_length = len(user_query.split())
        if query_length < 20:
            # 路由到 Flash
        else:
            # 路由到 Pro
```

### OpenAI / 自定义路由

```python
def classify_prompt(prompt) -> {"classification": "simple|reasoning|internet_search"}

def generate_response(prompt, classification):
    if classification == "simple":
        model = "gpt-4o-mini"
    elif classification == "reasoning":
        model = "o4-mini"
    elif classification == "internet_search":
        model = "gpt-4o"  # + Google Search 结果
```

### OpenRouter

提供统一 API 端点，支持顺序模型回退（`models` 数组依次尝试）：

```json
{
  "models": ["anthropic/claude-3.5-sonnet", "gryphe/mythomax-l2-13b"]
}
```

---

## 注意事项或权衡

| 权衡点 | 说明 |
|--------|------|
| 分类准确性 | 路由器分类错误会导致大任务用小模型（质量差）或小任务用大模型（浪费） |
| 额外延迟 | 先分类再路由引入额外的处理延迟 |
| 路由器成本 | 路由器本身也消耗计算资源，需要控制其复杂度 |
| 回退质量下降 | 降级到备用模型时响应质量可能不如主模型 |
| 维护复杂度 | 多智能体架构增加系统复杂度和运维成本 |

---

## 一句话总结

> 资源感知优化通过"路由器智能体"将请求动态分发到成本/性能最优的模型，用批评智能体持续改进路由质量，在资源约束下实现最优性价比。
