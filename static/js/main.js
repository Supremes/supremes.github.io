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

  // ───── 搜索（纯前端，基于 search-index.json）─────
  let _indexPromise = null;
  function loadIndex() {
    if (!_indexPromise) {
      _indexPromise = fetch('/search-index.json').then(r => r.json()).catch(() => []);
    }
    return _indexPromise;
  }

  function matchArticles(index, q) {
    const ql = q.toLowerCase();
    const hits = [];
    for (const a of index) {
      if (
        a.title.toLowerCase().includes(ql) ||
        (a.summary || '').toLowerCase().includes(ql) ||
        (a.text || '').includes(ql) ||
        (a.tags || []).some(t => t.toLowerCase().includes(ql))
      ) {
        // 摘取片段
        const src = a.text || '';
        const i = src.indexOf(ql);
        const snippet = i >= 0
          ? '...' + src.slice(Math.max(0, i - 50), i + ql.length + 50).replace(/\n/g, ' ') + '...'
          : (a.summary || '');
        hits.push({ ...a, snippet });
      }
    }
    return hits;
  }

  // 顶部下拉搜索
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
        const index = await loadIndex();
        const data = matchArticles(index, q).slice(0, 10);

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

    const headings = content.querySelectorAll('h2, h3');
    if (headings.length < 2) return;  // 标题太少不显示目录

    // 生成目录 HTML
    function buildTocHtml() {
      let html = '<ul class="toc-list">';
      headings.forEach((h, i) => {
        const id = h.id || h.textContent.trim().replace(/\s+/g, '-').toLowerCase();
        if (!h.id) h.id = id;
        const cls = h.tagName === 'H3' ? ' class="toc-h3"' : '';
        html += `<li${cls}><a href="#${id}" data-index="${i}">${h.textContent.replace(/¶$/, '').trim()}</a></li>`;
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
