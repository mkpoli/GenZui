(() => {
  const node = document.getElementById('compare-glyphs');
  const chart = document.getElementById('chart');
  if (!node || !chart) return;
  const state = {a: 'genzui-sans', b: 'sukima', set: 'hentaigana', overlay: false};
  let data = null;
  const $ = id => document.getElementById(id);
  const svg = (font, cp, cls) => {
    const entry = data.fonts[font].glyphs[cp];
    const inner = entry ? `<path d="${entry[1]}"/>` : '<rect x="140" y="-700" width="720" height="780"/>';
    return `<svg class="g ${cls}${entry ? '' : ' tofu'}" viewBox="0 -880 1000 1000" aria-hidden="true">${inner}</svg>`;
  };
  const credit = id => {
    const f = data.fonts[id];
    return `${f.credit}, <a href="${f.licence_url}">${f.licence}</a>`;
  };
  function render() {
    const codes = data.sets[state.set].codepoints;
    const pair = data.overlap[`${state.a}|${state.b}`] || data.overlap[`${state.b}|${state.a}`] || {};
    const nameA = data.fonts[state.a].name, nameB = data.fonts[state.b].name;
    let hasA = 0, hasB = 0, same = 0;
    chart.classList.toggle('overlay', state.overlay);
    chart.innerHTML = codes.map(cp => {
      const inA = !!data.fonts[state.a].glyphs[cp], inB = !!data.fonts[state.b].glyphs[cp];
      hasA += inA; hasB += inB;
      const overlap = pair[cp];
      const isSame = overlap >= 90;
      same += isSame;
      const name = data.names[cp] || '';
      const label = `U+${cp} ${name}. ${nameA}: ${inA ? 'drawn' : 'not mapped'}. ${nameB}: ${inB ? 'drawn' : 'not mapped'}.` +
        (overlap === undefined ? '' : ` Overlap ${overlap}%.`);
      return `<li class="cell${isSame ? ' same' : ''}" title="U+${cp} ${name}">` +
        `<div class="pair" role="img" aria-label="${label}">${svg(state.a, cp, 'a')}${svg(state.b, cp, 'b')}</div>` +
        `<code>${cp}</code>${overlap === undefined ? '' : `<small>${overlap}%</small>`}</li>`;
    }).join('');
    $('legend-a').textContent = nameA;
    $('legend-b').textContent = nameB;
    $('chart-status').textContent = `${data.sets[state.set].name}: ${codes.length} characters. ${nameA} maps ${hasA}, ${nameB} maps ${hasB}, ${same} overlap by 90% or more.`;
    $('chart-credit').innerHTML = `Outlines: ${credit(state.a)}; ${credit(state.b)}.`;
  }
  function start() {
    document.querySelectorAll('[data-set]').forEach(b => b.addEventListener('click', () => {
      state.set = b.dataset.set;
      document.querySelectorAll('[data-set]').forEach(x => x.setAttribute('aria-pressed', String(x === b)));
      render();
    }));
    $('font-a').addEventListener('change', e => { state.a = e.target.value; render(); });
    $('font-b').addEventListener('change', e => { state.b = e.target.value; render(); });
    const toggle = $('overlay');
    toggle.addEventListener('click', () => {
      state.overlay = toggle.getAttribute('aria-pressed') !== 'true';
      toggle.setAttribute('aria-pressed', String(state.overlay));
      toggle.textContent = state.overlay ? 'Side by side' : 'Overlay';
      render();
    });
    state.a = $('font-a').value; state.b = $('font-b').value;
    render();
  }
  const source = node.dataset.src;
  if (source) {
    fetch(source).then(r => r.json()).then(json => { data = json; start(); })
      .catch(() => { $('chart-status').textContent = 'The glyph data did not load.'; });
  } else {
    data = JSON.parse(node.textContent);
    start();
  }
})();
