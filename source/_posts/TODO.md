---
title: TODO
tags: []
categories:
  - 杂七杂八
sticky: "10"
abbrlink: 4947
date: 2025-11-29 08:50:05
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/TODO.webp
---

### Pending Issues
- [ ] 首页按照更新时间展示文章列表
	- [ ] 更新时间显示有误，导致列表展示乱序
	- [ ] 配置更新时间具体到分钟

### Fixed
- [x] 多级目录时，通过目录定位会出问题
	- 目录名一致，但是层级关系不一致，不会被视为同一目录，建议不要这样设置
- [x] Obsidian 双链转 hexo 链接
	- 引用hexo-filter-titlebased-link 库，添加配置项解决该问题
- [x] Mermaid 代码块渲染失败，需要引用 JS 语法
	- 引用hexo-filter-mermaid-diagrams 库，但是间歇性还是会渲染不出来，推荐还是使用**标签插件 (Tag Plugin)** 语法
```
{% mermaid %}
{% endmermaid %}
```
- [x] 本地测试经常性报 fontawesome failure
> 	使用隐私模式访问，大概率没问题

- [x] 图片多大太大，导致加载缓慢的问题。参考: https://gemini.google.com/share/320865e42713
	- [x] 配置图床(github repo: [blog-images]([Supremes/blog-images](https://github.com/Supremes/blog-images)))，并使用CDN - `cdn.jsdelivr.net ` 加速访问
	- [x] 压缩图片大小
