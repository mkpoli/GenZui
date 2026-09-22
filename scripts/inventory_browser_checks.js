(async () => {
  const $ = selector => document.querySelector(selector);
  const $$ = selector => [...document.querySelectorAll(selector)];
  const checks = [];
  const check = (name, condition) => { if (!condition) throw new Error(name); checks.push(name); };
  const change = (selector, value) => {
    const element = $(selector);
    element.value = value;
    element.dispatchEvent(new Event('change', { bubbles: true }));
  };
  await document.fonts.load('48px GenZui', '卄𝍲𝍳𝍴𝍵𝍶⿼⿽⿾⿿㇯');
  await document.fonts.ready;
  for (let i = 0; i < 100 && !$('.glyph-button'); i++) await new Promise(resolve => setTimeout(resolve, 50));
  const counts = { numerals: 80, tallies: 5, 'ideographic-description': 17 };
  const initial = new URLSearchParams(location.search).get('sample');
  if (Object.hasOwn(counts, initial)) {
    check(`${initial} permalink selects sample`, $('#preset').value === initial);
    check(`${initial} permalink selects collection`, $(`[data-filter="${initial}"]`).getAttribute('aria-pressed') === 'true');
    check(`${initial} permalink count`, $('#result-count').textContent.startsWith(`${counts[initial]} `));
  }
  check('no release-batch collection', !$('[data-filter="honkoku"]') && !$('#preset option[value="honkoku"]'));
  const sets = {
    numerals: [0x3007, 0x4E00, 0x5344, 0x5EFF, 0x5345, 0x534C, 0x3038],
    tallies: Array.from({ length: 5 }, (_, i) => 0x1D372 + i),
    'ideographic-description': [...Array.from({ length: 16 }, (_, i) => 0x2FF0 + i), 0x31EF],
  };
  for (const [name, points] of Object.entries(sets)) {
    change('#source-filter', 'all');
    $('[data-filter="' + name + '"]').click();
    check(`${name} count`, $('#result-count').textContent.startsWith(`${counts[name]} `));
    const visible = () => $$('.glyph-button').map(button => Number(button.dataset.cp));
    const actual = visible();
    while (!$('#next-page').disabled) { $('#next-page').click(); actual.push(...visible()); }
    while (!$('#previous-page').disabled) $('#previous-page').click();
    check(`${name} includes existing related characters`, points.every(cp => actual.includes(cp)));
    check(`${name} pagination is complete`, actual.length === counts[name] && new Set(actual).size === counts[name]);
    if (name !== 'numerals') check(`${name} exact repertoire`, actual.every(cp => points.includes(cp)));
    change('#preset', name);
    check(`${name} sample has full coverage`, !$('#type-status').textContent.includes('outside this font'));
    check(`${name} sample has relevant characters`, [...$('#type-input').value].some(ch => points.includes(ch.codePointAt(0))));
    $('[data-direction="vertical"]').click();
    check(`${name} vertical sample`, getComputedStyle($('#type-input')).writingMode === 'vertical-rl');
    $('[data-direction="horizontal"]').click();
    check(`${name} horizontal sample`, getComputedStyle($('#type-input')).writingMode === 'horizontal-tb');
    change('#source-filter', 'genzui');
    check(`${name} constructed outlines`, $$('.glyph-button').length === (name === 'numerals' ? 0 : 5));
    change('#source-filter', 'jp');
    check(`${name} native Noto outlines`, $('#result-count').textContent.startsWith(`${name === 'numerals' ? 79 : name === 'tallies' ? 0 : 12} `));
  }
  change('#source-filter', 'all');
  $('[data-filter="numerals"]').click();
  change('#source-filter', 'cjk');
  check('imported twenty is a numeral', $$('.glyph-button').length === 1 && $('#detail-glyph').textContent === '卄' && $('#detail-source').textContent === 'Noto Serif CJK JP');
  change('#source-filter', 'all');
  $('[data-filter="historical"]').click();
  check('extended kana has its own scope', $('#result-count').textContent.startsWith('329 '));
  $('[data-filter="all"]').click();
  check('full font count unchanged', $('#result-count').textContent.startsWith('17,090 '));
  const audit = await fetch('downloads/kana-coverage.json').then(response => response.json());
  check('all description characters covered', audit.coverage['Ideographic description characters'].covered === 17 && audit.coverage['Ideographic description characters'].missing.length === 0);
  check('all ideographic tally marks covered', audit.coverage['Ideographic tally marks'].covered === 5);
  check('CJK numeral twenty covered', audit.coverage['CJK numeral twenty (U+5344)'].covered === 1);
  check('audit has no batch category', !Object.hasOwn(audit.coverage, 'Honkoku additions'));
  check('no horizontal page overflow', document.documentElement.scrollWidth <= innerWidth);
  return checks;
})()
