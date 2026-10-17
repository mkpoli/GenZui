(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const input = OkinawanInput.createInput(JSON.parse($('okinawan-data').textContent));
  const source = $('okinawan-source'), output = $('okinawan-output');
  const system = $('okinawan-system'), method = $('okinawan-method');
  let composing = false;
  const drafts = {funatsu: 'とぅい　うとぅ　{' + "'ya" + '}ー', prefecture: 'ウトゥ　^uウトゥ'};
  let previousSystem = system.value;
  function update() {
    if (composing) return;
    const result = input.convert(source.value, system.value, method.value);
    output.value = result.text;
    $('okinawan-warning').textContent = result.warnings.join(' ');
    $('okinawan-codepoints').textContent = [...result.text].map(ch => 'U+' + ch.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')).join(' ');
    $('okinawan-copy-status').textContent = '';
  }
  function palette() {
    const fragment = document.createDocumentFragment();
    for (const entry of input.entries.filter(e => e.system === system.value)) {
      const button = document.createElement('button');
      button.type = 'button'; button.className = 'okinawan-key';
      const shortcut = `{${entry.id}}`;
      button.setAttribute('aria-label', `Insert ${entry.label}, ${shortcut}`);
      button.title = `${entry.label}: ${entry.output.map(cp => 'U+' + cp).join(' + ')}`;
      const glyph = document.createElement('span'); glyph.className = 'face'; glyph.lang = 'ryu'; glyph.textContent = input.text(entry); glyph.setAttribute('aria-hidden', 'true');
      const label = document.createElement('code'); label.textContent = shortcut;
      button.append(glyph, label);
      // Keep the editor's selection when using the mouse; keyboard activation
      // reads the textarea's retained selection and returns focus to the editor.
      button.addEventListener('mousedown', event => event.preventDefault());
      button.addEventListener('click', () => {
        source.setRangeText(shortcut, source.selectionStart, source.selectionEnd, 'end');
        source.focus(); update();
      });
      fragment.append(button);
    }
    $('okinawan-palette').replaceChildren(fragment);
    $('okinawan-funatsu-help').hidden = system.value !== 'funatsu';
    $('okinawan-prefecture-help').hidden = system.value !== 'prefecture';
  }
  source.addEventListener('input', update);
  function compositionState(active) {
    composing = active;
    document.querySelectorAll('#okinawan button, #okinawan select').forEach(control => { control.disabled = active; });
  }
  source.addEventListener('compositionstart', () => { compositionState(true); });
  source.addEventListener('compositionend', () => { compositionState(false); update(); });
  system.addEventListener('change', () => {
    drafts[previousSystem] = {value: source.value, method: method.value};
    const draft = drafts[system.value];
    source.value = typeof draft === 'string' ? draft : draft.value;
    method.value = typeof draft === 'string' ? 'kana' : draft.method;
    previousSystem = system.value; palette(); update();
  });
  method.addEventListener('change', update);
  $('okinawan-clear').addEventListener('click', () => { source.value = ''; source.focus(); update(); });
  $('okinawan-example').addEventListener('click', () => {
    source.value = system.value === 'funatsu' ? "tui utu {'ya}ー" : 'utu ^uutu';
    method.value = 'romaji'; update();
  });
  $('okinawan-copy').addEventListener('click', async () => {
    let copied = false;
    try { await navigator.clipboard.writeText(output.value); copied = true; } catch (_) {
      output.focus(); output.select();
      try { copied = document.execCommand('copy'); } catch (_) { /* Selection remains available. */ }
    }
    $('okinawan-copy-status').textContent = copied ? 'Copied.' : 'Select the result and copy it with Ctrl+C or ⌘C.';
  });
  source.value = drafts[system.value]; palette(); update();
})();
