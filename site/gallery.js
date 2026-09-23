(() => {
  const $ = s => document.querySelector(s);
  const cards = [...document.querySelectorAll('.glyph-card')];
  // Font fallback extensions can freeze a reading line to its initial family.
  // Each line must keep inheriting the selected version from its sample.
  const followSampleFont = line => {
    const family = line.matches('.native') ? 'GenZui, serif' : 'inherit';
    if (line.style.getPropertyValue('font-family') !== family ||
        line.style.getPropertyPriority('font-family') !== 'important') {
      line.style.setProperty('font-family', family, 'important');
    }
  };
  const readingFonts = new MutationObserver(records => {
    for (const {target} of records) followSampleFont(target);
  });
  document.querySelectorAll('.reading > span, .wu-fixed, .native').forEach(line => {
    followSampleFont(line);
    readingFonts.observe(line, {attributes:true, attributeFilter:['style']});
  });
  function filter() {
    const value = $('#collection').value;
    for (const card of cards) card.hidden = !(value === 'all' || card.dataset.kind === value || value === 'revised' && card.dataset.revised === 'true');
    const count = cards.filter(card => !card.hidden).length;
    const names = {drawn:'drawn forms', small:'small adaptations', revised:'revised forms', all:'constructions'};
    $('#count').textContent = `${count} ${names[value]}`;
  }
  $('#collection').addEventListener('change', filter);
  $('#weight')?.addEventListener('change', e => {
    const bold = e.target.value === '700';
    document.body.classList.toggle('weight-bold', bold);
    const label = $('#weight-label');
    if (label) label.textContent = label.dataset[bold ? 'bold' : 'regular'];
  });
  $('#reading-size').addEventListener('input', e => {
    document.documentElement.style.setProperty('--reading', `${e.target.value}px`);
    $('#size-value').textContent = `${e.target.value} px`;
  });
  for (const [id, cls, inverse] of [['guides','guides-off',true],['overlay','overlay-on',false]]) {
    $('#' + id)?.addEventListener('change', e => document.body.classList.toggle(cls, inverse ? !e.target.checked : e.target.checked));
  }
  $('#wu-style').addEventListener('change', e => {
    const hooked = e.target.value === 'hooked';
    document.body.classList.toggle('hooked-on', hooked);
    if (!hooked) {
      const sample = $('#u1b11f .current');
      sample.classList.remove('is-previous');
      const button = sample.querySelector('.swap');
      if (button) showSwapState(sample, button);
    }
    $('#wu-setting').textContent = hooked ? 'Hooked WU · ss01 on' : 'Default form · ss01 off';
  });
  function showSwapState(sample, button) {
    const previous = sample.classList.contains('is-previous');
    button.setAttribute('aria-pressed', String(previous));
    sample.querySelector('.version-label').textContent = previous ? button.dataset.previous : button.dataset.current;
    const description = sample.querySelector('.variant-description');
    if (description) description.textContent = previous ? button.dataset.previousLabel : button.dataset.currentLabel;
    button.textContent = `Swap to ${previous ? button.dataset.current : button.dataset.previous}`;
  }
  document.querySelectorAll('.swap').forEach(button => {
    button.addEventListener('click', () => {
      const sample = button.closest('.sample');
      sample.classList.toggle('is-previous');
      showSwapState(sample, button);
    });
  });
  if (document.querySelector('.before')) document.fonts.load('40px Previous', '𛄣𛄟').catch(() => {});
  const target = document.getElementById(location.hash.slice(1));
  if (target?.matches('.glyph-card')) { $('#collection').value = target.dataset.kind; filter(); }
  else filter();
})();
