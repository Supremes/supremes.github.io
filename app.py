#!/usr/bin/env python3
"""知识库网站 — Flask 应用"""

import os
import re
import json
import glob
from datetime import datetime
from flask import Flask, render_template, abort, request, jsonify
import markdown
from pygments.formatters import HtmlFormatter

app = Flask(__name__)
CONTENT_DIR = os.path.join(os.path.dirname(__file__), 'content')

@app.context_processor
def inject_now():
    return {'now': datetime.now}

# ──────────────────────────────── 内容加载 ────────────────────────────────

def process_callouts(text):
    """将 Obsidian 风格的 > [!info] callout 转换为 HTML"""
    import re
    
    # 匹配 > [!type]\n> content 格式
    def replace_callout(match):
        callout_type = match.group(1).lower()
        content = match.group(2)
        # 移除每行开头的 > 
        content = re.sub(r'^>\s?', '', content, flags=re.MULTILINE)
        content = content.strip()
        
        # 映射类型到图标和颜色
        type_config = {
            'info': ('ℹ️', '#3b82f6', '#eff6ff'),
            'tip': ('💡', '#10b981', '#ecfdf5'),
            'warning': ('⚠️', '#f59e0b', '#fffbeb'),
            'danger': ('🚨', '#ef4444', '#fef2f2'),
            'note': ('📝', '#6366f1', '#eef2ff'),
            'quote': ('💬', '#8b5cf6', '#f5f3ff'),
        }
        
        icon, border_color, bg_color = type_config.get(callout_type, ('ℹ️', '#3b82f6', '#eff6ff'))
        
        return f'''<div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 16px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
<div style="font-weight: 600; margin-bottom: 8px; color: {border_color};">{icon} {callout_type.upper()}</div>
<div>{content}</div>
</div>'''
    
    # 匹配模式：> [!type] 后跟多行 > 开头的内容
    pattern = r'^>\s*\[!(\w+)\]\s*\n((?:^>.*$\n?)+)'
    return re.sub(pattern, replace_callout, text, flags=re.MULTILINE)


def process_sublists(text):
    """将 tab 缩进的 a. b. c. 子列表转换为标准 Markdown 嵌套列表，
    并确保列表前有空行以被正确解析"""
    import re
    # 处理 \t\ta. 或 \ta. 或多空格+a. 格式 → 转为 4空格缩进的 - 
    def convert_sublist(match):
        content = match.group(2)
        return f'    - {content}'
    
    text = re.sub(r'^[\t ]{1,}([a-z])\.\s+(.*)', convert_sublist, text, flags=re.MULTILINE)
    
    # 确保列表项前有空行（无序 -/* 和有序 1. 2. 等）
    lines = text.split('\n')
    result = []
    for i, line in enumerate(lines):
        if i > 0:
            is_list_start = re.match(r'^[\-\*]\s', line) or re.match(r'^\d+\.\s', line)
            if is_list_start:
                prev = lines[i-1]
                prev_stripped = prev.strip()
                # 前一行非空、非列表项、非引用、非标题、非代码块 → 插入空行
                prev_is_list = re.match(r'^[\-\*]\s', prev) or re.match(r'^\d+\.\s', prev) or re.match(r'^\s+[\-\*]\s', prev)
                if (prev_stripped and
                    not prev_is_list and
                    not prev_stripped.startswith('>') and
                    not prev_stripped.startswith('#') and
                    not prev_stripped.startswith('```')):
                    result.append('')
        result.append(line)
    
    return '\n'.join(result)


def load_articles():
    """扫描 content/ 下所有 .md 文件，返回文章列表"""
    articles = []
    for md_path in glob.glob(os.path.join(CONTENT_DIR, '**', '*.md'), recursive=True):
        rel = os.path.relpath(md_path, CONTENT_DIR)
        parts = rel.split(os.sep)
        category = parts[0] if len(parts) > 1 else '未分类'
        slug = os.path.splitext(parts[-1])[0]

        with open(md_path, 'r', encoding='utf-8') as f:
            raw = f.read()

        # 解析 YAML front matter
        meta, body = parse_frontmatter(raw)
        # 预处理 Obsidian 风格的 callout 语法
        body = process_callouts(body)
        # 预处理 tab 缩进子列表
        body = process_sublists(body)
        html_body = markdown.markdown(
            body,
            extensions=['fenced_code', 'codehilite', 'toc', 'tables', 'attr_list'],
            extension_configs={
                'codehilite': {'css_class': 'highlight', 'guess_lang': True},
                'toc': {'permalink': True},
            }
        )

        articles.append({
            'slug': slug,
            'category': category,
            'title': meta.get('title', slug),
            'date': meta.get('date', ''),
            'tags': meta.get('tags', []) if isinstance(meta.get('tags'), list) else [t.strip() for t in meta.get('tags', '').split(',') if t.strip()],
            'summary': meta.get('summary', ''),
            'content': html_body,
            'raw': body,
            'path': rel,
        })

    articles.sort(key=lambda a: a['date'], reverse=True)
    return articles


