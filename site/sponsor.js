// The Sponsor dialog. A click on the backdrop closes it; one on its own scrollbar also
// targets the dialog, so only a click outside its box counts. The browser returns focus
// to the pill when the dialog closes. The supporters roll and its script load the first
// time the dialog opens, so a page view does not reach the roll's service.
(() => {
  const dialog = document.querySelector('#sponsor-dialog');
  if (!dialog) return;
  let rollLoaded = false;
  const loadRoll = () => {
    if (rollLoaded) return;
    rollLoaded = true;
    const roll = document.createElement('supporters-roll');
    roll.setAttribute('label', 'Recent supporters');
    roll.setAttribute('anonymous', 'Someone');
    dialog.querySelector('.sp-thanks').before(roll);
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://supporters.mkpo.li/roll.js';
    document.head.append(script);
  };
  document.querySelectorAll('.sp-pill').forEach(pill => pill.addEventListener('click', () => { dialog.showModal(); loadRoll(); }));
  dialog.querySelector('.sp-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
})();
