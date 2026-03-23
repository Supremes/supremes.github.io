---
title: '第7章：多智能体协作模式 (Multi-Agent Collaboration)'
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

# 第7章：多智能体协作模式 (Multi-Agent Collaboration)

**来源 URL：** https://adp.xindoo.xyz/chapters/Chapter%207_%20Multi-Agent%20Collaboration/  
**整理日期：** 2026-03-23

---

## 核心概念

多智能体协作（Multi-Agent Collaboration）模式将 AI 系统构建为由多个**专门化智能体**组成的协作集合，而非单一的全能智能体。其核心是**任务分解原则**：将高层目标拆解为离散子问题，将每个子问题分配给拥有最适合该任务的特定工具、数据访问或推理能力的智能体。系统的效能不仅来自劳动分工，更依赖智能体间标准化的通信协议，使它们能够交换数据、分配任务、协调行动，从而产生超越任何单个智能体能力的**协同效应**。

---

## 解决什么问题

单体智能体的固有局限：
- **专业深度不足**：单一智能体难以同时精通多个专业领域
- **工具访问受限**：不同任务需要不同的工具集，单体智能体难以兼顾
- **可扩展性差**：增加能力需要重新设计整个智能体
- **单点故障**：一个环节出错影响全局
- **并发能力弱**：复杂任务中不同部分无法同时推进

多智能体架构提供了增强的**模块化、可扩展性和稳健性**——单个智能体故障不必导致整个系统瘫痪。

---

## 工作原理 / 关键机制

### 协作形式分类

| 协作形式 | 描述 | 适用场景 |
|---------|------|---------|
| **顺序交接** | A → B → C，前者输出为后者输入 | 流水线式内容创作、文档处理 |
| **并行处理** | A、B 同时处理不同部分，结果合并 | 多源数据采集、独立子任务分析 |
| **辩论与共识** | 多智能体持不同观点，讨论达成共识 | 决策支持、方案评估 |
| **层次结构** | 管理者智能体委派给工作者智能体并综合结果 | 复杂项目管理、多阶段任务 |
| **专家团队** | 各领域专家（研究员/作家/编辑）协作 | 复杂内容生产、综合报告 |
| **批评者-审查者** | 生成智能体 + 评估智能体（检查政策/安全/质量） | 代码生成、合规检查、研究写作 |

### 通信与交互结构（从简单到复杂）

```
1. 单智能体      → 无交互，自主运行，能力受限
2. 网络（去中心化）→ 点对点通信，弹性强，但协调复杂
3. 监督者        → 中心枢纽协调下属，清晰但存在单点故障
4. 监督者作为工具  → 监督者提供资源/服务，而非直接命令控制
5. 层次化        → 多层监督者结构，适合大规模复杂问题
6. 自定义        → 根据具体需求混合设计，最大灵活性
```

### 关键系统要素

- **角色与职责定义**：每个智能体有明确的专业角色
- **通信渠道**：标准化的信息交换协议
- **任务流与交互协议**：指导协作努力的规则
- **结果综合**：将各智能体输出整合为连贯的最终结果

---

## 应用场景

1. **复杂研究与分析**
   - 研究者智能体搜索学术数据库 → 摘要智能体总结发现 → 趋势识别智能体分析模式 → 综合智能体生成报告
   - 反映人类研究团队的分工协作模式

2. **软件开发**
   - 需求分析智能体 → 代码生成智能体 → 测试智能体 → 文档编写智能体
   - 各角色相互传递输出，协同构建和验证系统组件

3. **创意内容生成**
   - 营销活动：市场研究 + 文案撰写 + 图形设计（调用图像生成工具）+ 社交媒体调度
   - 所有角色并行或顺序协作，最终整合输出

4. **财务分析**
   - 股票数据获取智能体 + 新闻情绪分析智能体 + 技术分析智能体 + 投资建议生成智能体

5. **客户支持升级**
   - 前线支持智能体处理简单查询 → 复杂问题升级给技术专家或计费专家智能体
   - 基于问题复杂性的顺序交接

