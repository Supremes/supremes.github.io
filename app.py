#!/usr/bin/env python3
"""知识库网站 — Flask 应用"""

import os
import re
import json
import glob
from datetime import datetime
import sqlite3
import threading
from flask import Flask, render_template, abort, request, jsonify, send_file, Response
import markdown
from pygments.formatters import HtmlFormatter
from werkzeug.security import safe_join

app = Flask(__name__)
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT_DIR = os.path.join(REPO_ROOT, 'content')
# ──────────────────────────────── AI Analysis Config ────────────────────────

LLM_API_KEY = os.environ.get('LLM_API_KEY', '')
LLM_API_BASE = os.environ.get('LLM_API_BASE', 'https://token-plan-sgp.xiaomimimo.com/v1')
LLM_MODEL = os.environ.get('LLM_MODEL', 'mimo-v2.5-pro')

DB_PATH = os.path.join(REPO_ROOT, 'data', 'ai_analyses.db')
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS ai_analyses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_slug TEXT NOT NULL,
        article_title TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        is_auto_summary INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    )""")
    conn.execute("""CREATE INDEX IF NOT EXISTS idx_analyses_slug
        ON ai_analyses(article_slug, created_at DESC)""")
    conn.commit()
    return conn

def get_analyses(slug):
    conn = get_db()
    rows = conn.execute(
        'SELECT id, question, answer, is_auto_summary, created_at FROM ai_analyses WHERE article_slug=? ORDER BY created_at DESC',
        (slug,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def save_analysis(slug, title, question, answer, is_auto=0):
    conn = get_db()
    conn.execute(
        'INSERT INTO ai_analyses (article_slug,article_title,question,answer,is_auto_summary) VALUES (?,?,?,?,?)',
        (slug, title, question, answer, is_auto)
    )
    conn.commit()
    conn.close()

def call_llm_stream(messages):
    """Stream tokens from LLM API"""
    import openai
    if not LLM_API_KEY:
        yield 'data: {"error": "LLM API key not configured"}\n\n'
        return
    try:
        client = openai.OpenAI(api_key=LLM_API_KEY, base_url=LLM_API_BASE)
        stream = client.chat.completions.create(
            model=LLM_MODEL, messages=messages, stream=True,
            max_tokens=2000, temperature=0.3)
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                yield f'data: {json.dumps({"token": token})}\n\n'
        yield 'data: {"done": true}\n\n'
    except Exception as e:
        yield f'data: {json.dumps({"error": str(e)})}\n\n'



@app.after_request
def add_no_cache_headers(response):
    """强制浏览器不缓存静态文件，避免移动端缓存旧版 CSS/JS"""
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

@app.context_processor
def inject_now():
    return {'now': datetime.now}


FEATURED_ARTICLE_PATHS = [
]


def build_cat_tree(articles):
    """按 content/ 下目录层级构建嵌套树。
    返回 dict {dirname: {name, path, articles, children, total}}。"""
    root = {'children': {}, 'articles': [], 'total': 0}
    for a in articles:
        parts = a['path'].replace(os.sep, '/').split('/')
        dirs = parts[:-1]  # 去掉文件名
        node = root
        path_acc = ''
        for d in dirs:
            path_acc = f'{path_acc}/{d}' if path_acc else d
            if d not in node['children']:
                node['children'][d] = {
                    'name': d, 'path': path_acc,
                    'articles': [], 'children': {}, 'total': 0,
                }
            node = node['children'][d]
        node['articles'].append(a)

    def count(n):
        c = len(n['articles'])
        for ch in n['children'].values():
            c += count(ch)
        n['total'] = c
        return c
    count(root)

    def sort_children(n):
        n['children'] = dict(sorted(n['children'].items()))
        for ch in n['children'].values():
            sort_children(ch)
    sort_children(root)

    return root['children']


@app.context_processor
def inject_cat_tree():
    return {'cat_tree': build_cat_tree(ARTICLES)}

# ──────────────────────────────── 内容加载 ────────────────────────────────

def process_callouts(text):
    """将 Obsidian 风格的 > [!info] callout 转换为 HTML"""
    import re
    
    # 匹配 > [!type] optional title\n> content 格式
    def replace_callout(match):
        callout_type = match.group(1).lower()
        title = match.group(2).strip() if match.group(2) else ''
        content = match.group(3)
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
            'abstract': ('📋', '#6366f1', '#eef2ff'),
            'success': ('✅', '#10b981', '#ecfdf5'),
            'question': ('❓', '#f59e0b', '#fffbeb'),
            'example': ('🧪', '#8b5cf6', '#f5f3ff'),
            # GitHub callout 兼容
            'important': ('❗', '#8b5cf6', '#f5f3ff'),
            'caution': ('🛑', '#ef4444', '#fef2f2'),
        }
        
        icon, border_color, bg_color = type_config.get(callout_type, ('ℹ️', '#3b82f6', '#eff6ff'))
        
        # 标题行：如果有自定义标题则用自定义标题，否则用类型名
        header_text = title if title else callout_type.upper()
        
        return f'''<div style="border-left: 4px solid {border_color}; background: {bg_color}; padding: 16px 20px; margin: 20px 0; border-radius: 0 8px 8px 0;">
<div style="font-weight: 600; margin-bottom: 8px; color: {border_color};">{icon} {header_text}</div>
<div>{content}</div>
</div>'''
    
    # 匹配模式：> [!type] optional title 后跟多行 > 开头的内容
    pattern = r'^>\s*\[!(\w+)\]\s*(.*?)\n((?:^>.*$\n?)+)'
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


def normalize_frontmatter_date(value):
    """将 front matter 日期规整为 YYYY-MM-DD；缺失或非法时返回空串。"""
    if not value:
        return ''
    text = str(value).strip().strip('"').strip("'")
    match = re.match(r'^(\d{4}-\d{2}-\d{2})', text)
    return match.group(1) if match else ''


def is_truthy_frontmatter(value):
    return str(value).strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def normalize_rel_path(path):
    return os.path.normpath(path).replace(os.sep, '/')


def rewrite_internal_markdown_links(html, current_rel_path, path_to_slug):
    current_dir = os.path.dirname(current_rel_path)

    def _rewrite_link(match):
        prefix, href, suffix = match.groups()
        if href.startswith(('http://', 'https://', 'mailto:', 'tel:', 'data:', '/', '#')):
            return match.group(0)

        href_without_anchor, anchor_sep, anchor = href.partition('#')
        href_path, query_sep, query = href_without_anchor.partition('?')
        if not href_path.endswith('.md'):
            return match.group(0)

        target_rel = normalize_rel_path(os.path.join(current_dir, href_path))
        slug = path_to_slug.get(target_rel)
        if not slug:
            return match.group(0)

        new_href = f'/article/{slug}'
        if query_sep:
            new_href += f'?{query}'
        if anchor_sep:
            new_href += f'#{anchor}'
        return f'{prefix}{new_href}{suffix}'

    return re.sub(r'(<a\s[^>]*href=")([^"]+)(")', _rewrite_link, html)


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
        if is_truthy_frontmatter(meta.get('hidden', '')):
            continue
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

        # 将相对路径的图片 src 重写为 /content-assets/ 绝对路径
        content_dir_rel = os.path.dirname(rel).replace(os.sep, '/')
        def _rewrite_img(m):
            src = m.group(1)
            if src.startswith(('http://', 'https://', '/', 'data:')):
                return m.group(0)
            asset_path = f'{content_dir_rel}/{src}' if content_dir_rel else src
            return m.group(0).replace(m.group(1), f'/content-assets/{asset_path}')
        html_body = re.sub(r'<img\s[^>]*src="([^"]+)"', _rewrite_img, html_body)

        date = normalize_frontmatter_date(meta.get('date', ''))
        updated = normalize_frontmatter_date(meta.get('updated', '')) or date
        sort_date = updated or '1970-01-01'

        articles.append({
            'slug': slug,
            'category': category,
            'title': meta.get('title', slug),
            'date': date,
            'updated': updated,
            'sort_date': sort_date,
            'featured': is_truthy_frontmatter(meta.get('featured', '')),
            'tags': meta.get('tags', []) if isinstance(meta.get('tags'), list) else [t.strip() for t in meta.get('tags', '').split(',') if t.strip()],
            'summary': meta.get('summary', ''),
            'content': html_body,
            'raw': body,
            'path': rel,
        })

    path_to_slug = {normalize_rel_path(a['path']): a['slug'] for a in articles}
    for article in articles:
        article['content'] = rewrite_internal_markdown_links(
            article['content'],
            article['path'],
            path_to_slug,
        )

    articles.sort(key=lambda a: (a['sort_date'], a['title']), reverse=True)
    return articles


def select_featured_articles(articles, limit=6):
    """首页精选常读：优先人工路径配置，其次 front matter featured。"""
    by_path = {a['path'].replace(os.sep, '/'): a for a in articles}
    selected = []
    seen = set()

    for path in FEATURED_ARTICLE_PATHS:
        article = by_path.get(path)
        if article:
            selected.append(article)
            seen.add(article['path'])

    for article in articles:
        if len(selected) >= limit:
            break
        if article.get('featured') and article['path'] not in seen:
            selected.append(article)
            seen.add(article['path'])

    return selected[:limit]


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
    featured = select_featured_articles(ARTICLES)
    recent = ARTICLES[:10]
    cat_counts = {c: sum(1 for a in ARTICLES if a['category'] == c) for c in CATEGORIES}
    sorted_cats = sorted(CATEGORIES, key=lambda c: cat_counts.get(c, 0), reverse=True)
    return render_template('index.html',
                           featured=featured, recent=recent,
                           categories=sorted_cats, cat_counts=cat_counts,
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
                           current_path=name,
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
            # current_path: 文章所在目录的完整相对路径，如 'AI' 或 'AI/ai-agent'
            dir_parts = a['path'].replace(os.sep, '/').split('/')[:-1]
            current_path = '/'.join(dir_parts)
            analyses = get_analyses(a['slug'])
            return render_template('article.html',
                                   article=a, prev=prev_a, next=next_a,
                                   current_slug=a['slug'], current_path=current_path,
                                   categories=CATEGORIES, all_tags=ALL_TAGS,
                                   ai_analyses=analyses)
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


# ──────────────────────────────── AI Analysis API ────────────────────────────

@app.route('/api/ai-analyses/<slug>')
def api_get_analyses(slug):
    analyses = get_analyses(slug)
    return jsonify(analyses)

@app.route('/api/ai-analyze', methods=['POST'])
def api_ai_analyze():
    data = request.get_json()
    slug = data.get('slug', '')
    question = data.get('question', '').strip()
    article_title = data.get('title', '')
    article_content = data.get('content', '')
    if not slug or not article_content:
        return jsonify({'error': 'Missing data'}), 400
    if len(article_content) > 8000:
        article_content = article_content[:8000] + '\n...(truncated)'
    is_auto = 0
    if not question:
        question = '请对这篇文章做结构化总结：核心要点、关键概念、实用建议。简洁要点格式。'
        is_auto = 1
    messages = [
        {'role': 'system', 'content': '你是知识库助手，擅长分析技术文章。回答简洁、有深度、用中文。'},
        {'role': 'user', 'content': f'文章：{article_title}\n\n{article_content}\n\n问题：{question}'}
    ]
    def generate():
        full = []
        for chunk in call_llm_stream(messages):
            if chunk.startswith('data: '):
                try:
                    d = json.loads(chunk[6:].strip())
                    if 'token' in d: full.append(d['token'])
                    if d.get('done'): save_analysis(slug, article_title, question, ''.join(full), is_auto)
                except: pass
            yield chunk
    return Response(generate(), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ──────────────────────────────── Portal (交互实验室) ────────────────────────

PORTAL_DIR = os.path.join(REPO_ROOT, 'portal')

def load_portal_pages():
    """扫描 portal/ 子目录，从 HTML <meta name="portal-*"> 提取元数据。
    优先级：meta portal-category > _categories.json 目录映射 > 目录原名 > 未分类
    """
    if not os.path.isdir(PORTAL_DIR):
        return []

    # 加载目录映射
    cat_map_path = os.path.join(PORTAL_DIR, '_categories.json')
    cat_map = {}
    if os.path.exists(cat_map_path):
        try:
            with open(cat_map_path, 'r', encoding='utf-8') as f:
                cat_map = json.load(f)
        except Exception:
            pass

    def resolve_category(meta_cat, dir_name):
        if meta_cat:
            return meta_cat
        if dir_name and dir_name in cat_map:
            return cat_map[dir_name].get('name', dir_name)
        if dir_name:
            return dir_name
        return '未分类'

    pages = []
    for root, dirs, files in os.walk(PORTAL_DIR):
        dirs[:] = [d for d in dirs if not d.startswith(('.', '_'))]
        for fname in sorted(files):
            if not fname.endswith('.html'):
                continue
            filepath = os.path.join(root, fname)
            slug = os.path.splitext(fname)[0]
            rel_dir = os.path.relpath(root, PORTAL_DIR)
            if rel_dir == '.':
                rel_dir = ''
            # 构建完整路径用于 URL（如 agent/memory/mem0-memory-system）
            full_slug = f'{rel_dir}/{slug}' if rel_dir else slug
            dir_name = rel_dir.split(os.sep)[0] if rel_dir else ''
            dir_info = cat_map.get(dir_name, {})
            meta = {}
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    head = f.read(4096)
                for m in re.finditer(r'<meta\s+name="portal-(\w+)"\s+content="([^"]*)"', head):
                    meta[m.group(1)] = m.group(2)
                tm = re.search(r'<title>([^<]*)</title>', head)
                title = meta.get('title') or (tm.group(1).strip() if tm else slug)
            except Exception:
                title = slug
            # 子分类：路径中间层（如 agent/memory/xxx → memory）
            parts = rel_dir.split(os.sep) if rel_dir else []
            subcategory = parts[1] if len(parts) >= 2 else ''
            pages.append({
                'slug': full_slug,
                'title': title,
                'subtitle': meta.get('subtitle', ''),
                'desc': meta.get('desc', ''),
                'category': resolve_category(meta.get('category', ''), dir_name),
                'subcategory': subcategory,
                'tags': [t.strip() for t in meta.get('tags', '').split(',') if t.strip()],
                'icon': meta.get('icon') or dir_info.get('icon', '📄'),
                'color': meta.get('color') or dir_info.get('color', '#6b7280'),
                'date': meta.get('date', ''),
                'difficulty': meta.get('difficulty', '入门'),
                'duration': meta.get('duration', '—'),
            })
    return pages


@app.route('/portal')
def portal_index():
    pages = load_portal_pages()
    portal_cats = sorted(set(p['category'] for p in pages))

    # 加载子分类配置
    cat_map_path = os.path.join(PORTAL_DIR, '_categories.json')
    cat_config = {}
    portal_subcategories = {}
    if os.path.exists(cat_map_path):
        try:
            with open(cat_map_path, 'r', encoding='utf-8') as f:
                cat_config = json.load(f)
            for dir_name, info in cat_config.items():
                subs = info.get('subcategories', {})
                if subs:
                    cat_name = info.get('name', dir_name)
                    portal_subcategories[cat_name] = {
                        k: v.get('name', k) for k, v in subs.items()
                    }
        except Exception:
            pass

    return render_template('portal.html', pages=pages, portal_categories=portal_cats,
                           portal_subcategories=portal_subcategories,
                           categories=CATEGORIES, all_tags=ALL_TAGS)

@app.route('/portal/<path:slug>')
def portal_page(slug):
    def is_public_path(rel_path):
        parts = rel_path.replace('\\', '/').split('/')
        return all(part and not part.startswith(('.', '_')) for part in parts)

    def find_legacy_basename(slug_value):
        if '/' in slug_value:
            return None
        target = slug_value if slug_value.endswith('.html') else f'{slug_value}.html'
        if not is_public_path(target):
            return None
        for root, dirs, files in os.walk(PORTAL_DIR):
            dirs[:] = [d for d in dirs if not d.startswith(('.', '_'))]
            if target in files:
                return os.path.join(root, target)
        return None

    candidates = [slug] if slug.endswith('.html') else [f'{slug}.html']
    for candidate in candidates:
        if not is_public_path(candidate):
            continue
        path = safe_join(PORTAL_DIR, candidate)
        if path and os.path.isfile(path) and path.endswith('.html'):
            return send_file(path)

    legacy_path = find_legacy_basename(slug)
    if legacy_path:
        return send_file(legacy_path)

    abort(404)


@app.route('/content-assets/<path:filepath>')
def content_assets(filepath):
    """Serve static assets (images, SVG, etc.) stored alongside markdown in content/"""
    ALLOWED_EXTENSIONS = {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp', '.ico', '.pdf'}
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        abort(404)
    path = safe_join(CONTENT_DIR, filepath)
    if path and os.path.isfile(path):
        return send_file(path)
    abort(404)


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', categories=CATEGORIES, all_tags=ALL_TAGS), 404


# ──────────────────────────────── 启动 ────────────────────────────────

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
