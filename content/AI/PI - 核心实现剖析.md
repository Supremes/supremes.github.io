---
updated: 2026-08-21 15:21
title: PI - 核心实现剖析
---

# 全流程

![img](../Assets/PI-输入到输出的全流程.svg)

## Trace 和 Turn 定义

Trace: Agent一次完整运行

Turn：模型一次调用及相关的工具调用

![img](../Assets/PI-trace-turn-nesting.svg)

## 事件机制：十种事件类型 - 事件观察类

PI通过**发布-订阅**模式实现了事件驱动，这也是PI扩展实现的核心之一。

![img](../Assets/PI-十种事件定义.svg)

## 工具调用

不能直接调用，因为LLM的输出不一定是规矩的，可能会犯这些错误：参数格式不对、类型错误、危险操作等

- 参数预处理：补默认值、类型修正
- Schema验证
- toolcall before钩子
- tool execute
- toolcall after钩子

![img](../Assets/PI-ToolCallDesign.svg)

## 上下文压缩

- **触发方式**：包括 threshold 自动触发、context overflow 恢复和 `/compact` 手动触发；自动触发条件是 `contextTokens > contextWindow - reserveTokens`
- **执行时机**：threshold 通常在一次 Agent 运行结束后的检查点执行；overflow 是例外，会中断失败或被截断的调用，压缩后最多自动重试一次
- **保留策略**：从最新消息向前累计，默认保留最近 `20k` tokens，并预留 `16,384` tokens 给下一次模型响应
- **切点约束**：优先在完整 Turn 边界切分；单个 Turn 过大时可以从 assistant message 处拆分，但不会切在 tool result，避免拆散 tool call 和对应结果
- **生成摘要**：调用 LLM 把较早消息压成结构化 summary；重复压缩时会带上 previous summary，并累计已读取、已修改的文件信息
- **写入 Session**：不删除旧节点，只在 Session Tree 末尾追加 `CompactionEntry`；之后发送给模型的是 `summary + firstKeptEntryId` 之后的近期消息
- **数据性质**：对模型上下文是有损压缩，对本地 JSONL 历史是无损保存；生成摘要本身也会消耗 token 和 cost
- **扩展入口**：`session_before_compact` 可以取消压缩或提供自定义结果，完成和失败分别触发 `session_compact`、`session_compact_failed`

## Session 会话管理

- 使用 jsonl 文件本地化管理，提供了持久化的接口，但默认未实现，纯本地化管理
- 树型结构：支持回退、分支和重试
- append-only：移动指针创建新节点，绑定到父节点上，“认父不认子”可以让追加操作不修改任务旧节点

![img](../Assets/PI-SessionTree.svg)

## 扩展机制

PI 的扩展不是继承 `Agent` 或改写主循环，而是通过**两阶段绑定 + 事件中间件**，把外部能力挂到 `AgentSession` 周围。

- **发现与加载**：`ResourceLoader` 汇总全局、项目、CLI 和 SDK inline 扩展；项目扩展受 trust gate 控制；`jiti` 直接加载 TypeScript，并等待 default factory 执行完成
- **声明注册**：factory 接收 `ExtensionAPI`。`pi.on()`、`registerTool()`、`registerCommand()` 等只把声明写入当前 `Extension` 的 Map；Core action 此时仍是未绑定的 stub，Provider 注册先进入队列
- **Core 绑定**：服务和 `ExtensionRunner` 拿到真实的 Session、Model、Tool、UI 操作后，注入 runtime、flush Provider 队列，并把扩展工具包装成 `AgentTool` 合并进工具注册表
- **运行时拦截**：`AgentSession` 在 prompt、context、tool、message、turn、session 等节点发事件；`ExtensionRunner` 按加载顺序串行调用 handler，把上一个扩展的修改交给下一个，因此可以注入上下文、修改 system prompt、阻断 tool call 或改写 tool result
- **状态与 reload**：扩展用 `appendEntry()` 把自定义状态写入 Session JSONL；`/reload` 先触发 `session_shutdown`，再 invalidate 旧 runtime 并重建，避免旧 `ctx` 继续操作新 Session
- **安全边界**：Extension 与 PI 在同一进程、拥有完整系统权限，不是 sandbox，只能加载可信代码

![img](../Assets/PI-ExtensionMechanism.svg)

- extension 目录：类似 Java 的 classpath，解决“去哪里找到插件”
- jiti ：类似 ClassLoader，解决“怎么加载 TypeScript 模块”
- `registerTool ()` 、` pi. on () ` ：类似 Spring 注册 Bean、Listener 或 Interceptor
- `ExtensionRunner` ：类似 Spring 容器，负责保存注册项并在合适时机调用
- ExtensionAPI  和事件  ctx ：属于 DI，PI 把扩展需要的依赖传进去