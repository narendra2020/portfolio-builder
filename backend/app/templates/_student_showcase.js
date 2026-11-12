(function(){
  const root = document.documentElement;
  const themeKey = document.body.dataset.themeKey;
  const themeToggle = document.querySelector('.theme-toggle');

  if (themeToggle) {
    const syncLabel = () => {
      themeToggle.textContent = root.dataset.theme === 'dark' ? 'Classic mode' : 'Dark mode';
    };
    syncLabel();
    themeToggle.addEventListener('click', () => {
      root.dataset.theme = root.dataset.theme === 'dark' ? 'classic' : 'dark';
      try { localStorage.setItem(themeKey, root.dataset.theme); } catch (e) {}
      syncLabel();
    });
  }

  const menu = document.querySelector('.menu');
  const nav = document.querySelector('nav');
  if (menu && nav) {
    menu.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      menu.setAttribute('aria-expanded', String(open));
    });
    nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
      nav.classList.remove('open');
      menu.setAttribute('aria-expanded', 'false');
    }));
  }

  const dialog = document.querySelector('dialog');
  if (dialog) {
    const details = dialog.querySelector('.details');
    document.querySelectorAll('.project-open').forEach((button) => button.addEventListener('click', () => {
      const source = button.closest('.card-body').querySelector('.project-details');
      details.innerHTML = source ? source.innerHTML : '';
      dialog.showModal();
    }));
    dialog.querySelector('.dialog-close').addEventListener('click', () => dialog.close());
    dialog.addEventListener('click', (e) => {
      if (e.target !== dialog) return;
      const r = dialog.getBoundingClientRect();
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dialog.close();
    });
  }
})();
