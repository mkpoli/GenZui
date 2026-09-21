// ==UserScript==
// @name         Historical kana font fallback
// @namespace    urn:historical-kana:font-fallback
// @version      0.2.0
// @license      MIT
// @description  Display historical kana using installed GenSeki Hentaigana Gothic, restricted to their Unicode ranges.
// @match        https://*/*
// @match        http://*/*
// @grant        GM_addStyle
// @run-at       document-start
// ==/UserScript==

(() => {
  'use strict';

  const family = 'Historical Kana Local Fallback';
  const ranges = 'U+3099-309A,U+1B000-1B128,U+1B132,U+1B150-1B152,' +
    'U+1B155,U+1B164-1B168,U+2A708,U+2CEFF,U+2CF00,U+2CF02';
  const historical = /[\u{1B000}-\u{1B128}\u{1B132}\u{1B150}-\u{1B152}\u{1B155}\u{1B164}-\u{1B168}\u{2A708}\u{2CEFF}\u{2CF00}\u{2CF02}]/u;

  GM_addStyle(`
    @font-face {
      font-family: "${family}";
      src: local("GenSeki Hentaigana Gothic"), local("GenSekiHentaiganaGothic");
      font-weight: 400;
      font-style: normal;
      unicode-range: ${ranges};
    }
    @font-face {
      font-family: "${family}";
      src: local("GenSeki Hentaigana Gothic Bold"), local("GenSekiHentaiganaGothic-Bold");
      font-weight: 700;
      font-style: normal;
      unicode-range: ${ranges};
    }
  `);

  function apply(element, text) {
    if (!element?.style || !historical.test(text)) return;
    if (element.matches('input[type="password"]')) return;
    if (element.closest('script, style, noscript, template')) return;
    const original = getComputedStyle(element).fontFamily;
    if (original.includes(family)) return;
    // A generic family can select a missing-glyph face before later fonts.
    // The Unicode range keeps this priority limited to historical kana.
    element.style.setProperty('font-family', `"${family}", ${original}`, 'important');
  }

  function visit(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      apply(root.parentElement, root.nodeValue || '');
      return;
    }
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) apply(walker.currentNode.parentElement, walker.currentNode.nodeValue || '');
    const inputs = 'input:not([type="password"]), textarea';
    if (root.matches?.(inputs)) apply(root, root.value || '');
    root.querySelectorAll?.(inputs).forEach(element => apply(element, element.value || ''));
  }

  const pending = new Set();
  let scheduled = false;
  function schedule(root) {
    pending.add(root);
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      for (const node of pending) if (node.isConnected) visit(node);
      pending.clear();
    });
  }

  function start() {
    visit(document.body);
    new MutationObserver(records => {
      for (const record of records) {
        if (record.type === 'characterData') schedule(record.target);
        else record.addedNodes.forEach(schedule);
      }
    }).observe(document.body, {subtree: true, childList: true, characterData: true});
    document.addEventListener('input', event => {
      if (event.target.matches?.('input[type="password"]')) return;
      if (typeof event.target.value === 'string') apply(event.target, event.target.value);
    }, true);
  }

  if (document.body) start();
  else document.addEventListener('DOMContentLoaded', start, {once: true});
})();
