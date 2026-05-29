#!/usr/bin/env python3
"""把 develop 分支的 hexo 博客文章迁移到 main 分支的 content/ 目录。

使用方法（确保 /tmp/develop-view 是 develop 分支的 worktree）:
    .venv/bin/python migrate.py
"""

import os
import re
import sys
import shutil
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent
HEXO_POSTS = Path('/tmp/develop-view/source/_posts')
TARGET_CONTENT = ROOT / 'content'

# main 已有文章的同主题/同名跳过清单（develop 路径 → main 已有 slug）
SKIP_MAP = {
    'AI/LLM 基础知识.md': 'main 已有 LLM 基础知识.md',
    'AI/MCP Introduction.md': 'main 已有 mcp-protocol-guide.md',
    'configs/Git.md': 'main 已有 git-branching-best-practices.md',
    '后端开发/Java/JAXB.md': 'main 已有 jaxb-spring-boot-guide.md',
}

# 一级目录名 → 最终分类名的覆盖映射（其他情况按 categories 字段或原一级目录）
DIR_TO_CAT_OVERRIDE = {
    'configs': '工具效率',
    '前端': '移动开发',  # develop 把 Chromium/objective-c 放前端但 categories 标移动开发
}


def slugify(name: str) -> str:
    """文件名 slug 化：小写 + 空格/下划线归一为 -，中文保留。"""
    if name.endswith('.md'):
        name = name[:-3]
    name = name.lower()
    name = re.sub(r'[\s_]+', '-', name)
    name = re.sub(r'-+', '-', name)
    return name.strip('-')


def decide_category(rel_path: Path, fm_categories) -> str:
    """决定文章最终归到哪个目录。"""
    path_str = str(rel_path)
    parts = rel_path.parts

    # 路径优先
    if '/Java/' in '/' + path_str or 'Java' in parts:
        return 'Java'
    if parts[0].lower() == 'spring':
        return 'Spring'
    if parts[0] in DIR_TO_CAT_OVERRIDE:
        return DIR_TO_CAT_OVERRIDE[parts[0]]

    # 看 categories 字段
    if fm_categories:
        cat = fm_categories[0].strip()
        if cat.lower() == 'spring':
            return 'Spring'
        return cat

    # 兜底：用一级目录名
    return parts[0]


def transform_frontmatter(fm: dict) -> dict:
    """hexo front matter → Flask 期望格式。"""
    new = {}
    if 'title' in fm:
        new['title'] = fm['title']
    # 日期截前 10 位
    if 'date' in fm and fm['date']:
        d = str(fm['date'])
        new['date'] = d[:10]
    # description → summary
    if fm.get('description'):
        new['summary'] = fm['description']
    elif fm.get('excerpt'):
        new['summary'] = fm['excerpt']
    # tags
    tags = fm.get('tags')
    if tags is None:
        new['tags'] = []
    elif isinstance(tags, str):
        new['tags'] = [tags] if tags else []
    elif isinstance(tags, list):
        new['tags'] = [t for t in tags if t]
    else:
        new['tags'] = []
    return new


def render_frontmatter(fm: dict) -> str:
    """生成 Flask app.py 能解析的简易 YAML（不用 PyYAML 输出，避免引号转义不一致）。"""
    lines = ['---']
    if 'title' in fm:
        lines.append(f'title: {fm["title"]}')
    if 'date' in fm:
        lines.append(f'date: {fm["date"]}')
    if 'summary' in fm:
        # 避免值里有冒号导致解析问题
        v = str(fm['summary']).replace('\n', ' ').strip()
        lines.append(f'summary: {v}')
    if 'tags' in fm:
        if fm['tags']:
            lines.append('tags:')
            for t in fm['tags']:
                lines.append(f'  - {t}')
        else:
            lines.append('tags: []')
    lines.append('---')
    return '\n'.join(lines) + '\n'


def collect_posts():
    """扫描所有 hexo 文章，返回 (rel_path, fm dict, body) 列表。"""
    posts = []
    for f in sorted(HEXO_POSTS.rglob('*.md')):
        rel = f.relative_to(HEXO_POSTS)
        text = f.read_text(encoding='utf-8', errors='ignore')
        m = re.match(r'^---\s*\n(.*?)\n---\s*\n?(.*)', text, re.DOTALL)
        if not m:
            print(f'⚠️  无 front matter，跳过: {rel}')
            continue
        try:
            fm = yaml.safe_load(m.group(1)) or {}
        except Exception as e:
            print(f'⚠️  YAML 解析失败 {rel}: {e}')
            continue
        body = m.group(2)
        cats = fm.get('categories')
        if isinstance(cats, str):
            cats = [cats]
        elif not isinstance(cats, list):
            cats = []
        cats = [c for c in cats if c]
        posts.append((rel, fm, cats, body))
    return posts


def main():
    if not HEXO_POSTS.exists():
        print(f'❌ {HEXO_POSTS} 不存在，请先 git worktree add /tmp/develop-view origin/develop')
        sys.exit(1)

    posts = collect_posts()
    print(f'扫描到 {len(posts)} 篇 hexo 文章\n')

    by_category = {}
    skipped = []
    conflicts = []
    written = 0

    for rel, fm, cats, body in posts:
        rel_str = str(rel)
        if rel_str in SKIP_MAP:
            skipped.append((rel_str, SKIP_MAP[rel_str]))
            continue

        category = decide_category(rel, cats)
        slug = slugify(rel.name)
        target_dir = TARGET_CONTENT / category
        target_file = target_dir / f'{slug}.md'

        # 检测冲突
        if target_file.exists():
            conflicts.append((rel_str, str(target_file.relative_to(ROOT))))
            continue

        # 同一次迁移内部冲突
        existing_in_cat = by_category.get(category, set())
        if slug in existing_in_cat:
            conflicts.append((rel_str, f'同次迁移中 {category}/{slug}.md 已被占用'))
            continue
        existing_in_cat.add(slug)
        by_category[category] = existing_in_cat

        new_fm = transform_frontmatter(fm)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file.write_text(render_frontmatter(new_fm) + body, encoding='utf-8')
        written += 1

    # 报告
    print('=== 分类分布 ===')
    for cat in sorted(by_category):
        print(f'  {cat}: {len(by_category[cat])} 篇')
    print(f'\n=== 跳过（同名/同主题）{len(skipped)} 篇 ===')
    for f, reason in skipped:
        print(f'  {f}  ← {reason}')
    if conflicts:
        print(f'\n⚠️  冲突 {len(conflicts)} 篇（未写入，请处理）')
        for f, reason in conflicts:
            print(f'  {f}  ← {reason}')
    print(f'\n✅ 写入 {written} 篇')


if __name__ == '__main__':
    main()