6. **供应链优化**
   - 供应商、制造商、分销商各由专门智能体代表
   - 协作优化库存水平、物流调度，响应需求变化

7. **网络分析与自动修复**
   - 多智能体协作分类和修复网络故障，建议最佳行动
   - 集成 ML 模型和工具，结合生成式 AI 优势

---

## 框架实现

### CrewAI（顺序协作）

```python
from crewai import Agent, Task, Crew, Process

# 定义专门化智能体
researcher = Agent(
    role='高级研究分析师',
    goal='查找并总结 AI 的最新趋势。',
    backstory="你是经验丰富的研究分析师，擅长识别趋势和综合信息。",
)
writer = Agent(
    role='技术内容作家',
    goal='基于研究发现撰写清晰且引人入胜的博客文章。',
)

# 定义任务（写作任务依赖研究任务）
research_task = Task(description="研究2024-2025年AI中出现的前3个趋势...", agent=researcher)
writing_task = Task(description="基于研究撰写500字博客...", agent=writer, context=[research_task])

# 顺序执行
crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    process=Process.sequential,
    llm=ChatGoogleGenerativeAI(model="gemini-2.0-flash")
)
result = crew.kickoff()
```

### Google ADK（层次化协作）

```python
from google.adk.agents import LlmAgent, BaseAgent, LoopAgent, ParallelAgent, SequentialAgent

# 层次化：协调者委派给子智能体
coordinator = LlmAgent(
    name="Coordinator",
    instruction="当被要求欢迎时，委托给 Greeter；被要求执行任务时，委托给 TaskExecutor。",
    sub_agents=[greeter, task_doer]  # 自动建立父子关系
)

# 并行处理：多智能体同时执行
data_gatherer = ParallelAgent(
    name="data_gatherer",
    sub_agents=[weather_fetcher, news_fetcher]  # 并发运行，结果存入 session.state
)

# 智能体作为工具（Agent as Tool）
image_tool = agent_tool.AgentTool(agent=image_generator_agent)
artist_agent = LlmAgent(tools=[image_tool])  # 父智能体将子智能体当工具调用

# 迭代协作（LoopAgent）
poller = LoopAgent(
    max_iterations=10,
    sub_agents=[process_step, ConditionChecker()]  # 条件检查器决定是否继续
)
```

### 对比

| 维度 | CrewAI | Google ADK |
|------|--------|------------|
| 协调方式 | 顺序/层次（Process.sequential/hierarchical） | Sequential/Parallel/Loop/Hierarchy 原生支持 |
| 通信机制 | 任务 context 参数传递依赖 | session.state 共享状态 |
| 父子关系 | 委派（allow_delegation=True） | sub_agents 参数显式定义 |
| 智能体作为工具 | 间接通过委派 | `AgentTool` 原生支持 |
| 并行支持 | 有限 | `ParallelAgent` 原生支持 |
| 适用生态 | 快速搭建多智能体团队 | Google 云生态深度集成 |

---

## 注意事项与权衡

- **通信开销**：智能体间频繁通信增加延迟和 Token 消耗，需权衡粒度
- **协调复杂性**：随智能体数量增加，协调逻辑指数级复杂（尤其是去中心化网络模型）
- **状态一致性**：多智能体并发访问共享状态时需防止竞态条件
- **监督者单点故障**：集中式监督者模型的致命弱点，需冗余设计
- **调试困难**：多智能体交互难以追踪，需完善日志和可观测性
- **错误传播**：上游智能体的错误输出会影响整个下游链路
- **角色设计至关重要**：角色描述不清晰会导致任务边界模糊和输出不连贯
- **成本叠加**：每个智能体独立调用 LLM，总成本是单智能体的数倍

---

## 一句话总结

> 多智能体协作模式通过将复杂任务分解给专门化智能体协同完成，以增加架构复杂度为代价，换取单体智能体无法企及的专业深度、并发效率和系统鲁棒性——其本质是将"全能但浅薄"的单体思路替换为"专精而协作"的团队思路。