def parse_frontmatter(text):
    """简易 YAML front matter 解析（兼容数组和列表语法）"""
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)', text, re.DOTALL)
    if not m:
        return {}, text
    meta = {}
    current_key = None
    for line in m.group(1).strip().splitlines():
        # 处理列表项（如 - AI）
        if line.strip().startswith('- ') and current_key:
            val = line.strip()[2:].strip().strip('"').strip("'")
            if isinstance(meta[current_key], list):
                meta[current_key].append(val)
            continue
        # 处理 key: value
        if ':' in line:
            k, v = line.split(':', 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            # 处理 YAML 空数组 []
            if v == '[]':
                meta[k] = []
                current_key = k
                continue
            # 处理空值（可能是后续跟列表项）
            if v == '' or v == '~' or v == 'null':
                meta[k] = []  # 初始化为空列表，等待后续列表项
                current_key = k
                continue
            meta[k] = v
            current_key = k
    return meta, m.group(2)


# ──────────────────────────────── 全局数据（热加载）────────────────────────

ARTICLES = []
CATEGORIES = []
ALL_TAGS = []
_content_mtime = 0

def reload_if_changed():
    """检测 content/ 目录变化，自动重新加载文章"""
    global ARTICLES, CATEGORIES, ALL_TAGS, _content_mtime
    try:
        # 获取 content 目录下所有 .md 文件的最新修改时间
        latest = 0
        for md_path in glob.glob(os.path.join(CONTENT_DIR, '**', '*.md'), recursive=True):
            mtime = os.path.getmtime(md_path)
            if mtime > latest:
                latest = mtime
        if latest > _content_mtime:
            ARTICLES = load_articles()
            CATEGORIES = sorted(set(a['category'] for a in ARTICLES))
            ALL_TAGS = sorted(set(t for a in ARTICLES for t in a['tags']))
            _content_mtime = latest
    except Exception:
        pass

# 首次加载
reload_if_changed()


# ──────────────────────────────── 路由 ────────────────────────────────

@app.route('/')
def index():
    reload_if_changed()
    featured = ARTICLES[:6]
    recent = ARTICLES[:10]
    cat_counts = {c: sum(1 for a in ARTICLES if a['category'] == c) for c in CATEGORIES}
    return render_template('index.html',
                           featured=featured, recent=recent,
                           categories=CATEGORIES, cat_counts=cat_counts,
                           all_tags=ALL_TAGS, total=len(ARTICLES))


@app.route('/articles')
def all_articles():
    reload_if_changed()
    return render_template('articles.html',
                           articles=ARTICLES,
                           categories=CATEGORIES, all_tags=ALL_TAGS)


@app.route('/category/<name>')
def category(name):
    reload_if_changed()
    arts = [a for a in ARTICLES if a['category'] == name]
    if not arts:
        abort(404)
    return render_template('category.html',
                           category=name, articles=arts,
                           categories=CATEGORIES, all_tags=ALL_TAGS)


@app.route('/article/<path:slug>')
def article(slug):
    reload_if_changed()
    for a in ARTICLES:
        if a['slug'] == slug:
            # 上下篇
            idx = ARTICLES.index(a)
            prev_a = ARTICLES[idx + 1] if idx + 1 < len(ARTICLES) else None
            next_a = ARTICLES[idx - 1] if idx > 0 else None
            return render_template('article.html',
                                   article=a, prev=prev_a, next=next_a,
                                   categories=CATEGORIES, all_tags=ALL_TAGS)
    abort(404)


@app.route('/search')
def search():
    reload_if_changed()
    q = request.args.get('q', '').strip()
    results = []
    if q:
        ql = q.lower()
        for a in ARTICLES:
            if ql in a['title'].lower() or ql in a['raw'].lower() or ql in a['summary'].lower():
                # 截取匹配片段
                idx = a['raw'].lower().find(ql)
                start = max(0, idx - 60)
                end = min(len(a['raw']), idx + len(q) + 60)
                snippet = '...' + a['raw'][start:end].replace('\n', ' ') + '...'
                results.append({**a, 'snippet': snippet})
    return render_template('search.html',
                           query=q, results=results,
                           categories=CATEGORIES, all_tags=ALL_TAGS)


@app.route('/tag/<name>')
def tag(name):
    reload_if_changed()
    arts = [a for a in ARTICLES if name in a['tags']]
    return render_template('tag.html',
                           tag=name, articles=arts,
                           categories=CATEGORIES, all_tags=ALL_TAGS)


@app.route('/api/search')
def api_search():
    reload_if_changed()
    q = request.args.get('q', '').strip().lower()
    if not q:
        return jsonify([])
    results = []
    for a in ARTICLES:
        if q in a['title'].lower() or q in a['raw'].lower() or q in a['summary'].lower():
            results.append({
                'title': a['title'],
                'url': f'/article/{a["slug"]}',
                'category': a['category'],
                'summary': a['summary'][:100],
            })
    return jsonify(results[:10])


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', categories=CATEGORIES, all_tags=ALL_TAGS), 404


# ──────────────────────────────── 启动 ────────────────────────────────

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
