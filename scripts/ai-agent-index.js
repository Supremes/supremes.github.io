'use strict';

const fs = require('fs');
const path = require('path');

const DIR_NAME = 'ai-agent';
const TITLE_RE = /<title[^>]*>([\s\S]*?)<\/title>/i;
const DESC_RE = /<meta\s+name=["']description["']\s+content=["']([^"']*)["']/i;

function collectPages(sourceDir) {
  const baseDir = path.join(sourceDir, DIR_NAME);
  if (!fs.existsSync(baseDir)) return [];

  return fs.readdirSync(baseDir, { withFileTypes: true })
    .filter(d => d.isDirectory())
    .map(d => {
      const htmlPath = path.join(baseDir, d.name, 'index.html');
      if (!fs.existsSync(htmlPath)) return null;
      const html = fs.readFileSync(htmlPath, 'utf8');
      const title = (html.match(TITLE_RE) || [, d.name])[1].trim();
      const desc = (html.match(DESC_RE) || [, ''])[1].trim();
      const stat = fs.statSync(htmlPath);
      return { slug: d.name, title, desc, mtime: stat.mtime };
    })
    .filter(Boolean)
    .sort((a, b) => b.mtime - a.mtime);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function renderIndex(pages) {
  const cards = pages.map(p => `
    <a class="aa-card" href="/${DIR_NAME}/${encodeURIComponent(p.slug)}/">
      <div class="aa-card-title">${escapeHtml(p.title)}</div>
      ${p.desc ? `<div class="aa-card-desc">${escapeHtml(p.desc)}</div>` : ''}
      <div class="aa-card-meta">${p.mtime.toISOString().slice(0, 10)}</div>
    </a>`).join('\n');

  const empty = `<div class="aa-empty">还没有页面，把 html 放到 <code>source/${DIR_NAME}/&lt;slug&gt;/index.html</code> 即可</div>`;

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI Agent</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
         max-width: 1100px; margin: 0 auto; padding: 48px 24px; line-height: 1.6;
         background: #fafafa; color: #222; }
  @media (prefers-color-scheme: dark) {
    body { background: #1a1a1a; color: #e8e8e8; }
    .aa-card { background: #262626; border-color: #333; }
    .aa-card:hover { border-color: #4a90e2; }
    .aa-card-meta { color: #888; }
  }
  h1 { font-size: 32px; margin: 0 0 8px; }
  .aa-sub { color: #888; margin: 0 0 32px; font-size: 14px; }
  .aa-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
  .aa-card { display: block; padding: 20px; border: 1px solid #e4e4e4; border-radius: 12px;
             background: #fff; text-decoration: none; color: inherit;
             transition: transform .15s, box-shadow .15s, border-color .15s; }
  .aa-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,.08); border-color: #4a90e2; }
  .aa-card-title { font-size: 17px; font-weight: 600; margin-bottom: 8px; }
  .aa-card-desc { font-size: 14px; color: #666; margin-bottom: 12px;
                  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .aa-card-meta { font-size: 12px; color: #aaa; }
  .aa-empty { padding: 48px; text-align: center; color: #888;
              border: 1px dashed #ccc; border-radius: 12px; }
  code { background: rgba(127,127,127,.15); padding: 2px 6px; border-radius: 4px; font-size: 13px; }
</style>
</head>
<body>
  <h1>AI Agent</h1>
  <p class="aa-sub">共 ${pages.length} 个页面 · 自动索引</p>
  ${pages.length ? `<div class="aa-grid">${cards}</div>` : empty}
</body>
</html>`;
}

hexo.extend.generator.register('ai-agent-index', function () {
  const sourceDir = this.source_dir;
  const pages = collectPages(sourceDir);
  return {
    path: `${DIR_NAME}/index.html`,
    data: renderIndex(pages),
  };
});
