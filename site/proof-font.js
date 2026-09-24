(() => {
  const historical = /[\u{1B000}-\u{1B16F}\u{2A708}\u{2CEFF}\u{2CF00}\u{2CF02}]/u;
  function protect(element) {
    if (!(element instanceof HTMLElement) || !element.closest('.face')) return;
    const root = element.matches('.face');
    if (!root && !historical.test(element.textContent)) return;
    const family = root ? `GenZui, ${document.body.dataset.fallback || 'serif'}` : 'inherit';
    if (element.style.getPropertyValue('font-family') !== family ||
        element.style.getPropertyPriority('font-family') !== 'important') {
      element.style.setProperty('font-family', family, 'important');
    }
  }
  function scan(root) {
    if (root instanceof HTMLElement) protect(root);
    root?.querySelectorAll?.('.face, .face *').forEach(protect);
    if (root instanceof HTMLElement && root.closest('.face')) root.querySelectorAll('*').forEach(protect);
  }
  scan(document.body);
  new MutationObserver(records => {
    for (const record of records) {
      if (record.type === 'attributes') protect(record.target);
      else if (record.type === 'characterData') protect(record.target.parentElement);
      else record.addedNodes.forEach(node => scan(node.nodeType === Node.TEXT_NODE ? node.parentElement : node));
    }
  }).observe(document.body, {subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:['style']});
})();
