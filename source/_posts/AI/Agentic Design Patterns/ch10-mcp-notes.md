---
title: '第10章：模型上下文协议 | Model Context Protocol (MCP)'
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

# 模型上下文协议 | Model Context Protocol (MCP)

- **来源 URL**：https://adp.xindoo.xyz/chapters/Chapter%2010_%20Model%20Context%20Protocol%20(MCP)/
- **整理日期**：2026-03-23
- **所属系列**：AI Agent Design Patterns（第10章）

---

## 1. 核心概念

模型上下文协议（Model Context Protocol，MCP）是一个**开放标准**，用于标准化 LLM（如 Gemini、GPT、Claude）与外部应用程序、数据源和工具之间的通信方式。可将其类比为"通用电源插座"——不是给 AI 提供特定工具，而是建立一套任何兼容工具都可以接入、任何兼容 LLM 都可以使用的标准接口体系。基于**客户端-服务器架构**，MCP 定义了数据（资源 Resources）、交互模板（提示 Prompts）和可执行函数（工具 Tools）的公开和访问方式。

---

## 2. 解决什么问题

没有标准化协议时，LLM 与外部工具的集成面临：

- **每次集成都需定制开发**，无法复用，扩展成本极高
- **供应商锁定**：不同 LLM 提供商的工具调用格式各异，切换成本大
- **无法动态发现能力**：智能体必须提前知道所有可用工具，无法运行时探索
- **遗留系统无法融入现代 AI 工作流**，需要昂贵的重写

---

## 3. 工作原理 / 关键机制

### MCP 三要素

| 元素 | 含义 | 示例 |
|------|------|------|
| **资源（Resources）** | 静态数据 | PDF 文件、数据库记录 |
| **工具（Tools）** | 可执行函数 | 发送邮件、查询 API |
| **提示（Prompts）** | 交互模板 | 指导 LLM 与资源/工具交互的结构化模板 |

### 交互流程

```
① 发现：MCP 客户端查询服务器 → 获取可用工具/资源清单
        ↓
② 请求制定：LLM 决定使用某工具 → 生成标准化请求（工具名 + 参数）
        ↓
③ 客户端通信：MCP 客户端将请求转发到对应 MCP 服务器
        ↓
④ 服务器执行：身份验证 → 参数校验 → 调用底层 API/服务
        ↓
⑤ 响应回传：执行结果标准化封装 → 返回客户端 → 更新 LLM 上下文
```

### MCP vs 工具函数调用对比

| 特性 | 工具函数调用 | MCP |
|------|------------|-----|
| 标准化 | 供应商专有，格式各异 | 开放标准，跨 LLM 互操作 |
| 范围 | LLM 直接请求预定义函数 | 广泛框架，定义发现和通信协议 |
| 架构 | 一对一 LLM-工具交互 | 客户端-服务器，一对多 |
| 发现 | 需提前告知可用工具 | 支持**动态发现**可用工具 |
| 可重用性 | 与特定应用紧耦合 | 独立 MCP 服务器可被任何兼容客户端复用 |

### 传输机制

- **本地通信**：STDIO（标准输入/输出）JSON-RPC，适合进程间通信
- **远程通信**：可流式 HTTP + 服务器发送事件（SSE），适合网络部署

---

## 4. 应用场景

1. **数据库集成**：智能体通过自然语言命令查询 BigQuery 等数据库，生成报告或更新记录。
2. **生成媒体编排**：编排涉及 Google Imagen（图像）、Veo（视频）、Chirp 3 HD（语音）、Lyria（音乐）的多媒体工作流。
3. **外部 API 交互**：获取实时天气、股票价格、发送邮件、与 CRM 系统交互。
4. **复杂工作流编排**：组合多个 MCP 服务，实现"从数据库取客户数据 → 生成个性化图像 → 起草邮件 → 发送"全流程自动化。
5. **物联网设备控制**：通过自然语言向智能家居、工业传感器、机器人发送控制命令。
6. **金融服务自动化**：分析市场数据、执行交易、生成财务建议、自动化合规报告。
7. **基于推理的信息提取**：从大量文本中精确提取回答复杂问题的特定条款或数字，超越传统关键字搜索。
8. **遗留系统现代化**：用 MCP 包装器封装遗留 API，使其融入现代 AI 工作流，无需重写底层代码。
9. **自定义工具开发**：通过 FastMCP 快速将内部函数或专有系统暴露为 AI 可用工具。

---

## 5. 框架实现

### Google ADK — 使用本地 MCP 服务器（文件系统）

```python
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

root_agent = LlmAgent(
    model='gemini-2.0-flash',
    name='filesystem_assistant_agent',
    instruction=f'Help the user manage their files in: {TARGET_FOLDER_PATH}',
    tools=[
        MCPToolset(
            connection_params=StdioServerParameters(
                command='npx',
                args=["-y", "@modelcontextprotocol/server-filesystem", TARGET_FOLDER_PATH],
            ),
        )
    ],
)
```

### FastMCP — 创建 MCP 服务器

```python
from fastmcp import FastMCP

mcp_server = FastMCP()

@mcp_server.tool
def greet(name: str) -> str:
    """生成个性化问候语"""
    return f"Hello, {name}! Nice to meet you."

if __name__ == "__main__":
    mcp_server.run(transport="http", host="127.0.0.1", port=8000)
```

FastMCP 优势：
- Python 装饰器快速定义工具
- 自动从函数签名、类型提示、文档字符串生成接口规范
- 支持服务器组合（Composition）和代理（Proxy）高级模式

### Google ADK — 消费 FastMCP 服务器

```python
MCPToolset(
    connection_params=HttpServerParameters(url="http://localhost:8000"),
    tool_filter=['greet']  # 可选过滤器
)
```

---

## 6. 注意事项与权衡

| 方面 | 说明 |
|------|------|
| **API 设计质量决定上限** | MCP 只是包装器，底层 API 若缺乏过滤/排序等功能，智能体效率依然低下 |
| **数据格式兼容性** | MCP 不保证数据对智能体友好（如返回 PDF 而非 Markdown 文本则无意义） |
| **安全性** | 必须实现身份验证和授权，控制客户端访问权限和可执行操作范围 |
| **实现复杂度** | 底层协议复杂，但 FastMCP、Anthropic SDK 等工具大幅简化了开发 |
| **错误处理** | 需要定义工具执行失败、服务器不可用等错误的标准传达方式 |
| **本地 vs 远程部署** | 本地服务器更快更安全；远程服务器支持共享和扩展 |
| **适用场景** | 简单固定工具用函数调用即可；复杂多工具、需要互操作性或动态能力发现时用 MCP |

---

## 7. 一句话总结

> **MCP 是 AI 智能体与外部世界互联的"通用插座标准"**——它通过开放的客户端-服务器协议，让任何兼容 LLM 都能动态发现并使用任何兼容工具，彻底解决了 LLM 与外部系统集成的碎片化和高成本问题，是构建真正"有手有脚"的 AI 智能体的基础设施层。
