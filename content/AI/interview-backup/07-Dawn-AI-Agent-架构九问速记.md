---
title: Dawn AI Agent 架构九问 · 速记版
date: 2026-08-27
tags:
  - interview
  - agent
  - dawn-ai
  - mcp
  - skills
  - prompt-injection
  - multimodal
  - sandbox
  - ssh
aliases:
  - Dawn AI Agent 九问速答
---

> [!info] 阅读口径
> 本文分析的是本机 `~/projects/github/dawn-ai` 当前 checkout：`feat/backup`，commit `98a62ad`（2026-08-07）。
> 文档写入 `knowledge-base` 的 `main` 分支。以下严格区分：
> - ✅ 已实现
> - ⚠️ 部分实现 / 只是软约束
> - ❌ 未实现
> - 🧭 推荐的生产级方案

> [!tip] 一句话总评
> dawn-ai 已经是一个有 **Tool Registry、Skill progressive disclosure、RAG、Memory、Sub-Agent、SSE 和基础安全门控**的 Spring AI Agent；但 **MCP、真正 sandbox、SSH 远端工作区、多模态自动路由、可靠的 workspace 同步、结构化编辑工具**都还没有落地。

深挖与源码证据见 [[08-Dawn-AI-Agent-架构九问深挖]]。

---

## 九问总览

| # | 问题 | dawn-ai 当前答案 | 面试时最该说的一句 |
|---|---|---|---|
| 1 | MCP 与 Skill | MCP ❌；Skill ✅ | MCP 是标准化连接外部能力，Skill 是按需加载 SOP；两者解决的问题不同 |
| 2 | Prompt injection | ⚠️ 有多层防御，但不是完整安全边界 | 防不住所有注入，关键是让注入即使成功也拿不到权限、secret 和网络出口 |
| 3 | 内置工具与局部替换 | 6 个工具；专用 edit/patch ❌ | 局部替换要做唯一匹配、版本校验、原子写入和 diff，不能只靠 `sed` |
| 4 | 1000 个 MCP | 当前全量工具注入不可扩展 | 先 policy filter，再检索 top-K，最后才按需加载 schema 和连接 server |
| 5 | 文本后再发图片 | 当前仅文本 ❌ | 最省事是始终使用多模态模型；要控成本就用 capability router 自动升级 |
| 6 | Sandbox | ❌，只有宿主机 Bash + 软门控 | `cwd` 不是 sandbox；真正隔离要靠 namespace/seccomp/cgroup/只读文件系统 |
| 7 | Agent 与 Docker | 当前项目本身跑在容器里 | Agent 不应直连 Docker socket，应通过受控的 Executor RPC 调容器 |
| 8 | SSH 远端工作区 | ❌ | 抽象 `WorkspaceProvider` + `CommandExecutor`，SSH 只是一个 transport adapter |
| 9 | 本地与 sandbox 一致性 | ❌，只有 Skill 只读挂载 | 用 base revision + 单写者 + hash/CAS + patch，把同步变成可检测的事务 |

---

# 1. dawn-ai 支持 MCP 和 Skill 吗？

**30 秒回答**：

- **MCP：不支持。** `pom.xml` 没有 MCP client 依赖，Skill 设计文档也明确把 MCP 列为 non-goal。
- **Skill：支持。** 使用 `./skills/{name}/SKILL.md` + YAML frontmatter。
- 启动时由 `SkillLoader` 解析，`SkillRegistry` 扫描并注册。
- system prompt 只常驻 `name + description`；模型匹配后调用 `loadSkillTool`，需要细节再调用 `readSkillResourceTool`。
- 这就是 **progressive disclosure**：先暴露便宜的索引，再按需加载昂贵正文。

```text
SKILL.md
   │ parse
   ▼
SkillRegistry
   │ name + description
   ▼
System Prompt
   │ 命中任务
   ▼
loadSkillTool ──► readSkillResourceTool
```

**区分概念**：

| 能力 | 解决什么问题 |
|---|---|
| MCP | 用统一协议连接外部 tool/resource/prompt server |
| Skill | 把团队 SOP、规范和工作流按需注入 Agent |

---

# 2. 如何防止 prompt injection？

**30 秒回答**：不能承诺“彻底防住”，只能做 defense in depth，并把攻击后的 blast radius 压到最小。

dawn-ai 已有：

