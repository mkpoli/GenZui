// The Sponsor dialog. A click on the backdrop closes it; one on its own scrollbar also
// targets the dialog, so only a click outside its box counts. The browser returns focus
// to the pill when the dialog closes.
(() => {
  const dialog = document.querySelector('#sponsor-dialog');
  if (!dialog) return;
  document.querySelectorAll('.sp-pill').forEach(pill => pill.addEventListener('click', () => dialog.showModal()));
  dialog.querySelector('.sp-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target !== dialog) return;
    const box = dialog.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) dialog.close();
  });
})();
