(function(){
  const $ = (selector, context = document) => context.querySelector(selector);
  const $$ = (selector, context = document) => Array.from(context.querySelectorAll(selector));

  const menuToggle = $('.menu-toggle');
  const nav = $('.nav');
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      const visible = nav.classList.toggle('open');
      document.body.classList.toggle('no-scroll', visible);
      menuToggle.setAttribute('aria-expanded', visible ? 'true' : 'false');
      nav.style.display = visible ? 'flex' : '';
    });
    $$('a', nav).forEach((link) =>
      link.addEventListener('click', () => {
        nav.classList.remove('open');
        nav.style.display = '';
        document.body.classList.remove('no-scroll');
        menuToggle.setAttribute('aria-expanded', 'false');
      })
    );
  }

  const toTop = $('.to-top');
  const themeToggle = $('.theme-toggle');
  const THEME_STORAGE_KEY = 'tpl-sage-theme';

  if (themeToggle) {
    const applyTheme = (next) => {
      document.body.dataset.theme = next;
      localStorage.setItem(THEME_STORAGE_KEY, next);
      themeToggle.textContent = next === 'dark' ? 'Classic mode' : 'Dark mode';
    };
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'classic';
    applyTheme(savedTheme);
    themeToggle.addEventListener('click', () => {
      const current = document.body.dataset.theme === 'dark' ? 'dark' : 'classic';
      applyTheme(current === 'dark' ? 'classic' : 'dark');
    });
  }

  window.addEventListener('scroll', () => {
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
  }, { threshold: 0.12 });
  $$('.reveal').forEach((el) => observer.observe(el));
})();
