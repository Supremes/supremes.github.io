# Hexo 主题配置说明

本博客同时配置了两个主题，可以随时切换：

1. **AnZhiYu 主题** - 当前使用的主题
2. **Butterfly 主题** - 备用主题

## 主题配置文件

- `_config.anzhiyu.yml` - AnZhiYu 主题配置
- `_config.butterfly.yml` - Butterfly 主题配置
- `_config.yml` - Hexo 主配置文件（其中 `theme` 字段控制使用哪个主题）

## 主题切换方法

### 方法一：使用脚本切换（推荐）

运行主题切换脚本：

```bash
./switch-theme.sh
```

或直接指定主题：

```bash
./switch-theme.sh anzhiyu    # 切换到 AnZhiYu 主题
./switch-theme.sh butterfly  # 切换到 Butterfly 主题
```

### 方法二：手动修改配置文件

编辑 `_config.yml` 文件，找到 `theme` 字段并修改：

```yaml
# 切换到 AnZhiYu 主题
theme: anzhiyu

# 或切换到 Butterfly 主题
theme: butterfly
```

## 查看效果

切换主题后，运行以下命令查看效果：

```bash
hexo clean        # 清理缓存
hexo generate     # 生成静态文件
hexo server       # 启动本地服务器
```

或使用简写命令：

```bash
hexo clean && hexo g && hexo s
```

然后在浏览器中访问 `http://localhost:4000` 查看效果。

## 主题配置差异

### 共同配置项

两个主题都已配置：
- 导航菜单（主页、时间线、分类、关于）
- 本地搜索功能
- 代码高亮和复制功能
- 文章目录（TOC）
- 暗黑模式
- Mermaid 图表支持
- 相关文章推荐
- 图标和头像路径

### AnZhiYu 特有功能

- 中控台（centerConsole）
- 人物画布效果（peoplecanvas）
- 主题主色调配置
- AI 摘要功能
- 更多动效配置

### Butterfly 特有功能

- 更简洁的配置结构
- 不同的侧边栏卡片样式
- 不同的页面布局选项

## 注意事项

1. **配置独立**：两个主题的配置文件完全独立，修改一个不会影响另一个
2. **资源路径**：确保图片、图标等资源路径在两个主题中都能正确访问
3. **清理缓存**：切换主题后建议运行 `hexo clean` 清理缓存
4. **插件兼容**：某些插件可能对特定主题有依赖，切换时注意测试

## 备份说明

使用脚本切换主题时，会自动备份当前的 `_config.yml` 文件为 `_config.yml.backup`，方便出现问题时恢复。
