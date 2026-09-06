---
title: Coding Agent 工程
date: 2026-09-06
tags: [interview, agent, coding-agent]
---

# Coding Agent 工程

Coding Agent 要完成理解仓库、制定修改、编辑文件、运行验证和交付变更。它的难点不只是生成代码，而是维护工程上下文和反馈循环。

## 复习范围

| 阶段 | 内容 |
|---|---|
| Discover | 仓库规则、依赖、入口、相关代码 |
| Plan | 目标、影响面、验收条件、任务依赖 |
| Edit | 精确修改、patch、结构化工具、冲突处理 |
| Verify | test、lint、build、类型检查、截图 |
| Deliver | diff、commit、PR、风险和回滚 |
| Isolation | worktree、容器、远端工作区 |

## 高频问题

1. Coding Agent 如何快速理解陌生仓库？
2. 为什么要先读再改，读多少才够？
3. `old_string` 精确替换为什么容易失败？
4. 多个 Agent 如何避免同时修改同一文件？
5. 如何让 Agent 验证 UI 改动？
6. AGENTS.md、Skill、MCP 各自放什么？

## 工具设计

至少要有搜索、读取、编辑、执行、诊断和版本控制能力。读取工具返回行号与范围，编辑工具要求精确上下文，执行工具保留退出码和结构化错误。

## 失败模式

- 没读项目规则就开始修改。
- 只修表面症状，没有追调用链。
- 测试失败后反复试错，不更新假设。
- 修改范围过大，夹带无关重构。
- 声称完成，但没有运行验收命令。
- 子 Agent 重复搜索，反而增加成本。

## 项目证据

选一个真实修复，展示初始假设、搜索路径、最小 diff、验证命令和最终结果。最好保留一次错误假设及其修正过程。

## 已有资料

- [Coding Agent 实践](03-Coding-Agent-实践.md)
- [Agent Skill](../Agent/skill.md)
- [Dawn 项目架构九问](07-Dawn-AI-Agent-架构九问速记.md)

## 待补

- [ ] 整理 Coding Agent 工具协议
- [ ] 准备 worktree 并发协作案例
- [ ] 设计仓库级回归评测集
