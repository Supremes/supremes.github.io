/* ═══════════════════════════════════════════════════
   知识库 — 前端交互
   ═══════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ───── 主题切换 ─────
  const html = document.documentElement;
  const themeBtn = document.getElementById('theme-toggle');
  const themeIcon = themeBtn?.querySelector('.theme-icon');

  function applyTheme(theme) {
    html.dataset.theme = theme;
    if (themeIcon) themeIcon.textContent = theme === 'dark' ? '🌙' : '☀️';
    localStorage.setItem('kb-theme', theme);
  }

  // 初始化主题
  const saved = localStorage.getItem('kb-theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  applyTheme(saved || (prefersDark ? 'dark' : 'light'));

  themeBtn?.addEventListener('click', () => {
    applyTheme(html.dataset.theme === 'dark' ? 'light' : 'dark');
  });

  // ───── 搜索索引 ─────
  let _indexCache = null;
  async function loadIndex() {
    if (_indexCache) return _indexCache;
    const resp = await fetch('/search-index.json');
    _indexCache = await resp.json();
    return _indexCache;
  }

  function matchArticles(index, query) {
    const terms = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];

    const scored = [];
    for (const a of index) {
      const title = (a.title || '').toLowerCase();
      const summary = (a.summary || '').toLowerCase();
      const tags = (a.tags || []).join(' ').toLowerCase();
      const text = a.text || '';

      let score = 0;
      let matched = true;
      for (const t of terms) {
        const inTitle = title.includes(t);
        const inSummary = summary.includes(t);
        const inTags = tags.includes(t);
        const inText = text.includes(t);
        if (!inTitle && !inSummary && !inTags && !inText) { matched = false; break; }
        if (inTitle) score += 10;
        if (inTags) score += 5;
        if (inSummary) score += 3;
        if (inText) score += 1;
      }
      if (!matched) continue;

      const snippet = summary || '';
      scored.push({ title: a.title, slug: a.slug, category: a.category, summary: a.summary, date: a.date, snippet, score });
    }

    scored.sort((a, b) => b.score - a.score);
    return scored;
  }

  // ───── 搜索（基于静态索引）─────
  const searchInput = document.getElementById('search-input');
  const searchDropdown = document.getElementById('search-results');
  let debounceTimer = null;

  if (searchInput && searchDropdown) {
    searchInput.addEventListener('input', () => {
      clearTimeout(debounceTimer);
      const q = searchInput.value.trim();

      if (q.length < 1) {
        searchDropdown.classList.remove('active');
        return;
      }

      debounceTimer = setTimeout(async () => {
        try {
          const index = await loadIndex();
          const data = matchArticles(index, q).slice(0, 8);

          if (data.length === 0) {
            searchDropdown.innerHTML = '<div class="search-item"><div class="search-item-title" style="color:var(--ink-muted)">没有找到相关文章</div></div>';
          } else {
            searchDropdown.innerHTML = data.map(item => `
              <a href="/article/${encodeURIComponent(item.slug)}/" class="search-item">
                <div class="search-item-title">${escHtml(item.title)}</div>
                <div class="search-item-cat">${escHtml(item.category)} · ${escHtml((item.summary || '').slice(0, 100))}</div>
              </a>
            `).join('');
          }
          searchDropdown.classList.add('active');
        } catch (e) {
          console.error('Search error:', e);
        }
      }, 150);
    });

    // 回车跳转搜索页
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && searchInput.value.trim()) {
        window.location.href = `/search/?q=${encodeURIComponent(searchInput.value.trim())}`;
      }
    });

    // 点击外部关闭
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.search-box')) {
        searchDropdown.classList.remove('active');
      }
    });
  }

  // 搜索结果页（/search/?q=xxx）渲染
  (async function initSearchPage() {
    const page = document.querySelector('[data-search-page]');
    if (!page) return;

    const params = new URLSearchParams(window.location.search);
    const q = (params.get('q') || '').trim();

    const qEl = document.getElementById('search-page-query');
    const countEl = document.getElementById('search-page-count');
    const listEl = document.getElementById('search-page-results');
    const emptyEl = document.getElementById('search-page-empty');

    if (!q) return;

    qEl.textContent = `「${q}」`;
    document.title = `搜索「${q}」— 知识库`;
    if (searchInput) searchInput.value = q;

    const index = await loadIndex();
    const hits = matchArticles(index, q);

    countEl.textContent = `找到 ${hits.length} 篇相关文章`;

    if (hits.length === 0) {
      emptyEl.style.display = '';
      return;
    }

    listEl.innerHTML = hits.map(a => `
      <a href="/article/${encodeURIComponent(a.slug)}/" class="article-row">
        <div class="article-row-body">
          <h3>${escHtml(a.title)}</h3>
          ${a.snippet ? `<p>${escHtml(a.snippet)}</p>` : ''}
        </div>
        <div class="article-row-meta">
          ${a.date ? `<span class="article-row-date">${escHtml(a.date)}</span>` : ''}
          <span class="article-row-cat">${escHtml(a.category)}</span>
        </div>
      </a>
    `).join('');
  })();

  // ───── 工具函数 ─────
  function escHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  // ───── 平滑滚动 ─────
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', e => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // ───── 文章目录 (TOC) ─────
  (function initToc() {
    const content = document.querySelector('.article-content');
    if (!content) return;

    // 收集正文中的一级至四级标题
    const headings = content.querySelectorAll('h1, h2, h3, h4');
    if (headings.length < 1) return;
    const topLevel = Math.min(...Array.from(headings, h => Number(h.tagName.slice(1))));

    // 生成目录 HTML
    function buildTocHtml() {
      let html = '<ul class="toc-list">';
      headings.forEach((h, i) => {
        const id = h.id || h.textContent.trim().replace(/\s+/g, '-').toLowerCase();
        if (!h.id) h.id = id;
        const level = Number(h.tagName.slice(1));
        html += `<li class="toc-h${level}" style="--toc-depth:${level - topLevel}"><a href="#${id}" data-index="${i}">${h.textContent.replace(/¶$/, '').trim()}</a></li>`;
      });
      html += '</ul>';
      return html;
    }

    const tocHtml = buildTocHtml();

    // 桌面端侧边栏
    const sidebar = document.createElement('nav');
    sidebar.className = 'toc-sidebar';
    sidebar.innerHTML = '<div class="toc-title">📑 目录</div>' + tocHtml;
    document.body.appendChild(sidebar);

    // 移动端按钮 + 抽屉 + 遮罩
    const overlay = document.createElement('div');
    overlay.className = 'toc-overlay';
    document.body.appendChild(overlay);

    const drawer = document.createElement('nav');
    drawer.className = 'toc-drawer';
    drawer.innerHTML = '<div class="toc-title">📑 目录</div>' + tocHtml;
    document.body.appendChild(drawer);

    const btn = document.createElement('button');
    btn.className = 'toc-mobile-btn';
    btn.textContent = '📑';
    btn.setAttribute('aria-label', '目录');
    document.body.appendChild(btn);

    // 响应式布局：JS 控制显隐（兼容微信等内置浏览器）
    // 用 matchMedia 代替 innerWidth，确保与 CSS @media 使用同一引擎判断
    const siteMain = document.querySelector('.site-main');
    const mql = window.matchMedia('(max-width: 1100px)');
    function updateTocLayout(e) {
      const isMobile = e ? e.matches : mql.matches;
      sidebar.style.display = isMobile ? 'none' : 'block';
      btn.style.display = isMobile ? 'flex' : 'none';
      if (siteMain) siteMain.style.paddingRight = isMobile ? '' : 'calc(220px + 36px)';
    }
    updateTocLayout();
    if (mql.addEventListener) {
      mql.addEventListener('change', updateTocLayout);
    } else if (mql.addListener) {
      mql.addListener(updateTocLayout);
    }

    // 移动端交互
    function openDrawer() {
      drawer.classList.add('open');
      overlay.classList.add('open');
      btn.textContent = '✕';
    }
    function closeDrawer() {
      drawer.classList.remove('open');
      overlay.classList.remove('open');
      btn.textContent = '📑';
    }

    btn.addEventListener('click', () => {
      drawer.classList.contains('open') ? closeDrawer() : openDrawer();
    });
    overlay.addEventListener('click', closeDrawer);

    // 抽屉内链接点击后关闭
    drawer.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        setTimeout(closeDrawer, 150);
      });
    });

    // 滚动高亮
    const allTocLinks = document.querySelectorAll('.toc-list a');
    let ticking = false;

    function updateActive() {
      let activeIndex = 0;
      const scrollY = window.scrollY + 100;

      headings.forEach((h, i) => {
        if (h.offsetTop <= scrollY) activeIndex = i;
      });

      allTocLinks.forEach(a => {
        a.classList.toggle('active', parseInt(a.dataset.index) === activeIndex);
      });

      // 桌面端自动滚动目录
      const sidebarActive = sidebar.querySelector('.active');
      if (sidebarActive) {
        sidebarActive.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }

      ticking = false;
    }

    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(updateActive);
        ticking = true;
      }
    }, { passive: true });

    updateActive();
  })();

  // ───── 文件树侧边栏 ─────
  (function () {
    const sidebar = document.getElementById('sidebar');
    if (!sidebar) return;

    // 移动端：汉堡按钮 + 关闭按钮 + 遮罩 + ESC
    const toggleBtn = document.getElementById('sidebar-toggle');
    const closeBtn = document.getElementById('sidebar-close');
    const backdrop = document.getElementById('sidebar-backdrop');
    const open = () => { sidebar.classList.add('open'); backdrop && backdrop.classList.add('open'); };
    const close = () => { sidebar.classList.remove('open'); backdrop && backdrop.classList.remove('open'); };

    toggleBtn && toggleBtn.addEventListener('click', () => {
      sidebar.classList.contains('open') ? close() : open();
    });
    closeBtn && closeBtn.addEventListener('click', close);
    backdrop && backdrop.addEventListener('click', close);
    document.addEventListener('keydown', e => { if (e.key === 'Escape') close(); });

    // sessionStorage 记忆分类展开/折叠状态
    sidebar.querySelectorAll('details.tree-node').forEach(d => {
      const cat = d.dataset.cat;
      if (!cat) return;
      const key = 'tree:open:' + cat;
      const saved = sessionStorage.getItem(key);
      if (saved !== null) d.open = saved === '1';
      d.addEventListener('toggle', () => {
        sessionStorage.setItem(key, d.open ? '1' : '0');
      });
    });

    // 把当前文章滚到可视区域
    const active = sidebar.querySelector('.tree-article.active');
    if (active) active.scrollIntoView({ block: 'center' });
  })();

})();

/* ───── 首页折叠交互 ───── */
function toggleExtra(type) {
  if (type === 'cats') {
    const extras = document.querySelectorAll('.category-card-extra');
    const btn = document.getElementById('btn-expand-cats');
    const isHidden = extras[0] && extras[0].classList.contains('hidden');
    extras.forEach(el => el.classList.toggle('hidden'));
    if (btn) btn.textContent = isHidden ? '收起 ▴' : '展开全部 ' + extras.length + ' 个分类 ▾';
  } else if (type === 'tags') {
    const cloud = document.getElementById('tag-cloud-body');
    const btn = document.getElementById('btn-expand-tags');
    if (!cloud) return;
    const isCollapsed = cloud.classList.contains('tag-cloud-collapsed');
    cloud.classList.toggle('tag-cloud-collapsed');
    cloud.classList.toggle('tag-cloud-expanded');
    if (btn) btn.textContent = isCollapsed ? '收起 ▴' : '展开 ' + cloud.children.length + ' 个标签 ▾';
  }
}

/* ───── 首页侧边栏：滚动高亮 ───── */
(function() {
  const tocLinks = document.querySelectorAll('.index-toc-link[href^="#"]');
  if (!tocLinks.length) return;

  const sections = [];
  tocLinks.forEach(link => {
    const id = link.getAttribute('href').slice(1);
    const section = document.getElementById(id);
    if (section) sections.push({ el: section, link: link });
  });

  function updateActive() {
    let current = null;
    const scrollY = window.scrollY + 120;

    for (const { el, link } of sections) {
      if (el.offsetTop <= scrollY) {
        current = link;
      }
    }

    tocLinks.forEach(l => l.classList.remove('active'));
    if (current) current.classList.add('active');
  }

  window.addEventListener('scroll', updateActive, { passive: true });
  updateActive();
})();
