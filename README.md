  # 本地验证
  uv sync
  uv run build.py
  python3 -m http.server 8000 -d dist   # 浏览器看一眼

## 隐藏文章

在 Markdown 的 front matter 中设置 `hidden: true`，构建时会跳过该文章，不生成详情页，也不会出现在首页、分类、标签或搜索结果中：

```yaml
---
title: 暂不公开的文章
hidden: true
---
```