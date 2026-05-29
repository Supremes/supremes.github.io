---
title: "从零构建 AI Agent 实战指南"
date: "2026-05-27"
tags: "AI Agent,实战教程,Python,LLM,Function Calling"
summary: "手把手教你从零构建一个完整的 AI Agent，涵盖核心循环、工具集成、错误处理和生产部署的关键实践。"
---

## 什么是 AI Agent？

一句话定义：

> **AI Agent = LLM + 工具调用 + 决策循环**

与普通的 LLM 对话不同，Agent 能够：
- 自主决定下一步做什么
- 调用外部工具获取信息或执行操作
- 根据结果调整策略
- 多步骤完成复杂任务

## 最小可行 Agent

不需要任何框架，50 行 Python 就能实现一个 Agent：

```python
import json
import openai

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "搜索互联网获取信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    }
]

def search(query: str) -> str:
    """模拟搜索"""
    return f"搜索结果：关于 '{query}' 的信息..."

def run_agent(user_input: str):
    messages = [
        {"role": "system", "content": "你是一个有用的助手，可以使用工具获取信息。"},
        {"role": "user", "content": user_input}
    ]
    
    while True:
        # 调用 LLM
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        
        # 如果 LLM 决定调用工具
        if msg.tool_calls:
            for tool_call in msg.tool_calls:
                func_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                # 执行工具
                result = search(**args)
                
                # 将结果返回给 LLM
                messages.append(msg)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # LLM 认为任务完成，返回最终答案
            return msg.content
```

这就是 Agent 的核心——一个**推理-行动循环**。

## 核心组件详解

### 1. 工具定义

工具是 Agent 与外部世界交互的接口：

```python
# 好的工具定义
{
    "name": "get_stock_price",
    "description": "获取股票实时价格。输入股票代码（如 AAPL、TSLA），返回当前价格。",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "股票代码，如 AAPL"
            }
        },
        "required": ["symbol"]
    }
}
```

**工具定义的黄金法则：**
- 名称要自解释（`get_stock_price` 而非 `func1`）
- 描述要详细（告诉 LLM 什么时候该用这个工具）
- 参数要有类型和描述
- 必填字段要标注

### 2. 工具执行

```python
# 工具注册表
tool_registry = {}

def register_tool(name, func, schema):
    tool_registry[name] = {"func": func, "schema": schema}

def execute_tool(name, arguments):
    if name not in tool_registry:
        return f"错误：工具 {name} 不存在"
    
    try:
        result = tool_registry[name]["func"](**arguments)
        return str(result)
    except Exception as e:
        return f"工具执行失败：{str(e)}"
```

### 3. 错误处理

Agent 必须优雅地处理错误：

```python
MAX_RETRIES = 3

def run_with_retry(messages, tools):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            response = call_llm(messages, tools)
            if response.tool_calls:
                results = execute_tools(response.tool_calls)
                messages.extend(results)
            else:
                return response.content
        except RateLimitError:
            retries += 1
            time.sleep(2 ** retries)  # 指数退避
        except Exception as e:
            return f"抱歉，遇到了错误：{str(e)}"
    
    return "抱歉，多次重试后仍然失败。"
```

## 进阶：添加结构化输出

让 Agent 返回结构化数据：

```python
from pydantic import BaseModel

class AgentResponse(BaseModel):
    answer: str
    confidence: float
    sources: list[str]
    follow_up_questions: list[str]

# 在 system prompt 中指定输出格式
system_prompt = """
请以 JSON 格式回答，包含以下字段：
- answer: 你的回答
- confidence: 置信度 (0-1)
- sources: 信息来源列表
- follow_up_questions: 建议的后续问题
"""
```

## 进阶：添加记忆

```python
class AgentWithMemory:
    def __init__(self):
        self.conversation_history = []
        self.long_term_memory = VectorStore()
    
    def chat(self, user_input: str):
        # 1. 检索相关记忆
        relevant_memories = self.long_term_memory.search(user_input, top_k=3)
        
        # 2. 构建上下文
        context = self.build_context(user_input, relevant_memories)
        
        # 3. 运行 Agent 循环
        response = self.run_agent_loop(context)
        
        # 4. 保存到记忆
        self.conversation_history.append({"user": user_input, "assistant": response})
        self.long_term_memory.add(f"用户问：{user_input}，回答：{response}")
        
        return response
```

## 生产部署清单

### 安全性

```python
# 1. 输入验证
def validate_input(user_input: str) -> bool:
    if len(user_input) > 10000:
        return False
    if contains_injection_attempt(user_input):
        return False
    return True

# 2. 工具权限控制
ALLOWED_TOOLS = {"search", "calculate", "get_weather"}

def can_execute_tool(tool_name: str) -> bool:
    return tool_name in ALLOWED_TOOLS

# 3. 敏感操作确认
SENSITIVE_TOOLS = {"send_email", "delete_file", "make_payment"}

def needs_confirmation(tool_name: str) -> bool:
    return tool_name in SENSITIVE_TOOLS
```

### 可观测性

```python
import logging

logger = logging.getLogger("agent")

def run_agent_with_logging(user_input):
    logger.info(f"Agent 启动，输入：{user_input[:100]}")
    
    step = 0
    while not done:
        step += 1
        logger.info(f"步骤 {step}：调用 LLM")
        
        response = call_llm(messages, tools)
        
        if response.tool_calls:
            for tc in response.tool_calls:
                logger.info(f"调用工具：{tc.function.name}")
                result = execute_tool(tc)
                logger.info(f"工具返回：{result[:200]}")
    
    logger.info(f"Agent 完成，共 {step} 步")
    return final_answer
```

### 成本控制

```python
MAX_TOKENS_PER_SESSION = 100000
MAX_TOOL_CALLS = 20

class CostController:
    def __init__(self):
        self.total_tokens = 0
        self.tool_call_count = 0
    
    def check_budget(self, tokens_used):
        self.total_tokens += tokens_used
        if self.total_tokens > MAX_TOKENS_PER_SESSION:
            raise BudgetExceeded("Token 预算超限")
    
    def check_tool_calls(self):
        self.tool_call_count += 1
        if self.tool_call_count > MAX_TOOL_CALLS:
            raise BudgetExceeded("工具调用次数超限")
```

## 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|------|------|---------|
| 无限循环 | Agent 反复调用同一工具 | 设置最大步数限制 |
| 工具滥用 | 用搜索回答已知问题 | 在 prompt 中明确何时不需要工具 |
| 上下文溢出 | 长对话导致 token 超限 | 压缩历史、使用记忆系统 |
| 错误传播 | 一次错误导致后续全错 | 及时纠错、回退机制 |
| 安全漏洞 | 执行恶意指令 | 输入验证 + 权限控制 |

## 总结

构建 AI Agent 的核心步骤：

```
1. 定义工具（Tools）     → Agent 能做什么
2. 实现决策循环（Loop）  → Agent 怎么思考
3. 添加记忆（Memory）    → Agent 怎么记住
4. 处理错误（Error）     → Agent 怎么应对失败
5. 部署上线（Deploy）    → Agent 怎么安全运行
```

> **最好的 Agent 是简单、可靠、可预测的。** 不要追求花哨的功能，先把核心循环做好。

开始构建吧。从 50 行代码的最小 Agent 开始，逐步添加功能。
