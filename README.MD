# Hexo 博客日常维护操作指南

这份文档记录了博客的日常写作、发布、备份以及环境恢复流程。

## 📅 核心工作流 (Daily Workflow)

**谨记：先发布网站，再备份源码。**

1. **写文章**：创建 Markdown 文件并写作。
2. **预览**：本地启动服务器检查样式。
3. **发布**：部署到 GitHub Pages (给读者看)。
4. **备份**：推送源码到 GitHub Main 分支 (给自己存档)。

---

## ✍️ 增删改查 (CRUD) 操作

### 1. 新建文章 (Create)
在终端执行以下命令：
```bash
hexo new "文章标题"
# 示例：hexo new "My-First-Blog"
````

  * 文件位置：`source/_posts/文章标题.md`
  * **技巧**：文件名建议使用英文或拼音（避免 URL 乱码），文章内的 `title` 字段可以写中文。

### 2\. 编辑/更新文章 (Update)

直接使用 Markdown 编辑器（如 VS Code, Typora, Obsidian）打开 `source/_posts/` 下对应的文件进行修改。

**Front-matter 配置说明（文章顶部区域）：**

```yaml
---
title: 我的第一篇博客  # 文章显示的大标题
date: 2023-11-26 14:00:00
tags: [Hexo, 教程]    # 标签
categories: 技术笔记  # 分类
---
```

### 3\. 删除文章 (Delete)

Hexo 没有专门的删除命令。

  * **操作**：直接在文件管理器中删除 `source/_posts/` 下对应的 `.md` 文件即可。
  * **注意**：删除后记得重新执行部署流程，网页上才会消失。

### 4\. 本地预览 (Read)

在部署前，务必在本地检查效果：

```bash
hexo clean   # 清理缓存（建议每次都加）
hexo s       # 启动本地服务器 (server)
```

  * 访问地址：`http://localhost:4000`
  * 退出预览：按 `Ctrl + C`

-----

## 🚀 发布与备份 (必读)

这是一个**双重操作**，缺一不可。

### 第一步：发布网站 (Deploy)

将生成的静态网页 (HTML) 推送到 `gh-pages` 分支：

```bash
hexo clean
hexo g
hexo d
```

  * *执行完这一步，访客就能看到更新了。*

### 第二步：备份源码 (Backup)

将 Markdown 源码、配置文件、主题文件推送到 `develop` 分支：

```bash
git add .
git commit -m "更新文章: 简述修改内容"
git push origin main
```

  * *执行完这一步，你的源代码才算安全。*

-----

## 🔧 常见问题与技巧

### 1\. 常用简写命令

  * `hexo n` = `hexo new`
  * `hexo g` = `hexo generate`
  * `hexo s` = `hexo server`
  * `hexo d` = `hexo deploy`

### 2\. 换电脑了如何恢复？(Clone & Install)

如果更换了新 Mac 或重装系统，按照以下步骤恢复博客环境：

1.  **安装环境**：安装 Node.js 和 Git。
2.  **克隆源码**（注意是 clone 你的 main 分支）：
    ```bash
    git clone [https://github.com/YourName/YourName.github.io.git](https://github.com/YourName/YourName.github.io.git) myblog
    cd myblog
    ```
3.  **还原依赖**：
    ```bash
    npm install
    npm install hexo-deployer-git --save  # 有时候部署插件需要单独再装一次
    ```
4.  **开始工作**：现在可以正常执行 `hexo s` 等命令了。

### 3\. 部署报错 "Spawn failed"

通常是因为 git 连接问题。

  * 检查网络（是否开启了代理）。
  * 检查 `_config.yml` 中的 repo 地址是否正确。
  * 检查 `.deploy_git` 文件夹是否冲突，可以尝试删除该文件夹后重试。

-----

## 📂 目录结构说明

  * `_config.yml`: **站点配置文件** (核心配置)
  * `themes/`: **主题文件夹** (存放下载的主题)
  * `source/`: **资源文件夹** (存放 Markdown 文章和图片)
      * `_posts/`: 文章都在这里
  * `scaffolds/`: **模版文件夹** (新建文章时的默认模板)
  * `public/`: **生成物** (不要动，`hexo g` 自动生成的)
  * `.deploy_git/`: **部署库** (不要动，`hexo d` 自动生成的)

<!-- end list -->
