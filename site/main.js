(async () => {
  'use strict';
  const source = document.querySelector('#font-data');
  const data = source.dataset.src
    ? await fetch(source.dataset.src).then(response => {
        if (!response.ok) throw new Error('Character inventory unavailable');
        return response.json();
      })
    : JSON.parse(source.textContent);
  const all = data.characters;
  const byCode = new Map(all.map(item => [item.cp, item]));
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const number = value => value.toLocaleString('en-US');
  const code = cp => `U+${cp.toString(16).toUpperCase().padStart(4, '0')}`;
  const character = item => String.fromCodePoint(item.cp);
  const origins = {
    jp: 'Noto Serif JP', hentaigana: 'Noto Serif Hentaigana',
     genzui: 'GenZui construction', frb: 'FRB Taiwanese Kana',
  };
  const filters = {
    historical: item => item.group !== 'base',
    hentaigana: item => item.group === 'hentaigana',
    unicode18: item => item.group !== 'base' && item.age === '18.0',
    small: item => item.group === 'small-kana',
    minnan: item => ['minnan-tone', 'phonetic-mark'].includes(item.group),
    ligatures: item => item.group !== 'base' && (item.label.includes('DIGRAPH') || item.group === 'cjk-kana-ligature'),
    all: () => true,
  };
  let filter = 'historical';
  let page = 0;
  const pageSize = 48;
  let selected = byCode.get(0x309F);
  let matches = [];

  function display(item) {
    if (item.category[0] === 'Z' || item.category[0] === 'C') {
      return { text: item.category[0] === 'Z' ? 'SPACE' : 'CONTROL', invisible: true };
    }
    if (item.category[0] === 'M') {
      const base = [0x0305, 0x0323].includes(item.cp) ? 'チ' : [0x3099, 0x309A].includes(item.cp) ? 'か' : (byCode.has(0x25CC) ? '◌' : 'a');
      return { text: base + character(item), mark: true };
    }
    return { text: character(item) };
  }

  function span(className, text) {
    const element = document.createElement('span');
    element.className = className;
    element.textContent = text;
    return element;
  }

  function updateInspector(item) {
    selected = item;
    const picture = display(item);
    $('#detail-code').textContent = code(item.cp);
    $('#detail-glyph').textContent = picture.text;
    $('#detail-glyph').classList.toggle('nonprinting', Boolean(picture.invisible));
    $('#detail-name').textContent = item.label;
    $('#detail-status').textContent = item.provisional ? 'Provisional' : 'Established';
    $('#detail-status').classList.toggle('provisional', item.provisional);
    $('#detail-description').textContent = picture.invisible
      ? 'This code point has no visible outline in ordinary text.'
      : picture.mark ? 'Combining mark, shown with a base character. Copy copies the mark only.'
      : item.description ? item.description
      : item.provisional ? 'Noto components and original drawing. Joins, proportions and weight remain under review.'
      : item.source === 'hentaigana' ? 'Original Noto Serif Hentaigana outline, preserved in GenZui.'
      : 'Original Noto Serif JP outline, with its Japanese layout behaviour preserved.';
    $('#detail-age').textContent = item.age;
    $('#detail-block').textContent = item.block;
    $('#detail-source').textContent = origins[item.source];
    $('#copy-status').textContent = '';
    $$('.glyph-button').forEach(button => {
      button.setAttribute('aria-pressed', String(Number(button.dataset.cp) === item.cp));
    });
  }

  function queryMatches(item, query) {
    if (!query) return true;
    const literal = [...query];
    if (literal.length === 1 && byCode.has(literal[0].codePointAt(0))) return item.cp === literal[0].codePointAt(0);
    if (/^[^\x00-\x7F]+$/u.test(query)) return literal.includes(character(item));
    const hex = query.match(/^(?:U\+|0X)([0-9A-F]{1,6})$/i);
    if (hex) return item.cp === parseInt(hex[1], 16);
    return [item.label, item.name, item.block, code(item.cp), origins[item.source]].some(text => text.toUpperCase().includes(query.toUpperCase()));
  }

  function renderInventory() {
    const query = $('#character-search').value.trim();
    const origin = $('#source-filter').value;
    matches = all.filter(item => filters[filter](item) && (origin === 'all' || item.source === origin) && queryMatches(item, query));
    if (matches.length && !matches.some(item => item.cp === selected.cp)) updateInspector(matches[0]);
    $('#glyph-detail').hidden = !matches.length;
    const pages = Math.max(1, Math.ceil(matches.length / pageSize));
    page = Math.min(page, pages - 1);
    const start = page * pageSize;
    const visible = matches.slice(start, start + pageSize);
    const grid = $('#character-grid');
    const fragment = document.createDocumentFragment();
    for (const item of visible) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'glyph-button';
      button.dataset.cp = String(item.cp);
      button.setAttribute('aria-pressed', String(selected.cp === item.cp));
      button.setAttribute('aria-label', `${item.label}, ${code(item.cp)}${item.provisional ? ', provisional' : ''}`);
      const picture = display(item);
      const drawing = span(`face${picture.invisible ? ' nonprinting' : ''}`, picture.text);
      drawing.lang = 'ja';
      drawing.setAttribute('aria-hidden', 'true');
      button.append(drawing, span('code', code(item.cp)));
      if (item.provisional) {
        const dot = span('construction-dot', '');
        dot.setAttribute('aria-hidden', 'true');
        button.append(dot);
      }
      button.addEventListener('click', () => {
        updateInspector(item);
        if (window.matchMedia('(max-width:520px)').matches) {
          $('#glyph-detail').scrollIntoView({ block: 'nearest' });
        }
      });
      fragment.append(button);
    }
    grid.replaceChildren(fragment);
    grid.hidden = !matches.length;
    $('#empty-state').hidden = Boolean(matches.length);
    $('#result-count').textContent = `${number(matches.length)} ${matches.length === 1 ? 'character' : 'characters'}${origin === 'genzui' ? ' · provisional outlines' : ''}`;
    $('#page-label').textContent = matches.length
      ? `${number(start + 1)}–${number(Math.min(start + pageSize, matches.length))} of ${number(matches.length)} · Page ${page + 1} / ${pages}`
      : '0 results';
    $('#previous-page').disabled = page === 0;
    $('#next-page').disabled = page >= pages - 1;
    $$('.inventory-filters button').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === filter)));
  }

  function chooseFilter(value) {
    filter = value; page = 0;
    renderInventory();
  }
  $$('.inventory-filters button').forEach(button => button.addEventListener('click', () => chooseFilter(button.dataset.filter)));
  $('#character-search').addEventListener('input', () => { page = 0; renderInventory(); });
  $('#source-filter').addEventListener('change', () => { page = 0; renderInventory(); });
  $('#search-all').addEventListener('click', () => { $('#source-filter').value = 'all'; chooseFilter('all'); });
  $('#previous-page').addEventListener('click', () => { page--; renderInventory(); });
  $('#next-page').addEventListener('click', () => { page++; renderInventory(); });

  $('#copy-character').addEventListener('click', async () => {
    const item = selected;
    let copied = false;
    if (navigator.clipboard && window.isSecureContext) {
      try { await navigator.clipboard.writeText(character(item)); copied = true; } catch { /* Try local-file-compatible copying below. */ }
    }
    if (!copied) {
      const input = document.createElement('textarea');
      input.value = character(item);
      input.setAttribute('aria-label', 'Character to copy');
      input.style.cssText = 'position:fixed;left:-9999px;top:0';
      document.body.append(input);
      input.select();
      try { copied = document.execCommand('copy'); } catch { copied = false; }
      input.remove();
      $('#copy-character').focus({ preventScroll: true });
    }
    if (selected.cp === item.cp) $('#copy-status').textContent = copied ? `Copied ${code(item.cp)}` : `Copy unavailable here. Select the glyph above to copy ${code(item.cp)}.`;
  });

  const shortNames = ['KOTO', 'TOKI', 'TOTE', 'YORI', 'ALTERNATE NE', 'ALTERNATE WI', 'SMALL YE'];
  all.filter(filters.unicode18).forEach((item, index) => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'unicode-card';
    button.setAttribute('aria-label', `Inspect ${item.label}, ${code(item.cp)}`);
    button.append(span('code', code(item.cp)), span('face', character(item)), span('label', shortNames[index]));
    button.addEventListener('click', () => {
      $('#character-search').value = ''; $('#source-filter').value = 'all';
      updateInspector(item); chooseFilter('unicode18');
      $('#characters').scrollIntoView({ block: 'start' });
    });
    $('#unicode-grid').append(button);
  });
  $('#browse-unicode').addEventListener('click', () => {
    $('#character-search').value = ''; $('#source-filter').value = 'all'; chooseFilter('unicode18');
  });

  const presets = {
    mixed: '春はあけぼの。\nかなのかたちを読む。\nあ𛀂 い𛀆 う𛀋 え𛀁 お𛀕',
    reading: '春はあけぼの。\nやうやう白くなりゆく山ぎは。\n文字を読み、ことばをたどる。',
    historical: 'あ 𛀂 𛀃 𛀄 𛀅\nい 𛀆 𛀇 𛀈 𛀉\nう 𛀊 𛀋 𛀌 𛀍 𛀎',
    unicode18: '𛄣 𛄤 𛄥 𛄦 𛄧 𛄨 𛅨',
    ligatures: 'ゟ ヿ 𪜈 𬻿 𬼀 𬼂\n𛄣 𛄤 𛄥 𛄦',
    marks: '𛀂\u3099 𛀂\u309a　𛀙\u3099 𛀙\u309a\n𛄤\u3099 𛄤\u309a　𛅨\u3099 𛅨\u309a',
    minnan: 'チ\u0305ァム𚿵 チ\u0305ァム𚿵 チ\u0305\u0323ア𚿷\nウ\u0305 ゥ\u0305 オ\u0305 ォ\u0305',
  };
  let loaded = false;
  let loadFailed = false;
  const typeInput = $('#type-input');
  function typeStatus() {
    const points = [...typeInput.value];
    const missing = [...new Set(points.filter(c => !/[\r\n\t]/.test(c) && !byCode.has(c.codePointAt(0))))];
    $('#type-status').textContent = loadFailed ? 'The embedded font could not load. Try reopening this page in a current browser.'
      : !loaded ? 'Loading the font…'
      : missing.length ? `${number(points.length)} characters · ${missing.length} outside this font: ${missing.slice(0, 4).map(c => code(c.codePointAt(0))).join(', ')}${missing.length > 4 ? '…' : ''}`
      : `${number(points.length)} characters · GenZui Serif Regular`;
  }
  function setPreset() { typeInput.value = presets[$('#preset').value]; typeInput.scrollTop = 0; typeInput.scrollLeft = 0; typeStatus(); }
  $('#preset').addEventListener('change', setPreset);
  typeInput.addEventListener('input', typeStatus);
  $('#type-size').addEventListener('input', event => {
    typeInput.style.fontSize = `${event.target.value}px`;
    $('#size-value').textContent = `${event.target.value} px`;
  });
  $('#type-spacing').addEventListener('input', event => {
    const amount = Number(event.target.value) / 100;
    typeInput.style.letterSpacing = `${amount}em`;
    $('#spacing-value').textContent = `${amount} em`;
  });
  function setDirection(direction) {
    typeInput.classList.toggle('is-vertical', direction === 'vertical');
    $$('[data-direction]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.direction === direction)));
  }
  $$('[data-direction]').forEach(button => button.addEventListener('click', () => setDirection(button.dataset.direction)));
  $('#reset-type').addEventListener('click', () => {
    const size = window.innerWidth <= 520 ? 30 : window.innerWidth <= 760 ? 36 : 48;
    $('#type-size').value = size; $('#type-spacing').value = 0;
    typeInput.style.fontSize = `${size}px`; typeInput.style.letterSpacing = '0em';
    $('#size-value').textContent = `${size} px`; $('#spacing-value').textContent = '0 em';
    setDirection('horizontal'); setPreset();
  });
  const initialSize = Math.round(parseFloat(getComputedStyle(typeInput).fontSize));
  $('#type-size').value = initialSize; $('#size-value').textContent = `${initialSize} px`;
  document.fonts.load('48px GenZui', '源萃𛄤').then(faces => {
    if (!faces.length) throw new Error('GenZui face unavailable');
    loaded = true; typeStatus();
  }).catch(() => { loadFailed = true; typeStatus(); });

  renderInventory();
  updateInspector(selected);
  typeStatus();
})().catch(() => {
  document.querySelector('#type-status').textContent = 'The specimen could not load. Please reload the page. Font downloads remain available below.';
});