- system prompt 明确区分“指令”和“外部数据”。
- Web/RAG 内容用 `<untrusted_external_content>` 包裹，并中和伪造闭合标签。
- Bash 有危险命令 denylist、写操作开关、timeout 和输出上限。
- Skill 资源读取防 `../` 路径穿越。
- 日志中的 API key / `Authorization` 会 mask。

仍缺：

- 真正逐次 HITL approval。
- 容器级 sandbox、网络 egress policy、secret broker。
- Bash 读取的文件内容没有统一 untrusted 包装。
- 外挂 Skill 没有签名和信任治理。
- `ProcessBuilder` 会继承环境变量，网络命令默认开放。

**生产级口诀**：

> **输入分级、权限最小化、参数强校验、危险操作审批、执行进 sandbox、secret 不进上下文、网络默认关闭、全链路审计。**

---

# 3. 内置工具有哪些？局部文本替换怎么做？

## 当前 6 个工具

| Bean 名 | 用途 |
|---|---|
| `bashTool` | 本地非交互 Bash |
| `knowledgeSearchTool` | 内部知识库 RAG |
| `webTool` | Tavily 搜索 / 网页提取 |
| `dispatchSubAgentTool` | 派发 research sub-agent |
| `loadSkillTool` | 加载 Skill 正文 |
| `readSkillResourceTool` | 读取 Skill 子资源 |

注册规则是：位于 `com.dawn.ai.agent.tools`、实现 `Function`、带 `@Description`。调用统一由 `ToolExecutionAspect` 记录 trace 和 metric。

## 局部文本替换

**当前没有专用 edit/patch tool。** `BashTool` 开写权限后可以间接改文件，但它不是可靠的结构化编辑接口。

推荐请求：

```json
{
  "path": "src/main/java/App.java",
  "oldText": "old block",
  "newText": "new block",
  "expectedMatches": 1,
  "expectedSha256": "..."
}
```

推荐算法：

1. 把路径解析到 workspace root，拒绝绝对路径、`..` 和 symlink escape。
2. 读取 UTF-8 文本并验证 `expectedSha256`，防止覆盖并发修改。
3. 精确统计 `oldText`；0 次或不等于 `expectedMatches` 就失败。
4. 写 sibling temp file，保留换行符和权限。
5. `fsync` 后用 atomic rename 替换原文件。
6. 返回 unified diff、旧/新 hash 和实际替换次数。

> [!warning]
> 默认不要用 regex，也不要默默替换全部匹配。多匹配时失败，比改错文件更安全。

---

# 4. 1000 个 MCP 怎么避免上下文爆掉，并选到最合适的 tool？

**错误做法**：把 1000 个 server 的所有 tool schema 全塞给模型。

假设每个 tool schema 300 tokens：

```text
1000 tools × 300 tokens = 300,000 tokens
```

正确做法是多阶段 retrieval：

```text
用户请求
  │
  ▼
Policy Filter：租户 / 权限 / 风险 / modality
  │
  ▼
Server Retriever：1000 个 server → top 10
  │
  ▼
Tool Retriever：候选 tools → top 20
  │
  ▼
LLM Reranker：top 20 → top 3~8
  │
  ▼
按需加载完整 schema + lazy connect server
```

选择依据不只看语义，还要看：

- 用户权限与 tenant。
- 输入 modality。
- tool 的成功率、延迟、成本。
- 是否有副作用、是否需要 approval。
- provider/server 当前健康状态。

dawn-ai 当前会把 `ToolRegistry` 的全部工具名交给 ChatClient，也会把全部描述交给 Planner；Skill 描述虽然有 500-token 截断，但这只是“砍尾巴”，不是检索式选择。

---

# 5. 第一轮文本、第二轮图片，怎么无感自动切模型？

## 最短路径

**始终使用一个同时支持 text + image + tool calling 的多模态模型。**

优点是零迁移、零路由状态；缺点是纯文本请求可能更贵、更慢。

## 成本优化路径

在模型前加 capability router：

```text
Request
  │ MIME / magic bytes / attachments
  ▼
Input Normalizer
  │ required={TEXT, VISION, TOOLS}
  ▼
Capability Router
  ├─ text-only model
  └─ multimodal model
```

第二轮收到图片时，在调用模型**之前**自动升级 session：

1. 检测到 `VISION`。
2. 从 Model Registry 选同时支持 vision、tools、streaming 的模型。
3. 把统一格式的历史消息重放给新模型。
4. 本轮之后把 session pin 到能力更高的模型，避免来回抖动。

