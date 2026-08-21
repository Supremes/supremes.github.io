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

发生在**两轮对话之间**，不是在对话进行中发生的

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