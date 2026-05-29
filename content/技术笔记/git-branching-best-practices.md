---
title: "Git 分支管理最佳实践"
date: "2026-05-18"
tags: "Git,版本控制,团队协作"
summary: "一个好的 Git 分支策略能让团队协作更顺畅，代码质量更高。本文总结了经过实战验证的分支管理方法。"
---

## 分支模型选择

### Trunk-Based Development（推荐）

适合：持续部署、团队有良好的 CI/CD 和代码审查流程

```
main ─────●─────●─────●─────●─────●─────
           \   /       \   /
            ●           ●
         feature-a   feature-b
```

**核心原则：**
- `main` 分支始终保持可部署状态
- feature 分支生命周期不超过 **2 天**
- 通过 feature flag 控制未完成功能的发布

### Git Flow（传统但仍有价值）

适合：有明确版本发布周期的项目

```
main    ─────●───────────────●────────
              \             /
release        ●───────────●
              /             \
develop ──●──●──●──●──●──●──●──●──●──
           \      /  \      /
            ●    ●    ●    ●
          feature branches
```

## 提交信息规范

好的提交信息是团队协作的基础：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型：**
- `feat` — 新功能
- `fix` — Bug 修复
- `docs` — 文档更新
- `refactor` — 重构
- `perf` — 性能优化
- `test` — 测试相关
- `chore` — 构建/工具

**示例：**

```
feat(auth): 添加 OAuth2 登录支持

- 集成 Google 和 GitHub OAuth
- 添加 token 刷新机制
- 更新用户表结构

Closes #123
```

## 常用 Git 技巧

### 交互式 rebase

整理提交历史，让每个提交都有意义：

```bash
git rebase -i HEAD~5
```

### Cherry-pick

从其他分支选择性地合并提交：

```bash
git cherry-pick <commit-hash>
```

### Bisect

二分查找引入 Bug 的提交：

```bash
git bisect start
git bisect bad          # 当前版本有 Bug
git bisect good v1.0    # v1.0 没有 Bug
# Git 会自动二分，你只需要测试并标记 good/bad
```

## 代码审查要点

1. **关注逻辑正确性**，而非代码风格（交给 linter）
2. **提出建设性建议**，而非单纯的批评
3. **及时响应**，不要让 PR 等超过 24 小时
4. **小 PR 优先**，每个 PR 控制在 400 行以内

## 总结

分支管理没有银弹，选择适合团队的方案最重要。关键是：

> **保持 main 分支健康，提交信息清晰，PR 小而精。**
