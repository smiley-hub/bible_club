(() => {
  'use strict';
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-nav');
  if (menu && nav) {
    document.documentElement.classList.add('js-enabled');
    menu.hidden = false;
    const closeMenu = () => { nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); };
    menu.addEventListener('click', () => {
      const opened = nav.classList.toggle('is-open');
      menu.setAttribute('aria-expanded', String(opened));
    });
    nav.addEventListener('click', (event) => { if (event.target.closest('a')) closeMenu(); });
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && nav.classList.contains('is-open')) { closeMenu(); menu.focus(); }
    });
  }

  // Expand in-page details when a link points directly at a collapsed section.
  document.querySelectorAll('a[href^="#"]').forEach((link) => {
    link.addEventListener('click', () => {
      const target = document.getElementById(link.getAttribute('href').slice(1));
      if (target?.tagName === 'DETAILS') target.open = true;
    });
  });

  const carousel = document.querySelector('[data-slideshow]');
  if (!carousel) return;
  const slides = Array.from(carousel.querySelectorAll('[data-slide]'));
  if (slides.length < 2) return;
  const controls = carousel.querySelector('[data-controls]');
  const dots = Array.from(carousel.querySelectorAll('[data-go]'));
  const pause = carousel.querySelector('[data-pause]');
  const status = carousel.querySelector('[data-slide-status]');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let current = 0;
  let paused = reducedMotion.matches;
  let hovered = false;
  let timer;
  let pointerPausedState = null;
  controls.hidden = false;

  function updateTimer() {
    window.clearInterval(timer);
    pause.textContent = paused ? 'Play' : 'Pause';
    pause.setAttribute('aria-label', paused ? 'Start automatic photo slideshow' : 'Pause automatic photo slideshow');
    if (!paused && !hovered && !document.hidden) timer = window.setInterval(() => show(current + 1, false), 6500);
  }
  function show(index, manual = true) {
    slides[current].hidden = true;
    dots[current].removeAttribute('aria-current');
    current = (index + slides.length) % slides.length;
    slides[current].hidden = false;
    dots[current].setAttribute('aria-current', 'true');
    if (manual) {
      paused = true;
      status.textContent = `Photo ${current + 1} of ${slides.length}`;
      updateTimer();
    }
  }
  carousel.querySelector('[data-previous]').addEventListener('click', () => show(current - 1));
  carousel.querySelector('[data-next]').addEventListener('click', () => show(current + 1));
  dots.forEach((dot, index) => dot.addEventListener('click', () => show(index)));
  // Preserve state before focusin pauses the carousel on a pointer click.
  pause.addEventListener('pointerdown', () => { pointerPausedState = paused; });
  pause.addEventListener('pointercancel', () => { pointerPausedState = null; });
  pause.addEventListener('click', () => {
    paused = !(pointerPausedState ?? paused);
    pointerPausedState = null;
    updateTimer();
  });
  carousel.addEventListener('focusin', () => { paused = true; updateTimer(); });
  carousel.addEventListener('mouseenter', () => { hovered = true; updateTimer(); });
  carousel.addEventListener('mouseleave', () => { hovered = false; updateTimer(); });
  carousel.addEventListener('keydown', (event) => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
      event.preventDefault();
      show(current + (event.key === 'ArrowRight' ? 1 : -1));
    }
  });
  reducedMotion.addEventListener('change', () => { if (reducedMotion.matches) paused = true; updateTimer(); });
  document.addEventListener('visibilitychange', updateTimer);
  updateTimer();
})();
