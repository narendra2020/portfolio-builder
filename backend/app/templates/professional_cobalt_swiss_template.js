(function(){
  const $ = (selector, context = document) => context.querySelector(selector);
  const $$ = (selector, context = document) => Array.from(context.querySelectorAll(selector));

  const menuToggle = $('.menu-toggle');
  const nav = $('.nav');
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      document.body.classList.toggle('no-scroll', open);
      menuToggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  const header = $('.site-header');
  const toTop = $('.to-top');
  const themeToggle = $('.theme-toggle');
  const THEME_STORAGE_KEY = 'tpl-cobalt-theme';

  if (themeToggle) {
    const applyTheme = (next) => {
      document.body.dataset.theme = next;
      localStorage.setItem(THEME_STORAGE_KEY, next);
      themeToggle.textContent = next === 'dark' ? 'Classic mode' : 'Dark mode';
    };
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'dark';
    applyTheme(savedTheme);
    themeToggle.addEventListener('click', () => {
      const current = document.body.dataset.theme === 'dark' ? 'dark' : 'classic';
      applyTheme(current === 'dark' ? 'classic' : 'dark');
    });
  }

  window.addEventListener('scroll', () => {
    if (header) header.classList.toggle('scrolled', window.scrollY > 40);
    if (toTop) toTop.classList.toggle('show', window.scrollY > 600);
  }, { passive: true });

  if (toTop) {
    toTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  }

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1 });
  $$('.reveal').forEach((el) => observer.observe(el));
})();
