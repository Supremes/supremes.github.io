---
title: MCP（Model Context Protocol）详解
date: 2025-11-28 14:47:21
tags:
  - MCP
  - Model Context Protocol
  - AI
  - Claude
  - 协议标准
  - 开发指南
categories:
  - 学习笔记
  - AI
description: 详细介绍MCP（Model Context Protocol）开源标准，包括架构设计、开发指南和企业级应用策略，连接AI应用与外部系统的标准化解决方案
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



## Company Policy for MCP Usage

#### Data

- **Customer Data**  You may not use customer data in AI systems without confirming that we are
  contractually and legally allowed to do so. In the absence of such contractual or other legal rights,
  you must secure customer instruction to use their data in AI systems.
- **Company Data:** Company data is classified according to the Company’s Information Classification &
  Handling Policy.
  - Public / Non-Confidential Information. You may use public Company data in AI systems.
  - Confidential Information. You may not use Confidential Information to train any AI model. In
    addition, the following rules regarding the different tiers of Confidential Information apply:
    - Confidential: Low. You may use confidential: low Company data with an articulated
      legitimate business need.
    - Confidential: Restricted. You may not use restricted Company data in AI systems
      without your ELT member’s approval.
    - Confidential: Highly Restricted. You may not use highly restricted Company data in AI
      systems without your ELT member’s sign-off and the CLAO’s review and approval.
- **Third Party Data**: For other third party (e.g., partner, vendor, public) data, you may be able to leverage
  such data for use in AI systems, provided that you have an appropriate contractual agreement in
  place with the third party data owner that affords the Company rights to use such data sets. If you are
  unsure as to whether we have such contractual rights, you may contact the Legal-Commercial team
  via AskLegal@cloud.com.
- **Synthetic Data:** You may use synthetic/fake data in AI systems/model training, POCs, and testing.



CSG Approved MCPs

![img](../Pics/WX20251124-172550@2x.png)

Guideline for using MCP in CSG

https://docs.google.com/document/d/10x2_jw_C3MCK9m62C3LcSGPflhqiByf4rNf2y_9kvIw/edit?tab=t.0

1. **CSG Hosted MCP Servers (Internal):** Must be internal, have RBAC, not send CSG data to third parties, and use a CSG-approved AI model (Contact Adam Mongiovi).
2. **Third-Party Hosted MCP Servers (External):** Must use a vendor with an existing CSG trust relationship (verified with Adam Mongiovi), have RBAC, and access only approved context.
3. **MCP Servers for Customer Usage (Customer-Facing):** Must be reviewed by the ProdSec team (Contact Mohan Sekar), prevent customers from accessing private CSG data, be multi-tenant aware, and support RBAC controls.







