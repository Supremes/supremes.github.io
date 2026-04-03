---
title: '第5章：工具使用模式 (Tool Use)'
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

# 第5章：工具使用模式 (Tool Use)

**来源 URL：** https://adp.xindoo.xyz/chapters/Chapter%205_%20Tool%20Use/  
**整理日期：** 2026-03-23

---

## 核心概念

工具使用（Tool Use）模式通过**函数调用（Function Calling）**机制，让 LLM 驱动的智能体能够突破训练数据的局限，与外部 API、数据库、服务进行交互，甚至执行代码。其核心思想是：LLM 负责**推理决策**（判断何时调用何种工具、传递什么参数），外部函数负责**执行操作**（实际访问现实世界）。"工具"概念比"函数调用"更宽泛——工具可以是 API 端点、数据库查询，甚至是向另一个专业智能体发出的指令，使智能体成为跨多样化数字资源和智能实体的编排者。

---

## 解决什么问题

纯 LLM 的固有局限：
- 训练数据存在截止日期，无法获取实时信息（如天气、股价）
- 无法执行确定性计算（数学运算需精确，非概率生成）
- 无法主动与外部系统交互（发邮件、控制 IoT 设备、写数据库）
- 无法访问用户特定的私有数据

工具使用模式打通了 LLM 推理能力与外部世界之间的桥梁，将语言模型从文本生成器转变为能够**感知、推理并在数字/物理世界中行动**的真正智能体。

---

## 工作原理 / 关键机制

```
用户请求
    │
    ▼
[LLM 决策] ──── 不需要工具 ────→ 直接生成响应
    │
    │ 需要工具
    ▼
[生成工具调用] → 结构化 JSON（工具名 + 参数）
    │
    ▼
[框架拦截执行] → 调用实际外部函数
    │
    ▼
[获取工具结果（Observation）]
    │
    ▼
[LLM 处理结果] → 生成最终响应 或 决定调用下一个工具
```

### 工具定义的关键要素
1. **函数名称**：让 LLM 识别何时使用
2. **功能描述**：让 LLM 理解该工具的用途（质量直接影响工具选择准确性）
3. **参数规格**：参数名、类型、描述，LLM 从用户请求中提取对应值

### 工具调用 vs 函数调用
- **函数调用（Function Calling）**：精确描述调用预定义代码函数的机制
- **工具调用（Tool Use）**：更宽泛概念，包括 API 端点、数据库查询、向其他智能体发指令，体现智能体作为编排者的全部潜力

---

## 应用场景

1. **实时信息检索**
   - 天气智能体：用户问"伦敦天气？" → LLM 调用天气 API → 返回格式化响应
   - 新闻/金融数据：获取训练数据截止日期后的最新信息

2. **数据库与 API 交互**
   - 电商智能体：查询库存状态、订单状态、处理支付
   - 企业系统集成：ERP、CRM 数据的读写操作

3. **精确计算与数据分析**
   - 金融智能体：调用股价 API + 计算器工具 → 精确计算盈亏
   - 数据分析：调用统计库、图表工具处理数据

4. **发送通信与触发操作**
   - 个人助理：根据用户指令发送邮件、创建日历事件
   - 工作流自动化：触发各类业务系统操作

5. **执行代码**
   - 编码助手：运行代码片段验证功能，分析执行结果
   - 数学问题求解：编写 Python 代码进行精确计算

6. **控制外部设备**
   - 智能家居智能体：通过 API 控制灯光、温控、安防设备

---

## 框架实现

### LangChain

```python
from langchain_core.tools import tool as langchain_tool
from langchain.agents import create_tool_calling_agent, AgentExecutor

@langchain_tool
def search_information(query: str) -> str:
    """提供有关给定主题的事实信息。"""
    # 工具实现逻辑
    return result

tools = [search_information]
agent = create_tool_calling_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, verbose=True, tools=tools)
response = await agent_executor.ainvoke({"input": query})
```

- 用 `@langchain_tool` 装饰器将 Python 函数注册为工具
- `create_tool_calling_agent` 将 LLM、工具、提示词绑定
- `AgentExecutor` 负责执行循环（调用 LLM → 执行工具 → 返回结果）

### CrewAI

```python
from crewai.tools import tool

@tool("Stock Price Lookup Tool")
def get_stock_price(ticker: str) -> float:
    """获取给定股票代码的最新模拟股票价格。"""
    return simulated_prices.get(ticker.upper())

financial_analyst_agent = Agent(
    role='高级财务分析师',
    tools=[get_stock_price],
    ...
)
```

- 工具以 `@tool` 装饰器定义，智能体在 `tools` 参数中接收工具列表
- 工具返回原始数据（如浮点数），由智能体决定如何呈现

### Google ADK

ADK 提供**原生集成工具库**，无需手动封装：

```python
# Google 搜索（预构建工具）
from google.adk.tools import google_search
root_agent = Agent(
    model="gemini-2.0-flash-exp",
    tools=[google_search]
)

# 代码执行（内置代码解释器）
from google.adk.code_executors import BuiltInCodeExecutor
code_agent = LlmAgent(
    model="gemini-2.0-flash",
    code_executor=BuiltInCodeExecutor(),
)

# 企业搜索（Vertex AI Search）
vsearch_agent = agents.VSearchAgent(
    datastore_id=DATASTORE_ID,
    model="gemini-2.0-flash-exp",
)

# 智能体作为工具（Agent as Tool）
image_tool = agent_tool.AgentTool(agent=image_generator_agent)
artist_agent = LlmAgent(tools=[image_tool])
```

### 对比

| 维度 | LangChain | CrewAI | Google ADK |
|------|-----------|--------|------------|
| 工具定义方式 | `@langchain_tool` 装饰器 | `@tool` 装饰器 | 原生工具库 + 函数 |
| 预构建工具 | 社区工具包丰富 | 有限 | Google Search、代码执行、Vertex Search |
| 智能体作为工具 | 通过自定义实现 | 通过委派 | `AgentTool` 原生支持 |
| 企业级工具 | 需第三方集成 | 需第三方集成 | Vertex Extensions（自动执行） |
| 异步支持 | `ainvoke` | 有限 | `run_async` 原生支持 |

**Vertex Extensions vs 工具调用关键区别**：Vertex AI 扩展由平台**自动执行**，工具调用需**客户端手动执行**，前者更适合企业级无服务器场景。

---

## 注意事项与权衡

- **工具描述质量至关重要**：描述不清会导致 LLM 错误决策（该用哪个工具、传什么参数）
- **安全风险**：智能体可以触发真实操作（发邮件、写数据库），需严格权限控制和参数校验
- **错误处理**：工具执行可能失败（API 超时、无效参数），需明确错误处理策略并在工具描述中说明
- **幻觉参数**：LLM 可能编造不存在的参数值，调用时需验证
- **成本与延迟**：每次工具调用增加一次网络往返，多工具链式调用延迟可观
- **工具数量限制**：过多工具会使 LLM 决策困难，建议按角色分组或使用工具路由
- **循环风险**：智能体可能陷入无限工具调用循环，需设置最大步骤数

---

## 一句话总结

> 工具使用模式通过函数调用机制让 LLM 能够与外部世界交互，是将语言模型从文本生成器升级为真正智能体的核心基础模式——LLM 负责"想"，工具负责"做"。
