---
updated: 2026-06-04 23:04
title: PI - 最轻量的agent
---

---

## PI 架构 — 四层依赖链（从上到下）

### Layer 4 · `@earendil-works/pi-coding-agent`
用户直接交互的 CLI 层。
- **Run Modes**：Interactive（TUI 对话）、Print（`-p` 单次）、RPC（进程间通信）、SDK（嵌入式调用）
- **Core Services**：session-manager、event-bus、settings、model-registry、compaction、extensions、skills
- **Built-in Tools**：`read` / `write` / `edit` / `bash` / `grep` / `find` / `ls`，外加 Extensions（YAML/JS 自定义工具）和 MCP/HTTP 外部工具分发
- **Session Features**：compaction（上下文压缩）、export-html、diagnostics、output-guard

### Layer 3 · `@earendil-works/pi-tui`
终端 UI 库，差量渲染。
- Terminal Engine（差量 ANSI 渲染）、Editor Component（undo-stack / kill-ring）、UI Components（chat、spinner、code-block…）、Autocomplete + Theme 系统

### Layer 2 · `@earendil-works/pi-agent-core`
有状态 Agent 运行时。
- **Agent Loop**：ReAct 风格（observe → think → act → repeat），工具调用 streaming
- **Agent State**：消息历史、工具注册与分发、AsyncIterable 事件流、context transforms
- **Harness/Node**：子 agent 生成、进程隔离、proxy. ts RPC 桥接

### Layer 1 · `@earendil-works/pi-ai`
底层统一 LLM API，无内部依赖。
- **Unified API Core**：stream. ts（SSE）、types. ts、models. generated. ts（脚本生成）
- **Providers**：OpenAI（Responses/Completions）、Anthropic、Google（Gemini/Vertex）、Azure、Amazon Bedrock、Mistral、Cloudflare、GitHub Copilot、Faux（测试用）

---

**数据流**：`User prompt → coding-agent（session/tools）→ agent-core（ReAct loop）→ pi-ai（provider）→ LLM API → stream 回路`