#!/usr/bin/env python3
"""静态化构建脚本：把 Flask 应用冻结成 dist/ 下的纯静态文件，供 GitHub Pages 部署。"""

import os
import shutil
import json
from urllib.parse import quote

from app import app, ARTICLES, CATEGORIES, ALL_TAGS, reload_if_changed

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, 'dist')
STATIC_SRC = os.path.join(ROOT, 'static')


def clean_dist():
    if os.path.exists(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)


def write_page(client, url, out_rel_path):
    resp = client.get(url)
    if resp.status_code != 200:
        print(f'  ⚠️  {url} → {resp.status_code}，跳过')
        return
    abs_out = os.path.join(DIST, out_rel_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)
    with open(abs_out, 'wb') as f:
        f.write(resp.data)
    print(f'  ✓ {url}')


def build_search_index():
    """生成前端搜索用的精简索引"""
    index = []
    for a in ARTICLES:
        index.append({
            'title': a['title'],
            'slug': a['slug'],
            'category': a['category'],
            'summary': a['summary'],
            'tags': a['tags'],
            'date': a['updated'],
            # 截前 2KB 原文用于全文匹配，大小写预归一
            'text': a['raw'][:2000].lower(),
        })
    out = os.path.join(DIST, 'search-index.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, separators=(',', ':'))
    size = os.path.getsize(out) // 1024
    print(f'  ✓ search-index.json ({len(index)} 篇, {size}KB)')


def main():
    reload_if_changed()
    print(f'文章 {len(ARTICLES)} 篇 · 分类 {len(CATEGORIES)} · 标签 {len(ALL_TAGS)}\n')

    clean_dist()
    client = app.test_client()

    # 首页
    write_page(client, '/', 'index.html')

    # 全部文章页
    write_page(client, '/articles', 'articles/index.html')

    # 文章详情
    for a in ARTICLES:
        slug = a['slug']
        write_page(client, f'/article/{quote(slug)}', f'article/{slug}/index.html')

    # 分类页
    for cat in CATEGORIES:
        write_page(client, f'/category/{quote(cat)}', f'category/{cat}/index.html')

    # 标签页
    for tag in ALL_TAGS:
        write_page(client, f'/tag/{quote(tag)}', f'tag/{tag}/index.html')

    # 搜索壳页（结果由 JS 填充）
    write_page(client, '/search', 'search/index.html')

    # 404
    resp = client.get('/__definitely_not_found__')
    with open(os.path.join(DIST, '404.html'), 'wb') as f:
        f.write(resp.data)
    print('  ✓ 404.html')

    # 拷贝静态资源
    shutil.copytree(STATIC_SRC, os.path.join(DIST, 'static'))
    print('  ✓ static/')

    # 搜索索引
    build_search_index()

    # GH Pages 防止 Jekyll 处理下划线开头目录
    with open(os.path.join(DIST, '.nojekyll'), 'w') as f:
        f.write('')
    print('  ✓ .nojekyll')

    print(f'\n✅ 构建完成: {DIST}')


if __name__ == '__main__':
    main()
