---
title: Skill
tags: []
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: false
updated: '2026-03-16 15:36'
abbrlink: 9ffccb73
date: 2026-03-16 15:36:35
categories:
sticky:
---
# Why AI-Assisted Testing Needs an SOP Model

## Overview

Most teams start using AI the same way: open a chat window, describe a problem, and hope for the best. That works for one-off questions — it fails for repeatable delivery work like testing, release validation, and triage, where **consistency actually matters**.

> [!tip] The Real Fix
> The answer is not better prompts. It is a better execution model — one where AI operates *inside* a defined process, not around it.

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/Agent-with-skill.webp)
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/SOP-Demo.webp)

*Figure: An SOP-style AI execution flow for software testing. Each stage has a defined input, a responsible skill, and a verifiable output.*

---

## Skills: The Unit of Repeatable AI Work

A **skill** is a self-contained instruction set that defines how a specific task should be completed — the right steps, the right tools, and the expected outputs. The outcome no longer depends on who wrote the prompt that day.

> [!warning] Without Skills, AI Execution Drifts
> Each team member prompts differently. The model fills gaps with assumptions. Results are inconsistent. Skills eliminate drift by turning intent into a documented, reusable procedure.

### Key Components

| Component | Purpose |
|-----------|---------|
| **Reference** | Loads only context relevant to the current step — keeps the active context window short, focused, and cost-efficient. |
| **Script** | Stores executable commands or static templates locally. The model needs only the declared commands and expected outputs — not full source code. |

### How Skills Are Invoked

> [!info] Two Invocation Modes
> - **Auto-discovery** — The agent detects available skills by reading metadata in each `SKILL.md` file.
> - **Explicit invocation** — Call a skill directly with a slash command (e.g. `/create-test-plan`).

---

## The Three-Layer Architecture

Reliable AI delivery is built from three distinct layers, each with a single, clear responsibility:

```
Custom Agent  +  Multiple Skills  +  Tool Connectivity (CLI / MCP)
```

| Layer | Responsibility | Analogy |
|-------|---------------|---------|
| **Agent** | *Who* the AI is — persona, safety constraints, tone, global behavior. Static and persistent. | Identity card |
| **Skill** | *How* work is done — task steps, API calls, templates, decision logic. Loaded on demand. | Professional license |
| **Tool (CLI / MCP)** | *What* the AI can reach — external services, databases, file systems. | Hands |

> [!abstract] In One Line
> Skills provide the brain. Tools provide the reach. The agent holds them together under a consistent identity.

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/Software%20Testing%20Workflow%20-%20AGENT%2BSKILLS.webp)
*Figure: Agent (left) owns identity and guardrails; Skill (right) owns task execution. The agent persists across sessions; skills are loaded per task.*

---

## Tool Connectivity: Default to CLI, Use MCP When It Earns Its Place

Two dominant patterns exist for agent-to-system interaction: **CLI execution** and **MCP (Model Context Protocol) servers**.

> [!tip] Default Rule
> For most internal delivery automation, **CLI should be the default.** Here is why.

### The Hidden Cost of MCP as a Default

Every MCP tool injects schema into the model's context — tool descriptions, parameter lists, capability declarations. Across a realistic integration set, MCP schemas can consume **30–40% of the usable context window** before any real work begins.

> [!danger] Context Is Not Free
> That overhead compresses the space available for task logic, output, and reasoning. CLIs carry none of it — an agent reads `--help` once and moves on.

### Why CLI-First Wins

- **Zero schema overhead** — command help is read on demand; nothing sits in context permanently.
- **Native composability** — commands chain through pipes exactly as engineers already work.
- **Testability** — CLIs slot directly into CI pipelines and return structured output for deterministic assertions.
- **No service layer** — no server to deploy, monitor, or maintain for local and CI-scoped tasks.

### When MCP Earns Its Place

> [!success] MCP Is Not Wrong — Just Often Overused
> MCP is the right call when:
> - **Governance and shared tool contracts** outweigh raw efficiency — regulated environments (finance, healthcare) where auditability and compliance are non-negotiable.
> - Direct CLI access is unavailable in a **distributed or sandboxed environment**.

### The Team Decision Rule

> [!quote] Decision Heuristic
> Default to CLI. Reach for MCP only when CLI cannot provide the connectivity or governance you need. Either way, capture the execution pattern in a skill so it stays auditable.

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/Software%20Testing%20Workflow%20-%20MCP%20-%20CLI.webp)
*Figure: CLI execution (left) vs MCP integration (right). CLI is lean and direct; MCP adds a justified protocol layer only when centralized access control or cross-service standardization is required.*

---

## Summary

| Principle | What It Means in Practice |
|-----------|--------------------------|
| Skills are the unit of quality | Consistency comes from documented process, not better prompts |
| Layers have single responsibilities | Agent = identity · Skill = procedure · Tool = reach |
| Context is a finite resource | Prefer execution patterns that spend it on work, not overhead |
| CLI-first is the team default | Simpler, faster, more testable — escalate to MCP only when justified |

> [!success] The Goal
> AI that behaves like a reliable team member, not a black box. An SOP-backed skill model is the most direct path to that outcome.
