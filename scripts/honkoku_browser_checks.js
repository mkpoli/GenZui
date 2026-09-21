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
  if (new URLSearchParams(location.search).get('sample') === 'honkoku') {
    check('honkoku permalink selects preset', $('#preset').value === 'honkoku');
    check('honkoku permalink selects inventory', $('[data-filter="honkoku"]').getAttribute('aria-pressed') === 'true');
  }
  $('[data-filter="honkoku"]').click();
  const points = [0x5344, 0x1D372, 0x1D373, 0x1D374, 0x1D375, 0x1D376, 0x2FFC, 0x2FFD, 0x2FFE, 0x2FFF, 0x31EF];
  const actual = $$('.glyph-button').map(button => Number(button.dataset.cp));
  check('exactly eleven honkoku additions', actual.length === points.length && points.every(cp => actual.includes(cp)));
  for (const cp of points) {
    $(`.glyph-button[data-cp="${cp}"]`).click();
    check(`source of U+${cp.toString(16).toUpperCase()}`, $('#detail-source').textContent === (cp === 0x5344 ? 'Noto Serif CJK JP' : 'GenZui construction'));
    check(`description of U+${cp.toString(16).toUpperCase()}`, $('#detail-description').textContent.length > 30);
  }
  change('#source-filter', 'cjk');
  check('CJK source isolates twenty', $$('.glyph-button').length === 1 && $('#detail-glyph').textContent === '卄');
  change('#source-filter', 'genzui');
  check('ten constructed honkoku symbols', $$('.glyph-button').length === 10);
  change('#source-filter', 'all');
  change('#preset', 'honkoku');
  check('sample includes all eleven', points.every(cp => $('#type-input').value.includes(String.fromCodePoint(cp))));
  check('sample has full coverage', !$('#type-status').textContent.includes('outside this font'));
  $('[data-direction="vertical"]').click();
  check('vertical honkoku sample', getComputedStyle($('#type-input')).writingMode === 'vertical-rl');
  $('[data-direction="horizontal"]').click();
  check('horizontal honkoku sample', getComputedStyle($('#type-input')).writingMode === 'horizontal-tb');
  const audit = await fetch('downloads/kana-coverage.json').then(response => response.json());
  check('all 17 description characters covered', audit.coverage['Ideographic description characters'].covered === 17 && audit.coverage['Ideographic description characters'].missing.length === 0);
  check('all five tally marks covered', audit.coverage['Ideographic tally marks'].covered === 5);
  check('honkoku count agrees with audit', audit.coverage['Honkoku additions'].covered === 11);
  check('CJK source licence included', (await fetch('downloads/NotoSerifCJK-OFL.txt').then(response => response.text())).includes('SIL OPEN FONT LICENSE Version 1.1'));
  check('no horizontal page overflow', document.documentElement.scrollWidth <= innerWidth);
  return checks;
})()
