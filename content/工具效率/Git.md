---
title: Git 学习笔记
tags: [git]
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

# `.gitignore`

只对 `未被追踪 untracked` 的文件有效，一旦文件之前被 commit 过，git 便会无视该文件的配置，因此需要配合 `git rm --cahce` 使用。

## git rm --cache <文件名>

>  让 git 停止跟踪某个文件，但是不删除本地的文件

常用语某些“亡羊补牢”的场景，把不该提交的配置文件提到到了 Git，现在需要从仓库中删除，但本地还需要使用，通常配合 `. gitignore`使用。

# `git stash`

## git stash -u
>  添加u 参数，会把 untracked files 也一并暂存

## git stash push -m <多个文件名或目录名>
- 旧版：git stash save "stash message"
- 新版：git stash push -m "stash message"

## git stash -p
 `交互式命令`，可以选择哪些需要暂存

## git stash branch <新分支名>
创建一个新的分支，检出你 stash 时的那个 commit，然后应用 stash。这样担心有冲突，就在新分支里解决，不会影响主分支。

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

#### git restore <文件名>

旧版命令：`git checkout -- <文件名>`

放弃 `工作区` 的修改，用 `暂存区` 覆盖 `工作区`。
- 如果 `工作区` 没有改动，便会直接撤销工作区的改动
- 如果 `工作区` 有改动，便会覆盖
### 2. 撤销暂存区的修改 (已 add，未 commit)

```Bash
# 将文件从暂存区移除，但保留文件内容修改
git restore --staged <file>
# 或者旧版命令：git reset HEAD <file>
```

#### git restore --staged <文件名>

旧命令: `git reset HEAD <filename>

将文件从 `暂存区` 切换到 `工作区` , 即在执行完 `git add` 命令后，用来撤回。
### 3. 撤销提交 (已 commit) —— **Reset**

这里有三种模式，切记区分：

- **`--soft` (温柔模式)**：撤销 commit，但代码保留在**暂存区**（适合想重新修改 commit message）。
- **`--mixed` (默认模式)**：撤销 commit，代码保留在**工作区**（未 add 状态）。
- **`--hard` (毁灭模式)**：撤销 commit，**删除所有代码修改**，彻底回到过去（慎用！）。

```Bash
# 回退到上一个版本 (保留代码在暂存区)
git reset --soft HEAD~1

# 彻底回退到指定版本 (代码全丢，慎用)
git reset --hard <commit-hash>
```

### 4. 安全撤销 —— **Revert**

如果你已经推送到远程仓库，**绝对不要用 Reset**，要用 Revert。它会生成一个新的 commit 来“反向”抵消之前的操作。

```Bash
git revert <commit-hash>
```

---

# 配置别名 (Aliases)

作为一名熟练工，敲 `git commit` 太慢了。在 `~/. gitconfig` 中添加这些别名，效率起飞。

**推荐配置项:**

```shell
# 设置 git add, commit, push 一系列操作别名
git config --global alias.addpush '!f () { git add -A && git commit -m "$1" && git push; }; f'

# 设置 git add, amend no-edit, push -f 别名:
git config --global alias.amendpush '! git add . && git commit --amend --no-edit && git push -f'
```
示例 : 
- `git amendpush`
-  `git addpush "修复了一个 bug"`

```toml
[alias]
	# 配置漂亮的log输出
    lg = log --graph --pretty=format:'%C(yellow)%h%Creset %s %C(dim green)(%cr)%Creset' --abbrev-commit -5
  ```

---

# `git fixup` — 优雅地修补历史提交

> 开发中经常遇到：刚提交完发现少改了一行、多了个 typo、忘加一个文件。这时候用 `git commit --amend` 只能修改**最近一次**提交，而 `fixup` + `autosquash` 可以精准修补**任意历史提交**。

## 核心流程

修改文件 → git add → git commit --fixup=<目标commit> → git rebase --autosquash

### Step 1：找到要修补的目标 commit

```bash
git log --oneline -10
```

输出示例：
```
a1b2c3d feat: 添加用户登录功能
e4f5g6h fix: 修复数据库连接问题
h7i8j9k refactor: 重构配置模块
```

假设你想修补 `a1b2c3d` 这个 commit。

### Step 2：修改文件并创建 fixup commit

```bash
# 修改需要补充的文件
git add <修改的文件>

# 创建 fixup commit，自动生成 "fixup! <原commit message>" 格式
git commit --fixup=a1b2c3d
```

此时 `git log` 会多一条：
```
x9y8z7w fixup! feat: 添加用户登录功能   ← 新生成的 fixup commit
a1b2c3d feat: 添加用户登录功能
e4f5g6h fix: 修复数据库连接问题
```

### Step 3：使用 autosquash rebase 合并

```bash
# 对目标 commit 的父提交进行 rebase
git rebase --autosquash <目标commit>~1

# 或者如果 fixup 的目标在最近几个 commit 内
git rebase --autosquash HEAD~5
```

Git 会自动将 fixup commit 移动到目标 commit 下方并合并，无需手动调整顺序。最终历史中只保留干净的 `a1b2c3d`，看不到修补痕迹。

## 进阶用法

### 设置 autosquash 为默认行为

每次 rebase 都加 `--autosquash` 很麻烦，可以全局开启：

```bash
git config --global rebase.autosquash true
```

之后只需要：
```bash
git rebase -i HEAD~5   # autosquash 自动生效
```

### `--fixup=amend:` — 同时修改 commit message

```bash
# 不仅合并代码变更，还允许修改目标 commit 的 message
git commit --fixup=amend:<commit-hash>
```

### `--fixup=reword:` — 只改 message 不改代码

```bash
# 只修改目标 commit 的 message，不涉及代码变更
git commit --allow-empty --fixup=reword:<commit-hash>
```

## fixup vs amend vs revert 对比

| 场景 | 命令 | 适用范围 |
|------|------|----------|
| 修补最近一次提交 | `git commit --amend` | 仅限最新 commit |
| 修补任意历史提交 | `git commit --fixup` + `rebase --autosquash` | 任意未推送的 commit |
| 撤销已推送的提交 | `git revert` | 已推送到远程的 commit |

> ⚠️ **注意**：`fixup` + `rebase` 会**改写历史**，仅适用于尚未推送到远程的本地提交。如果已经 push，需要 `git push --force`，在团队协作中请谨慎使用。
