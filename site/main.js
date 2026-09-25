(() => {
  'use strict';
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const number = value => value.toLocaleString('en-US');
  const code = cp => `U+${cp.toString(16).toUpperCase().padStart(4, '0')}`;
  const character = item => String.fromCodePoint(item.cp);
  const source = document.querySelector('#font-data');
  // The specimen works as soon as the page loads; the inventory arrives after its fetch.
  const familyName = source.dataset.family || 'GenZui Serif';
  let byCode = new Map();
  let inventoryLoaded = false;
  const presets = {
    numerals: '〇一二三四五六七八九十\n廿 卄 卅 卌　百千万億兆\n壱弐参拾　〡〢〣〤〥〦〧〨〩',
    tallies: '𝍲 𝍳 𝍴 𝍵 𝍶\n一 正',
    'ideographic-description': '⿰ ⿱ ⿲ ⿳ ⿴ ⿵\n⿶ ⿷ ⿸ ⿹ ⿺ ⿻\n⿼ ⿽ ⿾ ⿿ ㇯',
    mixed: '春はあけぼの。\nかなのかたちを読む。\nあ𛀂 い𛀆 う𛀋 え𛀁 お𛀕\nこの𛄣、その𛄤𛄦',
    reading: '春はあけぼの。\nやうやう白くなりゆく山ぎは。\n文字を読み、ことばをたどる。',
    historical: 'あ 𛀂 𛀃 𛀄 𛀅\nい 𛀆 𛀇 𛀈 𛀉\nう 𛀊 𛀋 𛀌 𛀍 𛀎',
    unicode18: '𛄣 𛄤 𛄥 𛄦 𛄧 𛄨 𛅨',
    ligatures: 'ゟ ヿ 𪜈 𬻿 𬼀 𬼂\n𛄣 𛄤 𛄥 𛄦 ㌬',
    drawings: 'この𛄣、その𛄤𛄦\n𛄣 𛄤 𛄥 𛄦 𪜈 𬻿 𬼀 𬼂\n𛄟 𛄧 𛄨　ネ𛄧 ヰ𛄨',
    small: 'ゃ ゅ ょ ゎ　𛄲 𛅐 𛅑 𛅒\nャ ュ ョ ヮ　𛅕 𛅤 𛅥 𛅦 𛅧 𛅨',
    okinawan: '\uF450 \uF452 \uF454 \uF456 \uF458 \uF465\n\uF45A \uF45B \uF45C \uF467 \uF469\n\uF45D \uF45E \uF45F \uF460 \uF461 \uF462 \uF463\n\uF450\u3099 \uF452\u3099 \uF454\u3099 \uF467\u3099 い\u3099 え\u3099\n\uE534ウトゥ \uE532\uE533\uE535\uE536\uE537\uE4EF\uE5AA',
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
      : isBold() && boldState === 'failed' ? `${familyName} Bold could not load. Try Regular, or reopen this page in a current browser.`
      : isBold() && boldState !== 'loaded' ? `Loading ${familyName} Bold…`
      : !inventoryLoaded ? `${number([...typeInput.value].length)} characters · ${familyName} ${weightName()}`
      : missing.length ? `${number(points.length)} characters · ${missing.length} outside this font: ${missing.slice(0, 4).map(c => code(c.codePointAt(0))).join(', ')}${missing.length > 4 ? '…' : ''}`
      : `${number(points.length)} characters · ${familyName} ${weightName()}`;
  }
  // One weight for every sample on the page. The header and specimen switches
  // show the current choice, and ?weight=bold keeps it in the link.
  const weightButtons = $$('button[data-weight]');
  const isBold = () => document.body.dataset.weight === '700';
  const weightName = () => isBold() ? 'Bold' : 'Regular';
  // Bold loads only when chosen, so the status and the Bold buttons wait for it.
  let boldState = 'idle';
  function setWeight(weight, remember = true) {
    document.body.dataset.weight = weight;
    weightButtons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.weight === weight)));
    if (weight === '700' && (boldState === 'idle' || boldState === 'failed')) {
      boldState = 'loading';
      weightButtons.forEach(button => { if (button.dataset.weight === '700') button.setAttribute('aria-busy', 'true'); });
      document.fonts.load('700 48px GenZui', '源萃𛄤').then(faces => {
        if (!faces.length) throw new Error('GenZui Bold unavailable');
        boldState = 'loaded';
      }).catch(() => { boldState = 'failed'; }).finally(() => {
        weightButtons.forEach(button => button.removeAttribute('aria-busy'));
        typeStatus();
      });
    }
    // Samples fade until every face the new layout requests has arrived.
    document.body.classList.add('weight-switching');
    requestAnimationFrame(() => requestAnimationFrame(() => document.fonts.ready
      .finally(() => document.body.classList.remove('weight-switching'))));
    if (remember) {
      const url = new URL(location.href);
      if (weight === '700') url.searchParams.set('weight', 'bold'); else url.searchParams.delete('weight');
      history.replaceState(history.state, '', url);
    }
    typeStatus();
    document.dispatchEvent(new CustomEvent('genzui:weight'));
  }
  weightButtons.forEach(button => button.addEventListener('click', () => setWeight(button.dataset.weight)));
  if (weightButtons.length && new URLSearchParams(location.search).get('weight') === 'bold') setWeight('700', false);
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

  const params = new URLSearchParams(location.search);
  const initialPreset = params.get('sample');
  // The Serif and Sans pages share these presets but each offers only its own.
  const offered = [...$('#preset').options].map(option => option.value);
  if (Object.hasOwn(presets, initialPreset) && offered.includes(initialPreset)) { $('#preset').value = initialPreset; setPreset(); }
  typeStatus();

  (async () => {
    const data = source.dataset.src
      ? await fetch(source.dataset.src).then(response => {
          if (!response.ok) throw new Error('Character inventory unavailable');
          return response.json();
        })
      : JSON.parse(source.textContent);
    const all = data.characters;
    byCode = new Map(all.map(item => [item.cp, item]));
    // Source labels come with the data, so both family pages share this script.
    const origins = data.origins || {
      jp: 'Noto Serif JP', hentaigana: 'Noto Serif Hentaigana',
       genzui: 'GenZui construction', frb: 'FRB Taiwanese Kana', cjk: 'Noto Serif CJK JP',
    };
    const filters = {
    historical: item => ['hentaigana', 'historic-kana', 'small-kana', 'bmp-digraph', 'cjk-kana-ligature', 'minnan-tone', 'phonetic-mark', 'compatibility-kana'].includes(item.group),
    hentaigana: item => item.group === 'hentaigana',
    unicode18: item => item.group !== 'base' && item.age === '18.0',
    small: item => item.group === 'small-kana',
    okinawan: item => item.group === 'okinawan',
    minnan: item => ['minnan-tone', 'phonetic-mark'].includes(item.group),
    ligatures: item => item.group !== 'base' && (item.label.includes('DIGRAPH') || item.group === 'cjk-kana-ligature'),
    numerals: item => item.group === 'han-numeral',
    tallies: item => item.group === 'tally-mark',
    'ideographic-description': item => item.group === 'ideographic-description',
    all: () => true,
    };
    let filter = 'historical';
    const initialSource = params.get('source');
    if (Object.hasOwn(origins, initialSource)) { $('#source-filter').value = initialSource; filter = 'all'; }
    if (['numerals', 'tallies', 'ideographic-description'].includes(params.get('sample'))) filter = params.get('sample');
    let page = 0;
    const pageSize = 48;
    let selected = byCode.get(0x309F);
    let matches = [];

    function display(item) {
    if (item.category[0] === 'Z' || ['Cc', 'Cf', 'Cs', 'Cn'].includes(item.category)) {
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

    document.addEventListener('genzui:weight', () => { if (selected) updateInspector(selected); });
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
      : isBold() && item.bold_description ? item.bold_description
      : item.description ? item.description
      : item.provisional ? 'Noto components and original drawing. Joins, proportions and weight remain under review.'
      : item.source === 'jp' ? `Original ${origins.jp} outline, with its Japanese layout behaviour preserved.`
      : `Original ${origins[item.source]} outline, preserved in GenZui.`;
    $('#detail-age').textContent = item.age;
    $('#detail-block').textContent = item.block;
    $('#detail-source').textContent = isBold() && item.bold_source ? item.bold_source : origins[item.source];
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
    $('#browse-constructions')?.addEventListener('click', event => {
    if (event.button || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    $('#character-search').value = ''; $('#source-filter').value = 'genzui'; chooseFilter('all');
    });


    renderInventory();
    updateInspector(selected);
    inventoryLoaded = true;
    typeStatus();
  })().catch(() => {
    $('#result-count').textContent = 'The character inventory could not load. Please reload the page.';
    $('#character-grid').hidden = true;
  });
})();
