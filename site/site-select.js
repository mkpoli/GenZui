// The logo link on each page becomes a button that opens a menu of the sibling fonts.
// Without script the link stays as it is. The menu is a popover, so no header overflow clips it.
(() => {
  if (!HTMLElement.prototype.showPopover) return;
  const own = document.currentScript;
  const SITES = [
    { id: 'kureedo', href: 'https://kureedo.mkpo.li/', name: 'Kureedo', sub: 'クレード' },
    { id: 'genzui', href: 'https://genzui.mkpo.li/', name: '源萃', sub: 'GenZui' },
  ];
  const TEXT = {
    en: ['Sites', 'More writing-system projects', ''],
    ja: ['サイト', '他の文字プロジェクト', 'ja/'],
    'zh-Hans': ['网站', '更多文字项目', 'zh-Hans/'],
    'zh-Hant': ['網站', '更多文字專案', 'zh-Hant/'],
    ko: ['사이트', '다른 문자 프로젝트', 'ko/'],
  };
  const language = () => {
    const tag = (document.documentElement.lang || 'en').toLowerCase();
    if (tag.startsWith('zh')) return /hant|tw|hk|mo/.test(tag) ? 'zh-Hant' : 'zh-Hans';
    return TEXT[tag.split('-')[0]] ? tag.split('-')[0] : 'en';
  };
  const [LABEL, MORE, MORE_PATH] = TEXT[language()];
  const NAME_KEY = /^(ja|zh)/i.test(document.documentElement.lang) ? 'name' : 'sub';
  const NS = 'http://www.w3.org/2000/svg';
  const el = (tag, props = {}, kids = []) => {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(props)) node.setAttribute(key, value);
    node.append(...kids);
    return node;
  };
  const icon = (cls, d) => {
    const svg = document.createElementNS(NS, 'svg');
    svg.setAttribute('viewBox', '0 0 24 24');
    svg.setAttribute('aria-hidden', 'true');
    if (cls) svg.setAttribute('class', cls);
    const path = document.createElementNS(NS, 'path');
    path.setAttribute('d', d);
    svg.append(path);
    return svg;
  };
  let openMenu = null;

  const upgrade = link => {
    const current = link.dataset.siteSelect;
    const name = SITES.find(site => site.id === current)[NAME_KEY];
    const trigger = el('button', { type: 'button', class: 'site-select-trigger', 'aria-haspopup': 'menu', 'aria-expanded': 'false', 'aria-label': `${name}: ${LABEL}` });
    const style = getComputedStyle(link);
    const logo = el('span', { class: 'site-select-logo' });
    Object.assign(logo.style, { display: style.display, alignItems: style.alignItems, gap: style.columnGap });
    logo.append(...link.childNodes);
    trigger.append(logo, icon('site-select-chev', 'M6 9l6 6 6-6'));
    const menu = el('div', { class: 'site-select-menu', role: 'menu', popover: 'manual', 'aria-label': LABEL });
    if (link.dataset.look) menu.dataset.look = link.dataset.look;
    const items = SITES.map(site => {
      const here = site.id === current;
      const row = el('a', { role: 'menuitem', tabindex: '-1', href: here ? link.getAttribute('href') : site.href }, [
        el('img', { src: own.dataset[site.id + 'Logo'] || '', alt: '', width: '28', height: '28' }),
        el('span', { class: 'site-select-name' }, [site.name, el('small', { lang: site.id === 'genzui' ? 'en' : 'ja' }, [site.sub])]),
        icon('site-select-tick', 'M4 12.5l5 5L20 6.5'),
      ]);
      if (here) row.setAttribute('aria-current', 'true');
      return row;
    });
    const more = el('a', { role: 'menuitem', tabindex: '-1', class: 'site-select-more', href: 'https://scripts.mkpo.li/' + MORE_PATH }, [
      el('span', { class: 'site-select-name' }, [MORE]), icon('site-select-arrow', 'M7 17L17 7M9 7h8v8'),
    ]);
    menu.append(...items, el('hr', { role: 'separator' }), more);
    items.push(more);
    const wrap = el('span', { class: (link.className + ' site-select').trim() }, [trigger, menu]);
    if (link.dataset.look) wrap.dataset.look = link.dataset.look;
    link.replaceWith(wrap);
    const first = items[SITES.findIndex(site => site.id === current)] || items[0];

    const isOpen = () => menu.matches(':popover-open');
    const close = back => {
      if (!isOpen()) return;
      menu.hidePopover();
      trigger.setAttribute('aria-expanded', 'false');
      if (openMenu === close) openMenu = null;
      if (back === true) trigger.focus({ preventScroll: true });
    };
    const show = () => {
      if (openMenu) openMenu();
      menu.showPopover();
      trigger.setAttribute('aria-expanded', 'true');
      const box = trigger.getBoundingClientRect(), gutter = 8;
      menu.style.left = Math.max(gutter, Math.min(box.left, innerWidth - menu.offsetWidth - gutter)) + 'px';
      const below = box.bottom + 8;
      menu.style.top = (below + menu.offsetHeight > innerHeight - gutter ? Math.max(gutter, box.top - 8 - menu.offsetHeight) : below) + 'px';
      openMenu = close;
      first.focus({ preventScroll: true });
    };
    trigger.addEventListener('click', () => (isOpen() ? close() : show()));
    trigger.addEventListener('keydown', e => {
      if (e.key === 'ArrowDown' && !isOpen()) { e.preventDefault(); show(); }
    });
    menu.addEventListener('keydown', e => {
      e.stopPropagation();
      let i = items.indexOf(document.activeElement);
      const n = items.length;
      if (e.key === 'ArrowDown') i = (i + 1) % n;
      else if (e.key === 'ArrowUp') i = (i - 1 + n) % n;
      else if (e.key === 'Home') i = 0;
      else if (e.key === 'End') i = n - 1;
      else if (e.key === ' ') { e.preventDefault(); if (i >= 0) items[i].click(); return; }
      else if (e.key === 'Escape') { e.preventDefault(); close(true); return; }
      else if (e.key === 'Tab') { close(true); return; }
      else return;
      e.preventDefault();
      items[i].focus({ preventScroll: true });
    });
    menu.addEventListener('click', e => { if (e.target.closest('a')) close(); });
    document.addEventListener('pointerdown', e => { if (isOpen() && !wrap.contains(e.target)) close(); });
    let width = innerWidth, top = scrollY;
    addEventListener('resize', () => { if (innerWidth !== width) close(); width = innerWidth; });
    addEventListener('scroll', () => { if (Math.abs(scrollY - top) > 1) close(); top = scrollY; }, { passive: true });
  };
  document.querySelectorAll('a[data-site-select]').forEach(upgrade);
})();
