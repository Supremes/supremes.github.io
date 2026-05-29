---
title: "MCP 协议：AI Agent 工具集成的 USB-C 接口"
date: "2026-05-27"
tags: "MCP,AI Agent,工具集成,协议,标准化"
summary: "MCP（Model Context Protocol）是 AI 应用连接外部系统的开源标准协议。理解 MCP 是构建生产级 AI Agent 的必备知识。"
---

## MCP 是什么？

MCP（Model Context Protocol，模型上下文协议）是一个开源标准协议，用于将 AI 应用连接到外部系统。

一个类比：

```
USB-C 之于电子设备 = MCP 之于 AI 应用

USB-C：一个接口连接所有设备（显示器、存储、充电）
MCP：一个协议连接所有系统（数据库、API、文件系统）
```

**核心价值：** 一次构建，处处集成（Build once, integrate everywhere）。

## MCP 支持的三大能力

```
┌─────────────────────────────────┐
│           MCP Server            │
├───────────┬───────────┬─────────┤
│  数据源    │   工具     │ 工作流   │
│ Resources │  Tools    │ Prompts │
├───────────┼───────────┼─────────┤
│ 本地文件   │ 搜索引擎   │ 提示词模板│
│ 数据库     │ 计算器     │ 工作流模板│
│ API 数据   │ 代码执行   │ Agent 技能│
└───────────┴───────────┴─────────┘
```

### 1. 数据源连接（Resources）

让 AI 应用访问外部数据：

```json
{
  "uri": "file:///project/src/main.py",
  "name": "主程序源码",
  "mimeType": "text/python"
}
```

### 2. 工具调用（Tools）

让 AI 应用执行操作：

```json
{
  "name": "search_web",
  "description": "搜索互联网",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "搜索关键词" }
    }
  }
}
```

### 3. 工作流模板（Prompts）

预定义的提示词和工作流模板，可复用。

## MCP 架构

```
┌─────────────┐    MCP 协议    ┌─────────────┐
│  MCP Client │ ←───────────→ │  MCP Server │
│  (AI 应用)   │               │  (工具/数据) │
└─────────────┘               └─────────────┘
     ↕                              ↕
┌─────────────┐               ┌─────────────┐
│    LLM      │               │  外部系统    │
│  (模型推理)  │               │ (DB/API/FS) │
└─────────────┘               └─────────────┘
```

**传输方式：**
- **本地：** stdio（标准输入输出）— 适合本地工具
- **远程：** HTTP + SSE — 适合云端服务

## 谁在用 MCP？

### AI 助手
- **Claude** — 原生支持 MCP，Anthropic 是 MCP 的发起者
- **ChatGPT** — 已支持 MCP 集成

### 开发工具
- **VS Code** — 通过扩展支持
- **Cursor** — 原生集成
- **Hermes Agent** — 原生 MCP 客户端

### 生态规模
- 已纳入 **Linux Foundation** 项目
- 数百个开源 MCP Server 可用
- 覆盖数据库、文件系统、云服务、开发工具等

## 开发一个 MCP Server

### Python 示例

```python
from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("my-tools")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="get_weather",
            description="获取天气信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名"}
                },
                "required": ["city"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "get_weather":
        city = arguments["city"]
        weather = await fetch_weather(city)
        return [TextContent(type="text", text=weather)]

# 启动服务器
server.run(transport="stdio")
```

### 配置文件

```json
{
  "mcpServers": {
    "weather": {
      "command": "python",
      "args": ["weather_server.py"],
      "env": { "API_KEY": "your-key" }
    }
  }
}
```

## MCP 对不同角色的价值

| 角色 | 价值 |
|------|------|
| **开发者** | 减少构建 AI 应用的时间和复杂度 |
| **工具提供者** | 通过生态获得更多用户和集成 |
| **终端用户** | 获得更强能力的 AI 应用 |

## Agent Skills：MCP 生态新概念

Agent Skills 是 MCP 生态中的新概念，用于构建可复用的 Agent 能力模块：

```
一个 Skill = 
  触发条件（什么时候用）
  + 执行步骤（怎么做）
  + 验证标准（怎么确认做对了）
  + 陷阱提示（常见错误）
```

Skills 让 Agent 的能力可以被标准化、共享和复用。

## 最佳实践

1. **单一职责** — 每个 MCP Server 专注一个领域
2. **清晰的 Schema** — 工具的输入输出要有明确的类型定义
3. **错误处理** — 返回有意义的错误信息，而非崩溃
4. **安全第一** — 敏感操作需要确认机制
5. **幂等性** — 工具调用应该是幂等的，支持重试

## 总结

MCP 正在成为 AI 工具集成的事实标准。如果你在构建 AI Agent：

> **先看看有没有现成的 MCP Server，再考虑自己造轮子。**

MCP 生态的成熟意味着你不需要从零开始——数据库、文件系统、云服务、开发工具的 MCP Server 大多已经存在。

**官方文档：** https://modelcontextprotocol.io