dawn-ai 当前 `ChatRequest` 只有 `message/sessionId/topicId`，历史也只存 `role + content` 文本，所以还做不到。

---

# 6. Sandbox 是如何实现的？

**dawn-ai 当前没有真正 sandbox。**

当前 `BashTool`：

- 直接 `ProcessBuilder("/bin/bash", "-c", command)` 跑在宿主机。
- `baseDir` 只是初始 cwd，不限制访问 cwd 外的文件。
- 有 timeout、输出截断、危险命令 denylist、默认禁止部分写命令。
- 网络默认开放，进程继承宿主环境变量。

**生产级 sandbox**至少要有：

- rootless container / gVisor / Firecracker。
- 独立 PID、mount、user、network namespace。
- read-only rootfs + 临时 overlay workspace。
- seccomp / AppArmor。
- CPU、memory、PID、disk、wall-clock 限额。
- 网络默认 deny，需要访问的域名走 egress proxy。
- secret 按任务临时挂载，不进入 prompt，也不继承整套宿主环境。

---

# 7. Agent1 和 Docker 容器之间怎么通信？

dawn-ai 当前没有“Agent1 控制执行容器”的独立架构：

```text
Browser / Client
      │ HTTP POST + SSE
      ▼
app container
  ├── PostgreSQL: postgres:5432
  ├── Redis: redis:6379
  ├── LLM API: HTTP
  └── ./skills:/app/skills:ro
```

如果要让 Agent 控制 sandbox container，推荐：

- Agent 只发结构化 `ExecuteRequest`。
- Sandbox Manager 持有 Docker/containerd 权限。
- 两者通过 gRPC/HTTP/Unix socket 传输。
- stdout/stderr/status 以事件流返回。
- **绝不把 `/var/run/docker.sock` 直接暴露给模型进程。**

---

# 8. SSH 远端工作区与远端执行怎么做？

**dawn-ai 当前未实现 SSH。**

推荐统一抽象：

```java
interface WorkspaceProvider {
    Workspace prepare(TaskSpec task);
    ChangeSet collectChanges(Workspace workspace);
}

interface CommandExecutor {
    ExecutionHandle execute(CommandSpec command);
    void cancel(String executionId);
}
```

实现三套 adapter：

- `LocalWorkspaceProvider`
- `ContainerWorkspaceProvider`
- `SshWorkspaceProvider`

SSH 侧要做：

- strict host key verification。
- 短期证书或最小权限 key。
- 固定 remote root，禁止任意路径。
- persistent channel / remote runner 支持流式输出、取消和断线恢复。
- rsync/SFTP 只传 delta。
- secret 由远端 runner 按句柄获取，不放进模型消息。

---

# 9. 如何保证 sandbox 与本地 workspace 状态一致？

**核心不是“多同步几次”，而是先定义一致性模型。**

| 模式 | 一致性 | 适用场景 |
|---|---|---|
| Bind mount | 同一文件系统，变更立即可见；并发冲突风险高 | 单机、低隔离 |
| Git worktree / snapshot | 任务内 snapshot isolation，结束时合并 patch | Coding Agent 首选 |
| SSH remote | 最终一致，需要 hash/CAS 检测冲突 | 远端构建、算力机 |

必须有五个机制：

1. `baseRevision`：任务开始时记录 commit + dirty diff/hash。
2. 单写者 lease：同一 workspace 同时只允许一个 writer。
3. 每次写入带 `expectedHash`，不一致就报 conflict。
4. 变更统一表示成 patch / change set。
5. apply 前验证，失败可 rollback，不能静默覆盖。

推荐状态机：

```text
PREPARING
   ↓
READY(baseRevision)
   ↓
DIRTY
   ↓
VERIFYING
   ├─ conflict ─► CONFLICT
   └─ pass ─────► APPLYING ─► COMMITTED
                         └──► ROLLED_BACK
```

---

## 最终背诵版

> dawn-ai 当前有本地 Tool Registry 和 Skill progressive disclosure，但没有 MCP。安全上做了不可信内容标记、Bash 门控和路径穿越防御，不过 cwd、denylist 和 prompt 都不等于 sandbox。要扩到 1000 个 MCP，必须把 tool discovery 变成 policy filter + semantic retrieval + lazy schema loading。多模态最简单是统一用多模态模型，成本敏感时再做 capability router。执行侧统一抽象 local/container/SSH executor，workspace 用 worktree snapshot、hash/CAS 和 patch 保证可回滚的一致性。
