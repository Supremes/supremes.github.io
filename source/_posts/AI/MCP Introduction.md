---
title: MCP（Model Context Protocol）详解
tags:
  - MCP
  - Model Context Protocol
  - AI
  - Claude
  - 协议标准
  - 开发指南
categories:
  - AI
description: 详细介绍MCP（Model Context Protocol）开源标准，包括架构设计、开发指南和企业级应用策略，连接AI应用与外部系统的标准化解决方案
abbrlink: 27915
date: 2025-11-28 14:47:21
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/MCP.webp
---

## What is the MCP?

- MCP (Model Context Protocol) is an **open-source standard** for connecting AI applications to external systems.
- Using MCP, AI applications like Claude or ChatGPT can connect to **data sources** (e.g. local files, databases), **tools** (e.g. search engines, calculators) and **workflows** (e.g. specialized prompts)—enabling them to access key information and perform tasks.
- Think of MCP like a USB-C port for AI applications. Just as USB-C provides a standardized way to connect electronic devices, MCP provides a standardized way to connect AI applications to external systems.



![img](https://mintcdn.com/mcp/bEUxYpZqie0DsluH/images/mcp-simple-diagram.png?fit=max&auto=format&n=bEUxYpZqie0DsluH&q=85&s=35268aa0ad50b8c385913810e7604550)

### Architecture

Key participants in the MCP architecture are:

- **MCP Host**: The AI application that coordinates and manages one or multiple MCP clients
- **MCP Client**: A component that maintains a connection to an MCP server and obtains context from an MCP server for the MCP host to use
- **MCP Server**: A program that provides context to MCP clients

![img](../Pics/WX20251124-172727@2x.png)






#### Data Layer

Defines the [**JSON-RPC**](https://en.wikipedia.org/wiki/JSON-RPC#Implementations) based protocol for client-server communication, including lifecycle management, and core primitives, such as tools, resources, prompts and notifications.

Core Primitives:

- **Tools**: Executable functions that AI applications can invoke to perform actions (e.g., file operations, API calls, database queries)
- **Resources**: Data sources that provide contextual information to AI applications (e.g., file contents, database records, API responses)
- **Prompts**: Reusable templates that help structure interactions with language models (e.g., system prompts, few-shot examples)



#### Transport Layer

Defines the communication mechanisms and channels that enable data exchange between clients and servers, including transport-specific connection establishment, message framing, and authorization.

- **STDIO** : Uses standard input/output streams for direct process communication between **local processes** on the same machine, providing optimal performance with no network overhead.
- **Server-Sent Events (SSE)** : This approach required two separate endpoints:
  1. An SSE endpoint (`/sse`) that established a persistent connection for the client to receive responses
  2. A separate messages endpoint (`/sse/messages`) where clients would send request
- **Streamable HTTP** : Offers a more elegant solution by enabling **bidirectional communication through a single endpoint**. 



![img](https://picx.zhimg.com/50/v2-987260a35809fece3edb804df7691c0a_720w.jpg?source=2c26e567)



##  Develop a MCP Server

1. Integrate MCP SDK
2. Develop tools/resources/prompts as your business needs
3. Debug it with MCP Inspector








