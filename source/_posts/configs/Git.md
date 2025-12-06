---
title: Git 学习笔记
date: 2025-12-06 10:47:14
tags:
  - git
categories:
  - 工具效率
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/GIT.webp
sticky:
hidden: false
updated: 2025-12-06 22:04
---
# 🍄 Git 全方位实战手册：从入门到通关

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/git-workflow.webp)

> 核心概念图解 (The Mental Model)
> 
> Git 的操作主要在三个区域流转：
> 
> 1. **工作区 (Working Directory)**：你实际写代码的地方。
>     
> 2. **暂存区 (Staging Area/Index)**：`git add` 后文件存放的地方（准备提交的包裹）。
>     
> 3. **本地仓库 (Local Repository)**：`git commit` 后版本存档的地方。
>     
> 4. **远程仓库 (Remote Repository)**：GitHub/GitLab 等服务器端。

# `git rm --cache <filename>`

>  让 git 停止跟踪某个文件，但是不删除本地的文件

常用语某些“亡羊补牢”的场景，把不该提交的配置文件提到到了 Git，现在需要从仓库中删除，但本地还需要使用，通常配合 `.gitignore` 使用。

#  `.gitignore`

只对 `未被追踪 untracked` 的文件有效，一旦文件之前被 commit 过，git 便会无视该文件的配置，因此需要配合上述 `git rm --cahce` 使用。

# `git restore <filename>`

旧版命令：`git checkout -- <文件名>`

放弃 `工作区` 的修改，用 `暂存区` 覆盖 `工作区`。
- 如果 `工作区` 没有改动，便会直接撤销工作区的改动
- 如果 `工作区` 有改动，便会覆盖

# `git restore --staged <filename>` 

旧命令: `git reset HEAD <filename>``

将文件从 `暂存区` 切换到 `工作区` , 即在执行完 `git add` 命令后，用来撤回。

# `git stash`

## git stash -u
u 参数，会把 untracked files 也一并暂存

## git stash push -m <多个文件名或目录名>
- 旧版：git stash save "stash message"
- 新版：git stash push -m "stash message"

## git stash -p
 交互式命令，可以选择哪些需要暂存

## git stash branch <新分支名>
创建一个新的分支，检出你stash 时的那个 commit，然后应用 stash。这样担心有冲突，就在新分支里解决，不会影响主分支。

---
# `删除分支 - git branch -d`

```bash
# 删除已合并的分支
git branch -d feature-login

# 强制删除未合并的分支 (慎用)
git branch -D feature-login
```

---

# `后悔药 (Undoing Changes) - git restore/reset/revert`

每个人都会犯错，Git 给了你重来的机会。

### 1. 撤销工作区的修改 (未 add)

```Bash
# 丢弃文件的修改，恢复到最近一次 commit 的状态
git restore <file>
# 或者旧版命令：git checkout -- <file>
```

### 2. 撤销暂存区的修改 (已 add，未 commit)

```Bash
# 将文件从暂存区移除，但保留文件内容修改
git restore --staged <file>
# 或者旧版命令：git reset HEAD <file>
```

### 3. 撤销提交 (已 commit) —— **Reset**

这里有三种模式，切记区分：

- **`--soft` (温柔模式)**：撤销 commit，但代码保留在**暂存区**（适合想重新修改 commit message）。
- **`--mixed` (默认模式)**：撤销 commit，代码保留在**工作区**（未 add 状态）。
- **`--hard` (毁灭模式)**：撤销 commit，**删除所有代码修改**，彻底回到过去（慎用！）。

```Bash
# 回退到上一个版本 (保留代码在暂存区)
git reset --soft HEAD^

# 彻底回退到指定版本 (代码全丢，慎用)
git reset --hard <commit-hash>
```

### 4. 安全撤销 —— **Revert**

如果你已经推送到远程仓库，**绝对不要用 Reset**，要用 Revert。它会生成一个新的 commit 来“反向”抵消之前的操作。

Bash

```
git revert <commit-hash>
```

---

# 配置别名 (Aliases)

作为一名熟练工，敲 `git commit` 太慢了。在 `~/.gitconfig` 中添加这些别名，效率起飞。

**推荐配置项:**

- 设置 *git add, commit, push 别名*： `git config --global alias.acp '!f() { git add -A && git commit -m "$1" && git push; }; f'`
	- 示例 : `git acp "修复了一个bug"`
- 设置 *git add, amend no-edit, push -f 别名*: `git config --global alias.amendpush '!git add . && git commit --amend --no-edit && git push -f'`
- 设置  *git log 漂亮的输出*: `git config --global alias.acp log --color --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit`